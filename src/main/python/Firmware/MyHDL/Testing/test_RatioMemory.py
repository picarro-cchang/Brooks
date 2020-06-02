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
from MyHDL.Common.RatioRam import RatioRam

from random import randrange

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
strobe_in = Signal(LOW)
wlm_ratio_we = Signal(LOW)
wlm_ratio_addr = Signal(intbv(0)[RATIO_MEM_ADDR_WIDTH:])
map_base = FPGA_RATIOMEMORY
dsp_data_in_ratioram = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in_ratiomemory = Signal(intbv(0)[EMIF_DATA_WIDTH:])
wlm_ratio_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
start = Signal(LOW)


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

    ratioRam = RatioRam(
        clk=clk, reset=reset, dsp_addr=dsp_addr,
        dsp_data_out=dsp_data_out,
        dsp_data_in=dsp_data_in_ratioram, dsp_wr=dsp_wr,
        wlm_ratio_in=wlm_ratio_in, wlm_ratio_we_in=wlm_ratio_we,
        wlm_ratio_addr_in=wlm_ratio_addr)

    # N.B. If there are several blocks configured, ensure that dsp_data_in is
    #  derived as the OR of the data buses from the individual blocks.
    ratiomemory = RatioMemory(clk=clk, reset=reset, dsp_addr=dsp_addr,
                              dsp_data_out=dsp_data_out,
                              dsp_data_in=dsp_data_in_ratiomemory, dsp_wr=dsp_wr,
                              strobe_in=strobe_in,
                              wlm_ratio_we_out=wlm_ratio_we,
                              wlm_ratio_addr_out=wlm_ratio_addr,
                              map_base=map_base)

    @always_comb
    def comb():
        dsp_data_in.next = (dsp_data_in_ratioram | dsp_data_in_ratiomemory)

    @instance
    def stimulus():
        memDict = {}
        result = Signal(intbv(0))
        yield assertReset()
        nWrites = 500
        # Check read-write access to laser current and laser ratio memory from
        # the DSP
        for iter_num in range(nWrites):
            addr = randrange(1 << RATIO_MEM_ADDR_WIDTH)
            d = randrange(1 << 32)
            memDict[addr] = d
            yield wrRingdownMem(addr, d)

        print "Finished writing to laser current and laser ratio memory from the DSP"
        # Read these data back via the DSP interface
        for a in memDict:
            yield rdRingdownMem(a, result)
            if result != memDict[a]:
                print "%4x: Wrote %8x read back %8x" % (a, memDict[a], result)
        print "Finished reading back memory via DSP"

        yield writeFPGA(FPGA_RATIOMEMORY + RATIOMEMORY_DIVISOR, 4)
        yield writeFPGA(
            FPGA_RATIOMEMORY + RATIOMEMORY_CS,
            (1 << RATIOMEMORY_CS_RUN_B) | (1 << RATIOMEMORY_CS_CONT_B) | (1 << RATIOMEMORY_CS_ACQUIRE_B))
        start.next = 1

        while True:
            yield delay(800 * PERIOD)
            yield readFPGA(FPGA_RATIOMEMORY + RATIOMEMORY_CS, result)
            if result & (1 << RATIOMEMORY_CS_DONE_B):
                break
        yield writeFPGA(
            FPGA_RATIOMEMORY + RATIOMEMORY_CS,
            (1 << RATIOMEMORY_CS_RUN_B) | (1 << RATIOMEMORY_CS_CONT_B))

        for a in range(1 << RATIO_MEM_ADDR_WIDTH):
            yield rdRingdownMem(a, result)
            print a, result

        raise StopSimulation

    @instance
    def genStrobe():
        yield start.posedge
        for i in xrange(10000):
            yield delay(100 * PERIOD)
            wlm_ratio_in.next = i
            yield clk.posedge
            yield clk.posedge
            yield clk.posedge
            strobe_in.next = HIGH
            yield clk.posedge
            yield clk.posedge
            yield clk.posedge
            strobe_in.next = LOW

    return instances()


def test_RatioMemory():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_RatioMemory()
