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
from myhdl import (Signal, Simulation, StopSimulation, always, always_comb,
                   delay, instance, instances, intbv, toVHDL, traceSignals)

from Host.autogen import interface
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH, EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, META_BANK_ADDR_WIDTH, PARAM_BANK_ADDR_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_SGDBRMANAGER, RDMEM_DATA_WIDTH, RDMEM_META_WIDTH, RDMEM_PARAM_WIDTH

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

from MyHDL.Common.AnalyzerMemory import AnalyzerMemory
from MyHDL.Common.SgdbrManager import SgdbrManager

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in_am = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in_sm = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
rec0_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rec1_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rec2_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rec3_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rec_strobe_in = Signal(LOW)
pb0_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
pb1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
pb_strobe_out = Signal(LOW)
rec_addr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
rec_data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
rec_wfm_sel = Signal(LOW)
rec_we = Signal(LOW)
pb_data = Signal(intbv(0)[RDMEM_META_WIDTH:])
pb_wfm_sel = Signal(LOW)
mode = Signal(LOW)
scan_active_out = Signal(LOW)
sgdbr_present_out = Signal(intbv(0)[2:])
sgdbr_select_out = Signal(LOW)
bank = Signal(LOW)
data_addr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
wr_data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
meta_addr = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
meta = Signal(intbv(0)[RDMEM_META_WIDTH:])
wr_meta = Signal(intbv(0)[RDMEM_META_WIDTH:])
param_addr = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH:])
param = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
wr_param = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
data_we, meta_we, param_we = [Signal(LOW) for i in range(3)]

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

    analyzermemory = AnalyzerMemory(clk=clk, reset=reset, dsp_addr=dsp_addr,
                                    dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_am,
                                    dsp_wr=dsp_wr, mode=mode, pb_data_out=pb_data,
                                    pb_wfm_sel=pb_wfm_sel, rec_data_in=rec_data,
                                    rec_wfm_sel=rec_wfm_sel, rec_addr=rec_addr, rec_we=rec_we,
                                    bank=bank, data_addr=data_addr, data=data, wr_data=wr_data, data_we=data_we,
                                    meta_addr=meta_addr, meta=meta, wr_meta=wr_meta, meta_we=meta_we,
                                    param_addr=param_addr, param=param, wr_param=wr_param, param_we=param_we)

    # N.B. If there are several blocks configured, ensure that dsp_data_in is
    #  derived as the OR of the data buses from the individual blocks.
    sgdbrmanager = SgdbrManager( clk=clk, reset=reset,
                                 dsp_addr=dsp_addr,
                                 dsp_data_out=dsp_data_out,
                                 dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                                 rec0_in=rec0_in, rec1_in=rec1_in,
                                 rec2_in=rec2_in, rec3_in=rec3_in,
                                 rec_strobe_in=rec_strobe_in,
                                 pb0_out=pb0_out, pb1_out=pb1_out,
                                 pb_strobe_out=pb_strobe_out,
                                 rec_addr_out=rec_addr,
                                 rec_data_out=rec_data,
                                 rec_wfm_sel_out=rec_wfm_sel,
                                 rec_we_out=rec_we,
                                 pb_data_in=pb_data,
                                 pb_wfm_sel_out=pb_wfm_sel,
                                 mode_out=mode,
                                 scan_active_out=scan_active_out,
                                 sgdbr_present_out=sgdbr_present_out,
                                 sgdbr_select_out=sgdbr_select_out,
                                 map_base=map_base )

    @always_comb
    def comb():
        dsp_data_in.next = dsp_data_in_am or dsp_data_in_sm
        rec0_in.next = pb1_out
        rec1_in.next = pb0_out
        rec2_in.next = pb1_out << 8
        rec3_in.next = pb0_out << 4

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
        result0 = Signal(intbv(0))
        result1 = Signal(intbv(0))
        result2 = Signal(intbv(0))
        result3 = Signal(intbv(0))
        scanSamples = 20
        yield assertReset()
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_SCAN_SAMPLES,
                        scanSamples)
        yield delay(10 * PERIOD)
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_SAMPLE_TIME,
                        2)
        yield delay(10 * PERIOD)
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_DELAY_SAMPLES,
                        2)
        yield delay(10 * PERIOD)

        yield writeFPGA(
            FPGA_SGDBRMANAGER + SGDBRMANAGER_SGDBR_PRESENT, 
            1 << SGDBRMANAGER_SGDBR_PRESENT_SGDBR_A_PRESENT_B)
        # Select mode 1 to use recorder
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CONFIG,
                        1 << SGDBRMANAGER_CONFIG_MODE_B)
        yield delay(10 * PERIOD)
        # Write playback waveforms
        for iter in range(scanSamples):
            addr = 0x1000 + iter
            d = 64 + 16 * iter
            yield wrRingdownMem(addr, d)
            addr = 0x5000 + iter
            d = 17 + 8 * iter
            yield wrRingdownMem(addr, d)
        print "Wrote playback waveforms"

        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CSR,
                        1 << SGDBRMANAGER_CSR_START_SCAN_B)
        yield delay(40000 * PERIOD)
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CSR,
                        1 << SGDBRMANAGER_CSR_START_SCAN_B)
        yield delay(10000 * PERIOD)
        # Read back record waveforms
        for iter in range(scanSamples):
            addr = 0x0000 + iter
            yield rdRingdownMem(addr, result0)
            addr = 0x4000 + iter
            yield rdRingdownMem(addr, result1)
            addr = 0x800 + iter
            yield rdRingdownMem(addr, result2)
            addr = 0x4800 + iter
            yield rdRingdownMem(addr, result3)

            print "%04x: %04x %04x %04x %04x" % (iter, result0, result1, result2, result3)
        # Select mode 0 to switch to ringdowns
        yield writeFPGA(FPGA_SGDBRMANAGER + SGDBRMANAGER_CONFIG, 0)
        yield delay(5000 * PERIOD)

        raise StopSimulation
    return instances()


def test_SgdbrManager():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_SgdbrManager()
