#!/bin/bash
#
# The user environment settings don't get passed down so
# we have to explicitly set which python interpreter to use.
# This also sets the search path correctly for anaconda and
# Picarro python modules.
# 
export PATH=/home/picarro/anaconda2/bin:$PATH
export PYTHONPATH=/home/picarro/git/host/src/main/python:$PYTHONPATH
export PICARRO_CONF_DIR=/home/picarro/git/host/src/main/python
export PICARRO_LOG_DIR=/home/picarro/I2000/Log
cd /home/picarro/git/host/src/main/python/Host/pydCaller;
python -O Supervisor.py -f -c ../../AppConfig/Config/Supervisor/supervisor_simulation.ini

