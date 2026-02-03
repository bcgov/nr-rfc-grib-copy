import datetime
import logging
import logging.config
import os
import requests
from ObjectStore import ObjectStoreUtil

#import GetCansip

# setup logging
log_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config')
logging.config.fileConfig(log_config_path)

LOGGER = logging.getLogger(__name__)

# looks like this needs to run at a specific time or the data won't be available

class ExtendedObjectStoreUtil(ObjectStoreUtil):
    def url_to_ostore(self, url, ostore_path):
        fname = os.path.basename(url)
        LOGGER.info(f"Downloading {fname}")
        local_dir = "raw_data"
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, fname)
        obj_path = os.path.join(ostore_path, fname)
        ostore_objs = super().listObjects(ostore_path,returnFileNamesOnly=True)
        if obj_path not in ostore_objs:
            with requests.get(url, stream=True) as r:
                if r.status_code == requests.codes.ok:
                    with open(local_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    super().putObject(localPath=local_path, destPath=obj_path)
                    os.remove(local_path)
                    LOGGER.info(f"Download Complete")
        else:
            LOGGER.info(f"File already exists in objectstore, skipping to next file")


url_template = "https://dd.meteo.gc.ca/today/model_cansips/100km/forecast/{year}/{month:02}/"
file_list = ["{year}{month:02}_MSC_CanSIPS_PrecipRate_Sfc_LatLon1.0_P{model_number:02}M.grib2",
             "{year}{month:02}_MSC_CanSIPS_AirTemp_AGL-2m_LatLon1.0_P{model_number:02}M.grib2"]



if __name__ == "__main__":
    model_range = range(12)
    ostore_path = 'RFC_DATA/CANSIP/'
    today = datetime.date.today()
    year = today.year
    month = today.month

    ostore = ExtendedObjectStoreUtil()
    for file in file_list:
        for model_number in model_range:
            full_url_template = os.path.join(url_template, file)
            download_url = full_url_template.format(year=year, month=month, model_number=model_number)
            ostore.url_to_ostore(url=download_url,ostore_path=ostore_path)





# download the monthly cansip data
#cansip_copy = GetCansip.CopyCanSip()
#cansip_copy.copy_grib_to_object_store()
