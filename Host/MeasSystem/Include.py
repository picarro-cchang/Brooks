#!/usr/bin/python
#
# File Name: Include.py
# Purpose:
#   This is a set of includes that are used to mesh MeasSys.py and
#   SpectrumManager.py
#
# Notes:
#
# ToDo:
#
# File History:
# 06-06-20 russ  First release

from SharedTypes import CrdsException
from SharedTypes import RPC_PORT_MEAS_SYSTEM, RPC_PORT_DRIVER, RPC_PORT_LOGGER, RPC_PORT_ARCHIVER
from SharedTypes import ACCESS_PICARRO_ONLY

class MeasSystemError(CrdsException):
    """Base class for MeasSystem errors."""
