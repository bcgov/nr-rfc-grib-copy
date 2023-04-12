#!/bin/bash

# License for this script is GNU 2

# A small bash script to download, compile and install latest wgrib2 from source. 
# I have written this script so that I can automate the proceedure whenever I change Linux OS 

# Make it executable before running the script using'chmod +x ./wgrib2_auto_compile_script.sh'
# Ensure to run the script with sudo (sudo ./wgrib2_auto_compile_script.sh) or under root environment


# Update the repo
apt update

# Install necessary development packages required for compilation
# Tested on Ubuntu 18.04 and 19.04
apt install -y build-essential libaec-dev zlib1g-dev libcurl4-openssl-dev libboost-dev curl wget zip unzip bzip2 gfortran gcc g++

# Make a working directory for cimpilation
mkdir -p ~/Downloads/wgrib2


# Move to working directory
cd ~/Downloads/wgrib2

# Download the latest wgrib2 source code
wget -c ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz

# Extract the source to current directory
tar -xzvf wgrib2.tgz

# Have to remove the .linuxbrew paths for the build to work
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/lib/wsl/lib

# Move to main grib directory for compilation
cd grib2

# Export the flags which are important for compalation. 
# If you are using different compilers then the flag is to be modified accordingly
export CC=gcc
export FC=gfortran

# Compile and make binary
make

# Check if the wgrib2 binary is made properly. Not necessary but you can see some output for info
wgrib2/wgrib2 -config

# Remove previous install of grib2 directory
rm -rfv /usr/local/grib2/

# Create the removed directory
mkdir -p /usr/local/grib2/

# Copy the wgrib2 binary to bin directory
# so that it can be executed directly from terminal
cp -rfv wgrib2/wgrib2 /usr/local/bin/wgrib2

# Move out of current working directory
cd ~

# Remove the working directoy.
rm -rfv ~/Downloads/wgrib2

# All fininshed. Now type wgrib2 in terminal and enter. You should see the list of all option wgrib2 supports.