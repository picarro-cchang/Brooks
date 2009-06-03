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

from MyHDL.Common.Inject import Inject
from MyHDL.Common.ClkGen import ClkGen
from Host.autogen import interface
from Host.autogen.interface import FPGA_INJECT

from Host.autogen.interface import INJECT_CONTROL
from Host.autogen.interface import INJECT_LASER1_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER2_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER3_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER4_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER1_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER2_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER3_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER4_FINE_CURRENT

from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH, FPGA_REG_MASK
from Host.autogen.interface import INJECT_CONTROL_MODE_B, INJECT_CONTROL_MODE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_LASER_CURRENT_ENABLE_B, INJECT_CONTROL_LASER_CURRENT_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_LASER_ENABLE_B, INJECT_CONTROL_MANUAL_LASER_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_SOA_ENABLE_B, INJECT_CONTROL_MANUAL_SOA_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W

LOW, HIGH = bool(0), bool(1)
PERIOD = 20

dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr, clk, reset = [Signal(LOW) for i in range(3)]
clk_2M5 = Signal(LOW)
dac_clock, strobe, laser_shutdown_in, soa_shutdown_in =\
    [Signal(LOW) for i in range(4)]
laser1_dac_sync_out, laser2_dac_sync_out, \
    laser3_dac_sync_out, laser4_dac_sync_out = \
    [Signal(LOW) for i in range(4)]
laser_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser1_dac_din_out = Signal(LOW)
laser2_dac_din_out = Signal(LOW)
laser3_dac_din_out = Signal(LOW)
laser4_dac_din_out = Signal(LOW)
laser1_disable_out,laser2_disable_out,laser3_disable_out,laser4_disable_out=\
    [Signal(LOW) for i in range(4)]
laser1_shutdown_out,laser2_shutdown_out,laser3_shutdown_out,laser4_shutdown_out=\
    [Signal(LOW) for i in range(4)]
soa_shutdown_out = Signal(LOW)

data1 = Signal(intbv(0)[24:])
data2 = Signal(intbv(0)[24:])
data3 = Signal(intbv(0)[24:])
data4 = Signal(intbv(0)[24:])
acq_done = Signal(LOW)

map_base = FPGA_INJECT

def  bench():
    """ Unit test for tuner wavedown generator """
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

    def writeRdmem(wordAddr,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readRdmem(wordAddr,result):
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

    inject = Inject(clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, laser_dac_clk_in=dac_clock,
                   strobe_in=strobe,
                   laser_fine_current_in=laser_fine_current_in,
                   laser_shutdown_in=laser_shutdown_in,
                   soa_shutdown_in=soa_shutdown_in,
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
                   map_base=FPGA_INJECT)

    clkGen = ClkGen(clk=clk, reset=reset, clk_5M=dac_clock,
                    clk_2M5=clk_2M5,pulse_100k=strobe)

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
                yield dac_clock.negedge
                data1.next[23-i] = laser1_dac_din_out
                data2.next[23-i] = laser2_dac_din_out
                data3.next[23-i] = laser3_dac_din_out
                data4.next[23-i] = laser4_dac_din_out
            acq_done.next = 1

    @instance
    def  stimulus():
        yield assertReset()
        assert laser1_disable_out == 1
        assert laser2_disable_out == 1
        assert laser3_disable_out == 1
        assert laser4_disable_out == 1
        assert laser1_shutdown_out == 1
        assert laser2_shutdown_out == 1
        assert laser3_shutdown_out == 1
        assert laser4_shutdown_out == 1
        assert soa_shutdown_out == 1
        # Test manual mode for laser and SOA switching
        for trials in range(100):
            laser_current_enable = randrange(1<<4)
            manual_laser_enable = randrange(1<<4)
            manual_soa_enable = randrange(1<<1)
            control = (laser_current_enable << INJECT_CONTROL_LASER_CURRENT_ENABLE_B) | \
                      (manual_laser_enable  << INJECT_CONTROL_MANUAL_LASER_ENABLE_B) | \
                      (manual_soa_enable << INJECT_CONTROL_MANUAL_SOA_ENABLE_B)
            yield writeFPGA(FPGA_INJECT+INJECT_CONTROL,control)
            assert laser1_disable_out == (not (laser_current_enable & 1))
            assert laser2_disable_out == (not ((laser_current_enable>>1) & 1))
            assert laser3_disable_out == (not ((laser_current_enable>>2) & 1))
            assert laser4_disable_out == (not ((laser_current_enable>>3) & 1))
            assert laser1_shutdown_out == (not (manual_laser_enable & 1))
            assert laser2_shutdown_out == (not ((manual_laser_enable>>1) & 1))
            assert laser3_shutdown_out == (not ((manual_laser_enable>>2) & 1))
            assert laser4_shutdown_out == (not ((manual_laser_enable>>3) & 1))
            assert soa_shutdown_out == (not((manual_soa_enable) & 1))
        for trials in range(5):
            laser1_coarse = randrange(1<<16)
            laser2_coarse = randrange(1<<16)
            laser3_coarse = randrange(1<<16)
            laser4_coarse = randrange(1<<16)
            laser1_fine = randrange(1<<16)
            laser2_fine = randrange(1<<16)
            laser3_fine = randrange(1<<16)
            laser4_fine = randrange(1<<16)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_COARSE_CURRENT,laser1_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_COARSE_CURRENT,laser2_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_COARSE_CURRENT,laser3_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_COARSE_CURRENT,laser4_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_FINE_CURRENT,laser1_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_FINE_CURRENT,laser2_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_FINE_CURRENT,laser3_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_FINE_CURRENT,laser4_fine)
            yield strobe.posedge
            yield acq_done.posedge
            assert (data1 & 0xFFFF) == laser1_coarse
            assert (data2 & 0xFFFF) == laser2_coarse
            assert (data3 & 0xFFFF) == laser3_coarse
            assert (data4 & 0xFFFF) == laser4_coarse
            yield acq_done.posedge
            assert (data1 & 0xFFFF) == laser1_fine
            assert (data2 & 0xFFFF) == laser2_fine
            assert (data3 & 0xFFFF) == laser3_fine
            assert (data4 & 0xFFFF) == laser4_fine
        yield delay(10*PERIOD)
        raise StopSimulation

    return instances()

def test_Inject():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_Inject()
