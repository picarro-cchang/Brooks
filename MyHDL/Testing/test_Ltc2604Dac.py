#!/usr/bin/python
#
# FILE:
#   test_Ltc2604Dac.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Aug-2009  sze  Initial version.
#   20-Sep-2009  sze  Register DAC lines to deglitch them
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK

from MyHDL.Common.Ltc2604Dac import Ltc2604Dac
from MyHDL.Common.ClkGen import ClkGen
from random import randrange

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dac_clock_in = Signal(LOW)
chanA_data_in = Signal(intbv(0)[16:])
chanB_data_in = Signal(intbv(0)[16:])
chanC_data_in = Signal(intbv(0)[16:])
chanD_data_in = Signal(intbv(0)[16:])
strobe_in = Signal(LOW)
dac_sck_out = Signal(LOW)
dac_sdi_out = Signal(LOW)
dac_ld_out = Signal(LOW)
data = Signal(intbv(0)[24:])
data_avail = Signal(LOW)

clk_5M = Signal(LOW)
clk_2M5 = Signal(LOW)
pulse_1M = Signal(LOW)

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
        yield clk.posedge
        reset.next = 0
        yield clk.negedge

    # N.B. If there are several blocks configured, ensure that dsp_data_in is 
    #  derived as the OR of the data buses from the individual blocks.
    ltc2604dac = Ltc2604Dac( clk=clk, reset=reset,
                             dac_clock_in=dac_clock_in,
                             chanA_data_in=chanA_data_in,
                             chanB_data_in=chanB_data_in,
                             chanC_data_in=chanC_data_in,
                             chanD_data_in=chanD_data_in,
                             strobe_in=strobe_in,
                             dac_sck_out=dac_sck_out,
                             dac_sdi_out=dac_sdi_out,
                             dac_ld_out=dac_ld_out )

    clkGen = ClkGen(clk=clk, reset=reset, clk_10M=dac_clock_in, clk_5M=clk_5M,
                    clk_2M5=clk_2M5, pulse_1M=pulse_1M, pulse_100k=strobe_in)

    @instance
    def stimulus():
        yield assertReset()
        for trials in range(10):
            chanA_data = randrange(1<<16)
            chanB_data = randrange(1<<16)
            chanC_data = randrange(1<<16)
            chanD_data = randrange(1<<16)
            chanA_data_in.next = chanA_data
            chanB_data_in.next = chanB_data
            chanC_data_in.next = chanC_data
            chanD_data_in.next = chanD_data
            yield data_avail.posedge
            assert (data&0xFF0000)>>16 == 0
            assert data&0xFFFF == chanA_data
            print "%02x, %04x" % ((data&0xFF0000)>>16,data&0xFFFF)
            yield data_avail.posedge
            assert (data&0xFF0000)>>16 == 1
            assert data&0xFFFF == chanB_data
            print "%02x, %04x" % ((data&0xFF0000)>>16,data&0xFFFF)
            yield data_avail.posedge
            assert (data&0xFF0000)>>16 == 2
            assert data&0xFFFF == chanC_data
            print "%02x, %04x" % ((data&0xFF0000)>>16,data&0xFFFF)
            yield data_avail.posedge
            assert (data&0xFF0000)>>16 == 0x23
            assert data&0xFFFF == chanD_data
            print "%02x, %04x" % ((data&0xFF0000)>>16,data&0xFFFF)
        raise StopSimulation

    @instance
    def  acquire():
        while True:
            yield dac_ld_out.negedge
            data_avail.next = 0
            data.next = 0
            for i in range(24):
                yield dac_sck_out.posedge
                data.next[23-i] = dac_sdi_out
            data_avail.next = 1
    
    return instances()

def test_Ltc2604Dac():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_Ltc2604Dac()
