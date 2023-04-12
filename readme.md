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

Remains a work in progress, but initially it will listen for messages using the
topic: 


