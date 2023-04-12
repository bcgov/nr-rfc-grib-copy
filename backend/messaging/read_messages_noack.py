import logging
import os

import pika

# configure root logger
RLOG = logging.getLogger()
RLOG.setLevel(logging.INFO)
hndlr = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
hndlr.setFormatter(formatter)
RLOG.addHandler(hndlr)
RLOG.debug("test")

# SET pika to INFO

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

url = os.environ.get('CLOUDAMQP_URL', f'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca/?heartbeat=600&blocked_connection_timeout=300')
url_params = pika.URLParameters(url)

def message_callback(ch, method, properties, body):
    msg = f" [x] Received {body.decode()}"
    LOGGER.info(msg)
    LOGGER.info(" [x] Done")
    channel.basic_ack(delivery_tag = method.delivery_tag)
    # this section needs to collect messages recieved from the event queue,
    # then when all the data that we are looking to recieve is available
    # trigger the download



try:
    LOGGER.debug(f"creating connection to {url}")
    connection = pika.BlockingConnection(url_params)
    channel = connection.channel() # start a channel

    q_name = 'q_anonymous.bcgov_rfc.testing' # 10km/grib2/06
    topic_string = 'v02.post.*.WXO-DD.#'

    channel.queue_declare(queue=q_name, durable=True)
    channel.queue_bind(
         exchange='xpublic', queue=q_name, routing_key=topic_string)
    LOGGER.debug(f"created channel and queue name: {q_name}")
    channel.basic_consume(queue=q_name, on_message_callback=message_callback, auto_ack=False)
    LOGGER.debug("consuming...")
    channel.start_consuming()

except KeyboardInterrupt:

    channel.queue_delete(q_name)
    channel.close()