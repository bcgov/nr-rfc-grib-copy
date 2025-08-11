import datetime
import os
import sys
import datetime
import pandas as pd
import numpy as np
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
import rasterio
import geopandas
import rasterstats
import logging
import logging.config

log_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config')
logging.config.fileConfig(log_config_path)

LOGGER = logging.getLogger(__name__)

def objstore_to_df(objpath, local_path = None):
    LOGGER.info(f"Fetching {objpath} from object storage")
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    local_folder = 'raw_data/temp_file'
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    if not local_path:
        local_path = os.path.join(local_folder,filename)
    ostore.get_object(local_path=local_path, file_path=objpath)
    match filetype:
        case 'csv':
            output = pd.read_csv(local_path)
        case 'parquet':
            output = pd.read_parquet(local_path)
    os.remove(local_path)

    return output

def df_to_objstore(df, objpath, onprem=False):
    LOGGER.info(f"Writing {objpath} to object storage")
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    if onprem:
        local_path = objpath
    else:
        local_folder = 'raw_data/temp_file'
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)
        local_path = os.path.join(local_folder,filename)
    match filetype:
        case 'csv':
            df.to_csv(local_path)
        case 'parquet':
            df.to_parquet(local_path)
    if not onprem:
        ostore.put_object(local_path=local_path, ostore_path=objpath)
        os.remove(local_path)

def update_data(data, newdata):
    #Add extra columns for any stations not already in dataframe:
    if len(data.columns)>0:
        old_col = set(data.columns)
        new_col = [x for x in newdata.columns if x not in old_col]
    else:
        new_col = newdata.columns
    if len(new_col)>0:
        new_col_df = pd.DataFrame(data=None,index=data.index,columns=new_col)
        data = pd.concat([data,new_col_df],axis=1)
    index_intersect = data.index.intersection(newdata.index)
    #newdata = newdata.loc[index_intersect]
    #data.loc[newdata.index,newdata.columns]=newdata
    data.loc[index_intersect,newdata.columns]=newdata.loc[index_intersect]

    return data

def get_summary(summary_fpath, year):
    summary_folder = os.path.dirname(summary_fpath)
    ostore_objs = ostore.list_objects(summary_folder,return_file_names_only=True)
    if summary_fpath not in ostore_objs:
        dt_range = pd.date_range(start = f'{year}/1/1', end = f'{year}/12/31', freq = 'D')
        summary = pd.DataFrame(data=None,index=dt_range,columns=None,dtype='float64')
    else:
        summary = objstore_to_df(summary_fpath)
        summary = summary.set_index(summary.columns[0])
        summary.index = pd.to_datetime(summary.index)
    return summary

