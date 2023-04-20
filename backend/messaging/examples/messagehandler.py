import os

import nats
from nats.js.api import DeliverPolicy


class MessageHandler:
    """
        This class handles connection nats jetstream and does push subscription.
    """

    def __init__(self, subject, queue, durable):
        self.durable = durable
        self.subject = subject
        self.queue = queue
        self.callback = self.qsub_b

    async def connect(self):
        """
            This method connects to nats jetstream and does push subscription.
        """
        nc = await nats.connect(os.getenv("NATS_URL", "nats://localhost:4222"))
        js = nc.jetstream()
        await js.subscribe(self.subject, self.queue, cb=self.callback, durable=self.durable, stream="EVENTS",
                           deliver_policy=DeliverPolicy.NEW)

    async def qsub_b(self, msg):
        print("QSUB B:", msg)
        await msg.ack()
