# Overview

Reworking of an existing process.  Existing process is deployed on prem using
bat files / wget / windows scheduler to download CMC data.  Problems with the
current process include:

* is configured to run on prem and is not scaleable
* takes a while to download and process all the data
* schedule does not always align with the availability of data

This repo represents the evolution of this process, and will eventually be used
to create an event driven data pipeline that will be triggered by the federal
governments Advanced Message Queue Protocol (AMQP).  The pipeline will then:

1. download the grib2 files
1. process the grib2 files
1. prepare the grib2 data for input into the CLEVER model.

# Components of the Repository:

## grib download and extract

The entire download and extract process is summarized in the [github action](.github/workflows/copy_cansip_grib_files copy.yaml)
which will:

1. configure the python env and install the dependencies
1. download the wgrib2 binary package
1. Run the python script that:
  1. downloads the CMC data from the federal government
  1. uses the wgrib2 binary to extract data and cache it temporarily
  1. upload the grib files and the processed data to on prem object
     storage

## message queue subscriber

The message queue code is in the `backend` folder.  To init the backend for
development:

``` bash
# create the virtual environment if not created already
python3 -m venv venv
# activate the virtual environment
. venv/bin/activate
# install the dependencies into the virtual environment
pip install -r requirements.txt -r requirements-dev.txt
# start the backend process
python backend/main.py

# or run through uvicorn
export DB_FILE_PATH=sqlite:///../data/event_database.db
dotenv
cd backend
uvicorn main:app --port=8000 --host=0.0.0.0
```

#### environment variables used by the subscriber

**DB_FILE_PATH**: example (sqlite:////data/event_database.db) where to find the sqllite database file
**AMPQ_USERNAME**: the username for the AMQP
**AMPQ_PASSWORD**: the password for the AMQP
**AMPQ_DOMAIN**: the domain for the AMQP

## Testing containerization

Create the image:

`docker build -t listener:listener .`

Run the image

`docker run --env-file=.env -v $PWD/cmc_cansip/data:/data  -p 8000:8000 listener:listener`

Once the image is running check the healthz end point