def watershed_forecast_averaging(file_list, zone, output, type = 'forecast'):
    output = output.copy()
    colnames = output.columns
    LOGGER.info(f"Starting function watershed_forecast_averaging, type = {type}")
    for i in range(len(file_list)):
        if type == 'forecast':
            local_path = os.path.join('raw_data/gribs',file_list[i].split('/')[-1])
            splitpath = local_path.split('_')
            hr = int(splitpath[-1][1:4])
            yr = int(splitpath[-2][0:4])
            mn = int(splitpath[-2][4:6])
            dy = int(splitpath[-2][6:8])
            run_hr = int(splitpath[-2][8:10])
            dt = datetime.datetime(yr,mn,dy) + datetime.timedelta(hours=(hr+run_hr-8))
        elif type == 'gfs':
            local_path = os.path.join('raw_data/gribs',file_list[i].split('/')[-1])
            splitpath = local_path.split('_')
            hr = int(splitpath[-1][1:4])
            yr = int(splitpath[-2][0:4])
            mn = int(splitpath[-2][4:6])
            dy = int(splitpath[-2][6:8])
            run_hr = int(splitpath[1].split('/')[-1][3:5])
            dt = datetime.datetime(yr,mn,dy) + datetime.timedelta(hours=(hr+run_hr-8))
        elif type == 'ifs':
            local_path = os.path.join('raw_data/gribs',file_list[i].split('/')[-1])
            splitpath = local_path.split('_')
            hr = int(splitpath[-1][1:4])
            yr = int(splitpath[-2][0:4])
            mn = int(splitpath[-2][4:6])
            dy = int(splitpath[-2][6:8])
            run_hr = int(splitpath[1].split('/')[-1][8:10])
            dt = datetime.datetime(yr,mn,dy) + datetime.timedelta(hours=(hr+run_hr-8))
        elif type == 'aifs':
            local_path = os.path.join('raw_data/gribs',file_list[i].split('/')[-1])
            splitpath = local_path.split('_')
            hr = int(splitpath[-1][1:4])
            yr = int(splitpath[-2][0:4])
            mn = int(splitpath[-2][4:6])
            dy = int(splitpath[-2][6:8])
            run_hr = int(splitpath[1].split('/')[-1][9:11])
            dt = datetime.datetime(yr,mn,dy) + datetime.timedelta(hours=(hr+run_hr-8))
        else:
            local_path = os.path.join('raw_data',file_list[i].split('/')[-1])
            splitpath = local_path.split('/')
            yr = int(splitpath[-1][0:4])
            mn = int(splitpath[-1][4:6])
            dy = int(splitpath[-1][6:8])
            #Precipitation is previous 24 hours, reflecting previous day total:
            dt = datetime.datetime(yr,mn,dy) - datetime.timedelta(days=1)
        if not os.path.isfile(local_path):
            ostore.get_object(local_path=local_path, file_path=file_list[i])
        with rasterio.open(local_path) as grib:
            raster = grib.read(1)
            affine = grib.transform
            zone = zone.to_crs(grib.crs)
            #Rasterstats averages all pixels which touch the polygon, or all pixels whose centoids are within the polygon
            #For exact averaging, weighting pixels by fraction within polygon, investigate this package:
            #https://github.com/isciences/exactextract
            stats = rasterstats.zonal_stats(zone, raster, affine=affine,stats="mean",all_touched=True)
            for j in range(len(stats)):
                output.loc[dt,colnames[j]] = stats[j]['mean']
            LOGGER.info(f"Processing complete for dt = {dt: %Y%m%d %H}:00")
    if type in ['forecast','gfs']:
        output.sort_index(inplace=True)
        output=output.astype(float)*3600
    elif type == "ifs":
        output.sort_index(inplace=True)
        output=output.astype(float).interpolate()*1000
        output.iloc[1:,:] = output.diff().iloc[1:,:]
        output = output.mask(output<0,0)
    elif type == "aifs":
        output.sort_index(inplace=True)
        output=output.astype(float).interpolate()
        output.iloc[1:,:] = output.diff().iloc[1:,:]
        output = output.mask(output<0,0)
    output.ffill(axis=0,inplace=True)
    output = output.astype(float).round(2)
    LOGGER.info(f"watershed_forecast_averaging complete, sum of first 5 columns: {output.sum()[0:5]}")
    return output

def return_grib_list(objpath, keyword):
    ostore_objs = ostore.list_objects(objpath,return_file_names_only=True)
    LOGGER.info(f"return_grib_list found {len(ostore_objs)} objects in the ostore folder: {objpath}")
    file_list = list()
    for fname in ostore_objs:
        if keyword in fname:
            file_list.append(fname)
    LOGGER.info(f"{len(file_list)} of {len(ostore_objs)} objects contain keyword {keyword}")
    return file_list

ostore = NRObjStoreUtil.ObjectStoreUtil()

