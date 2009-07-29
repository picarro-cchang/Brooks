#!/usr/bin/python
#
# FILE:
#   test_WlmSim.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   21-Jul-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_WLMSIM

from Host.autogen.interface import WLMSIM_OPTIONS, WLMSIM_Z0
from Host.autogen.interface import WLMSIM_RFAC, WLMSIM_WFAC
from Host.autogen.interface import WLMSIM_ETA1, WLMSIM_REF1
from Host.autogen.interface import WLMSIM_ETA2, WLMSIM_REF2

from Host.autogen.interface import WLMSIM_OPTIONS_INPUT_SEL_B, WLMSIM_OPTIONS_INPUT_SEL_W

from MyHDL.Common.WlmSim import WlmSim

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
start_in = Signal(LOW)
coarse_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
eta1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
ref1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
eta2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
ref2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
loss_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
pzt_cen_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
done_out = Signal(LOW)
map_base = FPGA_WLMSIM

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
    wlmsim = WlmSim( clk=clk, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                     dsp_wr=dsp_wr, start_in=start_in,
                     coarse_current_in=coarse_current_in,
                     fine_current_in=fine_current_in, eta1_out=eta1_out,
                     ref1_out=ref1_out, eta2_out=eta2_out,
                     ref2_out=ref2_out, loss_out=loss_out,
                     pzt_cen_out=pzt_cen_out, done_out=done_out,
                     map_base=map_base )
    @instance
    def stimulus():
        yield assertReset()
        # Write to the parameter area
        yield writeFPGA(FPGA_WLMSIM+WLMSIM_OPTIONS,1<<WLMSIM_OPTIONS_INPUT_SEL_B)
        yield writeFPGA(FPGA_WLMSIM+WLMSIM_RFAC,0x6000)
        yield writeFPGA(FPGA_WLMSIM+WLMSIM_WFAC,0xF000)
        for th in range(0,0x10000,0x40):
            # yield writeFPGA(FPGA_WLMSIM+WLMSIM_Z0,th)
            coarse_current_in.next = th
            fine_current_in.next = 0
            #
            yield clk.negedge
            start_in.next = True
            yield clk.negedge
            start_in.next = False
            yield done_out.posedge
        raise StopSimulation
    return instances()

def test_WlmSim():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_WlmSim()
