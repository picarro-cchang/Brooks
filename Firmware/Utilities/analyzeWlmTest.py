from tables import *
import matplotlib.pyplot as plt
import numpy as np
from Host.Common.WlmCalUtilities import parametricEllipse

# Analyze WLM test results
#fname = r"R:\crd\G2000\BETA02\WLMTest\test.h5"
fname = r"R:\crd\G2000\ALPHA03\WLMTest\test.h5"
h5 = openFile(fname,"r")
rd = h5.root.ringdowns
sensors = h5.root.sensors
# Plot the measured ratios
ratio1 = rd.read(field="ratio1",start=0,step=51,stop=1000000)/32768.0
ratio2 = rd.read(field="ratio2",start=0,step=51,stop=1000000)/32768.0
etalonTemp = rd.read(field="etalonTemperature",start=0,step=51,stop=1000000)
# Calculate parameters of ellipse
ratio1Center,ratio2Center,ratio1Scale,ratio2Scale,wlmPhase = \
    parametricEllipse(ratio1,ratio2)
# Calculate WLM angle from ratios
X = ratio1 - ratio1Center
Y = ratio2 - ratio2Center
thetaCal = (np.arctan2(ratio1Scale*Y - ratio2Scale*X*np.sin(wlmPhase),
                       ratio2Scale*X*np.cos(wlmPhase)))
