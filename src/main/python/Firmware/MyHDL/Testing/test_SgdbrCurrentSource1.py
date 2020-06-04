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
#   03-Feb-2018  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from random import randrange
from unittest import TestCase, main

from myhdl import (Signal, Simulation, StopSimulation, always, delay, enum, instance,
                   instances, intbv, toVHDL, traceSignals)

from Host.autogen import interface
from Host.autogen.interface import FPGA_SGDBRCURRENTSOURCE_A as FPGA_SGDBRCURRENTSOURCE
from Host.autogen.interface import (EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH,
                                    FPGA_REG_MASK, FPGA_REG_WIDTH,
                                    SGDBRCURRENTSOURCE_CSR,
                                    SGDBRCURRENTSOURCE_CSR_CPHA_B,
                                    SGDBRCURRENTSOURCE_CSR_CPHA_W,
                                    SGDBRCURRENTSOURCE_CSR_CPOL_B,
                                    SGDBRCURRENTSOURCE_CSR_CPOL_W,
                                    SGDBRCURRENTSOURCE_CSR_DESELECT_B,
                                    SGDBRCURRENTSOURCE_CSR_DESELECT_W,
                                    SGDBRCURRENTSOURCE_CSR_DONE_B,
                                    SGDBRCURRENTSOURCE_CSR_DONE_W,
                                    SGDBRCURRENTSOURCE_CSR_MISO_B,
                                    SGDBRCURRENTSOURCE_CSR_MISO_W,
                                    SGDBRCURRENTSOURCE_CSR_RESET_B,
                                    SGDBRCURRENTSOURCE_CSR_RESET_W,
                                    SGDBRCURRENTSOURCE_CSR_SELECT_B,
                                    SGDBRCURRENTSOURCE_CSR_SELECT_W,
                                    SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B,
                                    SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_W,
                                    SGDBRCURRENTSOURCE_CSR_SUPPRESS_UPDATE_B, 
                                    SGDBRCURRENTSOURCE_CSR_SUPPRESS_UPDATE_W,
                                    SGDBRCURRENTSOURCE_MAX_SYNC_CURRENT,
                                    SGDBRCURRENTSOURCE_MISO_DATA,
                                    SGDBRCURRENTSOURCE_MISO_DELAY,
                                    SGDBRCURRENTSOURCE_MOSI_DATA)
from MyHDL.Common.SgdbrCurrentSource import SgdbrCurrentSource

t_EnumType = enum("NORMAL", "PENDING", "SYNC_UPDATE")
LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
update = Signal(LOW)
prev_update = Signal(LOW)
strobe = Signal(LOW)
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
# sync_strobe_in = Signal(LOW)
data_out = Signal(LOW)
resetn_out = Signal(LOW)
done_out = Signal(LOW)
map_base = FPGA_SGDBRCURRENTSOURCE


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


def block_vars(block):
    names = []
    for inst in block:
        try:
            names.extend(inst.gen.gi_frame.f_locals[
                         "func"].__code__.co_freevars)
        except:
            try:
                names.extend(inst.gen.gi_frame.f_locals.keys())
            except:
                continue
    return set(names)


def fetch_block_var(block, name):
    # import pdb
    # pdb.set_trace()
    for inst in block:
        try:
            freevars = inst.gen.gi_frame.f_locals["func"].__code__.co_freevars
            try:
                index = freevars.index(name)
                return inst.gen.gi_frame.f_locals["func"].__closure__[index].cell_contents
            except:
                continue
        except:
            return inst.gen.gi_frame.f_locals[name]


