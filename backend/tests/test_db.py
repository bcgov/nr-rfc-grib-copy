import datetime
import logging

import db.model as model
import pytest

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
    LOGGER.debug(f"number of records: {len(event_db_recs)}")
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

