#!/usr/bin/python
#
# FILE:
#   test_LaserDac.py
#
# DESCRIPTION:
#   Driver for DAC8552 chip
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   31-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *

from MyHDL.Common.LaserDac import LaserDac
from MyHDL.Common.ClkGen import ClkGen
from Host.autogen import interface

LOW, HIGH = bool(0), bool(1)

clk, reset, dac_clock, strobe1M, strobe = [Signal(LOW) for i in range(5)]
dac_sync_out, dac_din_out = [Signal(LOW) for i in range(2)]
chanA_data_in = Signal(intbv(0)[16:])
chanB_data_in = Signal(intbv(0)[16:])
clk_10M = Signal(LOW)
clk_2M5 = Signal(LOW)
data_avail = Signal(LOW)

PERIOD = 20

def  bench():
    """ Unit test for laser DAC """
    data = Signal(intbv(0)[24:])

    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    laserDac = LaserDac(clk=clk, reset=reset,
                     dac_clock_in=dac_clock,
                     chanA_data_in=chanA_data_in,
                     chanB_data_in=chanB_data_in,
                     strobe_in=strobe,
                     dac_sync_out=dac_sync_out,
                     dac_din_out=dac_din_out)

    clkGen = ClkGen(clk=clk, reset=reset, clk_10M=clk_10M, clk_5M=dac_clock,
                    clk_2M5=clk_2M5, pulse_1M=strobe1M, pulse_100k=strobe)

    @instance
    def  stimulus():
        chanA_data_in.next = 0x1234
        chanB_data_in.next = 0x5678
        yield data_avail.posedge
        print "%x" % data
        yield data_avail.posedge
        print "%x" % data
        raise StopSimulation

    @instance
    def  acquire():
        while True:
            yield dac_sync_out.posedge
            data_avail.next = 0
            data.next = 0
            for i in range(24):
                yield dac_clock.negedge
                data.next[23-i] = dac_din_out
            data_avail.next = 1
            
    return instances()

def test_LaserDac():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_LaserDac()
