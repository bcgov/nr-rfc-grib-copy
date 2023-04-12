# Data is in grib2 format, need the wgrib2 to read the file

* for now can just build the component on every run to get up and running
* shortly after should cache an artifact and only build if the artifact doesn't
  exist.


# local install

```
wget -c ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz
tar -xzvf wgrib2.tgz
cd grib2
export CC=gcc
export FC=gfortran
make
# test
grib2/wgrib2 -config
# use
export PATH=$PATH;$(pwd)/grib2
```

or just get the binary 

```
curl -L -o wgrib2 https://github.com/franTarkenton/wgrib2-Cygwin-Build/releases/download/20230203-0000/wgrib2
```

