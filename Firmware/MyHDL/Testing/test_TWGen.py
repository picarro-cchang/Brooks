#!/usr/bin/python
#
# FILE:
#   test_TWGen.py
#
# DESCRIPTION:
#   Test tuner waveform generator
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   30-May-2009  sze  Initial version
#    2-Sep-2009  sze  Added pzt_out and TWGEN_PZT_OFFSET so that PZT value can be offset from the tuner value
#                      an extra bit in the CS register allows pzt_out to be driven using the offset alone
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from random import randrange

from MyHDL.Common.TWGen import TWGen
from Host.autogen import interface
from Host.autogen.interface import FPGA_TWGEN

from Host.autogen.interface import TWGEN_ACC
from Host.autogen.interface import TWGEN_CS
from Host.autogen.interface import TWGEN_SLOPE_DOWN
from Host.autogen.interface import TWGEN_SLOPE_UP
from Host.autogen.interface import TWGEN_SWEEP_LOW
from Host.autogen.interface import TWGEN_SWEEP_HIGH
from Host.autogen.interface import TWGEN_WINDOW_LOW
from Host.autogen.interface import TWGEN_WINDOW_HIGH
from Host.autogen.interface import TWGEN_PZT_OFFSET

from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH, FPGA_REG_MASK
from Host.autogen.interface import TWGEN_CS_RUN_B, TWGEN_CS_CONT_B, TWGEN_CS_RESET_B, TWGEN_CS_TUNE_PZT_B

LOW, HIGH = bool(0), bool(1)
PERIOD = 20
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
value_out  = Signal(intbv(0)[FPGA_REG_WIDTH:])
pzt_out  = Signal(intbv(0)[FPGA_REG_WIDTH:])
dsp_wr, clk, reset, synth_step_in, slope_out, in_window_out = [Signal(LOW) for i in range(6)]
map_base = FPGA_TWGEN
clk_count = 0

def  bench():
    """ Unit test for tuner wavedown generator """
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    @always(clk.posedge)
    def synthStepGen():
        global clk_count
        synth_step_in.next = (0 == clk_count % 10)
        clk_count += 1

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

    twGen = TWGen(clk=clk, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                  dsp_wr=dsp_wr, synth_step_in=synth_step_in,
                  value_out=value_out, pzt_out=pzt_out, slope_out=slope_out,
                  in_window_out=in_window_out,map_base=FPGA_TWGEN)

    @instance
    def  stimulus():
        yield assertReset()
        assert value_out == 0x8000
        assert slope_out == 1
        yield writeFPGA(FPGA_TWGEN + TWGEN_SLOPE_DOWN,0x100)
        yield writeFPGA(FPGA_TWGEN + TWGEN_SLOPE_UP,0x200)
        yield writeFPGA(FPGA_TWGEN + TWGEN_SWEEP_LOW,0x7FF0)
        yield writeFPGA(FPGA_TWGEN + TWGEN_SWEEP_HIGH,0x8010)
        yield writeFPGA(FPGA_TWGEN + TWGEN_WINDOW_LOW,0x7FF8)
        yield writeFPGA(FPGA_TWGEN + TWGEN_WINDOW_HIGH,0x8008)
        yield writeFPGA(FPGA_TWGEN + TWGEN_PZT_OFFSET,0x1000)
        
        yield writeFPGA(FPGA_TWGEN + TWGEN_CS,1<<(TWGEN_CS_RUN_B)|\
                                              1<<(TWGEN_CS_CONT_B)|\
                                              1<<(TWGEN_CS_TUNE_PZT_B))
        yield delay(5000*PERIOD)
        yield writeFPGA(FPGA_TWGEN + TWGEN_CS,1<<(TWGEN_CS_RUN_B)|\
                                              1<<(TWGEN_CS_CONT_B) |\
                                              1<<(TWGEN_CS_RESET_B) |\
                                              1<<(TWGEN_CS_TUNE_PZT_B))
        yield delay(50*PERIOD)
        yield writeFPGA(FPGA_TWGEN + TWGEN_CS,1<<(TWGEN_CS_RUN_B)|\
                                              1<<(TWGEN_CS_CONT_B) |\
                                              1<<(TWGEN_CS_RESET_B))
        yield delay(50*PERIOD)
        raise StopSimulation
    return instances()

def test_TWGen():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_TWGen()
