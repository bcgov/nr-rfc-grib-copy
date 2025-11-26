import requests
import os
import datetime
import NRUtil.NRObjStoreUtil as NRObjStoreUtil

ostore_path = 'RFC_DATA/RDPS/'
local_dir = 'raw_data'
os.makedirs(local_dir, exist_ok=True)

run_time_list = ['00','06','12','18']
time_step_list = ['000','001','002','003','004','005']
var_list = ['Albedo_Sfc','AirTemp_AGL-2m','Pressure_Sfc','WindU_AGL-10m','WindV_AGL-10m','DewPoint_AGL-2m']

#Get current date:
today = datetime.datetime.now()
date_list = [today, today-datetime.timedelta(days=1)]



ostore = NRObjStoreUtil.ObjectStoreUtil()
ostore_objs = ostore.list_objects(ostore_path,return_file_names_only=True)

def RDPS_download(ymd,run_time,time_step,var_name):
    url = f'https://hpfx.collab.science.gc.ca/{ymd}/WXO-DD/model_rdps/10km/{run_time}/{time_step}/{ymd}T{run_time}Z_MSC_RDPS_{var_name}_RLatLon0.09_PT{time_step}H.grib2'
    fname = os.path.basename(url)
    local_path = os.path.join(local_dir,fname)
    obj_path = os.path.join(ostore_path, fname)
    if obj_path not in ostore_objs:
        with requests.get(url, stream=True) as r:
            if r.status_code == requests.codes.ok:
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                ostore.put_object(local_path=local_path, ostore_path=obj_path)
                os.remove(local_path)

for date in date_list:
    ymd = date.strftime("%Y%m%d")
    for run_time in run_time_list:
        for time_step in time_step_list:
            forecast_dt = date.replace(hour=int(run_time)) + datetime.timedelta(hours=int(time_step))
            if forecast_dt < today:
                for var_name in var_list:
                    RDPS_download(ymd,run_time,time_step,var_name)
        var_name = ''
        RDPS_download(ymd,run_time,'006','DownwardShortwaveRadiationFlux-Accum_Sfc')
        RDPS_download(ymd,run_time,'006','DownwardShortwaveRadiationFlux-Accum_Sfc')