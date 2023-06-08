import datetime
import logging

import db.model as model

LOGGER = logging.getLogger(__name__)


def test_db_events(db_session):
    """sanity test that will recieve a database session, create a message record
    then verify that it exists.

    :param db_session: a sqlalchemy database session object, from the fixture
        with the same name
    """

    msg_text = 'test message 1 2 3'
    date_string = datetime.datetime.now().strftime('%Y%m%d')

    event = model.Events(event_message=msg_text, event_idempotency_key=date_string)
    db_session.add(event)
    db_session.flush()
    event_db_rec = db_session.query(model.Events).filter_by(
        event_message=msg_text).all()
    assert len(event_db_rec) == 1
    LOGGER.debug(f'date stamp for the record: {event_db_rec[0].event_timestmp}')
    LOGGER.debug(f'pk record: {event_db_rec[0].event_id}')
    LOGGER.debug(f'message: {event_db_rec[0].event_message}')
    assert event_db_rec[0].event_message == msg_text

    # add a new record
    msg_text = 'another message'
    event = model.Events(event_message=msg_text, event_idempotency_key=date_string)
    db_session.add(event)
    db_session.flush()
    event_db_recs = db_session.query(model.Events).filter_by(
        event_idempotency_key=date_string).all()
    assert len(event_db_recs) == 2
    # extract the messages
    msg_list = [event.event_message for event in event_db_recs]
    assert msg_text in msg_list

    # test generic query all
    all_event_recs = db_session.query(model.Events).all()
    assert len(all_event_recs) == 2

    all_event_recs_as_list_dict = []
    for rec in all_event_recs:
        as_dict = rec.__dict__
        del as_dict['_sa_instance_state']
        all_event_recs_as_list_dict.append(as_dict)
    LOGGER.debug(f"all_event_recs_as_dict: {all_event_recs_as_list_dict}")

def test_get_events(message_cache_instance_operation_data):
    # simple test to retrieve the events associated with one of the test
    # databases
    mc = message_cache_instance_operation_data
    test_date_with_all_data = '20230608'
    status = mc.is_all_data_there(idemkey=test_date_with_all_data)
    assert status

    # now verify a date that doesn't have any data associated with it
    test_date_with_missing_data = '20230607'
    status = mc.is_all_data_there(idemkey=test_date_with_missing_data)
    assert not status

    # finally try with a date that only has some data
    test_date_with_missing_data = '20230606'
    status = mc.is_all_data_there(idemkey=test_date_with_missing_data)
    assert not status

# def test_is_event_of_interest(message_cache_instance_operation_data):
#     pass
