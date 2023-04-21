
FROM python:3.11.3-alpine3.17

# ENV DB_FILE_PATH docker.db
# ENV AMPQ_USERNAME anonymous
# ENV AMPQ_PASSWORD anonymous
# ENV AMPQ_DOMAIN
# ENV CLOUDAMQP_URL
 


WORKDIR /app
COPY ["./backend/", \
      "scripts/src/GetGribConfig.py", \
      "/app/"]

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

#
# COPY ./app /code/app

# #
CMD ["python", "/app/main.py"]
