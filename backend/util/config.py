""" wrapper module to application level parameters, some of which may
originate in env variables
"""

import logging
import os
import urllib

LOGGER = logging.getLogger(__name__)

event_db_file_name = "event_cache.db"
ampq_params = {"heartbeat": 600, "blocked_connection_timeout": 300}
ampq_queue_org = "bcgov_rfc"
ampq_queue_topic_desc = "gems_reg_and_global"

# this is all published / public information so no need to hide it
# https://eccc-msc.github.io/open-data/msc-datamart/amqp_en/
default_ampq_user = "anonymous"
default_ampq_password = "anonymous"
default_ampq_exchange = "xpublic"
default_datestring_format = "%Y%m%d"

# list of expected env vars
DB_FILE_PATH = "DB_FILE_PATH"
AMPQ_USERNAME = "AMPQ_USERNAME"
AMPQ_PASSWORD = "AMPQ_PASSWORD"
AMPQ_DOMAIN = "AMPQ_DOMAIN"
AMPQ_EXCHANGE = "AMPQ_EXCHANGE"
CLOUDAMQP_URL = "CLOUDAMQP_URL"

MESSAGE_ACK = os.getenv("MESSAGE_ACK", "1")
MESSAGE_ACK = bool(int(MESSAGE_ACK))

GH_ORG = os.getenv("GH_ORG").strip()
GH_REPO = os.getenv("GH_REPO").strip()
GH_TOKEN = os.getenv("GH_TOKEN").strip()
required_params = [GH_ORG, GH_REPO, GH_TOKEN]
for param in required_params:
    if param is None:
        msg = f"the env var: {param} is required and has not been set"
        raise Exception(msg)

# using this parameter to alter the queue name when running locally vs in oc
DEBUG = os.getenv("DEBUG", False)
if (not isinstance(DEBUG, bool)) and DEBUG.isnumeric():
    DEBUG = bool(int(DEBUG))
else:
    DEBUG = bool(DEBUG)
print(f"DEBUG: {DEBUG}")

ZONE = os.getenv("ZONE", "DEV")

DAYS_TO_STALE = os.getenv("DAYS_TO_STALE", 3)


def get_db_string(ignore_env=False):
    """retrieves the database connection string

    ignore_env - used for debugging... forces method to ignore env vars
    """
    local_dir = os.path.dirname(__file__)
    local_db_path = os.path.realpath(os.path.join(local_dir, "..", "..", event_db_file_name))
    local_db_path = f"sqlite:///{local_db_path}"

    if not ignore_env:
        db_str = os.getenv("DB_FILE_PATH", local_db_path)
    else:
        db_str = local_db_path

    # example connection strings
    # sqlite:///C:\\sqlitedbs\\school.db
    # sqlite:////path/to/file.db
    # relative path sqlite:///../path/to/file.db

    return db_str


def get_amqp_queue_name():
    """Following the recommended q naming convension specified here:
    https://eccc-msc.github.io/open-data/msc-datamart/amqp_en/
    """
    # q_anonymous.sr_subscribe.config_name.company_name (static option)
    config_name = "cmc_gems"
    ampq_user = os.getenv(AMPQ_USERNAME, default_ampq_user)
    q_name = f"q_{ampq_user}.bcgov_listener.{config_name}.{ampq_queue_org}"

    if DEBUG:
        q_name = f"{q_name}-debug"
    else:
        q_name = f"{q_name}-{ZONE}"
    return q_name


def get_amqp_url():
    ampq_user = os.getenv(AMPQ_USERNAME, default_ampq_user)
    ampq_pass = os.getenv(AMPQ_PASSWORD, default_ampq_password)
    ampq_domain = os.getenv(AMPQ_DOMAIN, None)
    if ampq_domain is None:
        msg = f"the env var: {AMPQ_DOMAIN} is required and has not been set"
        raise AMQPDomainError(msg)

    ampq_params_str = urllib.parse.urlencode(ampq_params)

    # raise
    default_url = f"amqps://{ampq_user}:{ampq_pass}@{ampq_domain}/?{ampq_params_str}"
    url = os.environ.get(CLOUDAMQP_URL, default_url)
    return url


def get_amqp_exchange_name():
    return os.getenv(AMPQ_EXCHANGE, default_ampq_exchange)


class AMQPDomainError(Exception):
    def __init__(self, message):
        super().__init__(message)
