from math import pi, sin, cos, log, sqrt
from numpy import arange
import random
from Host.autogen.interface import FPGA_REG_WIDTH

from myhdl import *
from MyHDL.Common.wlmSimulator import WlmSimulator

LOW, HIGH = bool(0), bool(1)
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

def bench(nrTests=500):

    """ Test bench for WLM simulator """    
    # scaling factor to represent floats as integers
    M = 2**FPGA_REG_WIDTH
    M2 = M//2

    z0 = Signal(intbv(0, min=0, max=M))
    eta1 = Signal(intbv(0, min=0, max=M))
    ref1 = Signal(intbv(0, min=0, max=M))
    eta2 = Signal(intbv(0, min=0, max=M))
    ref2 = Signal(intbv(0, min=0, max=M))
    rfac = Signal(intbv(0, min=0, max=M))
    start = Signal(LOW)
    done  = Signal(LOW)
    clock = Signal(LOW)
    reset = Signal(LOW)

    # design under test
    dut = WlmSimulator(clock,reset,start,rfac,z0,eta1,ref1,eta2,ref2,done)

    # clock generator
    @always(delay(10))
    def clockgen():
        clock.next = not clock

    testAngles = arange(0,2*pi,2*pi/nrTests)
        
    # actual test
    @instance
    def check():
        #rfac.next = 0x6000
        rfac.next = 0x8000
        yield clock.negedge
        reset.next = True
        yield clock.negedge
        reset.next = False
        for z in testAngles:
            yield clock.negedge
            z0.next = int(round(M2*z/pi))
            start.next = True
            yield clock.negedge
            start.next = False
            yield done.posedge
        raise StopSimulation

    return instances()

def test_bench():
    errorMargin = FPGA_REG_WIDTH
    sim = Simulation(traceSignals(bench))
    sim.run(quiet=1)

if __name__ == "__main__":
    test_bench()
