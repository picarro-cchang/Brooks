#!/usr/bin/python
#
# FILE:
#   test_Interpolator.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   07-Feb-2015  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *

from MyHDL.Common.Interpolator import linear_interpolator

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
y0 = Signal(intbv(0)[16:])
y1 = Signal(intbv(0)[16:])
beta = Signal(intbv(0)[16:])
y_out = Signal(intbv(0)[16:])

def bench():
    PERIOD = 20  # 50MHz clock
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    # N.B. If there are several blocks configured, ensure that dsp_data_in is
    #  derived as the OR of the data buses from the individual blocks.
    interpolator = linear_interpolator(y0=y0, y1=y1, beta=beta, y_out=y_out)

    @instance
    def stimulus():
        yield clk.posedge
        y0.next = 0x0001
        y1.next = 0xFFFE
        for k in range(32):
            beta.next = 2048 * k
            yield clk.posedge
            yield clk.posedge
        beta.next = 0xFFFF
        yield clk.posedge
        yield clk.posedge

        y0.next = 0xFFFE
        y1.next = 0x0001
        for k in range(32):
            beta.next = 2048 * k
            yield clk.posedge
            yield clk.posedge
        beta.next = 0xFFFF
        yield clk.posedge
        yield clk.posedge

        yield delay(100*PERIOD)
        raise StopSimulation
    return instances()

def test_Interpolator():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_Interpolator()
