import logging

import util.grib_file_config

LOGGER = logging.getLogger(__name__)

def test_grib_classes(grib_config_files):
    gf = util.grib_file_config.GribFiles()
    #LOGGER.debug(f"grib config class list: {gf.grib_config_class_list}")
    grib_configs_list = gf.gribcollection.cls_dict.keys()
    LOGGER.debug(f"grib_configs_list: {grib_configs_list}")

def test_calculate_file_list(grib_config_files):
    gf = grib_config_files

    file_list = gf.calculate_expected_file_list(only_file_path=True)
    LOGGER.debug(f"file list: {file_list[0:4]} ...")
    LOGGER.debug(f"total number of files in list: {len(file_list)}")

def test_get_all_topic_strings(grib_config_files):

    gf = grib_config_files
    topic_strings = gf.get_all_topic_strings()
    LOGGER.debug(f"topic_strings: {topic_strings}")

