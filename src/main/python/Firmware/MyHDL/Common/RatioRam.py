#!/usr/bin/python
#
# FILE:
#   RatioMemory.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Jul-2017  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import *

from DualPortRamRw import DualPortRamRw
from Host.autogen import interface
from Host.autogen.interface import (EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH,
                                    FPGA_RDMEM_MASK, FPGA_REG_WIDTH)
from Host.autogen.interface import RATIO_MEM_ADDR_WIDTH

LOW, HIGH = bool(0), bool(1)
ADDR_WIDTH = RATIO_MEM_ADDR_WIDTH
DATA_WIDTH = 32
MAX_ADDR = (1 << ADDR_WIDTH) - 1


def RatioRam(clk, reset, dsp_addr, dsp_data_out, dsp_data_in, dsp_wr,
             wlm_ratio_in, wlm_ratio_we_in, wlm_ratio_addr_in):

    enA = Signal(HIGH)
    enB = Signal(HIGH)

    addrA = Signal(intbv(0)[ADDR_WIDTH:])
    wlm_ratio_addr = Signal(intbv(0)[ADDR_WIDTH:])

    rd_dataA = Signal(intbv(0)[DATA_WIDTH:])
    wlm_ratio = Signal(intbv(0)[DATA_WIDTH:])
    wlm_ratio_we = Signal(LOW)

    ratio_mem = DualPortRamRw(
        clockA=clk, enableA=enA, wr_enableA=dsp_wr,
        addressA=addrA, rd_dataA=rd_dataA, wr_dataA=dsp_data_out,
        clockB=clk, enableB=enB, wr_enableB=wlm_ratio_we,
        addressB=wlm_ratio_addr, rd_dataB=wlm_ratio, wr_dataB=wlm_ratio_in,
        addr_width=ADDR_WIDTH,
        data_width=DATA_WIDTH)

    @always_comb
    def comb():
        # Set up addresses from the DSP side
        sel = dsp_addr[EMIF_ADDR_WIDTH - 1] == FPGA_RDMEM_MASK
        enA.next = sel
        if sel:
            dsp_data_in.next = rd_dataA
        else:
            dsp_data_in.next = 0
        enB.next = 1
        addrA.next = dsp_addr[ADDR_WIDTH:]

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                wlm_ratio_addr.next = 0
                wlm_ratio_we.next = 0
            else:
                wlm_ratio_addr.next = wlm_ratio_addr_in
                wlm_ratio_we.next = wlm_ratio_we_in

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    wlm_ratio_we_in = Signal(LOW)
    wlm_ratio_in = Signal(intbv(0)[DATA_WIDTH:])
    wlm_ratio_addr_in = Signal(intbv(0)[ADDR_WIDTH:])

    toVHDL(RatioRam, clk=clk, reset=reset, dsp_addr=dsp_addr,
           dsp_data_out=dsp_data_out,
           dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
           wlm_ratio_in=wlm_ratio_in, wlm_ratio_we_in=wlm_ratio_we_in,
           wlm_ratio_addr_in=wlm_ratio_addr_in)
