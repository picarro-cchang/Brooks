import matplotlib.pyplot as plt
from Host.autogen import interface
from Host.Common import CmdFIFO, Listener
from Host.Common.SharedTypes import BROADCAST_PORT_RDRESULTS, RPC_PORT_DRIVER
import numpy as np
from Queue import Empty, Queue
import sys
import time

def myLog(msg):
    print "Listener log", msg
    
Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    "setup_extended_current", IsDontCareConnection = False)
rd_queue = Queue(1000)
rdListener = Listener.Listener(rd_queue,
                            BROADCAST_PORT_RDRESULTS,
                            interface.RingdownEntryType,
                            retry = True,
                            name = "Ringdown listener",
                            logFunc = myLog)


def setup_current_gen(levels, alpha=0.5, actual_laser=1, bank=0, step_samples=600, lower_window=43000, upper_window=53000):
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
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_LOWER_WINDOW", lower_window)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_UPPER_WINDOW", upper_window)
    control = ((1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B) |
               ((actual_laser - 1) << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B) |
               (bank << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B))
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS", control)
    # Wait until the parameters have been loaded for the particular laser
    while (Driver.rdFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS") &
           (1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B)):
        time.sleep(0.01)

# We specify the range of laser currents defining the window of interest
upper_window = 52000
lower_window = 43000
dig_units_per_mode = 750

# Synthesize an initial set of levels for determining the current to mode mapping coefficients
upper = upper_window + dig_units_per_mode
lower = lower_window - 3*dig_units_per_mode
nmodes = int(np.ceil(float(upper - lower) / dig_units_per_mode))
levels = [int(level) for level in np.linspace(lower, upper, nmodes)]
        
setup_current_gen(levels, alpha=0.5 , actual_laser=1, bank=0, step_samples=700, 
                  lower_window=lower_window, upper_window=upper_window)
        
off_grid = 0.15
# Generate the coefficient values for the quadratic model relating current to angle
qrange = np.linspace(0,100,51)
lrange = np.linspace(50,100, 25)
qq, ll = np.meshgrid(qrange, lrange)

while True:
    # merit is an array which indicates how good particular choices of
    #  qq and ll are. The best choice gives the largest absolute value
    #  of the merit
    merit = np.zeros_like(qq,dtype=complex)
    
    while not rd_queue.empty():
        try:
            rd_queue.get(False)
        except Empty:
            continue
        rd_queue.task_done()
    
    nringdown = 580
    print "Collecting data from %d ringdowns" % nringdown
    fine_currents = []
    count = 0
    while True:
        try:
            datum = rd_queue.get(False)
            fine_current = (datum.fineLaserCurrent - 32768.0)/65536.0
            fine_currents.append(fine_current)
            merit += np.exp(2j * np.pi * (qq * fine_current + ll) * fine_current)
            count += 1
            if count % 50 == 0:
                sys.stdout.write('.')
            if count > nringdown:
                break
        except Empty:
            time.sleep(0.5)
            print "Queue length", rd_queue.qsize()
    print        
    fine_currents = np.asarray(fine_currents)
    # Find maximum absolute value of merit function
    best = np.unravel_index(np.abs(merit).argmax(), merit.shape)

    # print qq[best], ll[best], np.abs(merit[best])
    phase = np.angle(merit[best])
    coeffs = np.array([qq[best], ll[best], -phase/(2.0*np.pi)])
    print "Coeffs: ", coeffs
    fsr_indices = np.polyval(coeffs, fine_currents)
    # Find averages by index
    averages = {}
    for fine_current, fsr_index in zip(fine_currents, fsr_indices):
        fsr_index_int = int(round(fsr_index))
        if abs(fsr_index - fsr_index_int) < off_grid:
            if fsr_index_int not in averages:
                averages[fsr_index_int] = []
            averages[fsr_index_int].append(fine_current)

    std_devs = {}
    count = {}
    for index in averages:
        count[index] = len(averages[index])
        std_devs[index] = 65536.0 * np.std(averages[index])
        averages[index] = 65536.0 * np.mean(averages[index]) + 32768

    # Next find a polynomial which relates the fsr index to the average laser current    
    pfit = np.polyfit([index for index in averages], [averages[index] for index in averages],3)

    expected = {}
    slopes = {}
    for index in sorted(averages):
        expected[index] = np.polyval(pfit, index)
        slopes[index] = np.polyval(np.polyder(pfit), index)
        print "%3d: %7.0f %7.0f (%4d) %7.0f %7.0f" % (index, averages[index], std_devs[index], count[index],
                                                      expected[index], slopes[index])

    imin, imax = min(averages.keys()), max(averages.keys())
    fsr_currents = []
    slopes = []
    for i in range(imin-3, imax+4):
        if i in averages:
            fsr_currents.append(int(round(averages[i])))
        else:
            fsr_currents.append(int(round(np.polyval(pfit,i))))
        slopes.append(np.polyval(np.polyder(pfit),i))

    fsr_currents = np.asarray(fsr_currents)
    pk = np.argmin(abs(fsr_currents - 47550))
        
    levels = []
    offset = [-4,-3,-2,-1,0,1,2,3,4]
    dwells = [5,3,3,3,30,3,3,3,5]
    
    for i, (slope, current) in enumerate(zip(slopes, fsr_currents)):
        dwell = 1
        if not (lower <= current < upper):
            continue
        try:
            idx = offset.index(i-pk)
            dwell = dwells[idx]
        except ValueError:
            pass
        for j in range(dwell):
            levels.append(int(current - 0.1*slope))
            levels.append(int(current + 0.1*slope))
            
    setup_current_gen(levels, alpha=0.5 , actual_laser=1, bank=0, step_samples=200,
                      lower_window=lower_window, upper_window=upper_window)


