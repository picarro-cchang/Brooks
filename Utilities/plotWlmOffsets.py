# Utility to plot WLM_OFFSETs from INI files in a directory

from glob import glob
import os
from configobj import ConfigObj
from pylab import *

dirName = r"R:\CostReducedPlatform\Alpha\002_Alpha_DataFiles\DriftingWLMOffset\08"
timestamps = []
wlmOffset1 = []
wlmOffset2 = []

for fname in glob(os.path.join(dirName,"*.ini")):
    config = ConfigObj(file(fname,"r"))
    timestamps.append(float(config["timestamp"]))
    wlmOffset1.append(float(config["VIRTUAL_PARAMS_1"]["WLM_OFFSET"]))
    wlmOffset2.append(float(config["VIRTUAL_PARAMS_2"]["WLM_OFFSET"]))
    print fname
    
figure(1)    
plot(timestamps,wlmOffset1)
figure(2)  
plot(timestamps,wlmOffset2)
show()

