"""
Starts the listener process and the api
"""

# TODO:
# - init the database
# - init the api/amqp listener
# - tie together with config.

import asyncio
import logging
import logging.config
import os

import fastapi
import messaging.api_routes
import messaging.cmc_grib_callbacks
import messaging.listener
import util.config
import util.file_path_config
import util.grib_file_config

# configure logging
log_file_path = util.file_path_config.get_log_config_file_path()
logging.config.fileConfig(log_file_path)
LOGGER = logging.getLogger(__name__)
LOGGER.info(f"log config: {log_file_path}")

# holder for the listener object
async_listener = None

# setup the message cache
grib_callback = messaging.cmc_grib_callbacks.CMC_Grib_Callback()

# setup the queue and exchange parameters
q_name = util.config.get_amqp_queue_name()
exchange_name = util.config.get_amqp_exchange_name()
ampq_url = util.config.get_amqp_url()
grib_config = util.grib_file_config.GribFiles()
topic_strings = grib_config.get_all_topic_strings()

# debugging
# topic_strings = ['v02.post.*.WXO-DD.#']
# q_name = 'q_anonymous.fastapi.listener.testing1'


listener = messaging.listener.AsyncioDataMart(
    amqp_url=ampq_url,
    exchange_name=exchange_name,
    queue_name=q_name,
    topic_strings=topic_strings,
    on_message_callback=grib_callback.cmc_callback
)

# setup the api
app = fastapi.FastAPI()
router = messaging.api_routes.API_Routes(listener, grib_callback)
app.include_router(router.router)

@app.on_event("startup")
async def startup() -> None:
    """gets run when the api starts, inits the rabbitmq listener process
    """
    global async_listener
    LOGGER.info('starting listener...')
    async_listener = listener.connect()
    # async_listener.ioloop.run_forever()
    await asyncio.sleep(5) # Wait for MQ

    LOGGER.info('startup complete')

if __name__ == "__main__":
    # adding this script to run through the debugger
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
