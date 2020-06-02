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
#   09-Apr-2018  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import (Signal, Simulation, StopSimulation, always, delay, instance,
                   instances, intbv, toVHDL, traceSignals)

from Host.autogen import interface
from Host.autogen.interface import (DATA_BANK_ADDR_WIDTH, EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH,
                                    FPGA_REG_MASK, FPGA_REG_WIDTH,
                                    FPGA_SGDBRMANAGER, RDMEM_DATA_WIDTH,
                                    RDMEM_META_WIDTH, SGDBRMANAGER_CSR,
                                    SGDBRMANAGER_CSR_DONE_B,
                                    SGDBRMANAGER_CSR_DONE_W,
                                    SGDBRMANAGER_CSR_SCAN_ACTIVE_B,
                                    SGDBRMANAGER_CSR_SCAN_ACTIVE_W,
                                    SGDBRMANAGER_CSR_START_SCAN_B,
                                    SGDBRMANAGER_CSR_START_SCAN_W,
                                    SGDBRMANAGER_DELAY_SAMPLES,
                                    SGDBRMANAGER_MEMORY_MODE,
                                    SGDBRMANAGER_MEMORY_MODE_MODE_B,
                                    SGDBRMANAGER_MEMORY_MODE_MODE_W,
                                    SGDBRMANAGER_SAMPLE_TIME,
                                    SGDBRMANAGER_SCAN_ADDRESS,
                                    SGDBRMANAGER_SCAN_SAMPLES)
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
map_base = FPGA_SGDBRMANAGER


def bench():
    PERIOD = 20  # 50MHz clock

    @always(delay(PERIOD // 2))
    def clockGen():
        clk.next = not clk

    def writeFPGA(regNum, data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1 << (EMIF_ADDR_WIDTH - 1)) + regNum
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readFPGA(regNum, result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1 << (EMIF_ADDR_WIDTH - 1)) + regNum
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def wrRingdownMem(wordAddr, data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def rdRingdownMem(wordAddr, result):
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
    sgdbrmanager = SgdbrManager(clk=clk, reset=reset,
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
                                map_base=map_base)

    @instance
    def rec_strobe():
        while True:
            yield delay(10000)
            yield clk.posedge
            rec_strobe_in.next = 1
            yield clk.posedge
            rec_strobe_in.next = 0

    @instance
    def stimulus():
        yield assertReset()
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_SCAN_SAMPLES,
                        20)
        yield delay(10 * PERIOD)
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_SAMPLE_TIME,
                        2)
        yield delay(10 * PERIOD)
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_DELAY_SAMPLES,
                        2)
        yield delay(10 * PERIOD)
        # Select mode 1 to use recorder
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_MEMORY_MODE,
                        1 << SGDBRMANAGER_MEMORY_MODE_MODE_B)
        yield delay(10 * PERIOD)
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CSR,
                        1 << SGDBRMANAGER_CSR_START_SCAN_B)
        yield delay(40000 * PERIOD)
        raise StopSimulation
    return instances()


def test_SgdbrManager():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_SgdbrManager()
