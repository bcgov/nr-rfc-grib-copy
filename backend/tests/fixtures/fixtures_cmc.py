import messaging.cmc_grib_callbacks
import pytest


@pytest.fixture(scope="function")
def cmc_callback():
    grib_callback = messaging.cmc_grib_callbacks.CMC_Grib_Callback()
    yield grib_callback

