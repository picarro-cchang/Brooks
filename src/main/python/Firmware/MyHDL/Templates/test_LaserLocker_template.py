#!/usr/bin/python
#
# FILE:
#   test_LaserLocker.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Jan-2019  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import WLM_ADC_WIDTH
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_LASERLOCKER

from Host.autogen.interface import LASERLOCKER_CS, LASERLOCKER_OPTIONS
from Host.autogen.interface import LASERLOCKER_ETA1, LASERLOCKER_REF1
from Host.autogen.interface import LASERLOCKER_ETA2, LASERLOCKER_REF2
from Host.autogen.interface import LASERLOCKER_ETA1_DARK
from Host.autogen.interface import LASERLOCKER_REF1_DARK
from Host.autogen.interface import LASERLOCKER_ETA2_DARK
from Host.autogen.interface import LASERLOCKER_REF2_DARK
from Host.autogen.interface import LASERLOCKER_ETA1_OFFSET
from Host.autogen.interface import LASERLOCKER_REF1_OFFSET
from Host.autogen.interface import LASERLOCKER_ETA2_OFFSET
from Host.autogen.interface import LASERLOCKER_REF2_OFFSET
from Host.autogen.interface import LASERLOCKER_RATIO1
from Host.autogen.interface import LASERLOCKER_RATIO2
from Host.autogen.interface import LASERLOCKER_RATIO1_CENTER
from Host.autogen.interface import LASERLOCKER_RATIO1_MULTIPLIER
from Host.autogen.interface import LASERLOCKER_RATIO2_CENTER
from Host.autogen.interface import LASERLOCKER_RATIO2_MULTIPLIER
from Host.autogen.interface import LASERLOCKER_TUNING_OFFSET
from Host.autogen.interface import LASERLOCKER_LOCK_ERROR
from Host.autogen.interface import LASERLOCKER_WM_LOCK_WINDOW
from Host.autogen.interface import LASERLOCKER_WM_INT_GAIN
from Host.autogen.interface import LASERLOCKER_WM_PROP_GAIN
from Host.autogen.interface import LASERLOCKER_WM_DERIV_GAIN
from Host.autogen.interface import LASERLOCKER_FINE_CURRENT
from Host.autogen.interface import LASERLOCKER_CYCLE_COUNTER

from Host.autogen.interface import LASERLOCKER_CS_RUN_B, LASERLOCKER_CS_RUN_W
from Host.autogen.interface import LASERLOCKER_CS_CONT_B, LASERLOCKER_CS_CONT_W
from Host.autogen.interface import LASERLOCKER_CS_PRBS_B, LASERLOCKER_CS_PRBS_W
from Host.autogen.interface import LASERLOCKER_CS_ACC_EN_B, LASERLOCKER_CS_ACC_EN_W
from Host.autogen.interface import (
    LASERLOCKER_CS_SAMPLE_DARK_B,
    LASERLOCKER_CS_SAMPLE_DARK_W,
)
from Host.autogen.interface import (
    LASERLOCKER_CS_ADC_STROBE_B,
    LASERLOCKER_CS_ADC_STROBE_W,
)
from Host.autogen.interface import (
    LASERLOCKER_CS_TUNING_OFFSET_SEL_B,
    LASERLOCKER_CS_TUNING_OFFSET_SEL_W,
)
from Host.autogen.interface import (
    LASERLOCKER_CS_LASER_FREQ_OK_B,
    LASERLOCKER_CS_LASER_FREQ_OK_W,
)
from Host.autogen.interface import (
    LASERLOCKER_CS_CURRENT_OK_B,
    LASERLOCKER_CS_CURRENT_OK_W,
)
from Host.autogen.interface import (
    LASERLOCKER_OPTIONS_SIM_ACTUAL_B,
    LASERLOCKER_OPTIONS_SIM_ACTUAL_W,
)
from Host.autogen.interface import (
    LASERLOCKER_OPTIONS_DIRECT_TUNE_B,
    LASERLOCKER_OPTIONS_DIRECT_TUNE_W,
)
from Host.autogen.interface import (
    LASERLOCKER_OPTIONS_RATIO_OUT_SEL_B,
    LASERLOCKER_OPTIONS_RATIO_OUT_SEL_W,
)

from MyHDL.Common.LaserLocker import LaserLocker

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
eta1_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
ref1_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
eta2_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
ref2_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
tuning_offset_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
acc_en_in = Signal(LOW)
adc_strobe_in = Signal(LOW)
ratio1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
ratio2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
lock_error_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
tuning_offset_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
pid_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser_freq_ok_out = Signal(LOW)
current_ok_out = Signal(LOW)
sim_actual_out = Signal(LOW)
map_base = FPGA_LASERLOCKER


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
    laserlocker = LaserLocker(
        clk=clk,
        reset=reset,
        dsp_addr=dsp_addr,
        dsp_data_out=dsp_data_out,
        dsp_data_in=dsp_data_in,
        dsp_wr=dsp_wr,
        eta1_in=eta1_in,
        ref1_in=ref1_in,
        eta2_in=eta2_in,
        ref2_in=ref2_in,
        tuning_offset_in=tuning_offset_in,
        acc_en_in=acc_en_in,
        adc_strobe_in=adc_strobe_in,
        ratio1_out=ratio1_out,
        ratio2_out=ratio2_out,
        lock_error_out=lock_error_out,
        fine_current_out=fine_current_out,
        tuning_offset_out=tuning_offset_out,
        pid_out=pid_out,
        laser_freq_ok_out=laser_freq_ok_out,
        current_ok_out=current_ok_out,
        sim_actual_out=sim_actual_out,
        map_base=map_base,
    )

    @instance
    def stimulus():
        yield delay(10 * PERIOD)
        raise StopSimulation

    return instances()


def test_LaserLocker():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)


if __name__ == "__main__":
    test_LaserLocker()
