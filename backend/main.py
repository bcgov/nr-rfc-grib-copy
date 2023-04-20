import logging
import logging.config
import os

# follows is a hack for local dev, the dockerfile should add the files in the
# correct places
import sys

import messaging.MSCDataMartSubscriber
import util.config as config
import util.file_path_config as file_path_config


log_file_path = file_path_config.get_log_config_file_path()
print(f'log_file_path: {log_file_path}')
logging.config.fileConfig(log_file_path)

LOGGER = logging.getLogger(__name__)

LOGGER.debug("first message")

q_name = config.get_amqp_queue_name()
exchange_name = config.get_amqp_exchange_name()
ampq_url = config.get_amqp_url()

datamart_listener = messaging.MSCDataMartSubscriber.MSCDataMartSubscriber(
    ampq_url=ampq_url,
    exchange_name=exchange_name,
    queue_name=q_name
)

# need to get these from the GetGribConfig.py
topic_string_1 = 'v02.post.*.WXO-DD.model_gem_regional.10km.grib2//*/#'
topic_string_2 = 'v02.post.*.MSC-SAT.#'

# topic_str =

# datamart_listener.add_topic()
