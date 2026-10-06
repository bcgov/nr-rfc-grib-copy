import datetime
import pandas as pd
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
import geopandas as gpd
import io
import zipfile
import requests
from exactextract import exact_extract
import re

ostore_path = 'RFC_DATA/SMAP/'
ostore = NRObjStoreUtil.ObjectStoreUtil()
ostore_objs = ostore.list_objects(ostore_path,return_file_names_only=True)
# Ensure our local processing directory exists
local_dir = "./temp_smap"
os.makedirs(local_dir, exist_ok=True)
os.makedirs("./smap_tiffs", exist_ok=True)

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

def parse_date_from_key(key):
    """Extracts date from S3 object key (e.g., 'folder/2026_09_22_sm_surface.tif')"""
    filename = os.path.basename(key)
    match = re.search(r'_\d{8}T', filename)
    if not match:
        return None
    return datetime.datetime.strptime(match.group(), "_%Y%m%dT").date()

def process_s3_raster(local_path, file_date):
    id_col = "BasinName"
    stats = exact_extract(local_path, gdf, ['mean'], include_cols=[id_col])

    # Format into a clean DataFrame
    df = pd.DataFrame(stats)
    df_flat = pd.json_normalize(df['properties'])

    df_flat.rename(columns={'mean': 'sm_surface_mean', id_col: 'basin_id'}, inplace=True)
    df_flat['date'] = file_date

    return df_flat[['date', 'basin_id', 'sm_surface_mean']]


def load_drought_boundaries():
    """
    Downloads and loads the BC drought basin boundaries shapefile into a GeoDataFrame.
    Returns:
        gdf (GeoDataFrame): The loaded drought basin boundaries.
    """
    clever_shp_path = 'data/shape/Drought/BC_Drought_Basins.shp'
    gdf = gpd.read_file(clever_shp_path)
    gdf = gdf.rename(columns={'BasinNm': 'BasinName'})
    return gdf.to_crs(epsg=4326)
    """
    # The direct download URL you provided
        url = "https://catalogue.data.gov.bc.ca/dataset/c4f3c7dd-d30e-42a3-a73d-373e72d6a906/resource/4df74124-baae-4040-9469-ff57aac54e37/download/bc_drought_basin_boundaries.zip"

        print("Downloading drought boundaries...")
        response = requests.get(url)

        if response.status_code == 200:
            # Read the zipped bytes directly into Geopandas without saving to disk
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Geopandas can read directly from a zip file buffer using the zip:// syntax
                gdf = gpd.read_file(io.BytesIO(response.content))

            print("Success! Data loaded into GeoDataFrame.")

            # 1. Load Polygons & Match Raster CRS (EPSG:4326)
            # Replace 'bc_drought_basin_boundaries.zip' with your source file path
            gdf = gdf.to_crs(epsg=4326)

            print(gdf.head())  # Inspect the first few rows
            return gdf
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return None
    """


gdf = load_drought_boundaries()


# Authenticate with NASA Earthdata
auth = earthaccess.login(strategy="environment")

# Define your target bounding box coordinates for cropping
lon_min, lat_min, lon_max, lat_max = -140, 48, -114, 60
# Official global grid extents (SMAP grid edge coordinates in EPSG:6933)
#xmin, xmax, ymin, ymax = -17367530.45, 17367530.45, -7314540.83, 7314540.83

# Define the variables you want to extract
target_variables = ["sm_surface", "sm_rootzone", "surface_temp"]

current_date = datetime.datetime.now()
start_date = (current_date - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
end_date = current_date.strftime('%Y-%m-%d')
#start_date = "2024-08-08"
#end_date = "2024-08-14"
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


print_memory_diagnostics("SCRIPT START")

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



# --- CONFIGURATION ---
BUCKET_NAME = "rfcdata"
PREFIX = "RFC_DATA/SMAP/"  # The folder containing the variables
MASTER_FILE = "drought_sm_surface_summary.parquet"

# Initialize Cloud Storage Client (Configure environment variables for credentials)
#s3_client = ostore.createBotoClient()

# --- STEP 1: HISTORICAL BACKFILL & OPERATIONAL STREAMING ---
ostore_objs = ostore.list_objects(ostore_path,return_file_names_only=True)

# Filter targets ending in 'sm_surface.tif' (or variations like 'sm_surface')
target_keys = []
for key in ostore_objs:
    if key.endswith('sm_surface.tif'):
        target_keys.append(key)

print(f"Found {len(target_keys)} relevant 'sm_surface' files.")

# Load existing tracking data to avoid re-processing files during daily runs
processed_dates = set()
objstore_summary = [key for key in ostore_objs if MASTER_FILE in key]
local_summary_path = os.path.join(local_dir, MASTER_FILE)
if objstore_summary:
    print(f"Found existing summary file in object store: {objstore_summary[0]}")
    # Download the existing summary file to local disk for processing
    ostore.get_object(local_path=local_summary_path, file_path=objstore_summary[0])
if os.path.exists(local_summary_path):
    existing_df = pd.read_parquet(local_summary_path)
    processed_dates = set(existing_df['date'].unique())

# Process and append data loop
new_records = []
for key in sorted(target_keys):
    file_date = parse_date_from_key(key)
    if file_date in processed_dates:
        continue  # Skip files we have already processed historically

    # Generate temporary local filepath
    local_filename = f"temp_{file_date}_sm_surface.tif"
    local_path = os.path.join(local_dir, local_filename)
    print(f"Processing cloud raster for date: {file_date}...")
    try:
        ostore.get_object(local_path=local_path, file_path=key)
        df_day = process_s3_raster(local_path, file_date)
        if df_day is not None:
            new_records.append(df_day)
    except Exception as e:
        print(f"Failed processing {key}: {e}")
    finally:
        # CRITICAL: Clean up the local disk space immediately after processing
        if os.path.exists(local_path):
            os.remove(local_path)

# Append any newly found data to the master Parquet file
if new_records:
    df_new_all = pd.concat(new_records, ignore_index=True)
    if os.path.exists(local_summary_path):
        df_final = pd.concat([existing_df, df_new_all], ignore_index=True)
    else:
        df_final = df_new_all

    df_final.to_parquet(local_summary_path, index=False)
    # Upload the updated summary back to object storage
    ostore.put_object(local_path=local_summary_path, ostore_path=os.path.join(ostore_path, MASTER_FILE))
    print(f"Saved update to {MASTER_FILE}")
else:
    ostore.put_object(local_path=local_summary_path, ostore_path=os.path.join(ostore_path, MASTER_FILE))
    print("Database is completely up to date. No new files found.")




