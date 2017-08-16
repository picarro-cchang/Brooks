#!/bin/bash
#
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
#
cd ..
cwd=$(pwd)

# Set source tree links
#
if [ -d "../../src/main/python/AppConfig" ] 
then
    rm ../../src/main/python/AppConfig
fi

if [ -d "../../src/main/python/CommonConfig" ] 
then
    rm ../../src/main/python/CommonConfig
fi

if [ -d "../../src/main/python/InstrConfig" ] 
then
    rm ../../src/main/python/InstrConfig
fi

if [ -d "./CommonConfig" ] 
then
    rm ./CommonConfig
fi

ln -s ../CommonConfig
ln -s $cwd/AppConfig ../../src/main/python
ln -s $cwd/CommonConfig/ ../../src/main/python
ln -s $cwd/InstrConfig/ ../../src/main/python


# Set installed package links
#
if [ -d "/home/picarro/I2000/AppConfig" ] 
then
    rm /home/picarro/I2000/AppConfig
fi

if [ -d "/home/picarro/I2000/CommonConfig" ] 
then
    rm /home/picarro/I2000/CommonConfig
fi

if [ -d "/home/picarro/I2000/InstrConfig" ] 
then
    rm /home/picarro/I2000/InstrConfig
fi

if [ -d "/home/picarro/I2000/Firmware" ] 
then
    rm /home/picarro/I2000/Firmware
fi

mkdir -p /home/picarro/I2000

ln -s $cwd/AppConfig /home/picarro/I2000
ln -s $cwd/CommonConfig /home/picarro/I2000
ln -s $cwd/InstrConfig /home/picarro/I2000
ln -s /home/picarro/git/host/src/main/python/Firmware /home/picarro/I2000

cd /home/picarro/git/host/src/main/python/Host/Fitter
bash makeFitutils
