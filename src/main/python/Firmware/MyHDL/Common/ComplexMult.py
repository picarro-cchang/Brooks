#!/usr/bin/python
#
# FILE:
#   ComplexMult.py
#
# DESCRIPTION:
#   Block for performing complex multiplication of quantities with
#    real and imaginary parts of less than unit magnitude
#
# SEE ALSO:
#
# HISTORY:
#   11-Jul-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import FPGA_REG_WIDTH

from SignedMultiplier import SignedMultiplier

LOW, HIGH = bool(0), bool(1)

def ComplexMult(clk,reset,a_in,b_in,c_in,d_in,start_in,
                          x_out,y_out,done_out):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    a_in                -- Real part of multiplier
    b_in                -- Imaginary part of multiplier
    c_in                -- Real part of multiplicand
    d_in                -- Imaginary part of multiplicand
    start_in            -- Raise fot 1 clock cycle to start product
    x_out               -- Real part of product
    y_out               -- Imaginary part of product
    done_out            -- Goes high when result is valid

    Notes:
        The multiplier and multiplicand must not change during operation
        (i.e., while done_out is low)
    """

    MULT_LATENCY = 2
    MAX_CYCLES = 4*MULT_LATENCY + 1
    FPGA_REG_MAXVAL = 1<<FPGA_REG_WIDTH

    cycle_counter = Signal(intbv(0)[4:])

    # Signals interfacing to multiplier
    mult_a, mult_b, mult_p = [Signal(intbv(0)[FPGA_REG_WIDTH:]) for i in range(3)]
    mult_o = Signal(LOW)

    signedMultiplier = SignedMultiplier(p=mult_p, a=mult_a, b=mult_b,
                                        overflow=mult_o)

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                cycle_counter.next = MAX_CYCLES
                x_out.next = 0
                y_out.next = 0
                done_out.next = HIGH
            else:
                if start_in:
                    cycle_counter.next = 0
                    done_out.next = LOW
                elif cycle_counter == 0:
                    mult_a.next = a_in
                    mult_b.next = c_in
                elif cycle_counter == MULT_LATENCY:
                    mult_a.next = b_in
                    mult_b.next = d_in
                    x_out.next = mult_p
                elif cycle_counter == 2*MULT_LATENCY:
                    mult_a.next = a_in
                    mult_b.next = d_in
                    x_out.next = (x_out - mult_p) % FPGA_REG_MAXVAL
                elif cycle_counter == 3*MULT_LATENCY:
                    mult_a.next = b_in
                    mult_b.next = c_in
                    y_out.next = mult_p
                elif cycle_counter == 4*MULT_LATENCY:
                    y_out.next = (y_out + mult_p) % FPGA_REG_MAXVAL
                    done_out.next = HIGH

                if cycle_counter < MAX_CYCLES:
                    cycle_counter.next = cycle_counter + 1

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    a_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    b_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    c_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    d_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    start_in = Signal(LOW)
    x_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    y_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    done_out = Signal(LOW)

    toVHDL(ComplexMult, clk=clk, reset=reset, a_in=a_in, b_in=b_in,
                        c_in=c_in, d_in=d_in, start_in=start_in,
                        x_out=x_out, y_out=y_out, done_out=done_out)
