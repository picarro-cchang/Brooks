#!/usr/bin/python
#
# FILE:
#   test_Kernel.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   27-Jul-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import FPGA_MAGIC_CODE
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_KERNEL

from Host.autogen.interface import KERNEL_MAGIC_CODE, KERNEL_FPGA_RESET
from Host.autogen.interface import KERNEL_DIAG_1
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL
from Host.autogen.interface import KERNEL_INTRONIX_1, KERNEL_INTRONIX_2
from Host.autogen.interface import KERNEL_INTRONIX_3

from Host.autogen.interface import KERNEL_FPGA_RESET_RESET_B, KERNEL_FPGA_RESET_RESET_W
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL_DIVISOR_B, KERNEL_INTRONIX_CLKSEL_DIVISOR_W
from Host.autogen.interface import KERNEL_INTRONIX_1_CHANNEL_B, KERNEL_INTRONIX_1_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_2_CHANNEL_B, KERNEL_INTRONIX_2_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_3_CHANNEL_B, KERNEL_INTRONIX_3_CHANNEL_W

from MyHDL.Common.Kernel import Kernel

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
usb_connected = Signal(LOW)
cyp_reset = Signal(LOW)
diag_1_out = Signal(intbv(0)[8:])
intronix_clksel_out = Signal(intbv(0)[5:])
intronix_1_out = Signal(intbv(0)[8:])
intronix_2_out = Signal(intbv(0)[8:])
intronix_3_out = Signal(intbv(0)[8:])
map_base = FPGA_KERNEL

def bench():
    PERIOD = 20  # 50MHz clock
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    def writeFPGA(regNum,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readFPGA(regNum,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def wrRingdownMem(wordAddr,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def rdRingdownMem(wordAddr,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def assertReset():
        yield clk.negedge
        yield clk.posedge
        reset.next = 1
        dsp_wr.next = 0
        yield clk.posedge
        reset.next = 0
        yield clk.negedge

    # N.B. If there are several blocks configured, ensure that dsp_data_in is 
    #  derived as the OR of the data buses from the individual blocks.
    kernel = Kernel( clk=clk, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                     dsp_wr=dsp_wr, usb_connected=usb_connected,
                     cyp_reset=cyp_reset, diag_1_out=diag_1_out,
                     intronix_clksel_out=intronix_clksel_out,
                     intronix_1_out=intronix_1_out,
                     intronix_2_out=intronix_2_out,
                     intronix_3_out=intronix_3_out, map_base=map_base )
    @instance
    def stimulus():
        yield delay(10*PERIOD)
        raise StopSimulation
    return instances()

def test_Kernel():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_Kernel()
