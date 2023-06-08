

import logging

import fastapi

LOGGER = logging.getLogger(__name__)


class API_Routes:
    def __init__(self, listener):
        self.router = fastapi.APIRouter()
        self.listener = listener
        self.router.add_api_route("/healthz", self.health, methods=["GET"])
        self.router.add_api_route("/", self.root, methods=["GET"])
        self.router.add_api_route("/msg_id", self.message_count, methods=["GET"])

    async def health(self, response: fastapi.Response):
        payload = {"status": "ok"}
        healthy = False
        if (self.listener) and self.listener._connection and self.listener._channel:
            connection = self.listener._connection.is_open
            channel = self.listener._channel.is_open
            LOGGER.info(f"connection: {connection}, channel: {channel}")
            if connection and channel:
                healthy = True
        if not healthy:
            response.status_code = fastapi.status.HTTP_503_SERVICE_UNAVAILABLE
            payload['status'] = 'error'
        return payload

    async def root(self):
        return {"message": "Hello World"}

    async def message_count(self):
        return {'messageid': self.listener.cur_message_tag}

