import os
import earthaccess
import xarray as xr
import rioxarray
#from rasterio.transform import from_bounds
import h5netcdf
import NRUtil.NRObjStoreUtil as NRObjStoreUtil

#import h5py

# Authenticate with NASA Earthdata
auth = earthaccess.login(strategy="environment")

# Define your target bounding box coordinates for cropping
lon_min, lat_min, lon_max, lat_max = -140, 48, -114, 60
# Official global grid extents (SMAP grid edge coordinates in EPSG:6933)
#xmin, xmax, ymin, ymax = -17367530.45, 17367530.45, -7314540.83, 7314540.83

# Define the variables you want to extract
target_variables = ["sm_surface", "sm_rootzone", "surface_temp"]

# 1. Search for 19Z granules
results = earthaccess.search_data(
    short_name="SPL4SMGP",
    temporal=("2026-01-01", "2026-08-20"),
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

for i, f_stream in enumerate(file_streams):
    # Extract filename information for the output
    granule_name = os.path.basename(f_stream.path)
    base_name = granule_name.split(".")[0]
    extension = granule_name.split(".")[-1]
    if extension != "h5":
        print(f"Skipping non-HDF5 file: {granule_name}")
        continue

    print(f"Processing in-memory: {granule_name}")

    # 4. Read the corresponding grid coordinate pairs to geolocate the pixels
    with xr.open_dataset(f_stream, engine="h5netcdf") as ds_coords:
        # 1. Grab the coordinates from the root level
        native_x = ds_coords["x"].load().values
        native_y = ds_coords["y"].load().values

    # 4. Loop through each variable to process and save them separately
    for var_name in target_variables:
        filename = f"{base_name}_{var_name}.tif"
        output_tif = f"./smap_tiffs/{filename}"

        #da = raw_data[var_name]
        with xr.open_dataset(f_stream, group="Geophysical_Data", engine="h5netcdf") as ds:
            da = ds[var_name].load()
        da = xr.DataArray(
                 data=da.values,
                 dims=["y", "x"],
                 coords={"x": native_x, "y": native_y}
             )
        #ny, nx = da.shape
        #transform = from_bounds(xmin, ymin, xmax, ymax, nx, ny)

        # 5. Georeference, Crop, and Reproject into EPSG:4326 using rioxarray
        da = da.rio.write_crs("EPSG:6933")
        #da = da.rio.write_transform(transform)
        da = da.rio.set_spatial_dims("x", "y")

        # 4. Reproject the matrix safely into standard WGS84 Geographic coordinates
        da_4326 = da.rio.reproject("EPSG:4326")

        # Subset (clip) the array down exclusively to your bounding box limits
        subset = da_4326.rio.clip_box(
            minx=lon_min,
            miny=lat_min,
            maxx=lon_max,
            maxy=lat_max
        )

        # 6. Save the final processed raster directly to disk
        subset.rio.to_raster(output_tif)
        da.rio.to_raster(f"./smap_tiffs/test.tif")
        obj_path = os.path.join(ostore_path,filename)
        if obj_path not in ostore_objs:
            ostore.put_object(local_path=output_tif, ostore_path=obj_path)
            os.remove(output_tif)
        print(f" -> Saved: {output_tif}")

print("Processing complete! Raw HDF5 files were never saved to disk.")
