from configobj import ConfigObj
from numpy import *


def getWlmSplines(configFile,vLaserNum):
    config = ConfigObj(configFile)
    current = config["VIRTUAL_CURRENT_%d" % vLaserNum]
    currentValues = array([float(current[k]) for k in current])
    original = config["VIRTUAL_ORIGINAL_%d" % vLaserNum]
    originalValues = array([float(original[k]) for k in original])
    return currentValues, originalValues