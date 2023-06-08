    """ Creates an api that initially will provide a health check endpoint
    to allow for monitoring of the api.  This will be expanded later to provide
    visibility into the status of cached events, and events recieved by the
    listener (AMQP) process.
    """

import logging

import fastapi
import listener_api_routes

# this code might be a main_api.py file
app = fastapi.FastAPI()
router = listener_api_routes.API_Routes()
app.include_router(router.router)


LOGGER = logging.getLogger(__name__)