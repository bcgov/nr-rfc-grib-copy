import Copy2ObjectStorage
import logging
import logging.config
import os
import GetGrib
import GetGribConfig

# setup logging
log_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config')
logging.config.fileConfig(log_config_path)

LOGGER = logging.getLogger(__name__)

dest_folder_gribs = os.path.join('tmp', 'gribs')
dest_folder_summary = os.path.join('tmp', 'summary')
coalate = GetGrib.CoalateGribOutput()


# looks like this needs to run at a specific time or the data won't be available

# download the monthly cansip data
#cansip_copy = Copy2ObjectStorage.CopyCanSip()
#cansip_copy.copy_grib_to_object_store()

# download the daily cansip data to local
'''
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
'''
glob2 = GetGribConfig.GribGlobal_2()
grib_get_glob2 = GetGrib.GetGrib(config=glob2, dest_folder=dest_folder_gribs)
grib_get_glob2.get()
#grib_glob2_data = grib_get_glob2.extract()

"""
coalate.add_dict(grib_reg1_data)
coalate.add_dict(grib_reg2_data)
coalate.add_dict(grib_glob1_data)
coalate.add_dict(grib_glob2_data)
coalate.output(dest_folder_summary)
"""

