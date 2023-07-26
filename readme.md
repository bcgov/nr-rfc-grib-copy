# Overview

Re-worked an existing process that previously ran on prem via windows scheduler
using a wget command to retrieve the original data.  Problems with the
current process include:

* is configured to run on prem and is not scaleable
* takes a while to download and process all the data
* schedule does not always align with the availability of data
* is not robust, fails if a network hickup occurs.

This repo represents the evolution of this process, and will eventually be used
to create an event driven data pipeline that will be triggered by the federal
governments Advanced Message Queue Protocol (AMQP).  The pipeline will then:

1. download the grib2 files
1. process the grib2 files
1. prepare the grib2 data for input into the CLEVER model.

The new process will monitor for a 200 status code.  If it doesn't recieve the 200
status code response then the downloader will pause and retry until it succeeds.

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

The message queue code is in the `backend` folder.  The subscriber creates a long
running process that will monitor the event queue for specific events that identify
that the expected data for the CMC pipeline is ready for download.  When the data
becomes available, it will trigger a downstream proces.  In this case a github
action via the remote_workflow rest call.

To init the backend for development purposes:

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
uvicorn main:app --port=8000 --host=0.0.0.0 --reload
```

#### environment variables used by the subscriber

**DB_FILE_PATH**: example (sqlite:////data/event_database.db) where to find the sqllite database file
**AMPQ_USERNAME**: the username for the AMQP
**AMPQ_PASSWORD**: the password for the AMQP
**AMPQ_DOMAIN**: the domain for the AMQP

## Testing containerization

Build/Create the image:

`docker build -t listener:listener .`

Run the image

`docker run --env-file=.env -v $PWD/cmc_cansip/data:/data  -p 8000:8000 listener:listener`

Once the image is running check the healthz end point

# Testing Remote job trigger / Manual Trigger

The following is an example of calling a github action that has a remote_workflow
execution type defined for it:

curl -H "Accept: application/vnd.github.everest-preview+json" \
    -H "Authorization: token <insert github personal access toke>" \
    --request POST \
    --data '{"event_type": "<the type defined for the action>", "message": "mymessage"}' \
    https://api.github.com/repos/<repo-org>/<repository_name>/dispatches

The following is an example of a job that has been triggered using a webhook:
https://github.com/bcgov/nr-rfc-grib-copy/actions/runs/5273197792/jobs/9536328668

Recieving this in a github action:

``` yaml
...
jobs:
  build:
    name: Run Some Thing
    runs-on: ubuntu-latest
    steps:
      - env:
          MESSAGE: ${{ github.event.client_payload.message }}
        name: Do Something
        run: |
          echo Doing Something...
          echo Incomming message: $MESSAGE
```

should print out:

```
Doing Something...
Incomming message: mymessage
```

# Cycle the token

[See this doc](docs/Cycle_remote_token.md)
