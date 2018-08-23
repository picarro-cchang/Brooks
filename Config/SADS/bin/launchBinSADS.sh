#!/bin/bash
#
# The user environment settings don't get passed down so
# we have to explicitly set which python interpreter to use.
# This also sets the search path correctly for anaconda and
# Picarro python modules.
# 
export PATH=/home/picarro/anaconda2/bin:$PATH
cd /home/picarro/I2000/Host/pydCaller/
python -O Supervisor.py -c ../../AppConfig/Config/Supervisor/supervisorEXE_SADS_140Torr.ini