days_back = 0
current_date = datetime.datetime.now().replace(hour=0,minute=0, second=0,microsecond=0) - datetime.timedelta(days=days_back)
end_date = current_date + datetime.timedelta(days=9, hours=23)
dt_text = current_date.strftime('%Y%m%d')
ECCC_objpath = os.path.join('cmc/gribs',dt_text)
IFS_objpath = os.path.join('ecmwf/ifs00Z',dt_text)
AIFS_objpath = os.path.join('ecmwf/aifs00Z',dt_text)
GFS_objpath = os.path.join('NWP/gfs00Z',dt_text)
CLEVER_obj_path = os.path.join('cmc/CleverBasinsSummary',f'{dt_text}.csv')
CLEVER_ifs_objpath = os.path.join('ecmwf/ifs00Z_CleverBasinsSummary',f'{dt_text}.csv')
CLEVER_aifs_objpath = os.path.join('ecmwf/aifs00Z_CleverBasinsSummary',f'{dt_text}.csv')
CLEVER_gfs_objpath = os.path.join('NWP/gfs00Z_CleverBasinsSummary',f'{dt_text}.csv')
COFFEE_obj_path = os.path.join('cmc/COFFEEBasinsSummary',f'{dt_text}.csv')



""" ostore_objs = ostore.list_objects(objpath,return_file_names_only=True)
file_list = list()
for fname in ostore_objs:
    if 'PRATE' in fname:
        #hr_index.append(int(fname.split('.')[-2][-3:]))
        file_list.append(fname) """
hr_index = pd.date_range(start=current_date,end=end_date,freq='h')

#Load shape files:
clever_shp_path = 'data/shape/CLEVER/CLEVER_BASINS.shp'
clever_shp = geopandas.read_file(clever_shp_path)
coffee_shp_path = 'data/shape/COFFEE/COFFEE_BASIN.shp'
coffee_shp = geopandas.read_file(coffee_shp_path)

#CLEVER Zonal Precip:
output_template = pd.DataFrame(data=None, index = hr_index, columns = clever_shp.WSDG_ID)

#ECCC:
if CLEVER_obj_path not in ostore.list_objects(os.path.dirname(CLEVER_obj_path),return_file_names_only=True):
    LOGGER.info(f" {CLEVER_obj_path}")
    ECCC_grib_list = return_grib_list(ECCC_objpath, 'PRATE')
    CLEVER_precip = watershed_forecast_averaging(ECCC_grib_list, clever_shp, output_template)
    df_to_objstore(CLEVER_precip,CLEVER_obj_path)
else:
    LOGGER.info(f"{CLEVER_obj_path} already exists")

#GFS:
if CLEVER_gfs_objpath not in ostore.list_objects(os.path.dirname(CLEVER_gfs_objpath),return_file_names_only=True):
    try:
        GFS_grib_list = return_grib_list(GFS_objpath, 'PRATE')
        CLEVER_precip = watershed_forecast_averaging(GFS_grib_list, clever_shp, output_template, type = "gfs")
        df_to_objstore(CLEVER_precip,CLEVER_gfs_objpath)
    except:
        print("GFS processing failed")
else:
    LOGGER.info(f"{CLEVER_gfs_objpath} already exists")

#IFS:
if CLEVER_ifs_objpath not in ostore.list_objects(os.path.dirname(CLEVER_ifs_objpath),return_file_names_only=True):
    try:
        IFS_grib_list = return_grib_list(IFS_objpath, 'tp')
        CLEVER_precip = watershed_forecast_averaging(IFS_grib_list, clever_shp, output_template, type = "ifs")
        df_to_objstore(CLEVER_precip,CLEVER_ifs_objpath)
    except:
        print("IFS processing failed")
else:
    LOGGER.info(f"{CLEVER_ifs_objpath} already exists")

#AIFS:
if CLEVER_aifs_objpath not in ostore.list_objects(os.path.dirname(CLEVER_aifs_objpath),return_file_names_only=True):
    try:
        AIFS_grib_list = return_grib_list(AIFS_objpath, 'tp')
        CLEVER_precip = watershed_forecast_averaging(AIFS_grib_list, clever_shp, output_template, type = "aifs")
        df_to_objstore(CLEVER_precip,CLEVER_aifs_objpath)
    except:
        print("GFS processing failed")
