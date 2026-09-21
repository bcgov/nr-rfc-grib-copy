import multiprocessing
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

start_date = "2024-08-08"
end_date = "2024-08-14"
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
local_dir = "./temp_smap"
os.makedirs(local_dir, exist_ok=True)

ostore_path = 'RFC_DATA/SMAP/'
ostore = NRObjStoreUtil.ObjectStoreUtil()
ostore_objs = ostore.list_objects(ostore_path,return_file_names_only=True)

print_memory_diagnostics("SCRIPT START")


def process_single_file(f_stream, i):
    granule_name = os.path.basename(f_stream.path)
    base_name = granule_name.split(".")[0]
    extension = granule_name.split(".")[-1]

    if extension != "h5":
        print(f"Skipping non-HDF5 file: {granule_name}")
        return

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

    # === FORCE MEMORY FLUSH & DEEP CACHE RESET ===
    # 1. Clear any local data variables
    if 'native_x' in locals(): del native_x
    if 'native_y' in locals(): del native_y

    # 2. Reset rioxarray/rasterio's underlying GDAL state cache
    try:
        # Destroys the persistent thread-local cache built up by spatial operations
        rioxarray._io.clean_spatial_dims()
    except:
        pass

    # 3. Force Close Xarray Backend caching managers
    try:
        xr.backends.file_manager.FILE_CACHE.clear()
    except:
        pass
    gc.collect()
    print_memory_diagnostics(f"FINISHED FILE [{i}]")


# Ensure our local processing directory exists
local_dir = "./temp_smap"
os.makedirs(local_dir, exist_ok=True)
os.makedirs("./smap_tiffs", exist_ok=True)

# Loop through the raw results list instead of streaming
for idx, granule in enumerate(results):
    print(f"\n==================================================")
    print(f"FILE [{idx+1}/{len(results)}]: Downloading to disk...")

    # 1. Download EXACTLY ONE file to your runner's disk
    downloaded_files = earthaccess.download(granule, local_path=local_dir)

    if not downloaded_files:
        print(f" -> Skip: Download failed or empty granule metadata.")
        continue

    # earthaccess returns a list of local file path strings
    local_file_path = downloaded_files[0]
    granule_name = os.path.basename(local_file_path)
    base_name = granule_name.split(".")[0]

    print(f" -> Downloaded locally to: {local_file_path}")
    print(f" -> Processing structures...")

    try:
        # 2. Open via the file string path (no fsspec memory tracking leak)
        with xr.open_dataset(local_file_path, engine="h5netcdf", phony_dims='access') as ds_coords, \
             xr.open_dataset(local_file_path, group="Geophysical_Data", engine="h5netcdf", phony_dims='access') as ds_data:

            native_x = ds_coords["x"].values
            native_y = ds_coords["y"].values

            for var_name in target_variables:
                if var_name not in ds_data:
                    continue

                filename = f"{base_name}_{var_name}.tif"
                output_tif = f"./smap_tiffs/{filename}"
                obj_path = os.path.join(ostore_path, filename)

                # Check object storage before running intensive coordinates re-projection
                if obj_path in ostore_objs:
                    print(f"    -> Skipping {var_name}: Already exists in ostore.")
                    continue

                da_val = ds_data[var_name].values
                da = xr.DataArray(
                    data=da_val,
                    dims=["y", "x"],
                    coords={"x": native_x, "y": native_y}
                )

                da = da.rio.write_crs("EPSG:6933")
                da = da.rio.set_spatial_dims("x", "y")

                # Crop down to coordinates bounding box
                subset = da.rio.clip_box(
                    minx=lon_min, miny=lat_min, maxx=lon_max, maxy=lat_max,
                    crs="EPSG:4326"
                )

                # Project matrix out to standard geographic maps
                subset_4326 = subset.rio.reproject("EPSG:4326")
                subset_4326.rio.to_raster(output_tif)

                # Push to Object Store
                ostore.put_object(local_path=output_tif, ostore_path=obj_path)

                # Delete temporary tiff slice immediately
                if os.path.exists(output_tif):
                    os.remove(output_tif)

                print(f"    -> Processed & uploaded: {filename}")

                # Inline clean inside the variable loop
                del da, da_val, subset, subset_4326
                gc.collect()

    except Exception as e:
        print(f"!!! Error processing granule {granule_name}: {e}")

    # 3. ABSOLUTE SYSTEM CLEANUP FOR THE ITERATION
    # Close out explicit variables
    if 'native_x' in locals(): del native_x
    if 'native_y' in locals(): del native_y

    # Wipe the physical HDF5 file from disk so the runner's storage doesn't cap
    if os.path.exists(local_file_path):
        try:
            os.remove(local_file_path)
            print(f" -> Cleaned up physical file from disk.")
        except Exception as disk_err:
            print(f" -> Warning: Could not delete local file: {disk_err}")

    # Flush all underlying xarray backend engines out of memory
    try:
        xr.backends.file_manager.FILE_CACHE.clear()
        import rioxarray
        rioxarray._io.clean_spatial_dims()
    except:
        pass

    gc.collect()
    print_memory_diagnostics(f"FINISHED FILE [{idx}]")
    print(f"==================================================")


print("Processing complete! Raw HDF5 files were never saved to disk.")
