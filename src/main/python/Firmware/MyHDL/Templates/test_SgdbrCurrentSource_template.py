#!/usr/bin/python
#
# FILE:
#   test_SgdbrCurrentSource.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   15-May-2019  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_SGDBRCURRENTSOURCE

from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR
from Host.autogen.interface import SGDBRCURRENTSOURCE_MISO_DELAY
from Host.autogen.interface import SGDBRCURRENTSOURCE_MOSI_DATA
from Host.autogen.interface import SGDBRCURRENTSOURCE_MISO_DATA
from Host.autogen.interface import SGDBRCURRENTSOURCE_SYNC_REGISTER
from Host.autogen.interface import SGDBRCURRENTSOURCE_MAX_SYNC_CURRENT

from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_RESET_B, SGDBRCURRENTSOURCE_CSR_RESET_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_SELECT_B, SGDBRCURRENTSOURCE_CSR_SELECT_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_DESELECT_B, SGDBRCURRENTSOURCE_CSR_DESELECT_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_CPOL_B, SGDBRCURRENTSOURCE_CSR_CPOL_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_CPHA_B, SGDBRCURRENTSOURCE_CSR_CPHA_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_DONE_B, SGDBRCURRENTSOURCE_CSR_DONE_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_MISO_B, SGDBRCURRENTSOURCE_CSR_MISO_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B, SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_CSR_SUPPRESS_UPDATE_B, SGDBRCURRENTSOURCE_CSR_SUPPRESS_UPDATE_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_SYNC_REGISTER_REG_SELECT_B, SGDBRCURRENTSOURCE_SYNC_REGISTER_REG_SELECT_W
from Host.autogen.interface import SGDBRCURRENTSOURCE_SYNC_REGISTER_SOURCE_B, SGDBRCURRENTSOURCE_SYNC_REGISTER_SOURCE_W

from MyHDL.Common.SgdbrCurrentSource import SgdbrCurrentSource

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
sck_out = Signal(LOW)
csn_out = Signal(LOW)
data_in = Signal(LOW)
sync_current_in = Signal(intbv(0)[16:])
sync_register_in = Signal(intbv(0)[4:])
sync_strobe_in = Signal(LOW)
data_out = Signal(LOW)
resetn_out = Signal(LOW)
done_out = Signal(LOW)
map_base = FPGA_SGDBRCURRENTSOURCE

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
    sgdbrcurrentsource = SgdbrCurrentSource( clk=clk, reset=reset,
                                             dsp_addr=dsp_addr,
                                             dsp_data_out=dsp_data_out,
                                             dsp_data_in=dsp_data_in,
                                             dsp_wr=dsp_wr,
                                             sck_out=sck_out,
                                             csn_out=csn_out,
                                             data_in=data_in,
                                             sync_current_in=sync_current_in,
                                             sync_register_in=sync_register_in,
                                             sync_strobe_in=sync_strobe_in,
                                             data_out=data_out,
                                             resetn_out=resetn_out,
                                             done_out=done_out,
                                             map_base=map_base )
    @instance
    def stimulus():
        yield delay(10*PERIOD)
        raise StopSimulation
    return instances()

def test_SgdbrCurrentSource():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_SgdbrCurrentSource()
