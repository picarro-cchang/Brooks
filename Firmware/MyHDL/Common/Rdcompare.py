#!/usr/bin/python
#
# FILE:
#   Rdcompare.py
#
# DESCRIPTION:
#   MyHDL for simple ringdown threshold comparator
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   12-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *

from Host.autogen import interface
from Host.autogen.interface import RDCOMPARE_THRESHOLD
from Host.autogen.interface import RDCOMPARE_RATE_DIVISOR
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK
from Host.autogen.interface import FPGA_RDCOMPARE
LOW, HIGH = bool(0), bool(1)

def  Rdcompare(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
                divisor,value,result,map_base):
    """Ringdown ADC comparator"""

    rdcompare_threshold_addr = map_base + RDCOMPARE_THRESHOLD
    rdcompare_rate_divisor_addr = map_base + RDCOMPARE_RATE_DIVISOR
    dsp_data_from_regs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    threshold = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rate_divisor = Signal(intbv(0)[FPGA_REG_WIDTH:])

    @always_comb
    def comb():
        dsp_data_in.next = dsp_data_from_regs
        result.next = value > threshold
        divisor.next = rate_divisor

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                threshold.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdcompare_threshold_addr:
                        if dsp_wr: threshold.next = dsp_data_out
                        dsp_data_from_regs.next = threshold
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdcompare_rate_divisor_addr:
                        if dsp_wr: rate_divisor.next = dsp_data_out
                        dsp_data_from_regs.next = rate_divisor
                    else:
                        dsp_data_from_regs.next = 0
                else:
                    dsp_data_from_regs.next = 0
    return instances()

if __name__ == "__main__":
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    divisor = Signal(intbv(0)[5:])
    clk, reset, dsp_wr, result = [Signal(LOW) for i in range(4)]
    value  = Signal(intbv(0)[16:])
    map_base = FPGA_RDCOMPARE

    toVHDL(Rdcompare, clk=clk, reset=reset, dsp_addr=dsp_addr,
                      dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                      dsp_wr=dsp_wr, divisor=divisor, value=value,
                      result=result,
                      map_base=map_base)
