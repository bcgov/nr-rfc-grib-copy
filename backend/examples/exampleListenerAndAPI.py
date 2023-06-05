import asyncio
import functools
import json
import logging
import os
import queue
import threading
import time
from typing import Any, Dict

import fastapi
import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exchange_type import ExchangeType

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
LOGGER = logging.getLogger(__name__)


class AsyncioDataMart(object):
    EXCHANGE = 'xpublic'
    EXCHANGE_TYPE = ExchangeType.topic
    PUBLISH_INTERVAL = 1
    QUEUE = 'q_anonymous.fastapi.listener'
    ROUTING_KEYS = ['v02.post.*.WXO-DD.#']

    def __init__(self, amqp_url):
        self._connection = None
        self._channel = None

        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0

        self._stopping = False
        self._url = amqp_url

    def connect(self):
        LOGGER.info('Connecting to %s', self._url)
        return AsyncioConnection(
            pika.URLParameters(self._url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed)

    def on_connection_open(self, connection):
        LOGGER.info('Connection opened')
        self._connection = connection
        LOGGER.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_open_error(self, _unused_connection, err):
        LOGGER.error('Connection open failed: %s', err)

    def on_connection_closed(self, _unused_connection, reason):
        LOGGER.warning('Connection closed: %s', reason)
        self._channel = None

    def on_channel_open(self, channel):
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        LOGGER.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        LOGGER.warning('Channel %i was closed: %s', channel, reason)
        self._channel = None
        if not self._stopping:
            self._connection.close()

    def setup_exchange(self, exchange_name):
        LOGGER.info('Declaring exchange %s', exchange_name)
        # Note: using functools.partial is not required, it is demonstrating
        # how arbitrary data can be passed to the callback when it is called
        cb = functools.partial(self.on_exchange_declareok, userdata=exchange_name)
        self._channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=self.EXCHANGE_TYPE,
            passive=True,
            durable=True,
            callback=cb)

    def on_exchange_declareok(self, _unused_frame, userdata):
        LOGGER.info('Exchange declared: %s', userdata)
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        LOGGER.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(queue=queue_name, callback=self.on_queue_declareok)

    def on_queue_declareok(self, _unused_frame):
        """defines the topics that the listener will listen for

        :param _unused_frame: _description_
        """
        for routing_key in self.ROUTING_KEYS:
            LOGGER.info('Binding %s to %s with %s', self.EXCHANGE, self.QUEUE, routing_key)
            self._channel.queue_bind(
                self.QUEUE,
                self.EXCHANGE,
                routing_key=routing_key,
                callback=self.on_bindok)

    def on_bindok(self, _unused_frame):
        LOGGER.info('Queue bound')

        self.start_publishing()


    def on_delivery_confirmation(self, method_frame):
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        LOGGER.info('Received %s for delivery tag: %i', confirmation_type, method_frame.method.delivery_tag)
        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1
        self._deliveries.remove(method_frame.method.delivery_tag)
        LOGGER.info(
            'Published %i messages, %i have yet to be confirmed, '
            '%i were acked and %i were nacked', self._message_number,
            len(self._deliveries), self._acked, self._nacked)

app = fastapi.FastAPI()
ep = None

@app.on_event("startup")
async def startup() -> None:
    """gets run when the api starts, inits the rabbitmq listener process
    """
    global ep
    url = 'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca/?heartbeat=600&blocked_connection_timeout=300'
    LOGGER.info('starting listener...')
    ep = AsyncioDataMart(url)
    ep.connect()
    await asyncio.sleep(5) # Wait for MQ

JSONObject = Dict[str, Any]

@app.get("/")
async def root() -> JSONObject:
    return {"message": "Hello World"}

@app.get("/healthz", status_code=fastapi.status.HTTP_200_OK)
async def healthz(response: fastapi.Response) -> JSONObject:
    global ep
    payload = {"status": "ok"}
    healthy = False
    if (ep) and ep._connection and ep._channel:
        connection = ep._connection.is_open
        channel = ep._channel.is_open
        LOGGER.info(f"connection: {connection}, channel: {channel}")
        if connection and channel:
            healthy = True
    if not healthy:
        response.status_code = fastapi.status.HTTP_503_SERVICE_UNAVAILABLE
        payload['status'] = 'error'
    return payload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
