import os
import sys


class required_parameter_exception(Exception):
    def __init__(self, param_name, param_value):
        self.message = ('The process cannot run without populating the ' +
           f"environment variable: {param_name}")
        super().__init__(self.message)

thismodule = sys.modules[__name__]

RFC_ROOT_FOLDER = 'RFC_DATA'
CANSIP_FOLDER = 'CANSIP'
CANSIP_RAW_URL =  'http://dd.weather.gc.ca/ensemble/cansips/grib2/forecast/raw'
MINIO_SECURE = False

# these are required
params2populate = ['OBJ_STORE_BUCKET', 'OBJ_STORE_SECRET', 
    'OBJ_STORE_USER', 'OBJ_STORE_HOST']

for param_name in params2populate:
    param_value = os.getenv(param_name)
    if not param_value:
        raise required_parameter_exception(param_name, param_value)
    setattr(thismodule, param_name, param_value)

# if the env var is set the use it, 
WGRIB_UTILITY = os.getenv('WGRIB_UTILITY', 
    os.path.realpath(os.path.join(os.path.dirname(__file__), 'wgrib2', 'wgrib2')))