"""
while True:
    # Next collect information about which level is associated with which ringdown
    time.sleep(1.0)
    with rd_queue.mutex:
        rd_queue.queue.clear()
    nringdown = 400
    print "Collecting data from %d ringdowns" % nringdown
    fine_currents = []
    level_counts = []
    count = 0
    while True:
        try:
            datum = rd_queue.get(False)
            fine_current = (datum.fineLaserCurrent - 32768.0)/65536.0
            fine_currents.append(fine_current)
            level_counts.append(datum.schemeRow)
            merit += np.exp(2j * np.pi * (qq * fine_current + ll) * fine_current)
            count += 1
            if count % 50 == 0:
                sys.stdout.write('.')
            if count > nringdown:
                break
        except Empty:
            time.sleep(0.5)
    print
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
        if abs(fsr_index - fsr_index_int) < off_grid:
            if fsr_index_int not in averages:
                averages[fsr_index_int] = []
            averages[fsr_index_int].append(fine_current)

    std_devs = {}
    count = {}
    for index in averages:
        count[index] = len(averages[index])
        std_devs[index] = 65536.0 * np.std(averages[index])
        averages[index] = 65536.0 * np.mean(averages[index]) + 32768

    for index in sorted(averages):
        print "%3d: %7.0f %7.0f (%4d)" % (index, averages[index], std_devs[index], count[index])

    # Next find a polynomial which relates the index to the average laser current
    pfit = np.polyfit([index for index in averages], [averages[index] for index in averages],3)

    imin, imax = min(averages.keys()), max(averages.keys())
    fsr_currents = []
    slopes = []
    for i in range(imin-1, imax+2):
        if i in averages:
            fsr_currents.append(int(round(averages[i])))
        else:
            fsr_currents.append(int(round(np.polyval(pfit,i))))
        slopes.append(np.polyval(np.polyder(pfit),i))

    fsr_currents = np.asarray(fsr_currents)
    pk = np.argmin(abs(fsr_currents - 47550))
        
    levels = []
    for i, (slope, current) in enumerate(zip(slopes, fsr_currents)):
        if i == pk:
            for j in range(10):
                levels.append(int(current - 0.2*slope))
                levels.append(int(current + 0.2*slope))
        elif abs(pk-i) <= 1:
            for j in range(4):
                levels.append(int(current - 0.2*slope))
                levels.append(int(current + 0.2*slope))
        else:
            levels.append(int(current - 0.2*slope))
            levels.append(int(current + 0.2*slope))
        
    setup_current_gen(levels, alpha=0.5 , actual_laser=1, bank=0, step_samples=300)
"""