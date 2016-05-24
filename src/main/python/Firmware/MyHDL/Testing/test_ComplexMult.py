#!/usr/bin/python
#
# FILE:
#   test_ComplexMult.py
#
# DESCRIPTION:
#   Test complex multiplication
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   11-Jul-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from random import random, randrange
from math import *

from MyHDL.Common.ComplexMult import ComplexMult
from Host.autogen import interface
from Host.autogen.interface import FPGA_REG_WIDTH

LOW, HIGH = bool(0), bool(1)
PERIOD = 20

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

mod = (1<<FPGA_REG_WIDTH)

def add_sim(x,y):
    return (x+y) % mod

def sub_sim(x,y):
    return (x-y) % mod

def div_sim(x,y):
    x = x % mod
    y = y % mod
    return x*(mod//2)//y

def signed_mul_sim(x,y):
    x = x % mod
    if x>mod//2: x -= mod
    y = y % mod
    if y>mod//2: y -= mod
    maxMag = float(mod//2)
    p = int(((x/maxMag)*(y/maxMag))*maxMag)
    if p<0: p += mod
    return p

def  bench():
    """ Unit test for tuner wavedown generator """
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    def assertReset():
        yield clk.negedge
        yield clk.posedge
        reset.next = 1
        yield clk.posedge
        reset.next = 0
        yield clk.negedge

    complexMult = ComplexMult(clk=clk, reset=reset, a_in=a_in, b_in=b_in,
                      c_in=c_in, d_in=d_in, start_in=start_in,
                      x_out=x_out, y_out=y_out, done_out=done_out)
    @instance
    def  stimulus():
        yield assertReset()
        for trials in range(100):

            phi = random() * 2.0 * pi
            z1 = cos(phi) + 1j*sin(phi)
            theta = random() * 2.0 * pi
            z2 = cos(theta) + 1j*sin(theta)
            a = (mod/2)*z1.real
            b = (mod/2)*z1.imag
            c = (mod/2)*z2.real
            d = (mod/2)*z2.imag
            z = z1*z2
            x = (mod/2)*z.real
            y = (mod/2)*z.imag

            yield clk.negedge
            a_in.next = int(round(a)) % mod
            b_in.next = int(round(b)) % mod
            c_in.next = int(round(c)) % mod
            d_in.next = int(round(d)) % mod
            yield clk.negedge
            start_in.next = HIGH
            yield clk.negedge
            start_in.next = LOW

            yield done_out.posedge
            # print "%4x, %4x" % (x_out, int(round(x)) % mod)
            # print "%4x, %4x" % (y_out, int(round(y)) % mod)
            assert abs(x_out - (int(round(x)) % mod)) <= 2
            assert abs(y_out - (int(round(y)) % mod)) <= 2

        yield delay(20*PERIOD)
        raise StopSimulation
    return instances()

def test_ComplexMult():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_ComplexMult()
