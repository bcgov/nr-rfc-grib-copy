import logging
import os
import urllib.parse

import db.message_cache
import db.model as model
import pytest
import util.grib_file_config
from sqlalchemy import create_engine, event, select
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
def db_connection_string():
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
    LOGGER.debug(f"SQL Alchemy URL: {SQLALCHEMY_DATABASE_URL}")
    yield SQLALCHEMY_DATABASE_URL

@pytest.fixture(scope="module")
def dbEngine(db_connection_string) -> Engine:

    # urllib.parse
    urlib_obj = urllib.parse.urlparse(db_connection_string)
    dbPath = urlib_obj.path
    # remove leading /
    dbPath = dbPath[1:]
    LOGGER.debug(f"dbPath: {dbPath}")

    # should re-create the database every time the tests are run, the following
    # line ensure database that maybe hanging around as a result of a failed
    # test is deleted
    if os.path.exists(dbPath):
        LOGGER.debug(f"remove the database: {dbPath}")
        # os.remove("./test_db.db")

    SQLALCHEMY_DATABASE_URL = db_connection_string
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
    if os.path.exists(dbPath):
        LOGGER.debug(f"remove the database: {dbPath}")
        os.remove(dbPath)

@pytest.fixture(scope="function")
def message_cache_instance(db_connection_string, dbEngine):
    # turn down logging in specific modules
    logging.getLogger("util.grib_file_config").setLevel(logging.INFO)

    mc = db.message_cache.MessageCache(db_str=db_connection_string)
    # replace the engine with the one that is gonna get cleaned up...
    #mc.db = dbEngine
    yield mc

@pytest.fixture(scope="function")
def message_cache_instance_with_data(message_cache_instance):
    mc = message_cache_instance
    msg1 = 'junk 1 message'
    msg2 = 'junk 2 message'
    mc.cache_event(msg=msg1)
    mc.cache_event(msg=msg2)
    yield mc

    with mc.session_maker() as session:
        from sqlalchemy import delete
        stmt = delete(model.Events).where(model.Events.event_message.in_([msg1, msg2]))
        session.execute(stmt)


@pytest.fixture(scope="function")
def grib_config_files():
    gf = util.grib_file_config.GribFiles()
    yield gf