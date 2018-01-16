#!/bin/bash
#
# The user environment settings don't get passed down so
# we have to explicitly set which python interpreter to use.
# This also sets the search path correctly for anaconda and
# Picarro python modules.
# 
export PATH=/home/picarro/anaconda2/bin:$PATH
export PYTHONPATH=/home/picarro/SI2000:$PYTHONPATH
cd /usr/local/picarro/qtLauncher
python -O qtLauncher.py

