import os
import sys
import earthaccess
import xarray as xr
import rioxarray
#from rasterio.transform import from_bounds
import h5netcdf
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
import gc
import psutil

#import h5py
def print_memory_diagnostics(label=""):
    """Prints current Python process memory and system-wide available RAM."""
    process = psutil.Process(os.getpid())
    process_ram = process.memory_info().rss / (1024 ** 3)  # Convert to GB

    sys_mem = psutil.virtual_memory()
    sys_available = sys_mem.available / (1024 ** 3)       # Convert to GB
    sys_percent = sys_mem.percent

    print(f"--- [RAM DIAGNOSTIC - {label}] ---")
    print(f"    Script RAM usage: {process_ram:.3f} GB")
    print(f"    System RAM Free : {sys_available:.3f} GB ({sys_percent}% Used)")
    print("---------------------------------")

# Authenticate with NASA Earthdata
auth = earthaccess.login(strategy="environment")

# Define your target bounding box coordinates for cropping
lon_min, lat_min, lon_max, lat_max = -140, 48, -114, 60
# Official global grid extents (SMAP grid edge coordinates in EPSG:6933)
#xmin, xmax, ymin, ymax = -17367530.45, 17367530.45, -7314540.83, 7314540.83

# Define the variables you want to extract
target_variables = ["sm_surface", "sm_rootzone", "surface_temp"]

start_date = "2024-05-08"
end_date = "2024-05-10"
if len(sys.argv) > 1:
        start_date = sys.argv[1]
if len(sys.argv) > 2:
        end_date = sys.argv[2]
# 1. Search for 19Z granules
results = earthaccess.search_data(
    short_name="SPL4SMGP",
    temporal=(start_date, end_date),
    bounding_box=(lon_min, lat_min, lon_max, lat_max),
    granule_name="*T19*"
)

print(f"Found {len(results)} files to stream.")

# 2. Open data streams from NASA servers without downloading raw files
# earthaccess.open returns python file-like objects pointing directly to the cloud
file_streams = earthaccess.open(results, provider="NSIDC_ECS")

os.makedirs("./smap_tiffs", exist_ok=True)

ostore_path = 'RFC_DATA/SMAP/'
ostore = NRObjStoreUtil.ObjectStoreUtil()
ostore_objs = ostore.list_objects(ostore_path,return_file_names_only=True)

print_memory_diagnostics("SCRIPT START")

for i, f_stream in enumerate(file_streams):
    granule_name = os.path.basename(f_stream.path)
    base_name = granule_name.split(".")[0]
    extension = granule_name.split(".")[-1]

    if extension != "h5":
        print(f"Skipping non-HDF5 file: {granule_name}")
        continue

    print(f"Processing in-memory: {granule_name}")

    try:
        # 1. Open the root for coordinates and the Geophysical group TOGETHER
        # Using a single context manager stops memory leaks from streaming data
        with xr.open_dataset(f_stream, engine="h5netcdf", phony_dims='access') as ds_coords, \
             xr.open_dataset(f_stream, group="Geophysical_Data", engine="h5netcdf", phony_dims='access') as ds_data:

            # Load coordinates once per file
            native_x = ds_coords["x"].values
            native_y = ds_coords["y"].values

            # 2. Loop through your target variables using the already open dataset
            for var_name in target_variables:
                if var_name not in ds_data:
                    print(f" -> Variable {var_name} not found in {granule_name}")
                    continue

                filename = f"{base_name}_{var_name}.tif"
                output_tif = f"./smap_tiffs/{filename}"
                obj_path = os.path.join(ostore_path, filename)

                # OPTIMIZATION: Skip processing entirely if it already exists in object storage
                if obj_path in ostore_objs:
                    print(f" -> Skipping (already in ostore): {filename}")
                    continue

                # Pull out just the array data values directly (saves RAM over .load())
                da_val = ds_data[var_name].values

                da = xr.DataArray(
                    data=da_val,
                    dims=["y", "x"],
                    coords={"x": native_x, "y": native_y}
                )

                # 3. Spatial operations using rioxarray
                da = da.rio.write_crs("EPSG:6933")
                da = da.rio.set_spatial_dims("x", "y")

                # Subset (clip) to your bounding box
                subset = da.rio.clip_box(
                    minx=lon_min,
                    miny=lat_min,
                    maxx=lon_max,
                    maxy=lat_max,
                    crs="EPSG:4326"
                )

                # Reproject and save
                subset_4326 = subset.rio.reproject("EPSG:4326")
                subset_4326.rio.to_raster(output_tif)

                # 4. Upload to Object Store and clean up file
                ostore.put_object(local_path=output_tif, ostore_path=obj_path)
                if os.path.exists(output_tif):
                    os.remove(output_tif)

                print(f" -> Saved & Uploaded: {filename}")

    except Exception as e:
        print(f"Error processing file {granule_name}: {e}")

    # Explicitly clear file-level references and flush memory back to the OS
    del native_x, native_y
    gc.collect()
    print_memory_diagnostics(f"FINISHED FILE [{i}]")

print("Processing complete! Raw HDF5 files were never saved to disk.")
