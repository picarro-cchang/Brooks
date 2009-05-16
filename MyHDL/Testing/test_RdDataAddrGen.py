#!/usr/bin/python
#
# FILE:
#   test_Rdmemory.py
#
# DESCRIPTION:
#   Dual ported memory for storing ringdown information
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   14-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from random import randrange

from MyHDL.Common.RdDataAddrGen import RdDataAddrGen
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH, META_BANK_ADDR_WIDTH, PARAM_BANK_ADDR_WIDTH
from Host.autogen.interface import RDMEM_DATA_WIDTH, RDMEM_META_WIDTH, RDMEM_PARAM_WIDTH

LOW, HIGH = bool(0), bool(1)

clk, addr_reset, enable = [Signal(LOW) for i in range(3)]
addr_div = Signal(intbv(0)[5:])
data_addr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
data_we, adc_clk = [Signal(LOW) for i in range(2)]

PERIOD = 20

def  bench():
    """ Unit test for ringdown memory """
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    rdDataAddrGen = RdDataAddrGen(clk=clk,addr_reset=addr_reset,
                                  enable=enable,addr_div=addr_div,
                                  data_addr=data_addr,data_we=data_we,
                                  adc_clk=adc_clk)

    @instance
    def  stimulus():
        for div in [5,1,2,16]:
            addr_div.next = div
            for iter in range(10):
                addr_reset.next = True
                yield clk.posedge
                addr_reset.next = False
                enable.next = True
                yield clk.posedge
                assert data_addr==0
                ndelay = randrange(1,32)
                yield delay(ndelay*2*(div+1)*PERIOD)
                assert data_addr==ndelay
                enable.next = False
                yield delay(randrange(10)*PERIOD)
        raise StopSimulation

    return instances()

def test_rdDataAddrGen():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_rdDataAddrGen()
