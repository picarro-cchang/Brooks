from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER
import numpy as np
import sys
import tables
import time

class Waveform(tables.IsDescription):
    index = tables.Int16Col()
    value = tables.Int16Col()

driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, "", IsDontCareConnection = False)

def genData():
    while True:
        driverRpc.wrDasReg("SPECT_CNTRL_STATE_REGISTER", "SPECT_CNTRL_PausedState")
        time.sleep(0.2)
        data1, meta, params = driverRpc.rdRingdown(0)
        data2, meta, params = driverRpc.rdRingdown(1)
        driverRpc.wrDasReg("SPECT_CNTRL_STATE_REGISTER", "SPECT_CNTRL_RunningState")
        time.sleep(0.05)
        yield np.asarray(data1) & 0x3FFF
        yield np.asarray(data2) & 0x3FFF
    
outputFile = raw_input("Name of output file? ")
numRingdowns = int(raw_input("Number of ringdowns? "))

tSamp = (1.0 + driverRpc.rdFPGA("FPGA_RDMAN","RDMAN_DIVISOR")) * 40.0e-9
h5f = tables.openFile(outputFile,"w")
filters = tables.Filters(complevel=1,fletcher32=True)
table = h5f.createTable(h5f.root,"ringdown",Waveform,filters=filters)
table.attrs.sample_time = tSamp
table.attrs.next_index = 0

for k,data in enumerate(genData()):
    if k == numRingdowns:
        break
    for v in data:
        entry = table.row
        entry["index"] = table.attrs.next_index
        entry["value"] = v
        entry.append()
    table.attrs.next_index += 1    
    table.flush()
    sys.stdout.write(".")
    if (k+1) % 50 == 0:
        print " %d" % (k+1,)
print "\nTotal of %d ringdowns collected" % (k,)
h5f.close()
