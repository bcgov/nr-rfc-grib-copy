import datetime
import logging
import logging.config
import os

import pytz

import GetCansip
import GetGrib
import GetGribConfig

# setup logging
log_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config')
logging.config.fileConfig(log_config_path)

LOGGER = logging.getLogger(__name__)

dest_folder_gribs = os.path.join('cmc_data', 'gribs')
ostore_folder_gribs = os.path.join('cmc', 'gribs')
dest_folder_summary = os.path.join('cmc_data', 'summary')
ostore_folder_summary = os.path.join('cmc', 'summary')

# TZ = 'America/Toronto'
TZ = pytz.timezone('America/Vancouver')

def get_extract_gribs():
    # needs to run at a specific time or the data won't be available
    # suspect its before noon

    # download and process the daily CMC data to local
    regional1 = GetGribConfig.GribRegional_1()
    grib_get_reg1 = GetGrib.GetGrib(config=regional1, dest_folder=dest_folder_gribs)
    grib_get_reg1.get()
    grib_reg1_data = grib_get_reg1.extract()

    regional2 = GetGribConfig.GribRegional_2()
    grib_get_reg2 = GetGrib.GetGrib(config=regional2, dest_folder=dest_folder_gribs)
    grib_get_reg2.get()
    grib_reg2_data = grib_get_reg2.extract()

    globl = GetGribConfig.GribGlobal_1()
    grib_get_glob1 = GetGrib.GetGrib(config=globl, dest_folder=dest_folder_gribs)
    grib_get_glob1.get()
    grib_glob1_data = grib_get_glob1.extract()

    glob2 = GetGribConfig.GribGlobal_2()
    grib_get_glob2 = GetGrib.GetGrib(config=glob2, dest_folder=dest_folder_gribs)
    grib_get_glob2.get()
    grib_glob2_data = grib_get_glob2.extract()
    # ^^ think about caching the data from this step, then re-read and continue
    # to make easier to debug / run


    # write the grib outputs
    coalate = GetGrib.CoalateGribOutput()
    coalate.add_dict(grib_reg1_data)
    coalate.add_dict(grib_reg2_data)
    coalate.add_dict(grib_glob1_data)
    coalate.add_dict(grib_glob2_data)
    datestr = datetime.datetime.now(TZ).strftime('%Y%m%d')
    dest_folder = os.path.join(dest_folder_summary, datestr)
    LOGGER.info(f'dest folder: {dest_folder}')
    coalate.output(dest_folder)

def persist_gribs_to_object_store():
    # finally copy gribs from local storage to object storage
    copy_2_ostore = GetGrib.CopyCMC2ObjectStorage()
    datestr = datetime.datetime.now(TZ).strftime('%Y%m%d')
    src_folder = os.path.join(dest_folder_gribs, datestr)
    ostore_folder = os.path.join(ostore_folder_gribs, datestr)
    copy_2_ostore.copy_to_ostore(
        src_folder=src_folder,
        ostore_folder=ostore_folder)

    # and lastly copy the summaries to the object storage
    src_folder = os.path.join(dest_folder_summary, datestr)
    ostore_folder = os.path.join(ostore_folder_summary, datestr)
    copy_2_ostore.copy_to_ostore(
        src_folder=src_folder,
        ostore_folder=ostore_folder)

get_extract_gribs()
#persist_gribs_to_object_store()
