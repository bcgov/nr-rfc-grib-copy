# Running Climate Forecast Script (cmc)

## Background

The cmc scripts will:
* download the data from the environment canada hpfx server
* extract the grib2 data into the various T1... T4, and P1 ... P4 files

Each file contains a series of lat longs and values for data that has been
extracted from the grib2 data.


## Prerequisites

The script requires the wgrib2 binary to extract data from the various grib2
formatted files.

The github action run is tied to this repository which has a cached binary
artifact with the grib2 binary compiled for x86 linux as well as github
actions to build the various artifacts.

https://github.com/franTarkenton/wgrib2-Cygwin-Build

The actions will grab the binary from the repo, however when running locally
you will have to either download the binary (if running under WSL), or compile
it yourself.



### Compile WGRIB2 Utility - Local development

To run / debug the scripts locally you will need a binary wgrib2 utility.

* Navigate to the wgrib folder
```
cd scripts/src/wgrib2
```

* get the source code, extract it, and change to that directory
```
wget -c ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz
tar -xzvf wgrib2.tgz
cd grib2
```

* Ensure you have the required dependencies

``` sh
sudo apt install -y build-essential libaec-dev zlib1g-dev libcurl4-openssl-dev libboost-dev curl wget zip unzip bzip2 gfortran gcc g++ cmake
```

* set compiler flag env vars and compile
```
export CC=gcc
export FC=gfortran
make
```

* copy the binary to the expected directory

```
cp wgrib2/wgrib2 ../.

```

* verify that things are setup

```
# return the the root of the project directory
cd ../../../../

# update paths
export PATH=$PATH:$(pwd)/scripts/src/wgrib2

# test the binary - should return usage details.
wgrib2
```

* cleanup - assuming working
```
rm -rf ./scripts/src/wgrib2/grib2
```

### Download the Binary

or... rather than compile you can just download the binary from the repo
mentioned previously

* download the binary

```
curl -L -o scripts/src/wgrib2/wgrib2 https://github.com/franTarkenton/wgrib2-Cygwin-Build/releases/download/20230203-0000/wgrib2
```

* set the executable flag, and add dir to PATHS
```
chmod +x scripts/src/wgrib2/wgrib2
export PATH=$PATH:$(pwd)/scripts/src/wgrib2
```

* test
```
wgrib2
```

