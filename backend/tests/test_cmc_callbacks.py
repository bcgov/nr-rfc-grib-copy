import logging

import pytest

LOGGER = logging.getLogger(__name__)

class Mock_Channel:
    def __init__(self):
        pass

    def basic_ack(self, delivery_tag):
        LOGGER.debug(f"mock ack, delivery tag: {delivery_tag}")

class Mock_Decode_Message:
    def __init__(self, body) -> None:
        self.body = body

    def decode(self):
        LOGGER.debug(f"mock decode, body: {self.body}")
        return self.body

def test_init(cmc_callback):
    """making sure the callback class can be instantiated.

    :param cmc_callback: _description_
    :type cmc_callback: _type_
    """
    LOGGER.debug(f"cmc_callback: {cmc_callback.mc.db_str}")
    cached_events = cmc_callback.mc.get_cached_events_as_struct()
    LOGGER.debug(f"cached events from db: {cached_events}")

    # if the db has any events in it, delete them
    for date_str in cached_events:
        # ensure unique
        event_set = list(set(cached_events[date_str]))
        for event in event_set:
            cmc_callback.mc.clear_cache(date_str)

    cached_events = cmc_callback.mc.get_cached_events_as_struct()
    LOGGER.debug(f"cached_events: {cached_events}")
    assert not cached_events


def test_cmc_callback(cmc_callback):
    """tests the callback method.  This method is called by the listener
    when a message is received.

    :param cmc_callback: _description_
    :type cmc_callback: _type_
    """
    LOGGER.debug(f"cached events before: {cmc_callback.mc.cached_events}")

    body = '20230628181943.032 https://hpfx.collab.science.gc.ca /20230620/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/099/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023062000_P099.grib2'
    mock_channel = Mock_Channel()
    mock_body = Mock_Decode_Message(body=body)
    cmc_callback.cmc_callback(body=mock_body, delivery_tag=1, channel=mock_channel)

    LOGGER.debug(f"cached events after: {cmc_callback.mc.cached_events}")
    # make sure that events are not double logged
    cmc_callback.cmc_callback(body=mock_body, delivery_tag=1, channel=mock_channel)
    LOGGER.debug(f"cached events second: {cmc_callback.mc.cached_events}")

