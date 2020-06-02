#!/usr/bin/python
#
# FILE:
#   test_SgdbrManager.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   25-Jan-2019  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_SGDBRMANAGER

from Host.autogen.interface import SGDBRMANAGER_CSR
from Host.autogen.interface import SGDBRMANAGER_CONFIG
from Host.autogen.interface import SGDBRMANAGER_SCAN_SAMPLES
from Host.autogen.interface import SGDBRMANAGER_SAMPLE_TIME
from Host.autogen.interface import SGDBRMANAGER_DELAY_SAMPLES
from Host.autogen.interface import SGDBRMANAGER_SCAN_ADDRESS
from Host.autogen.interface import SGDBRMANAGER_SGDBR_PRESENT

from Host.autogen.interface import SGDBRMANAGER_CSR_START_SCAN_B, SGDBRMANAGER_CSR_START_SCAN_W
from Host.autogen.interface import SGDBRMANAGER_CSR_DONE_B, SGDBRMANAGER_CSR_DONE_W
from Host.autogen.interface import SGDBRMANAGER_CSR_SCAN_ACTIVE_B, SGDBRMANAGER_CSR_SCAN_ACTIVE_W
from Host.autogen.interface import SGDBRMANAGER_CONFIG_MODE_B, SGDBRMANAGER_CONFIG_MODE_W
from Host.autogen.interface import SGDBRMANAGER_CONFIG_SELECT_B, SGDBRMANAGER_CONFIG_SELECT_W
from Host.autogen.interface import SGDBRMANAGER_SGDBR_PRESENT_SGDBR_A_PRESENT_B, SGDBRMANAGER_SGDBR_PRESENT_SGDBR_A_PRESENT_W
from Host.autogen.interface import SGDBRMANAGER_SGDBR_PRESENT_SGDBR_B_PRESENT_B, SGDBRMANAGER_SGDBR_PRESENT_SGDBR_B_PRESENT_W

from MyHDL.Common.SgdbrManager import SgdbrManager

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
rec0_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rec1_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rec_strobe_in = Signal(LOW)
pb0_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
pb1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
pb_strobe_out = Signal(LOW)
rec_addr_out = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
rec_data_out = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
rec_wfm_sel_out = Signal(LOW)
rec_we_out = Signal(LOW)
pb_data_in = Signal(intbv(0)[RDMEM_META_WIDTH:])
pb_wfm_sel_out = Signal(LOW)
mode_out = Signal(LOW)
scan_active_out = Signal(LOW)
sgdbr_present_out = Signal(intbv(0)[2:])
sgdbr_select_out = Signal(LOW)
map_base = FPGA_SGDBRMANAGER

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
    sgdbrmanager = SgdbrManager( clk=clk, reset=reset,
                                 dsp_addr=dsp_addr,
                                 dsp_data_out=dsp_data_out,
                                 dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                                 rec0_in=rec0_in, rec1_in=rec1_in,
                                 rec_strobe_in=rec_strobe_in,
                                 pb0_out=pb0_out, pb1_out=pb1_out,
                                 pb_strobe_out=pb_strobe_out,
                                 rec_addr_out=rec_addr_out,
                                 rec_data_out=rec_data_out,
                                 rec_wfm_sel_out=rec_wfm_sel_out,
                                 rec_we_out=rec_we_out,
                                 pb_data_in=pb_data_in,
                                 pb_wfm_sel_out=pb_wfm_sel_out,
                                 mode_out=mode_out,
                                 scan_active_out=scan_active_out,
                                 sgdbr_present_out=sgdbr_present_out,
                                 sgdbr_select_out=sgdbr_select_out,
                                 map_base=map_base )
    @instance
    def stimulus():
        yield delay(10*PERIOD)
        raise StopSimulation
    return instances()

def test_SgdbrManager():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_SgdbrManager()
