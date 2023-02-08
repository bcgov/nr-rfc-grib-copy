import GetCansip
import logging
import logging.config
import os
import GetGrib
import GetGribConfig
import datetime

# setup logging
log_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config')
logging.config.fileConfig(log_config_path)

LOGGER = logging.getLogger(__name__)

# looks like this needs to run at a specific time or the data won't be available

# download the monthly cansip data
cansip_copy = GetCansip.CopyCanSip()
cansip_copy.copy_grib_to_object_store()
