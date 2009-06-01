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
from MyHDL.Common.ClkGen import ClkGen
from Host.autogen import interface

LOW, HIGH = bool(0), bool(1)
PERIOD = 20
clk, reset, clk_5M, clk_2M5, pulse_100k = [Signal(LOW) for i in range(5)]

def  bench():
    """ Unit test for clock generator """
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    clkGen = ClkGen(clk=clk, reset=reset, clk_5M=clk_5M, clk_2M5=clk_2M5,
        pulse_100k=pulse_100k)

    @instance
    def  stimulus():
        yield delay(50000)
        raise StopSimulation

    return instances()

def test_clkGen():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_clkGen()
