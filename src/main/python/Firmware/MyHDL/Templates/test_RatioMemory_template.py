#!/usr/bin/python
#
# FILE:
#   test_RatioMemory.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   01-Aug-2017  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import RATIO_MEM_ADDR_WIDTH
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_RATIOMEMORY

from Host.autogen.interface import RATIOMEMORY_CS
from Host.autogen.interface import RATIOMEMORY_RATIO_ADDRESS
from Host.autogen.interface import RATIOMEMORY_DIVISOR

from Host.autogen.interface import RATIOMEMORY_CS_RUN_B, RATIOMEMORY_CS_RUN_W
from Host.autogen.interface import RATIOMEMORY_CS_CONT_B, RATIOMEMORY_CS_CONT_W
from Host.autogen.interface import RATIOMEMORY_CS_ACQUIRE_B, RATIOMEMORY_CS_ACQUIRE_W
from Host.autogen.interface import RATIOMEMORY_CS_DONE_B, RATIOMEMORY_CS_DONE_W

from MyHDL.Common.RatioMemory import RatioMemory

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
strobe_in = Signal(LOW)
wlm_ratio_we_out = Signal(LOW)
wlm_ratio_addr_out = Signal(intbv(0)[RATIO_MEM_ADDR_WIDTH:])
map_base = FPGA_RATIOMEMORY


def bench():
    PERIOD = 20  # 50MHz clock

    @always(delay(PERIOD // 2))
    def clockGen():
        clk.next = not clk

    def writeFPGA(regNum, data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1 << (EMIF_ADDR_WIDTH - 1)) + regNum
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readFPGA(regNum, result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1 << (EMIF_ADDR_WIDTH - 1)) + regNum
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def wrRingdownMem(wordAddr, data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def rdRingdownMem(wordAddr, result):
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
    ratiomemory = RatioMemory(
        clk=clk,
        reset=reset,
        dsp_addr=dsp_addr,
        dsp_data_out=dsp_data_out,
        dsp_data_in=dsp_data_in,
        dsp_wr=dsp_wr,
        strobe_in=strobe_in,
        wlm_ratio_we_out=wlm_ratio_we_out,
        wlm_ratio_addr_out=wlm_ratio_addr_out,
        map_base=map_base,
    )

    @instance
    def stimulus():
        yield delay(10 * PERIOD)
        raise StopSimulation

    return instances()


def test_RatioMemory():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)


if __name__ == "__main__":
    test_RatioMemory()
