#!/usr/bin/python
#
# FILE:
#   ClkGen.py
#
# DESCRIPTION:
#   Clock generator
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
LOW, HIGH = bool(0), bool(1)

def  ClkGen(clk,reset,clk_5M,clk_2M5,pulse_100k):
    # Generates 5MHz, 2.5MHz and 100kHz clocks from 50MHz input
    # 5MHz and 2.5MHz clocks have 1:1 MS ratio, 100kHz clock
    # is high for 20ns every 10us
    div5 = Signal(intbv(0)[3:])  # Counts up to 5
    div25 = Signal(intbv(0)[5:]) # Counts up to 25
    ff1 = Signal(LOW)
    ff2 = Signal(LOW)

    @instance
    def  logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                div5.next = 0
                div25.next = 0
                ff1.next = 0
                ff2.next = 0
            else:
                pulse_100k.next = 0
                if div5 == 4:
                    div5.next = 0
                    ff1.next = not ff1
                    if ff1:
                        ff2.next = not ff2
                        if ff2:
                            if div25 == 24:
                                div25.next = 0
                                pulse_100k.next = 1
                            else:
                                div25.next = div25 + 1
                else:
                    div5.next = div5 + 1

    @always_comb
    def  comb():
        clk_5M.next = ff1
        clk_2M5.next = ff2

    return instances()

if __name__ == "__main__":
    # Define the pinouts for VHDL synthesis
    clk, reset, clk_5M, clk_2M5, pulse_100k = [Signal(LOW) for i in range(5)]
    toVHDL(ClkGen, clk=clk, reset=reset, clk_5M=clk_5M,
                   clk_2M5=clk_2M5, pulse_100k=pulse_100k)
