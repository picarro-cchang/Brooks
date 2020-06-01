#!/bin/bash


# To run the uncompiled python code (for example for
# debugging), the ini files need to be in a specific
# directories.
#
# Clone a project from github: picarro/host.
# Select an analyzer configs and run this script. For
# example, cd to  ~/git/host/Config/AMADS and
# run setDevLinks.sh.
#
# This will set links in the source tree so that when
# you run the VirtualAnalyzer.sh or Supervisor.py
# the processes can find their ini files, schemes,
# and scripts.
#
# Edit:
# Some config files now reference other files in the
# binary installation directory '/home/picarro/I2000'.
# Add additional soft links so that the files can
# still be found without requiring us to build and
# install a package.
#
# We are assuming this script is run from 
# /home/picarro/git/host/Config/<analyzer type>/bin


cd ..

CWD=$(pwd)
GIT_DIR="${HOME}/git/host"
SOURCE_DIR="${GIT_DIR}/src/main/python/"
COMMON_CONFIG_DIR="${GIT_DIR}/Config/CommonConfig"
HOST_DIR="${HOME}/I2000"
TIMESTAMP=`date +"%Y-%m-%d_%H%M%S"`

# Clean up any existing symlinks in the source code
if [ -d "../../src/main/python/AppConfig" ]; then
    rm ../../src/main/python/AppConfig
fi

if [ -d "../../src/main/python/CommonConfig" ]; then
    rm ../../src/main/python/CommonConfig
fi

if [ -d "../../src/main/python/InstrConfig" ]; then
    rm ../../src/main/python/InstrConfig
fi

if [ -d "./CommonConfig" ]; then
    rm ./CommonConfig
fi

# Create symbolic links in the source code
ln -s ../CommonConfig
ln -s ${CWD}/AppConfig ../../src/main/python
ln -s ${CWD}/CommonConfig/ ../../src/main/python
ln -s ${CWD}/InstrConfig/ ../../src/main/python

# Make a temporary backup of InstrConfig to recover later
if [ -d "${HOST_DIR}/InstrConfig" ]; then

    cp -rv ${HOST_DIR}/InstrConfig /tmp/InstrConfig
fi

# Archive a timestamped backup of I2000 if it exists
if [ -d ${HOST_DIR} ]; then
    mv -v ${HOST_DIR} ${HOST_DIR}_backup_${TIMESTAMP}
fi

mkdir -p ${HOST_DIR}

# If we already had a running instrument, let's recover that
# instead of running from git default paramaters
if [ -d "/tmp/InstrConfig" ]; then
    mv -v /tmp/InstrConfig ${HOST_DIR}/InstrConfig
else
    ln -sv ${CWD}/InstrConfig ${HOST_DIR}
fi

# Create symbolic links for everything else
ln -sv ${CWD}/AppConfig ${HOST_DIR}
ln -sv ${COMMON_CONFIG_DIR} ${HOST_DIR}
ln -sv ${SOURCE_DIR}/Firmware ${HOST_DIR}
ln -sv ${SOURCE_DIR}/Host ${HOST_DIR}

# Create an installerSignature so we don't get an EEPROM
# error log message on Driver startup
echo "SOURCE" > ${HOST_DIR}/installerSignature.txt

# Compile the fitter
cd ${SOURCE_DIR}/Host/Fitter
bash makeFitutils

