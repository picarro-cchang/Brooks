from numpy import *
from pylab import *
from tables import *
from glob import *
import os.path

dirName = raw_input("Directory with H5 spectral files? ")
fnames = glob(os.path.join(dirName,"*.h5"))
waveNumByRow = {}
lossByRow = {}
for fname in fnames:
    h5 = openFile(fname,"r")
    print fname
    data = h5.root.rdData.read()
    waveNum = data['waveNumber']
    loss = data['uncorrectedAbsorbance']
    schemeRow = data['schemeRow']
    for i,row in enumerate(schemeRow):
        if row not in waveNumByRow:
            waveNumByRow[row] = []
            lossByRow[row] = []
        waveNumByRow[row].append(waveNum[i])
        lossByRow[row].append(loss[i])
    h5.close()
    
rowNum = []
mean_waveNum = []
std_waveNum = []
mean_loss = []
std_loss = []
for row in sorted(waveNumByRow.keys()):
    rowNum.append(row)
    waveNum = asarray(waveNumByRow[row])
    mean_waveNum.append(mean(waveNum))
    std_waveNum.append(std(waveNum))
    loss = asarray(lossByRow[row])
    mean_loss.append(mean(loss))
    std_loss.append(std(loss))

figure()
plot(mean_waveNum,mean_loss,'.')
xlabel('Wavenumber')
ylabel('Mean Loss')
grid(True)

figure()
plot(mean_waveNum,std_loss,'.')
xlabel('Wavenumber')
ylabel('StdDev Loss')
grid(True)

show()
