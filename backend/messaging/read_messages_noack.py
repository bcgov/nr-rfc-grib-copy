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


"""

2023-04-17 20:33:42,767 - __main__ - INFO - 25 - [x] Received 20230417203341.618 https://hpfx.collab.science.gc.ca /20230417/WXO-DD/observations/swob-ml/20230417/CPRJ/2023-04-17-2033-CPRJ-AUTO-minute-swob.xml
2023-04-17 20:33:42,767 - __main__ - INFO - 26 - [x] Done
2023-04-17 20:33:42,792 - __main__ - INFO - 25 - [x] Received 20230417203341.618 https://hpfx.collab.science.gc.ca /20230417/WXO-DD/observations/swob-ml/20230417/CPRJ/2023-04-17-2027-CPRJ-AUTO-minute-swob.xml
2023-04-17 20:33:42,792 - __main__ - INFO - 26 - [x] Done
2023-04-17 20:33:42,802 - __main__ - INFO - 25 - [x] Received 20230417203341.352 https://hpfx.collab.science.gc.ca /20230417/WXO-DD/observations/swob-ml/partners/bc-env-aq/20230416/94/2023-04-16-2300-bc-env-aq-94-AUTO-swob.xml
2023-04-17 20:33:42,802 - __main__ - INFO - 26 - [x] Done
2023-04-17 20:33:42,828 - __main__ - INFO - 25 - [x] Received 20230417203341.620 https://hpfx.collab.science.gc.ca /20230417/WXO-DD/observations/swob-ml/20230417/CWWB/2023-04-17-2033-CWWB-AUTO-minute-swob.xml
2023-04-17 20:33:42,828 - __main__ - INFO - 26 - [x] Done
2023-04-17 20:33:42,860 - __main__ - INFO - 25 - [x] Received 20230417203341.621 https://hpfx.collab.science.gc.ca /20230417/WXO-DD/observations/swob-ml/20230417/CXGD/2023-04-17-2033-CXGD-AUTO-minute-swob.xml
2023-04-17 20:33:42,860 - __main__ - INFO - 26 - [x] Done
2023-04-17 20:33:42,990 - __main__ - INFO - 25 - [x] Received 20230417203342.716 https://hpfx.collab.science.gc.ca /20230417/WXO-DD/observations/swob-ml/20230417/CPIF/2023-04-17-2033-CPIF-AUTO-minute-swob.xml
2023-04-17 20:33:42,991 - __main__ - INFO - 26 - [x] Done
2023-04-17 20:33:43,045 - __main__ - INFO - 25 - [x] Received 20230417203342.718 https://hpfx.collab.science.gc.ca /20230417/WXO-DD/observations/swob-ml/20230417/CGCH/2023-04-17-2033-CGCH-AUTO-minute-swob.xml
2023-04-17 20:33:43,045 - __main__ - INFO - 26 - [x] Done
2023-04-17 20:33:43,097 - __main__ - INFO - 25 - [x] Received 20230417203342.71

"""

def message_callback_regional_gems(ch, method, properties, body):
    """This callback gets called on events that relate to the regional
    gems model.  This callback will do the following:

    a) determine if the message is related to a piece of data we are
       interested in.
    b) if yes then write to cache that what we are looking for is available.
      - having successfully cached the message, send and acknowledgement
        for the message back to the message queue
    c) checks to see if we now have all the data we are expecting
    d) if so then triggers a new event to currently, the github action
        that will initiate a data pipeline.
    e) having recieved a 200 status from that request, will now iterate
       over all the messages in memory


    :param ch: _description_
    :param method: _description_
    :param properties: _description_
    :param body: _description_
    """
    msg = f" [x] Received {body.decode()}"

    LOGGER.info(msg)
    LOGGER.info(" [x] Done")

    # collecting events related to either:
    # *  gems regional model
    # *  gems global model


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