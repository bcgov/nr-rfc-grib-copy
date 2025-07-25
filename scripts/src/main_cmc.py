import datetime
import logging
import logging.config
import os
import sys

#import GetCansip
import GetGrib
import GetGribConfig
import pytz

# setup logging
log_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config')
logging.config.fileConfig(log_config_path)

LOGGER = logging.getLogger(__name__)

dest_folder_gribs = os.path.join('cmc_data', 'gribs')
ostore_folder_gribs = os.path.join('cmc', 'gribs')
dest_folder_summary = os.path.join('cmc_data', 'summary_V2024')
ostore_folder_summary = os.path.join('cmc', 'summary_V2024')

# TZ = 'America/Toronto'
TZ = pytz.timezone('America/Vancouver')

def get_extract_gribs(date_str:str, GribConfigList:list, grib_folder:str, summary_folder:str):
    # needs to run at a specific time or the data won't be available
    # suspect its before noon
    coalate = GetGrib.CoalateGribOutput()
    for config in GribConfigList:
    # download and process the daily CMC data to local
        if date_str is not None: config.datestr = date_str
        grib_get = GetGrib.GetGrib(config=config,
                                        dest_folder=grib_folder,
                                        date_str=date_str)
        grib_get.get()
        grib_data = grib_get.extract()
        # write the grib outputs
        coalate.add_dict(grib_data)

    if date_str is None: date_str = datetime.datetime.now(TZ).strftime('%Y%m%d')
    summary_path = os.path.join(summary_folder, date_str)
    LOGGER.info(f'dest folder: {summary_path}')
    coalate.output(summary_path)

# def persist_gribs_to_object_store(date_str=None):
#     # finally copy gribs from local storage to object storage
#     copy_2_ostore = GetGrib.CopyCMC2ObjectStorage(date_str)
#     if date_str is None: date_str = datetime.datetime.now(TZ).strftime('%Y%m%d')
#     src_folder = os.path.join(dest_folder_gribs, date_str)
#     LOGGER.debug("src_folder: %s", src_folder)
#     ostore_folder = os.path.join(ostore_folder_gribs, date_str)
#     copy_2_ostore.copy_to_ostore(
#         src_folder=src_folder,
#         ostore_folder=ostore_folder)

#     # and lastly copy the summaries to the object storage
#     src_folder = os.path.join(dest_folder_summary, date_str)
#     ostore_folder = os.path.join(ostore_folder_summary, date_str)
#     copy_2_ostore.copy_to_ostore(
#         src_folder=src_folder,
#         ostore_folder=ostore_folder)

def persist_gribs_to_object_store(date_str, grib_folder, summary_folder, ostore_grib_folder=None, ostore_summary_folder=None):
    dest_folder_gribs = grib_folder
    if ostore_grib_folder is None:
        ostore_grib_folder = grib_folder
    dest_folder_summary = summary_folder
    if ostore_summary_folder is None:
        ostore_summary_folder = summary_folder
    # finally copy gribs from local storage to object storage
    copy_2_ostore = GetGrib.CopyCMC2ObjectStorage(date_str)
    if date_str is None: date_str = datetime.datetime.now(TZ).strftime('%Y%m%d')
    src_folder = os.path.join(dest_folder_gribs, date_str)
    LOGGER.debug("src_folder: %s", src_folder)
    ostore_folder = os.path.join(ostore_grib_folder, date_str)
    copy_2_ostore.copy_to_ostore(
        src_folder=src_folder,
        ostore_folder=ostore_folder)

    # and lastly copy the summaries to the object storage
    src_folder = os.path.join(dest_folder_summary, date_str)
    ostore_folder = os.path.join(ostore_summary_folder, date_str)
    copy_2_ostore.copy_to_ostore(
        src_folder=src_folder,
        ostore_folder=ostore_folder)

if __name__ == "__main__":
    date_str = None
    #date_str = "20250709"
    if len(sys.argv) > 1:
        date_str = sys.argv[1]

    cmc_configs = []
    cmc_configs.append(GetGribConfig.GribRegional_1())
    cmc_configs.append(GetGribConfig.GribRegional_2())
    cmc_configs.append(GetGribConfig.GribGlobal_1())
    cmc_configs.append(GetGribConfig.GribGlobal_2())
    get_extract_gribs(date_str=date_str,
                    GribConfigList=cmc_configs,
                    grib_folder=dest_folder_gribs,
                    summary_folder=dest_folder_summary)
    persist_gribs_to_object_store(date_str=date_str,
                                grib_folder=dest_folder_gribs,
                                summary_folder=dest_folder_summary,
                                ostore_grib_folder=ostore_folder_gribs,
                                ostore_summary_folder=ostore_folder_summary)

    ecmwf_configs = []
    ecmwf_configs.append(GetGribConfig.GribECMWF1())
    ecmwf_configs.append(GetGribConfig.GribECMWF2())
    get_extract_gribs(date_str=date_str,
                    GribConfigList=ecmwf_configs,
                    grib_folder='ecmwf/ifs00Z',
                    summary_folder='ecmwf/ifs00Z_summary')
    persist_gribs_to_object_store(date_str=date_str,
                                grib_folder='ecmwf/ifs00Z',
                                summary_folder='ecmwf/ifs00Z_summary')

    ecmwf_configs = []
    ecmwf_configs.append(GetGribConfig.GribECMWF3())
    ecmwf_configs.append(GetGribConfig.GribECMWF4())
    get_extract_gribs(date_str=date_str,
                    GribConfigList=ecmwf_configs,
                    grib_folder='ecmwf/aifs00Z',
                    summary_folder='ecmwf/aifs00Z_summary')
    persist_gribs_to_object_store(date_str=date_str,
                                grib_folder='ecmwf/aifs00Z',
                                summary_folder='ecmwf/aifs00Z_summary')
    #get_extract_gribs(date_str=date_str)
    #persist_gribs_to_object_store(date_str=date_str)
    gfs_configs = []
    gfs_configs.append(GetGribConfig.GribGFS1())
    gfs_configs.append(GetGribConfig.GribGFS2())
    get_extract_gribs(date_str=date_str,
                    GribConfigList=gfs_configs,
                    grib_folder='NWP/gfs00Z',
                    summary_folder='NWP/gfs00Z_summary')
    persist_gribs_to_object_store(date_str=date_str,
                                grib_folder='NWP/gfs00Z',
                                summary_folder='NWP/gfs00Z_summary')