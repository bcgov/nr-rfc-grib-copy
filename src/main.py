import Copy2ObjectStorage
import logging
import logging.config
import os

# setup logging
log_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config')
logging.config.fileConfig(log_config_path)

# call the download process
cansip_copy = Copy2ObjectStorage.CopyCanSip()
cansip_copy.copy_grib_to_object_store()

