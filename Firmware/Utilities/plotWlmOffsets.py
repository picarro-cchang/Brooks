# Utility to plot WLM_OFFSETs from INI files in a directory

from glob import glob
import os
from configobj import ConfigObj
from pylab import *
import matplotlib
from matplotlib.ticker import *
import pytz
import datetime
from Host.Common.timestamp import *


dirName = r"c:\temp\wlmCal"
timestamps = []
wlmOffset1 = []
wlmOffset2 = []

for fname in glob(os.path.join(dirName,"*.ini")):
    config = ConfigObj(file(fname,"r"))
    timestamps.append(float(config["timestamp"]))
    wlmOffset1.append(float(config["VIRTUAL_PARAMS_1"]["WLM_OFFSET"]))
    wlmOffset2.append(float(config["VIRTUAL_PARAMS_2"]["WLM_OFFSET"]))
    print fname

tz = pytz.timezone("UTC")    
formatter = matplotlib.dates.DateFormatter('%H:%M:%S\n%Y/%m/%d',tz)
t = array([unixTime(ts) for ts in timestamps])
dt = datetime.datetime.fromtimestamp(t[0],tz)
t0 = matplotlib.dates.date2num(dt)
tbase = t0 + (t-t[0])/(24.0*3600.0)
figure(1)    
plot_date(tbase,wlmOffset1,'.')
grid(True)
gca().xaxis.set_major_formatter(formatter)
figure(2)  
plot_date(tbase,wlmOffset2,'.')
grid(True)
gca().xaxis.set_major_formatter(formatter)
show()

