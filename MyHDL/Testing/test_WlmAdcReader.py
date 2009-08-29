#!/usr/bin/python
#
# FILE:
#   test_WlmAdcReader.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Aug-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK

from MyHDL.Common.WlmAdcReader import WlmAdcReader
from MyHDL.Common.ClkGen import ClkGen

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
adc_clock_in = Signal(LOW)
strobe_in = Signal(LOW)
eta1_in = Signal(LOW)
ref1_in = Signal(LOW)
eta2_in = Signal(LOW)
ref2_in = Signal(LOW)
adc_rd_out = Signal(LOW)
adc_convst_out = Signal(LOW)
data_available_out = Signal(LOW)
eta1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
ref1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
eta2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
ref2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])

clk_10M  = Signal(LOW)
clk_5M   = Signal(LOW)
pulse_1M = Signal(LOW)

busy1 = Signal(LOW)
busy2 = Signal(LOW)

def AdcModel(clock,convst,rd,dataA,dataB,busy,valueA,valueB):
    cycle = Signal(intbv(0)[5:])
    dataA_word = Signal(intbv(valueA)[16:])
    dataB_word = Signal(intbv(valueB)[16:])

    @always_comb
    def comb():
        busy.next = cycle<=16

    @instance
    def logic():
        while True:
            yield clock.negedge
            if rd and cycle == 19:
                cycle.next = 0
            yield clock.posedge
            if cycle < 19:
                cycle.next = cycle + 1
            if cycle >= 2 and cycle < 18:       
                dataA.next = dataA_word[17-int(cycle)]
                dataB.next = dataB_word[17-int(cycle)]
            else:
                dataA.next = LOW
                dataB.next = LOW
    return instances()

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
    wlmadcreader = WlmAdcReader( clk=clk, reset=reset,
                                 adc_clock_in=adc_clock_in,
                                 strobe_in=strobe_in, eta1_in=eta1_in,
                                 ref1_in=ref1_in, eta2_in=eta2_in,
                                 ref2_in=ref2_in, adc_rd_out=adc_rd_out,
                                 adc_convst_out=adc_convst_out,
                                 data_available_out=data_available_out,
                                 eta1_out=eta1_out, ref1_out=ref1_out,
                                 eta2_out=eta2_out, ref2_out=ref2_out )
    
    clkGen = ClkGen(clk=clk, reset=reset, clk_10M=clk_10M, clk_5M=clk_5M,
                    clk_2M5=adc_clock_in, pulse_1M=pulse_1M, pulse_100k=strobe_in)

    etaref1 = AdcModel(clock=adc_clock_in,convst=adc_convst_out,rd=adc_rd_out,dataA=eta1_in,dataB=ref1_in,busy=busy1,valueA=0x1234,valueB=0xFEDC)
    etaref2 = AdcModel(clock=adc_clock_in,convst=adc_convst_out,rd=adc_rd_out,dataA=eta2_in,dataB=ref2_in,busy=busy2,valueA=0xA5A5,valueB=0xBEEF)

    @instance
    def stimulus():
        yield assertReset()
        yield delay(3000*PERIOD)
        raise StopSimulation
    return instances()

def test_WlmAdcReader():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_WlmAdcReader()
