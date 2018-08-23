from Host.autogen import interface
from Host.Common import CmdFIFO, Listener
from Host.Common.SharedTypes import BROADCAST_PORT_RDRESULTS, RPC_PORT_DRIVER
import numpy as np
from Queue import Empty, Queue
import sys
import time

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    "setup_extended_current", IsDontCareConnection = False)
rd_queue = Queue(1000)
rdListener = Listener.Listener(rd_queue,
                            BROADCAST_PORT_RDRESULTS,
                            interface.RingdownEntryType,
                            retry = True,
                            name = "Ringdown listener")


def setup_current_gen(levels, alpha=0.5, actual_laser=1, bank=0):
    step_samples =600 # Units of 10us
    assert len(levels) <= 0x200

    Driver.wrRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, levels)
    print Driver.rdRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, len(levels))

    period = len(levels)
    M = 1 << interface.LASER_CURRENT_GEN_ACC_WIDTH
    T = step_samples
    slow_slope = int(round((M / T) * alpha / (1 - alpha)))
    fast_slope = int(round((M / T) * (1 - alpha) / alpha))
    first_offset = int(round(M * (2 * alpha - 1) / (2 * alpha))) % M
    second_offset = int(round(M * (2 * alpha - 1) / (alpha - 1)))
    first_breakpoint = int(np.ceil((1 - alpha) * T / 2))
    second_breakpoint = int(np.ceil((1 + alpha) * T / 2))
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SLOW_SLOPE", slow_slope)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FAST_SLOPE", fast_slope)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FIRST_OFFSET", first_offset)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SECOND_OFFSET", second_offset)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FIRST_BREAKPOINT", first_breakpoint)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SECOND_BREAKPOINT", second_breakpoint)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT", step_samples)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT", period)
    control = ((1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B) |
               ((actual_laser - 1) << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B) |
               (bank << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B))
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS", control)
    # Wait until the parameters have been loaded for the particular laser
    while (Driver.rdFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS") &
           (1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B)):
        time.sleep(0.01)

off_grid = 0.15
#levels = [int(x) for x in np.round(np.linspace(36000,46000,13))]
#setup_current_gen(levels, alpha=0.5, actual_laser=1, bank=0)        
# Generate the coefficient values for the quadratic model relating current to angle
qrange = np.linspace(0,100,51)
lrange = np.linspace(30,100,15)
qq, ll = np.meshgrid(qrange, lrange)
merit = np.zeros_like(qq,dtype=complex)

with rd_queue.mutex:
    rd_queue.queue.clear()
print "Collecting ringdown data"
for i in range(5):
    time.sleep(1.0)
    sys.stdout.write('.')
fine_currents = []
while not rd_queue.empty():
    try:
        datum = rd_queue.get(False)
        fine_current = (datum.fineLaserCurrent - 32768.0)/65536.0
        fine_currents.append(fine_current)
        merit += np.exp(2j * np.pi * (qq * fine_current + ll) * fine_current)
    except Empty:
        continue
fine_currents = np.asarray(fine_currents)
# Find maximum absolute value of merit function
best = np.unravel_index(np.abs(merit).argmax(), merit.shape)
#print qq[best], ll[best], np.abs(merit[best])
phase = np.angle(merit[best])
coeffs = np.array([qq[best], ll[best], -phase/(2.0*np.pi)])
fsr_indices = np.polyval(coeffs, fine_currents)
# Find averages by index
averages = {}
for fine_current, fsr_index in zip(fine_currents, fsr_indices):
    fsr_index_int = int(round(fsr_index))
    if abs(fsr_index - fsr_index_int) < 0.15:
        if fsr_index_int not in averages:
            averages[fsr_index_int] = []
        averages[fsr_index_int].append(fine_current)

for index in averages:
    averages[index] = 65536.0 * np.mean(averages[index]) + 32768
pfit = np.polyfit([index for index in averages], [averages[index] for index in averages],3)
imin, imax = min(averages.keys()), max(averages.keys())
#imin = max(imin,2)
#imax = min(imax,20)
fsr_currents = []
for i in range(imin-1, imax+2):
    if i in averages:
        fsr_currents.append(int(round(averages[i])))
    else:
        fsr_currents.append(int(round(np.polyval(pfit,i))))
# fsr_currents = [fsr_currents[0]] * 2 + fsr_currents
print fsr_currents
#print np.abs(fsr_index - np.round(fsr_index)).max()

# Compute currents corresponding to FSR spaced frequencies
#nfsr = np.arange(-100,101)
#fsr_frac = 0.5*(np.sqrt(4 * coeffs[0] * (nfsr - coeffs[2]) + coeffs[1] ** 2) - coeffs[1])/coeffs[0]
#fsr_currents = 65536.0 * fsr_frac + 32768.0
#fsr_currents = [int(current+0.5) for current in fsr_currents if current >= 30000.0 and current < 48000]
#print fsr_currents
setup_current_gen(fsr_currents, alpha=0.15 , actual_laser=1, bank=0)