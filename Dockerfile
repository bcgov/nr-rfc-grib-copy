
FROM python:3.11.3-alpine3.17

WORKDIR /app
COPY ["./backend/requirements.txt", "./backend/messaging/read_messages_noack.py", "/app/"]

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

#
# COPY ./app /code/app

# #
CMD ["python", "/app/read_messages_noack.py"]
