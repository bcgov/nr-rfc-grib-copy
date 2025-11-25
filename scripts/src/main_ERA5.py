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
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
        "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24",
        "25", "26", "27", "28", "29", "30", "31"
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

    #Copy file to objectstore:
    ostore.put_object(local_path=file_path,ostore_path=objpath)

    #Delete local version of file:
    os.remove(file_path)
    #Delete previous (non current) versions of file on objectstore:
    delete_all_non_current_version(objpath)

def delete_all_non_current_version(ostore_path):
    """
    it looks like the versions can get layered on top of one another in a stack like structure.
    When one version gets deleted thenext one in the stack will show up.

    This function will iterate over all the versions, deleting all but the latest version, all
    the way to the bottom of the stack. Can take a while if there are a lot of versions.

    :param ostore_path: the path in object store who's versions you want to delete
    :type ostore_path: str, path
    """

    keys = ["Versions", "DeleteMarkers"]
    bucket = ostore.obj_store_bucket
    ostore.createBotoClient()
    s3 = ostore.boto_client

    while True:
        response = s3.list_object_versions(Bucket=bucket, Prefix=ostore_path)
        versions_to_delete = []

        for k in keys:
            if k in response:
                data = response[k]
                for item in data:
                    # print("item: ", item)
                    if item["Key"] == ostore_path and not item['IsLatest']:
                        versions_to_delete.append({
                            'Key': ostore_path,
                            'VersionId': item['VersionId'],
                            'LastModified': item['LastModified']
                        })

        if not versions_to_delete:
            break
        # version_string = '\n'.join([v['VersionId'] + ' ' + str(v['LastModified']) for v in versions_to_delete])

        versions_to_delete_send = []
        for ver in versions_to_delete:
            del ver['LastModified']
            versions_to_delete_send.append(ver)

        delete_response = s3.delete_objects(
            Bucket=bucket,
            Delete={
                'Objects': versions_to_delete_send,
                'Quiet': True
            }
        )

#Download data to path specified:
file_name = 'ERA5_u10_2025-11.nc'

ostore = NRObjStoreUtil.ObjectStoreUtil()

#Dictionary of ERA5 variables to download
#key: value
#key = variable name used in filename
#value = variable name used in API call
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

#Get current date:
date = datetime.datetime.now()
day = int(date.strftime("%d"))
#If day of month <= 5, download previous month instead of current month
if day <= 5:
    date = date - datetime.timedelta(days=7)
#Create list of dates (months) to download. Two most recent months
datelist = [date, date - datetime.timedelta(days=31)]

for key, value in variable_dict.items():
    for date in datelist:
        year = date.strftime("%Y")
        month = date.strftime("%m")
        request_update = {
            "variable": [value],
            "year": year,
            "month": [month],
        }
        #Construct filename from key (variable name) and date:
        filename = f"ERA5_{key}_{year}-{month}.nc"
        ERA5_download(request_update, filename)

#Only update whole year data on Mondays:
if datelist[0].weekday() == 0:
    for key, value in variable_dict.items():
        year = date.strftime("%Y")
        month_list = [str(num+1).zfill(2) for num in range(12)]
        request_update = {
            "variable": [value],
            "year": year,
            "month": month_list,
        }
        #Construct filename from key (variable name) and date:
        filename = f"ERA5_{key}_{year}.nc"
        ERA5_download(request_update, filename)
