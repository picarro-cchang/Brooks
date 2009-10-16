#!/usr/bin/python
#
# File Name: MeasSystemStates.py
# Purpose:
#   Contains the possible state numbers and their human readable names/
#
# Notes:
#   This was removed from the main MeasSystem.py file in order to allow other
#   modules to use it if needed.

# ToDo:
#
# File History:
# 06-12-19 russ  First release

MEAS_STATE__UNDEFINED = -100
MEAS_STATE_ERROR = 0x0F
MEAS_STATE_INIT = 0
MEAS_STATE_READY = 1
MEAS_STATE_ENABLED = 2
MEAS_STATE_SHUTDOWN = 3

MeasStateName = {}
MeasStateName[MEAS_STATE__UNDEFINED] = "<ERROR - UNDEFINED STATE!>"
MeasStateName[MEAS_STATE_ERROR] = "ERROR"
MeasStateName[MEAS_STATE_INIT] = "INIT"
MeasStateName[MEAS_STATE_READY] = "READY"
MeasStateName[MEAS_STATE_ENABLED] = "ENABLED"
MeasStateName[MEAS_STATE_SHUTDOWN] = "SHUTDOWN"
