import asyncio
import logging

import nest_asyncio
from fastapi import FastAPI

# from app.messaging.messagehandler import MessageHandler

app = FastAPI(title="Consumer Python", version="0.0.1")
# jsMsgHandler = MessageHandler("EVENTS-TOPIC", "consumer-python", "consumer-python")


# Define the filter
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] != "/"


# Add filter to the logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


# async def connect():
#     await jsMsgHandler.connect()


# nest_asyncio.apply()
# asyncio.run(connect())


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
