import functools
import logging
import os

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exchange_type import ExchangeType

LOGGER = logging.getLogger(__name__)


class AsyncioDataMart(object):
    # EXCHANGE = 'xpublic'
    # EXCHANGE_TYPE = ExchangeType.topic
    # QUEUE = 'q_anonymous.fastapi.listener'
    # ROUTING_KEYS = ['v02.post.*.WXO-DD.#']

    def __init__(
        self,
        amqp_url: str,
        exchange_name: str,
        queue_name: str,
        topic_strings: list[str],
        on_message_callback=None,
    ):
        self.exchange_name = exchange_name
        self.exchange_type = ExchangeType.topic
        self.queue_name = queue_name
        self.topic_strings = topic_strings

        self.was_consuming = False
        self.should_reconnect = False

        self._connection = None
        self._channel = None

        self._stopping = False
        self._url = amqp_url

        self._consumer_tag = None
        self._closing = False
        self._consuming = False

        # In production, experiment with higher prefetch values
        # for higher consumer throughput
        self._prefetch_count = 1

        self.on_message_callback = on_message_callback
        self.cur_message_tag = None

    def connect(self):
        LOGGER.info("Connecting to %s", self._url)
        return AsyncioConnection(
            pika.URLParameters(self._url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed,
        )

    def on_connection_open(self, connection):
        LOGGER.info("Connection opened")
        self._connection = connection
        LOGGER.info("Creating a new channel")
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_open_error(self, _unused_connection, err):
        LOGGER.error("Connection open failed: %s", err)

    def on_connection_closed(self, _unused_connection, reason):
        LOGGER.warning("Connection closed: %s", reason)
        self._channel = None

    def on_channel_open(self, channel):
        LOGGER.info("Channel opened")
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.exchange_name)

    def add_on_channel_close_callback(self):
        LOGGER.info("Adding channel close callback")
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        LOGGER.warning("Channel %i was closed: %s", channel, reason)
        self._channel = None
        if not self._stopping:
            self._connection.close()

    def setup_exchange(self, exchange_name):
        LOGGER.info("Declaring exchange %s", exchange_name)
        # Note: using functools.partial is not required, it is demonstrating
        # how arbitrary data can be passed to the callback when it is called
        cb = functools.partial(self.on_exchange_declareok, userdata=exchange_name)
        self._channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=self.exchange_type,
            passive=True,
            durable=True,
            callback=cb,
        )

    def on_exchange_declareok(self, _unused_frame, userdata):
        LOGGER.info("Exchange declared: %s", userdata)
        self.setup_queue(self.queue_name)

    def setup_queue(self, queue_name):
        LOGGER.info("Declaring queue %s", queue_name)
        self._channel.queue_declare(queue=queue_name, callback=self.on_queue_declareok)

    def on_queue_declareok(self, _unused_frame):
        """defines the topics that the listener will listen for

        :param _unused_frame: _description_
        """
        for routing_key in self.topic_strings:
            LOGGER.info(
                "Binding %s to %s with %s", self.exchange_name, self.queue_name, routing_key
            )
            self._channel.queue_bind(
                self.queue_name,
                self.exchange_name,
                routing_key=routing_key,
                callback=self.on_bindok,
            )

    def on_bindok(self, _unused_frame):
        LOGGER.info("Queue bound")
        self.set_qos()

    def set_qos(self):
        """This method sets up the consumer prefetch to only be delivered
        one message at a time. The consumer must acknowledge this message
        before RabbitMQ will deliver another one. You should experiment
        with different prefetch values to achieve desired performance.

        """
        LOGGER.debug("setting QOS")
        self._channel.basic_qos(prefetch_count=self._prefetch_count, callback=self.on_basic_qos_ok)

    def on_basic_qos_ok(self, _unused_frame):
        """Invoked by pika when the Basic.QoS method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method _unused_frame: The Basic.QosOk response frame

        """
        LOGGER.info("QOS set to: %d", self._prefetch_count)
        self.start_consuming()

    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        LOGGER.info("Issuing consumer related RPC commands")
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.queue_name, self.on_message)
        self.was_consuming = True
        self._consuming = True

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        LOGGER.info("Adding consumer cancellation callback")
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        LOGGER.info("Consumer was cancelled remotely, shutting down: %r", method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, _unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel _unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param bytes body: The message body

        """
        LOGGER.info(
            "Received message # %s from %s: %s",
            basic_deliver.delivery_tag,
            properties.app_id,
            body,
        )
        self.cur_message_tag = basic_deliver.delivery_tag
        if self.on_message_callback is not None:
            # sending the callback the body and the channel so that it can
            # determine whether or not to ack the message
            # callback should handle the ack
            self.on_message_callback(body, basic_deliver.delivery_tag, self._channel)
        else:
            LOGGER.info("no callback defined, acknowledge message")
            self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        LOGGER.info("Acknowledging message %s", delivery_tag)
        self._channel.basic_ack(delivery_tag)