else:
    LOGGER.info(f"{CLEVER_aifs_objpath} already exists")


#COFFEE Zonal Precip:
if COFFEE_obj_path not in ostore.list_objects(os.path.dirname(COFFEE_obj_path),return_file_names_only=True):
    output_template = pd.DataFrame(data=None, index = hr_index, columns = coffee_shp.WSDG_ID)
    COFFEE_precip = watershed_forecast_averaging(ECCC_grib_list, coffee_shp, output_template)
    COFFEE_daily_precip = COFFEE_precip.resample('D').sum()
    df_to_objstore(COFFEE_daily_precip,COFFEE_obj_path)
else:
    LOGGER.info(f"{COFFEE_obj_path} already exists")


# Transform to a difference CRS.


import requests
#importdates = pd.date_range(start = '20240615', end = '20240730')
importdates = pd.date_range(start = current_date-datetime.timedelta(days=1), end = current_date)

RDPA_objfolder = os.path.join('RFC_DATA','RDPA')
ostore_objs = ostore.list_objects(RDPA_objfolder,return_file_names_only=True)
url_template = 'https://hpfx.collab.science.gc.ca/{dt_text}/WXO-DD/model_rdpa/10km/06/{dt_text}T06Z_MSC_RDPA_APCP-Accum24h_Sfc_RLatLon0.09_PT0H.grib2'
for dt in importdates:
    dt_text = dt.strftime('%Y%m%d')
    url = url_template.format(dt_text=dt_text)
    filename = url.split('/')[-1]
    local_filename = os.path.join('raw_data',filename)
    obj_path = os.path.join(RDPA_objfolder,filename)
    if obj_path not in ostore_objs:
        with requests.get(url, stream=True) as r:
            if r.status_code == requests.codes.ok:
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        ostore.put_object(local_path=local_filename, ostore_path=obj_path)
        os.remove(local_filename)

year = current_date.strftime('%Y')

RDPA_Summary_objfolder = 'RFC_DATA/RDPA/Summary'
COFFEE_summary_fpath = os.path.join(RDPA_Summary_objfolder,f'COFFEE_Summary_{year}.csv')
CLEVER_summary_fpath = os.path.join(RDPA_Summary_objfolder,f'CLEVER_Summary_{year}.csv')
COFFEE_summary = get_summary(COFFEE_summary_fpath, year)
CLEVER_summary = get_summary(CLEVER_summary_fpath, year)

file_list = list()
for dt in importdates:
    dt_text = dt.strftime('%Y%m%d')
    url = url_template.format(dt_text=dt_text)
    filename = url.split('/')[-1]
    obj_path = os.path.join('RFC_DATA','RDPA',filename)
    local_filename = os.path.join('raw_data',filename)
    ostore.get_object(local_path=local_filename, file_path=obj_path)
    file_list.append(local_filename)

output_template = pd.DataFrame(data=None, index = importdates - datetime.timedelta(days=1), columns = coffee_shp.WSDG_ID)
COFFEE_precip = watershed_forecast_averaging(file_list, coffee_shp, output_template, type = 'analysis')
COFFEE_summary = update_data(COFFEE_summary, COFFEE_precip)
df_to_objstore(COFFEE_summary, COFFEE_summary_fpath, onprem=False)

output_template = pd.DataFrame(data=None, index = importdates - datetime.timedelta(days=1), columns = clever_shp.WSDG_ID)
CLEVER_precip = watershed_forecast_averaging(file_list, clever_shp, output_template, type = 'analysis')
CLEVER_summary = update_data(CLEVER_summary, CLEVER_precip)
df_to_objstore(CLEVER_summary, CLEVER_summary_fpath, onprem=False)
