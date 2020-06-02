#!/usr/bin/python
#
# FILE:
#   EdgeDetectors.py
#
# DESCRIPTION:
#   Block PosEdge monitors an input for a low-to-high transition and produces an
#    output which goes high until the next clock cycle when it is detected. Similarly
#    NegEdge monitors an input for a high-to-low transition and produces an
#    output which goes high until the next clock cycle when it is detected.
#
# SEE ALSO:
#
# HISTORY:
#   21-Nov-2016  sze  Initial version
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
"""
Timing diagram (paste into http://wavedrom.com/editor.html):
    {
    signal: [
        {name: 'clk', wave: 'P.........'},
        {name: 'input', wave: '0.1...0...'},
        {name: 'posedge_output', wave: '0.10......'},
        {name: 'negedge_output', wave: '0.....10..'},
    ],
        config: { hscale: 1 },
    }
"""
from myhdl import (always_comb, always_seq, instance, instances, Signal)

LOW, HIGH = bool(0), bool(1)


def PosEdge(clk, reset, input, output):
    ff = Signal(HIGH)

    @instance
    def sequential():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                ff.next = LOW
            else:
                ff.next = input

    @always_comb
    def logic():
        output.next = input and not ff

    return instances()


def NegEdge(clk, reset, input, output):
    ff = Signal(LOW)

    @instance
    def sequential():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                ff.next = LOW
            else:
                ff.next = input

    @always_comb
    def logic():
        output.next = ff and not input

    return instances()
