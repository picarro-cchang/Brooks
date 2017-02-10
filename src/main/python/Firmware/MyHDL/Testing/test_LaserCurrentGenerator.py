#!/usr/bin/python
#
# FILE:
#   test_LaserCurrentGenerator.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   05-Feb-2015  sze  Initial version.
#   01-Oct-2015  sze  Add output for level counter
#   11-Oct-2015  sze  Added sequence identifiers
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from math import ceil
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import LASER_CURRENT_GEN_ACC_WIDTH
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_LASERCURRENTGENERATOR

from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS
from Host.autogen.interface import LASERCURRENTGENERATOR_SLOW_SLOPE
from Host.autogen.interface import LASERCURRENTGENERATOR_FAST_SLOPE
from Host.autogen.interface import LASERCURRENTGENERATOR_FIRST_OFFSET
from Host.autogen.interface import LASERCURRENTGENERATOR_SECOND_OFFSET
from Host.autogen.interface import LASERCURRENTGENERATOR_FIRST_BREAKPOINT
from Host.autogen.interface import LASERCURRENTGENERATOR_SECOND_BREAKPOINT
from Host.autogen.interface import LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT
from Host.autogen.interface import LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT
from Host.autogen.interface import LASERCURRENTGENERATOR_LOWER_WINDOW
from Host.autogen.interface import LASERCURRENTGENERATOR_UPPER_WINDOW
from Host.autogen.interface import LASERCURRENTGENERATOR_SEQUENCE_ID

from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B, LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_W
from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B, LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_W
from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B, LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_W

from MyHDL.Common.LaserCurrentGenerator import LaserCurrentGenerator
from MyHDL.Common.ClkGen import ClkGen

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
strobe_in = Signal(LOW)
sel_laser_in = Signal(intbv(0)[2:])
laser1_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser2_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser3_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser4_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser_current_in_window_out = Signal(LOW)
level_counter_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
sequence_id_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
map_base = FPGA_LASERCURRENTGENERATOR

clk_10M = Signal(LOW)
clk_5M = Signal(LOW)
clk_2M5 = Signal(LOW)
strobe_1M = Signal(LOW)

def bench():
    PERIOD = 20  # 50MHz clock
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    def writeFPGA(regNum,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readFPGA(regNum,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def wrRingdownMem(wordAddr,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def rdRingdownMem(wordAddr,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def assertReset():
        yield clk.negedge
        yield clk.posedge
        reset.next = 1
        dsp_wr.next = 0
        yield clk.posedge
        reset.next = 0
        yield clk.negedge

    # N.B. If there are several blocks configured, ensure that dsp_data_in is
    #  derived as the OR of the data buses from the individual blocks.
    lasercurrentgenerator = LaserCurrentGenerator( clk=clk, reset=reset,
                                                   dsp_addr=dsp_addr,
                                                   dsp_data_out=dsp_data_out,
                                                   dsp_data_in=dsp_data_in,
                                                   dsp_wr=dsp_wr,
                                                   strobe_in=strobe_in,
                                                   sel_laser_in=sel_laser_in,
                                                   laser1_fine_current_out=laser1_fine_current_out,
                                                   laser2_fine_current_out=laser2_fine_current_out,
                                                   laser3_fine_current_out=laser3_fine_current_out,
                                                   laser4_fine_current_out=laser4_fine_current_out,
                                                   laser_current_in_window_out=laser_current_in_window_out,
                                                   level_counter_out=level_counter_out,
                                                   sequence_id_out=sequence_id_out,
                                                   map_base=map_base )

    clkGen = ClkGen(clk=clk, reset=reset, clk_10M=clk_10M, clk_5M=clk_5M,
                    clk_2M5=clk_2M5, pulse_1M=strobe_1M, pulse_100k=strobe_in)

    @instance
    def stimulus():
        yield assertReset()
        alpha = 0.2
        M = 1 << LASER_CURRENT_GEN_ACC_WIDTH
        T = 32

        slow_slope = int(round((M / T) * alpha / (1 - alpha)))
        fast_slope = int(round((M / T) * (1 - alpha) / alpha))
        first_offset = int(round(M * (2 * alpha - 1) / (2 * alpha))) % M
        second_offset = int(round(M * (2 * alpha - 1) / (alpha - 1)))
        first_breakpoint = int(ceil((1 - alpha) * T / 2))
        second_breakpoint = int(ceil((1 + alpha) * T / 2))
        transition_counter_limit = T

        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_SLOW_SLOPE,
                        slow_slope)
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_FAST_SLOPE,
                        fast_slope)
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_FIRST_OFFSET,
                        first_offset)
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_SECOND_OFFSET,
                        second_offset)
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_FIRST_BREAKPOINT,
                        first_breakpoint)
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_SECOND_BREAKPOINT,
                        second_breakpoint)
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT,
                        transition_counter_limit)
        period_counter_limit = 5
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT,
                        period_counter_limit)

        # Write into the laser1 memory area
        baseAddr = 0x8000
        for offset in range(10):
            yield wrRingdownMem(baseAddr + offset, (15 - offset) * 0x1000)


        # Having written the registers, we set the mode bit and select a laser / bank
        #  in the control register
        aLaserNum = 1
        control_status = ((1 << LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B) |
                          ((aLaserNum - 1) << LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B))
        yield writeFPGA(FPGA_LASERCURRENTGENERATOR + LASERCURRENTGENERATOR_CONTROL_STATUS,
                        control_status)
        yield delay(240*500*PERIOD)
        raise StopSimulation
    return instances()

def test_LaserCurrentGenerator():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_LaserCurrentGenerator()
