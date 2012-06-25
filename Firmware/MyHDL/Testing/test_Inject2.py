#!/usr/bin/python
#
# FILE:
#   test_Inject.py
#
# DESCRIPTION:
#   Test optical injection subsystem
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   1-Jun-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from random import randrange

from MyHDL.Common.ClkGen import ClkGen
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_INJECT

from Host.autogen.interface import INJECT_CONTROL, INJECT_CONTROL2
from Host.autogen.interface import INJECT_LASER1_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER2_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER3_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER4_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER1_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER2_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER3_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER4_FINE_CURRENT

from Host.autogen.interface import INJECT_CONTROL_MODE_B, INJECT_CONTROL_MODE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_LASER_CURRENT_ENABLE_B, INJECT_CONTROL_LASER_CURRENT_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_LASER_ENABLE_B, INJECT_CONTROL_MANUAL_LASER_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_SOA_ENABLE_B, INJECT_CONTROL_MANUAL_SOA_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_OPTICAL_SWITCH_SELECT_B, INJECT_CONTROL_OPTICAL_SWITCH_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_SOA_PRESENT_B, INJECT_CONTROL_SOA_PRESENT_W
from Host.autogen.interface import INJECT_CONTROL2_FIBER_AMP_PRESENT_B, INJECT_CONTROL2_FIBER_AMP_PRESENT_W

from MyHDL.Common.Inject import Inject

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
laser_dac_clk_in = Signal(LOW)
strobe_in = Signal(LOW)
laser_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser_shutdown_in = Signal(LOW)
soa_shutdown_in = Signal(LOW)
fiber_amp_pwm_in = Signal(LOW)
laser1_dac_sync_out = Signal(LOW)
laser2_dac_sync_out = Signal(LOW)
laser3_dac_sync_out = Signal(LOW)
laser4_dac_sync_out = Signal(LOW)
laser1_dac_din_out = Signal(LOW)
laser2_dac_din_out = Signal(LOW)
laser3_dac_din_out = Signal(LOW)
laser4_dac_din_out = Signal(LOW)
laser1_disable_out = Signal(LOW)
laser2_disable_out = Signal(LOW)
laser3_disable_out = Signal(LOW)
laser4_disable_out = Signal(LOW)
laser1_shutdown_out = Signal(LOW)
laser2_shutdown_out = Signal(LOW)
laser3_shutdown_out = Signal(LOW)
laser4_shutdown_out = Signal(LOW)
soa_shutdown_out = Signal(LOW)
sel_laser_out = Signal(intbv(0)[2:])
sel_coarse_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
sel_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
optical_switch1_out = Signal(LOW)
optical_switch2_out = Signal(LOW)
optical_switch4_out = Signal(LOW)

data1 = Signal(intbv(0)[24:])
data2 = Signal(intbv(0)[24:])
data3 = Signal(intbv(0)[24:])
data4 = Signal(intbv(0)[24:])
acq_done = Signal(LOW)
clk_10M = Signal(LOW)
clk_2M5 = Signal(LOW)
pulse_100k = Signal(LOW)
pulse_1M = Signal(LOW)

map_base = FPGA_INJECT

def bench():
    PERIOD = 20  # 50MHz clock
    MS = 1000000
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
    inject = Inject( clk=clk, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                     dsp_wr=dsp_wr, laser_dac_clk_in=laser_dac_clk_in,
                     strobe_in=strobe_in,
                     laser_fine_current_in=laser_fine_current_in,
                     laser_shutdown_in=laser_shutdown_in,
                     soa_shutdown_in=soa_shutdown_in,
                     fiber_amp_pwm_in=fiber_amp_pwm_in,
                     laser1_dac_sync_out=laser1_dac_sync_out,
                     laser2_dac_sync_out=laser2_dac_sync_out,
                     laser3_dac_sync_out=laser3_dac_sync_out,
                     laser4_dac_sync_out=laser4_dac_sync_out,
                     laser1_dac_din_out=laser1_dac_din_out,
                     laser2_dac_din_out=laser2_dac_din_out,
                     laser3_dac_din_out=laser3_dac_din_out,
                     laser4_dac_din_out=laser4_dac_din_out,
                     laser1_disable_out=laser1_disable_out,
                     laser2_disable_out=laser2_disable_out,
                     laser3_disable_out=laser3_disable_out,
                     laser4_disable_out=laser4_disable_out,
                     laser1_shutdown_out=laser1_shutdown_out,
                     laser2_shutdown_out=laser2_shutdown_out,
                     laser3_shutdown_out=laser3_shutdown_out,
                     laser4_shutdown_out=laser4_shutdown_out,
                     soa_shutdown_out=soa_shutdown_out,
                     sel_laser_out=sel_laser_out,
                     sel_coarse_current_out=sel_coarse_current_out,
                     sel_fine_current_out=sel_fine_current_out,
                     optical_switch1_out=optical_switch1_out,
                     optical_switch2_out=optical_switch2_out,
                     optical_switch4_out=optical_switch4_out,
                     map_base=map_base )

    clkGen = ClkGen(clk=clk, reset=reset, clk_10M=clk_10M, clk_5M=laser_dac_clk_in,
                    clk_2M5=clk_2M5, pulse_1M=strobe_in, pulse_100k=pulse_100k)

    @instance
    def  acquire():
        while True:
            yield laser1_dac_sync_out.posedge
            acq_done.next = 0
            data1.next = 0
            data2.next = 0
            data3.next = 0
            data4.next = 0
            for i in range(24):
                yield laser_dac_clk_in.negedge
                data1.next[23-i] = laser1_dac_din_out
                data2.next[23-i] = laser2_dac_din_out
                data3.next[23-i] = laser3_dac_din_out
                data4.next[23-i] = laser4_dac_din_out
            acq_done.next = 1

    @instance
    def  stimulus():
        yield assertReset()
        # Test optical switch operation
        yield delay(MS/5)
        for trials in range(10):
            laser_sel = randrange(4)
            control = (laser_sel << INJECT_CONTROL_LASER_SELECT_B)
            yield writeFPGA(FPGA_INJECT+INJECT_CONTROL,control)
            yield delay(MS/5)
        raise StopSimulation
    return instances()

def test_Inject():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_Inject()
