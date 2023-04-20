import logging

import util.grib_file_config

LOGGER = logging.getLogger(__name__)

def test_grib_classes():
    gf = util.grib_file_config.GribFiles()
    #LOGGER.debug(f"grib config class list: {gf.grib_config_class_list}")
    grib_configs_list = gf.gribcollection.cls_dict.keys()
    LOGGER.debug(f"grib_configs_list: {grib_configs_list}")

def test_calculate_file_list():
    gf = util.grib_file_config.GribFiles()
    file_list = gf.calculate_expected_file_list(only_file_path=True)
    LOGGER.debug(f"file list: {file_list[0:4]} ...")
    LOGGER.debug(f"total number of files in list: {len(file_list)}")

