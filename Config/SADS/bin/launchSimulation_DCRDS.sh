#!/bin/bash
#
# The user environment settings don't get passed down so
# we have to explicitly set which python interpreter to use.
# This also sets the search path correctly for anaconda and
# Picarro python modules.
# 
export PATH=/home/picarro/anaconda2/bin:$PATH
export PYTHONPATH=/home/picarro/git/host/src/main/python:$PYTHONPATH
export PICARRO_CONF_DIR=/home/picarro/I2000
export PICARRO_LOG_DIR=/home/picarro/I2000/Log
#export GTK_DATA_PREFIX=""
#export GTK2_RC_FILES=/usr/share/themes/Greybird/gtk-2.0/gtkrc
#export COVERAGE_PROCESS_START=/home/picarro/.coveragerc
cd /home/picarro/git/host/src/main/python/Host/pydCaller;
python Supervisor.py -f -c ../../AppConfig/Config/Supervisor/supervisor_simulation_DCRDS.ini

