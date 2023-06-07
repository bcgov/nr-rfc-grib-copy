
FROM python:3.11.3-alpine3.17

WORKDIR /app
COPY ["./backend/", \
      "scripts/src/GetGribConfig.py", \
      "/app/"]

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

#
# COPY ./app /code/app
EXPOSE 8000

# should run be init with uvicorn app.main:app --reload --host
# CMD ["python", "/app/main.py"]
CMD ["uvicorn", "main:app", "--port=8000", "--host=0.0.0.0"]
