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
cwd=$(pwd)

ln -s $cwd/AppConfig ../../src/main/python/AppConfig
ln -s $cwd/CommonConfig/ ../../src/main/python/
ln -s $cwd/InstrConfig/ ../../src/main/python/
