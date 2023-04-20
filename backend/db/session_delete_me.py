# tagged for deleting...
# what this module does is going to be handled by the message_cache.py
# module

import logging

import util.config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

LOGGER = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = util.config.get_db_string()

_session_local = None


def get_db(db_conn_str=None) -> sessionmaker:
    """centralized call to create a database sessionmaker

    :yield: a db session
    """
    # allowing for override of defaults, helps with testing.
    if db_conn_str is None:
        db_conn_str = SQLALCHEMY_DATABASE_URL

    try:
        # Initialize session local on first call
        global _session_local
        if not _session_local:
            LOGGER.debug("starting a new db session")
            engine = create_engine(db_conn_str, echo=False)
            LOGGER.debug("database engine created!")
            _session_local = sessionmaker(autocommit=False,
                                          autoflush=False,
                                          bind=engine)

        db = _session_local()
        yield db

    except Exception:
        db.rollback()

    finally:
        db.commit()
        LOGGER.debug("closing db session")
        db.close()