class TestSPI(TestCase):

    def test_spi(self):
        self.CPOL = 1
        self.CPHA = 1
        self.num_of_clock_pulses = 32
        self.miso_data  = 0
        def bench():
            PERIOD = 20  # 50MHz clock

            @always(delay(500 * PERIOD // 2))
            def strobeGen():
                update.next = not update

            @always(delay(PERIOD // 2))
            def clockGen():
                clk.next = not clk
                prev_update.next = update
                strobe.next = update and not prev_update

            # N.B. If there are several blocks configured, ensure that dsp_data_in is
            #  derived as the OR of the data buses from the individual blocks.
            sgdbrcurrentsource = SgdbrCurrentSource(clk=clk, reset=reset,
                                                    dsp_addr=dsp_addr,
                                                    dsp_data_out=dsp_data_out,
                                                    dsp_data_in=dsp_data_in,
                                                    dsp_wr=dsp_wr,
                                                    sck_out=sck_out,
                                                    csn_out=csn_out,
                                                    data_in=data_in,
                                                    sync_current_in=sync_current_in,
                                                    sync_register_in=sync_register_in,
                                                    sync_strobe_in=strobe,
                                                    data_out=data_out,
                                                    resetn_out=resetn_out,
                                                    done_out=done_out,
                                                    map_base=map_base)

            @instance
            def stimulus():
                self.CPOL = 1  # randrange(0, 2)
                self.CPHA = 1  # randrange(0, 2)
                yield assertReset()
                sync_current_in.next = 0xAAAA
                sync_register_in.next = 0x5
                for trials in range(100):
                    self.miso_data = randrange(
                        0, 1 << self.num_of_clock_pulses)
                    self.mosi_data = randrange(
                        0, 1 << self.num_of_clock_pulses)
                    print "%08x" % self.miso_data
                    print "%08x" % self.mosi_data

                    miso_data = Signal(intbv(0)[EMIF_DATA_WIDTH:])
                    # 1 << SGDBRCURRENTSOURCE_CSR_CPHA_B)
                    yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_CSR,
                                    (self.CPHA << SGDBRCURRENTSOURCE_CSR_CPHA_B) | (self.CPOL << SGDBRCURRENTSOURCE_CSR_CPOL_B) |
                                    (1 << SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B))
                    yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MISO_DELAY, 2)
                    max_sync_current = 0xD800
                    yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MAX_SYNC_CURRENT, max_sync_current)
                    yield delay(10 * PERIOD)
                    yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MOSI_DATA, self.mosi_data)
                    yield done_out.posedge
                    yield readFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MISO_DATA, miso_data)
                    self.assertEqual(miso_data, self.miso_data)
                    yield delay(randrange(0*PERIOD, 50 * PERIOD))
                raise StopSimulation

            @instance
            def data_generator():
                while True:
                    yield csn_out.negedge
                    value = self.miso_data
                    if self.CPHA == 0:
                        for k in range(self.num_of_clock_pulses):
                            data_in.next = 1 & (
                                value >> (self.num_of_clock_pulses - k - 1))
                            yield sck_out.negedge if self.CPOL == 0 else sck_out.posedge, csn_out.posedge
                            if csn_out:
                                break
                    else:
                        for k in range(self.num_of_clock_pulses):
                            yield sck_out.posedge if self.CPOL == 0 else sck_out.negedge, csn_out.posedge
                            if csn_out:
                                break
                            data_in.next = 1 & (
                                value >> (self.num_of_clock_pulses - k - 1))

            @instance
            def data_receiver():
                result = 0
                if self.CPHA == 0:
                    while True:
                        yield csn_out.negedge
                        while True:
                            yield sck_out.posedge if self.CPOL == 0 else sck_out.negedge, csn_out.posedge
                            if csn_out:
                                if str(fetch_block_var(sgdbrcurrentsource, "access_type")) in ["SYNC_UPDATE"]:
                                    self.assertEqual(
                                        result, (sync_register_in << 24) | min(sync_current_in, max_sync_current))
                                else:

                                    self.assertEqual(result, self.mosi_data)
                                result = 0
                                break
                            else:
                                result = 2 * result + data_out
                else:
                    while True:
                        yield csn_out.negedge
                        while True:
                            yield sck_out.negedge if self.CPOL == 0 else sck_out.posedge, csn_out.posedge
                            if csn_out:
                                sync_value = int((sync_register_in << 24) | sync_current_in)
                                mosi_value = int(self.mosi_data)
                                self.assertTrue(result == sync_value or result == mosi_value)
                                # if str(fetch_block_var(sgdbrcurrentsource, "access_type")) in ["SYNC_UPDATE"]:
                                #     if int(result) != int((sync_register_in << 24) | sync_current_in):
                                #         print "%x != %x" % (result, (sync_register_in << 24) | sync_current_in)
                                #     self.assertEqual(
                                #         result, (sync_register_in << 24) | sync_current_in)
                                # else:
                                #     if int(result) != int(self.mosi_data):
                                #         print "%x != %x" % (result, self.mosi_data)
                                #     self.assertEqual(result, self.mosi_data)
                                result = 0
                                break
                            else:
                                result = 2 * result + data_out
            return instances()

        s = Simulation(traceSignals(bench))
        s.run(quiet=1)

if __name__ == "__main__":
    main()
