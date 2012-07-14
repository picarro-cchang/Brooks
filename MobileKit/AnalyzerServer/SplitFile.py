'''
Split a .dat file for testing SendToP3.py
Created on Jul 13, 2012

@author: stan
'''
import os
import time

if __name__ == '__main__':
    outDir = 'C:\Picarro\Eclipse\Sending Files To P3\Example'
    anzName = 'TEST6543'
    numFiles = 10
    linesPerFile = 400
    
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    fname = 'C:\Picarro\Eclipse\Sending Files To P3\FCDS2006-20120323-020431Z-DataLog_User_Minimal.dat'
    fp = file(fname,'rb')
    hdr = fp.readline()
    columns = hdr.split()
    timeCol = columns.index("EPOCH_TIME")
    assert timeCol >= 0
    for i in range(numFiles):
        data = [fp.readline() for j in range(linesPerFile)]
        startTime = float(data[0].split()[timeCol])
        fname = "%s-%s-DataLog_User_Minimal.dat" % (anzName,time.strftime("%Y%m%d-%H%M%SZ",time.gmtime(startTime)))
        op = open(os.path.join(outDir,fname),'wb')
        op.write(hdr)
        for d in data: op.write(d)
        op.close()
    fp.close() 
