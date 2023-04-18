import logging
import os

import db.model as model
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import session, sessionmaker

LOGGER = logging.getLogger(__name__)


# This @event is important. By default FOREIGN KEY constraints have no effect
# on the operation of the table from SQLite.
# It (FOREIGN KEY) only works when emitting CREATE statements for tables.
# Reference:
# https://docs.sqlalchemy.org/en/14/dialects/sqlite.html#foreign-key-support
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="module")
def db_session_maker(dbEngine: Engine) -> sessionmaker:
    # Use connect_args parameter only with sqlite
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=dbEngine)
    LOGGER.debug(f"session type: {type(SessionTesting)}")
    yield SessionTesting


@pytest.fixture(scope="function")
def db_session(db_session_maker: sessionmaker, dbEngine) -> session:
    connection = dbEngine.connect()
    # transaction = connection.begin()
    session = db_session_maker(bind=connection)
    yield session  # use the session in tests.
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        LOGGER.debug(f"error: {e}")
    session.close()
    # transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def dbEngine() -> Engine:
    # should re-create the database every time the tests are run, the following
    # line ensure database that maybe hanging around as a result of a failed
    # test is deleted
    if os.path.exists("./test_db.db"):
        LOGGER.debug("remove the database: ./test_db.db'")
        # os.remove("./test_db.db")

    SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
    LOGGER.debug(f"SQL Alchemy URL: {SQLALCHEMY_DATABASE_URL}")
    execution_options = {"schema_translate_map": {"app_fam": None}}

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        execution_options=execution_options,
    )

    model.Base.metadata.create_all(bind=engine)
    LOGGER.debug("tables should be created now")
    LOGGER.debug(f"engine type: {type(engine)}")
    yield engine

    # dropping all objects in the test database and...
    # delete the test database

    model.Base.metadata.drop_all(engine)
    if os.path.exists("./test_db.db"):
        LOGGER.debug("remove the database: ./test_db.db'")
        os.remove("./test_db.db")
