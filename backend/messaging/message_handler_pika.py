import logging

import pika

LOGGER = logging.getLogger(__name__)


import datetime
import os
import sys
import time

import pika

start_time = datetime.datetime.now()

config = {"server": 'hpfx.collab.science.gc.ca/',
          "topic": '*.WXO-DD.model_gem_regional.10km.grib2.#',
          "exchange": 'xpublic'}

output_file = 'message.log'
fh = open(output_file, 'a')

def callback_gem_global(ch, method, properties, body):
    """recieves events from the message queue

    :param ch: _description_
    :param method: _description_
    :param properties: _description_
    :param body: _description_
    """
    # TODO: should watch / monitor for all the expected gem_global files to
    #       become avaiable
    #
    # TODO: refine the pattern for the subtopic so it only alerts about specific
    #       files
    msg = f" [x] Received {body.decode()}"
    print(msg)
    print(" [x] Done")
    # ch.basic_ack(delivery_tag=method.delivery_tag)
    fh.write(msg + '\n')
    fh.flush()
    # TODO: should ack, commented out for debugging
    #ch.basic_ack(delivery_tag = method.delivery_tag)

def callback_gem_regional(ch, method, properties, body):
    msg = f" [x] Received {body.decode()}"
    print(msg)
    print(" [x] Done")
    # ch.basic_ack(delivery_tag=method.delivery_tag)
    fh.write(msg + '\n')
    fh.flush()
    # TODO: should ack, commented out for debugging
    #ch.basic_ack(delivery_tag = method.delivery_tag)


# amqps://hpfx.collab.science.gc.ca/
# Access the CLODUAMQP_URL environment variable and parse it (fallback to localhost)
# http://hpfx.collab.science.gc.ca/20230403/WXO-DD/model_gem_regional/10km/grib2/

url = os.environ.get('CLOUDAMQP_URL', f'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca/?heartbeat=600&blocked_connection_timeout=300')
url_params = pika.URLParameters(url)

connection = pika.BlockingConnection(url_params)
channel = connection.channel() # start a channel

# queue_name recommended pattern: q_${BROKER_USER}.${PROGRAM}.${CONFIG}.${HOSTNAME} (dynamic option)
# newly

#topic_str = '*.WXO-DD.model_gem_regional.10km.grib2.#'
#topic_str = '*.WXO-DD.model_gem_regional.#'
# q_name = 'q_anonymous.bcgov_rfc.gem_regional.test1'
#q_name = 'q_anonymous.sr_subscribe.citypage.companyZ1'

# debugging WXO-DD/marine_weather
# v02.post
q_name_gem_regional = 'q_anonymous.bcgov_rfc.gem_regional.10km' # 10km/grib2/06
topic_str_gem_regional = 'v02.post.*.WXO-DD.model_gem_regional.10km.grib2.06.#'
channel.queue_declare(queue=q_name_gem_regional, durable=True)
channel.queue_bind(
         exchange='xpublic', queue=q_name_gem_regional, routing_key=topic_str_gem_regional)

# https://hpfx.collab.science.gc.ca/20230405/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/
q_name_gem_global = 'q_anonymous.bcgov_rfc.gem_global.15km' # 10km/grib2/06
topic_str_gem_global = 'v02.post.*.WXO-DD.model_gem_global.15km.grib2.lat_lon.00.#'
channel.queue_declare(queue=q_name_gem_global, durable=True)
channel.queue_bind(
         exchange='xpublic', queue=q_name_gem_global, routing_key=topic_str_gem_global)

#channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=q_name_gem_regional, on_message_callback=callback_gem_regional, auto_ack=False) # , auto_ack=True
channel.basic_consume(queue=q_name_gem_global, on_message_callback=callback_gem_global, auto_ack=False) # , auto_ack=True

try:
    channel.start_consuming()
except Exception as e:
    # calculate delta time
    crashTime = datetime.datetime.now()
    elapsed_time = crashTime - start_time
    print(f"elapsed time since start of script: {elapsed_time}")
    raise e

# to delete a queue, in case want to do that, this is required if want to change
# the subtopics
#channel.queue_delete(self.o['queueName'])

"""
last message:
/20230406/WXO-DD/model_gem_regional/coupled/gulf_st-lawrence/grib2/18/048/CMC_coupled-rdps-stlawrence-ocean_latlon0.02x0.03_2023040518_P048.grib2

error out

(venv) kjnether@NG401489:~/rfc_proj/cmc_cansip/backend/messaging$ python3 message_handler_pika.py
Traceback (most recent call last):
  File "/home/kjnether/rfc_proj/cmc_cansip/backend/messaging/message_handler_pika.py", line 50, in <module>
    channel.start_consuming()
  File "/home/kjnether/rfc_proj/cmc_cansip/venv/lib/python3.11/site-packages/pika/adapters/blocking_connection.py", line 1883, in start_consuming
    self._process_data_events(time_limit=None)
  File "/home/kjnether/rfc_proj/cmc_cansip/venv/lib/python3.11/site-packages/pika/adapters/blocking_connection.py", line 2044, in _process_data_events
    self.connection.process_data_events(time_limit=time_limit)
  File "/home/kjnether/rfc_proj/cmc_cansip/venv/lib/python3.11/site-packages/pika/adapters/blocking_connection.py", line 842, in process_data_events
    self._flush_output(common_terminator)
  File "/home/kjnether/rfc_proj/cmc_cansip/venv/lib/python3.11/site-packages/pika/adapters/blocking_connection.py", line 523, in _flush_output
    raise self._closed_result.value.error
pika.exceptions.AMQPHeartbeatTimeout: No activity or too many missed heartbeats in the last 60 seconds

"""