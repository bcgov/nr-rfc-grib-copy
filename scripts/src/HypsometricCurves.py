import datetime
import os
import datetime
import pandas as pd
import numpy as np
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
import rasterio
import rasterio.mask
import geopandas

from arcgis.gis import GIS
from arcgis.features import FeatureLayer
#from IPython.display import display
gis = GIS()

feature_url = "https://services6.arcgis.com/ubm4tcTYICKBpist/ArcGIS/rest/services/Snow_Basins_Indices_View/FeatureServer/0"
feature_layer = FeatureLayer(feature_url)
feature_set = feature_layer.query()
feature_geojson = feature_set.to_geojson
snow_basins_shp = geopandas.read_file(feature_geojson)
snow_basins_shp = snow_basins_shp.to_crs("EPSG:3979")

ostore = NRObjStoreUtil.ObjectStoreUtil()
clever_shp_path = 'data/shape/CLEVER/CLEVER_BASINS.shp'
clever_shp = geopandas.read_file(clever_shp_path)
clever_shp = clever_shp.to_crs("EPSG:3979")
cog_path = "https://datacube-prod-data-public.s3.ca-central-1.amazonaws.com/store/elevation/mrdem/mrdem-30/mrdem-30-dtm.tif"

def ecdf(a):
    x, counts = np.unique(a, return_counts=True)
    cusum = np.cumsum(counts)
    return x, np.round(cusum / cusum[-1],5)

def elevation_ecdf(shapes, names_col, obj_dir):
       names = shapes.loc[:,names_col]
       for i in range(len(names)):
        colname = names[i]
        try:
                output_path = f"data/DEM/mrdem_bc_{names[i]}.tif"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                vector = shapes.iloc[i].geometry
                with rasterio.open(cog_path) as src:
                        #window = src.window(min_x, min_y, max_x, max_y)
                        #raster_data = src.read(window=window)
                        raster_data=rasterio.mask.mask(src,[vector],crop=True)

                raster_data = raster_data.astype(int)
                elevation_data = raster_data[raster_data>=0]
                elevation_data = 10*np.round(elevation_data/10).astype(int)
                x, cdf = ecdf(elevation_data)

                ecdf_df = pd.DataFrame(data = cdf, index=x, columns=[colname])
                fname = f"data/ECDF/{colname}_ECDF.csv"
                oname = os.path.join(obj_dir,f"{colname}_ECDF.csv")
                os.makedirs(os.path.dirname(fname), exist_ok=True)
                ecdf_df.to_csv(fname, index_label="Elevation")
                ostore.put_object(local_path=fname, ostore_path=oname)
        except:
               print(f"{colname} failed")

#names_col = "WSDG_ID"
#obj_dir = "Spatial_Files/DEM/ECDF/CLEVER"
#elevation_ecdf(clever_shp, names_col, obj_dir)

names_col = "basinName"
obj_dir = "Spatial_Files/DEM/ECDF/SnowBasins"
elevation_ecdf(snow_basins_shp, names_col, obj_dir)



# min_x = int(clever_bounds.minx.min()) - 1
# min_y = int(clever_bounds.miny.min()) - 1
# max_x = int(clever_bounds.maxx.max()) + 1
# max_y = int(clever_bounds.maxy.max()) + 1

# objpath = "objectstore2.nrs.bcgov/RSImgShare/MRDEM/mrdem-30-dtm-bc.tif"
        # with rasterio.open(objpath) as src:
        #     raster_data = src.read()