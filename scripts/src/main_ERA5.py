from ecmwf.datastores import Client
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
import datetime
import os

#Initialize ecmwf datastore client:
#Client will grab authentication credentials from ECMWF_DATASTORES_URL and ECMWF_DATASTORES_KEY environment variables
client = Client()
client.check_authentication()


def ERA5_download(request_update, filename):
    dataset = "derived-era5-single-levels-daily-statistics"

    request = {
    "product_type": "reanalysis",
    "variable": [
        "10m_u_component_of_wind"
    ],
    "year": "2025",
    "month": ["11"],
    "day": [
        "01", "02", "03",
        "04", "05", "06",
        "07", "08", "09",
        "10", "11", "12",
        "13", "14", "15",
        "16", "17", "18",
        "19", "20", "21",
        "22", "23", "24",
        "25", "26", "27",
        "28", "29", "30",
        "31"
    ],
    "daily_statistic": "daily_mean",
    "time_zone": "utc+08:00",
    "frequency": "1_hourly",
    "area": [62, -142, 46, -111]
    }

    #local folder to download to:
    download_folder = 'raw_data/'
    #Create download folder if it does not already exist:
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    objfolder = "RFC_DATA/ERA5"

    objpath = os.path.join(objfolder,filename)
    file_path = os.path.join(download_folder,filename)

    request.update(request_update)
    client.retrieve(dataset, request, file_path)

    ostore_objs = ostore.list_objects(objfolder,return_file_names_only=True)
    #To Do: Delete old versions of files
    #if objpath in ostore_objs:
    #    ostore.delete_remote_file(objpath)
    #Copy file to objectstore:
    ostore.put_object(local_path=file_path,ostore_path=objpath)

    #Delete local version of file:
    os.remove(file_path)




#Download data to path specified:
file_name = 'ERA5_u10_2025-11.nc'

ostore = NRObjStoreUtil.ObjectStoreUtil()

variable_dict = {
    "u10": "10m_u_component_of_wind",
    "v10": "10m_v_component_of_wind",
    "dewT": "2m_dewpoint_temperature",
    "t": "2m_temperature",
    "net_solor_radiation": "surface_net_solar_radiation",
    "net_thermal_radiation": "surface_net_thermal_radiation",
    "p": "total_precipitation",
    "s_pressure": "surface_pressure"
}

date = datetime.datetime.now()

for key, value in variable_dict.items():
    request_update = {
        "variable": [value]
    }
    year = "2025"
    month = "11"
    #Construct filename from key (variable name) and date:
    filename = f"ERA5_{key}_{year}-{month}.nc"
    ERA5_download(request_update, filename)
