from Host.autogen import interface
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER
import sys
import time

# Routine to adjust ringdown threshold according to a schedule

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    'Threshold Steps', IsDontCareConnection = False)
                                    
if __name__ == '__main__':
    nargs = len(sys.argv)
    if nargs>1: 
        minThreshold  = float(sys.argv[1])
    else:
        minThreshold  = input('Minimum threshold value: ')
    
    if nargs>2: 
        maxThreshold  = float(sys.argv[2])
    else:
        maxThreshold  = input('Maximum threshold value: ')
        
    if nargs>3: 
        incrThreshold = float(sys.argv[3])
    else:
        incrThreshold = input('Increment in threshold: ')
        
    if nargs>4: 
        dwell = float(sys.argv[4])
    else:
        dwell = input('Minutes for each threshold: ')
    
    threshold = minThreshold
    while threshold <= maxThreshold:
        print "Setting threshold to %s and waiting for %s minutes" % (threshold,dwell)
        Driver.wrDasReg('SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER',threshold)
        tWake = time.time() + 60.0*dwell
        while True:
            tSleep = tWake - time.time()
            if tSleep <= 0.0: break
            time.sleep(min(30.0,tSleep))
            sys.stderr.write('.')
        print
        threshold += incrThreshold
    print 'Threshold stepping complete'
