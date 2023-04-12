import datetime
import logging
import os

import pytz
import requests

import config
import ObjectStore

LOGGER = logging.getLogger(__name__)


class CopyCanSip:

    def __init__(self):
        self.now = datetime.datetime.now()
        self.date_str_format = "%Y%m%d_%H%M%S"
        self.outFolder = os.path.join(
            config.RFC_ROOT_FOLDER,
            config.CANSIP_FOLDER)

        self.ostore = ObjectStore.ObjectStoreUtil()

    def getUTCDateTimeString(self):
        utc_dt = self.now.astimezone(pytz.utc)
        date_str_utc = utc_dt.strftime(self.date_str_format)
        LOGGER.debug(f"utc date string: {date_str_utc}")
        return date_str_utc

    def getLocalDateTimeString(self):
        date_str_now = self.now.strftime(self.date_str_format)
        LOGGER.debug(f"date now: {date_str_now}")
        return date_str_now

    def getGribFile(self):
        year_str = self.now.strftime('%Y')
        month_str = self.now.strftime("%m")
        grib_file_name = f'cansips_forecast_raw_latlon1.0x1.0_TMP_TGL_2m_{year_str}-{month_str}_allmembers.grib2'
        return grib_file_name

    def getUrl(self):
        #http://dd.weather.gc.ca/ensemble/cansips/grib2/forecast/raw/%YYYY%/%MT%/
        year_str = self.now.strftime('%Y')
        month_str = self.now.strftime("%m")
        url = os.path.join(config.CANSIP_RAW_URL, year_str, month_str)
        # %URL%cansips_forecast_raw_latlon1.0x1.0_TMP_TGL_2m_%YYYY%-%MT%_allmembers.grib2
        grib_file_name = self.getGribFile()
        LOGGER.debug("grib file: {grib_file_name}")
        grib_file_url = os.path.join(url, grib_file_name)
        return grib_file_url

    def get_o_store_path(self):
        """get the path that the grib file should be copied to in
        object store
        """
        grib_file = self.getGribFile()
        grib_file_path = os.path.join(config.RFC_ROOT_FOLDER, config.CANSIP_FOLDER, grib_file)
        return grib_file_path

    def copy_grib_to_object_store(self):
        # pull file from nrcan
        grib_file_name = self.getGribFile()
        gribUrl = self.getUrl()
        LOGGER.info(f"pulling the file {grib_file_name}...")
        LOGGER.debug(f"gribUrl: {gribUrl}")
        r = requests.get(gribUrl, allow_redirects=True)
        with open(grib_file_name, 'wb') as fh:
            fh.write(r.content)

        # copy to object store...
        LOGGER.info(f"pushing the file {grib_file_name} to object store...")
        grib_o_store_path = self.get_o_store_path()
        self.ostore.putObject(destPath=grib_o_store_path,
            localPath=grib_file_name)

if __name__ == "__main__":
    # simple test code

    pass