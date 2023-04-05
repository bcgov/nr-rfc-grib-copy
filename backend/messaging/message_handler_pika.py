import logging

import pika

LOGGER = logging.getLogger(__name__)


import os
import time

import pika

config = {"server": 'hpfx.collab.science.gc.ca/',
          "topic": '*.WXO-DD.model_gem_regional.10km.grib2.#',
          "exchange": 'xpublic'}

output_file = 'message.log'
fh = open(output_file, 'a')

def callback(ch, method, properties, body):
    msg = f" [x] Received {body.decode()}"
    print(msg)
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)
    fh.write(msg + '\n')
    fh.flush()
    ch.basic_ack(delivery_tag = method.delivery_tag)

# amqps://hpfx.collab.science.gc.ca/
# Access the CLODUAMQP_URL environment variable and parse it (fallback to localhost)
# http://hpfx.collab.science.gc.ca/20230403/WXO-DD/model_gem_regional/10km/grib2/
datestr = '20230403'

url = os.environ.get('CLOUDAMQP_URL', f'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca/')
params = pika.URLParameters(url)
connection = pika.BlockingConnection(params)
channel = connection.channel() # start a channel

# queue_name recommended pattern: q_${BROKER_USER}.${PROGRAM}.${CONFIG}.${HOSTNAME} (dynamic option)
# newly

#topic_str = '*.WXO-DD.model_gem_regional.10km.grib2.#'
#topic_str = '*.WXO-DD.model_gem_regional.#'
q_name = 'q_anonymous.bcgov_rfc.gem_regional.test1'
#q_name = 'q_anonymous.sr_subscribe.citypage.companyZ1'

# debugging WXO-DD/marine_weather
q_name = 'q_anonymous.bcgov_rfc.gem_regional.test2b'
topic_str = '*.WXO-DD.#'

channel.queue_declare(queue=q_name, durable=True)
channel.queue_bind(
         exchange='xpublic', queue=q_name, routing_key=topic_str)


#channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=q_name, on_message_callback=callback, auto_ack=False) # , auto_ack=True
channel.start_consuming()


"""error out

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