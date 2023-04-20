import logging

import pika
import util.config as config

LOGGER = logging.getLogger(__name__)

class MSCDataMartSubscriber:
    """utility class to setup communication with AMQP

        ampq_url: the amqp url form is amqps://user:password@host/?params
        callback_reference: the function that will be called when an event that
            matches the topic is called
            callback needs to recieve the following args:
                * ch - blockingchannel
                * method - the message object
                * properties object describing the message
                * body - message string in the format:
                    datetimestamp - 20230418190118.288
                    source data host - https://hpfx.collab.science.gc.ca
                    filepath - the file path for the data on the ^^ source data host

                    example string: b' https://hpfx.collab.science.gc.ca /20230418/WXO-DD/observations/swob-ml/20230418/CXKI/2023-04-18-1900-CXKI-AUTO-swob.xml'
    """
    # TODO: define the return type for the callback_reference once the
    #       args and their type are defined
    def __init__(self, ampq_url: str, exchange_name: str, queue_name: str):

        LOGGER.debug(f"ampq_url: {ampq_url}")
        self.ampq_url = ampq_url
        url_params = pika.URLParameters(self.ampq_url)

        self.exchange_name = exchange_name
        self.queue_name = queue_name

        self.connection = pika.BlockingConnection(url_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def add_topic(self, topic_str):
        LOGGER.info(f"binding the channel to the topic: {topic_str}")
        self.channel.queue_bind(
            exchange='xpublic', queue=self.queue_name, routing_key=topic_str)

    def start_listening(self, callback):
        """initiates the long running process that will listen for events on the
        AMQP server and make calls to the callback function provided in the
        configuration.
        """
        LOGGER.info("starting listener...")
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback,
            auto_ack=False)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.queue_delete(self.queue_name)
            self.channel.close()







