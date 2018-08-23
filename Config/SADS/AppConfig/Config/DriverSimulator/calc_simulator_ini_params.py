import numpy as np

from configobj import ConfigObj
from Host.DriverSimulator.Simulators import LaserDacModel, LaserOpticalModel

fname = "./SADS_Analyzer_Setup.ini"
aLaserNum = input("Actual laser number (1-4)? ")

name = "Laser%d" % aLaserNum
opticalModel = None
dacModel = None

config = ConfigObj(fname)
print config
for section in config:
    if section.startswith(name):
        if section.endswith("OpticalModel"):
            opticalModel = LaserOpticalModel(**config[section])
        elif section.endswith("DacModel"):
            dacModel = LaserDacModel(**config[section])

if opticalModel is None:
    opticalModel = LaserOpticalModel()
if dacModel is None:
    dacModel = LaserDacModel()

print "Enter the following from the SETTINGS section of the MakeWlmFile1.ini file"
print
LASER_CURRENT = input("LASER_CURRENT (digU)? ")
TEMP_MIN = input("TEMP_MIN (degC)? ")
TEMP_MAX = input("TEMP_MAX (degC)? ")

current = dacModel.dacToCurrent(LASER_CURRENT, 32768)
print
print "Append the following section to the MakeWlmFile1.ini file"
print
print "[SIMULATION]"
print "WAVENUM_MINTEMP = %f" % opticalModel.calcWavenumber(TEMP_MIN, current)
print "WAVENUM_MAXTEMP = %f" % opticalModel.calcWavenumber(TEMP_MAX, current)

