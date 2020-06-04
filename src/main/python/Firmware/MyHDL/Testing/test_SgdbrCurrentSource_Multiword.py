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

from myhdl import (Signal, Simulation, StopSimulation, always, delay, instance,
                   instances, intbv, toVHDL, traceSignals)

from Host.autogen import interface
from Host.autogen.interface import (EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH,
                                    FPGA_REG_MASK, FPGA_REG_WIDTH,
                                    FPGA_SGDBRCURRENTSOURCE,
                                    SGDBRCURRENTSOURCE_CSR,
                                    SGDBRCURRENTSOURCE_CSR_CPHA_B,
                                    SGDBRCURRENTSOURCE_CSR_CPHA_W,
                                    SGDBRCURRENTSOURCE_CSR_CPOL_B,
                                    SGDBRCURRENTSOURCE_CSR_CPOL_W,
                                    SGDBRCURRENTSOURCE_CSR_DONE_B,
                                    SGDBRCURRENTSOURCE_CSR_DONE_W,
                                    SGDBRCURRENTSOURCE_CSR_MISO_B,
                                    SGDBRCURRENTSOURCE_CSR_MISO_W,
                                    SGDBRCURRENTSOURCE_CSR_RESET_B,
                                    SGDBRCURRENTSOURCE_CSR_RESET_W,
                                    SGDBRCURRENTSOURCE_CSR_SELECT_B,
                                    SGDBRCURRENTSOURCE_CSR_SELECT_W,
                                    SGDBRCURRENTSOURCE_MISO_DATA,
                                    SGDBRCURRENTSOURCE_MOSI_DATA,
                                    SGDBRCURRENTSOURCE_NUM_OF_CLOCK_PULSES,
                                    SGDBRCURRENTSOURCE_SCK_DIVISOR)
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


class TestSPI(TestCase):

    def test_spi(self):
        self.CPOL = 1
        self.CPHA = 1
        self.num_of_clock_pulses = 16
        self.miso_data = 0xF1D0
        self.mosi_data = 0xA5A5

        def bench():
            PERIOD = 20  # 50MHz clock

            @always(delay(PERIOD // 2))
            def clockGen():
                clk.next = not clk

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
                                                    data_out=data_out,
                                                    resetn_out=resetn_out,
                                                    done_out=done_out,
                                                    map_base=map_base)

            @instance
            def stimulus():
                miso_data = Signal(intbv(0)[EMIF_DATA_WIDTH:])
                yield assertReset()
                # 1 << SGDBRCURRENTSOURCE_CSR_CPHA_B)
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_SCK_DIVISOR, 5)
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_CSR,
                                (self.CPHA << SGDBRCURRENTSOURCE_CSR_CPHA_B) |
                                (self.CPOL << SGDBRCURRENTSOURCE_CSR_CPOL_B))
                yield delay(50 * PERIOD)
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_CSR,
                                (self.CPHA << SGDBRCURRENTSOURCE_CSR_CPHA_B) |
                                (self.CPOL << SGDBRCURRENTSOURCE_CSR_CPOL_B) |
                                (1 << SGDBRCURRENTSOURCE_CSR_SELECT_B))

                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_NUM_OF_CLOCK_PULSES, self.num_of_clock_pulses)
                yield delay(4 * PERIOD)
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MOSI_DATA, self.mosi_data)
                yield done_out.posedge
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MOSI_DATA, self.mosi_data)
                yield done_out.posedge
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MOSI_DATA, self.mosi_data)
                yield done_out.posedge
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_MOSI_DATA, self.mosi_data)
                yield done_out.posedge
                yield writeFPGA(FPGA_SGDBRCURRENTSOURCE + SGDBRCURRENTSOURCE_CSR,
                                (self.CPHA << SGDBRCURRENTSOURCE_CSR_CPHA_B) |
                                (self.CPOL << SGDBRCURRENTSOURCE_CSR_CPOL_B))
                yield delay(50 * PERIOD)
                raise StopSimulation

            # @instance
            # def data_generator():
            #     value = self.miso_data
            #     if self.CPHA == 0:
            #         while True:
            #             yield csn_out.negedge
            #             for k in range(self.num_of_clock_pulses):
            #                 data_in.next = 1 & (
            #                     value >> (self.num_of_clock_pulses - k - 1))
            #                 yield sck_out.negedge if self.CPOL == 0 else sck_out.posedge, csn_out.posedge
            #                 if csn_out:
            #                     break
            #     else:
            #         while True:
            #             yield csn_out.negedge
            #             for k in range(self.num_of_clock_pulses):
            #                 yield sck_out.posedge if self.CPOL == 0 else sck_out.negedge, csn_out.posedge
            #                 if csn_out:
            #                     break
            #                 data_in.next = 1 & (
            #                     value >> (self.num_of_clock_pulses - k - 1))

            # @instance
            # def data_receiver():
            #     result = 0
            #     if self.CPHA == 0:
            #         while True:
            #             yield csn_out.negedge
            #             while True:
            #                 yield sck_out.posedge if self.CPOL == 0 else sck_out.negedge, csn_out.posedge
            #                 if csn_out:
            #                     self.assertEqual(result, self.mosi_data)
            #                     break
            #                 else:
            #                     result = 2 * result + data_out
            #     else:
            #         while True:
            #             yield csn_out.negedge
            #             while True:
            #                 yield sck_out.negedge if self.CPOL == 0 else sck_out.posedge, csn_out.posedge
            #                 if csn_out:
            #                     self.assertEqual(result, self.mosi_data)
            #                     break
            #                 else:
            #                     result = 2 * result + data_out

            return instances()

        s = Simulation(traceSignals(bench))
        s.run(quiet=1)


if __name__ == "__main__":
    main()
