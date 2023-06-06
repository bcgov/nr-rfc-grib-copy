import datetime
import logging

import db.model as model
import pytest

LOGGER = logging.getLogger(__name__)


def test_get_all_messages(message_cache_instance_with_data):
    LOGGER.debug(f"message_cache_instance_with_data: {message_cache_instance_with_data}")
    mc = message_cache_instance_with_data
    events = mc.get_cached_events()
    assert len(events) == 2

def test_cache_event(message_cache_instance):
    mc = message_cache_instance
    msg = 'msg 1 2 4'
    idem_key = 'test_idem_key'
    mc.cache_event(msg, idem_key)

    events = mc.get_cached_events()
    msgs = [msg.event_message for msg in events]
    idem_keys = [msg.event_idempotency_key for msg in events]

    assert idem_key in idem_keys
    assert msg in msgs

def test_is_of_interest(message_cache_instance):
    mc = message_cache_instance
    is_interesting = mc.is_event_of_interest('junkjunkjunk')
    assert not is_interesting

    expected_value = mc.expected_data[3]
    assert mc.is_event_of_interest(expected_value)

def test_is_all_data_there(message_cache_instance):
    mc = message_cache_instance
    assert not mc.is_all_data_there()

    if mc.current_idempotency_key not in mc.cached_events:
        mc.cached_events[mc.current_idempotency_key] = []

    # now setup for a pass
    mc.cached_events[mc.current_idempotency_key] = mc.expected_data
    assert mc.is_all_data_there()

    # rearrange the order a bit
    value = mc.cached_events[mc.current_idempotency_key].pop(7)
    mc.cached_events[mc.current_idempotency_key].append(value)
    assert mc.is_all_data_there()

def test_is_all_data_there_operational_data(message_cache_instance_operation_data):

    # problems with the message queue not picking up the expected events.
    # this dataset seems to be missing now
    #  - '/20230606/WXO-DD/model_gem_regional/10km/grib2/06/040/CMC_reg_PRATE_SFC_0_ps10km_2023060606_P040.grib2'
    #                                                           CMC_reg_PRATE_SFC_0_ps10km_2023060606_P040.grib2
    mc = message_cache_instance_operation_data

    data_there = mc.is_all_data_there(idemkey='20230606')
    LOGGER.debug(f"data_there: {data_there}")

# args fixture_name, test params, indirect=True
# @pytest.mark.parametrize()
# def test_is_all_data_there_with_data(message_cache_instance_with_data):
#     mc = message_cache_instance_with_data
#     mc.is_all_data_there(idem_key='20230422')
#     pass

def test_cache_filter(message_cache_instance_operation_data):
    # either this message isn't getting emitted, or the filter isn't
    # letting it get logged
    # '/20230422/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/090/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023042200_P090.grib2'
    #
    # is_event_of_interest()
    date_str = '20230606'
    test_event = f'/{date_str}/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/090/CMC_glb_PRATE_SFC_0_latlon.15x.15_{date_str}00_P090.grib2'
    mc = message_cache_instance_operation_data
    is_of_interest = mc.is_event_of_interest(msg=test_event)
    LOGGER.debug(f"test_event is of interest: {is_of_interest}")

def test_clear_cache(message_cache_instance_with_data):
    mc = message_cache_instance_with_data

    # call clear cache
    mc.clear_cache()

    # assert that no data exists in memory
    assert mc.current_idempotency_key not in mc.cached_events

    # assert the database has been cleared
    events_from_db = mc.get_cached_events()
    idem_keys = set([event.event_idempotency_key for event in events_from_db])
    LOGGER.debug(f"idem keys: {idem_keys}")
    assert mc.current_idempotency_key not in idem_keys

    # now add a bunch of events with different idem keys
    key1 = '20230419'
    key2 = '20230420'

    msgs = ['msg1', 'msg2', 'msg4', 'mssg3']
    for key in [key1, key2]:
        for msg in msgs:
            mc.cache_event(msg, key)

    # now clear the cache
    mc.clear_cache(idemkey=key2)
    # get events that are left in the db
    events_from_db = mc.get_cached_events()
    # make sure the key that was cleared is no longer in the db
    idem_keys = set([event.event_idempotency_key for event in events_from_db])
    assert key2 not in idem_keys
    # make sure the key that wasn't cleared is still there
    assert key1 in idem_keys
    # make sure the in memory struct was cleared also
    assert key2 not in mc.cached_events
    # make sure the key that wasn't cleared is still in memory
    assert key1 in mc.cached_events


