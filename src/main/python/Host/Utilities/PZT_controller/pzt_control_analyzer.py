from __future__ import print_function

from Host.autogen import interface
import numpy as np
import matplotlib.pyplot as plt

import os
import time

fname = "pzt_cal.npz"
data = np.load(fname)
print(data.keys())

plt.figure()
plt.plot(data['pztValue'], data['waveNumber'] - data['waveNumberSetpoint'], '.')
plt.xlabel('PZT Value')
plt.ylabel('Wavenumber offset')
plt.grid()
plt.savefig("pzt_cal1.png")
plt.figure()
plt.plot(data['pztValue'], data['wlmAngle'] - data['angleSetpoint'], '.')
plt.xlabel('PZT Value')
plt.ylabel('WLM angle offset')
plt.grid()
plt.savefig("pzt_cal2.png")
plt.figure()
plt.plot(data['pztValue'], data['tunerValue'], '.')
plt.xlabel('PZT Value')
plt.ylabel('Tuner Value')
plt.grid()
plt.savefig("pzt_cal3.png")
plt.show()
