import logging
import os

import util.config as config

LOGGER = logging.getLogger(__name__)


def test_get_db_string_local():
    if config.DB_FILE_PATH in os.environ:
        os.unsetenv(config.DB_FILE_PATH)
    db_str = config.get_db_string(ignore_env=True)
    LOGGER.debug(f"db_str: {db_str}")
    expected_str = os.path.realpath(os.path.join(
        os.path.dirname(__file__),
        '..', '..',
        config.event_db_file_name))
    expected_str = f'sqlite:///{expected_str}'
    #db_str = os.path.realpath(db_str)
    LOGGER.debug(f"expected_str: {expected_str}")
    assert db_str == expected_str


def test_get_db_string_env():
    mock_db_path = os.path.join(
        os.path.dirname(__file__),
        'mygreatdb.db'
    )
    #if config.DB_FILE_PATH not in os.environ:
    os.environ[config.DB_FILE_PATH] = mock_db_path
    db_str = config.get_db_string()
    assert db_str == mock_db_path




