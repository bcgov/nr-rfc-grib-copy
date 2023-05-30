import logging
import logging.config
import os

# follows is a hack for local dev, the dockerfile should add the files in the
# correct places
import sys

import messaging.cmc_grib_callbacks
import messaging.MSCDataMartSubscriber
import util.config as config
import util.file_path_config as file_path_config
import util.grib_file_config as grib_file_config

log_file_path = file_path_config.get_log_config_file_path()
print(f'log_file_path: {log_file_path}')
logging.config.fileConfig(log_file_path)

LOGGER = logging.getLogger(__name__)
LOGGER.info(f"log config: {log_file_path}")

q_name = config.get_amqp_queue_name()
exchange_name = config.get_amqp_exchange_name()
ampq_url = config.get_amqp_url()

datamart_listener = messaging.MSCDataMartSubscriber.MSCDataMartSubscriber(
    ampq_url=ampq_url,
    exchange_name=exchange_name,
    queue_name=q_name
)

# get and add topic strings to the listener channel
grib_config = grib_file_config.GribFiles()
topic_strings = grib_config.get_all_topic_strings()
# don't want duplicates
topic_strings = list(set(topic_strings))
for topic_string in topic_strings:
    LOGGER.debug(f"topic string: {topic_string}")
    datamart_listener.add_topic(topic_string)

# start the listener with the callback
callbacks = messaging.cmc_grib_callbacks.CMC_Grib_Callback()

datamart_listener.start_listening(callback=callbacks.cmc_callback)