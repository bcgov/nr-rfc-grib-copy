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
    event = model.Events(event_message=msg_text)
    db_session.add(event)
    db_session.flush()
    event_db_rec = db_session.query(model.Events).filter_by(
        event_message=msg_text).all()
    assert len(event_db_rec) == 1
    LOGGER.debug(f'date stamp for the record: {event_db_rec[0].event_timestmp}')
    LOGGER.debug(f'pk record: {event_db_rec[0].event_id}')
    LOGGER.debug(f'message: {event_db_rec[0].event_message}')
    assert event_db_rec[0].event_message == msg_text
