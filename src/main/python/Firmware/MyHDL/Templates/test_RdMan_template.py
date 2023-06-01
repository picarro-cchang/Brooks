#!/usr/bin/python
#
# FILE:
#   test_RdMan.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   20-Apr-2018  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import (
    DATA_BANK_ADDR_WIDTH,
    META_BANK_ADDR_WIDTH,
    PARAM_BANK_ADDR_WIDTH,
)
from Host.autogen.interface import (
    RDMEM_DATA_WIDTH,
    RDMEM_META_WIDTH,
    RDMEM_PARAM_WIDTH,
    RDMEM_RESERVED_BANK_ADDR_WIDTH,
)
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_RDMAN

from Host.autogen.interface import RDMAN_CONTROL, RDMAN_STATUS
from Host.autogen.interface import RDMAN_OPTIONS, RDMAN_PARAM0
from Host.autogen.interface import RDMAN_PARAM1, RDMAN_PARAM2
from Host.autogen.interface import RDMAN_PARAM3, RDMAN_PARAM4
from Host.autogen.interface import RDMAN_PARAM5, RDMAN_PARAM6
from Host.autogen.interface import RDMAN_PARAM7, RDMAN_PARAM8
from Host.autogen.interface import RDMAN_PARAM9, RDMAN_PARAM10
from Host.autogen.interface import RDMAN_PARAM11, RDMAN_PARAM12
from Host.autogen.interface import RDMAN_PARAM13, RDMAN_PARAM14
from Host.autogen.interface import RDMAN_PARAM15, RDMAN_DATA_ADDRCNTR
from Host.autogen.interface import RDMAN_METADATA_ADDRCNTR
from Host.autogen.interface import RDMAN_PARAM_ADDRCNTR, RDMAN_DIVISOR
from Host.autogen.interface import RDMAN_NUM_SAMP, RDMAN_THRESHOLD
from Host.autogen.interface import RDMAN_LOCK_DURATION
from Host.autogen.interface import RDMAN_PRECONTROL_DURATION
from Host.autogen.interface import RDMAN_OFF_DURATION
from Host.autogen.interface import RDMAN_EXTRA_DURATION
from Host.autogen.interface import RDMAN_TIMEOUT_DURATION
from Host.autogen.interface import RDMAN_TUNER_AT_RINGDOWN
from Host.autogen.interface import RDMAN_METADATA_ADDR_AT_RINGDOWN
from Host.autogen.interface import RDMAN_RINGDOWN_DATA

from Host.autogen.interface import RDMAN_CONTROL_RUN_B, RDMAN_CONTROL_RUN_W
from Host.autogen.interface import RDMAN_CONTROL_CONT_B, RDMAN_CONTROL_CONT_W
from Host.autogen.interface import RDMAN_CONTROL_START_RD_B, RDMAN_CONTROL_START_RD_W
from Host.autogen.interface import RDMAN_CONTROL_ABORT_RD_B, RDMAN_CONTROL_ABORT_RD_W
from Host.autogen.interface import (
    RDMAN_CONTROL_RESET_RDMAN_B,
    RDMAN_CONTROL_RESET_RDMAN_W,
)
from Host.autogen.interface import (
    RDMAN_CONTROL_BANK0_CLEAR_B,
    RDMAN_CONTROL_BANK0_CLEAR_W,
)
from Host.autogen.interface import (
    RDMAN_CONTROL_BANK1_CLEAR_B,
    RDMAN_CONTROL_BANK1_CLEAR_W,
)
from Host.autogen.interface import (
    RDMAN_CONTROL_RD_IRQ_ACK_B,
    RDMAN_CONTROL_RD_IRQ_ACK_W,
)
from Host.autogen.interface import (
    RDMAN_CONTROL_ACQ_DONE_ACK_B,
    RDMAN_CONTROL_ACQ_DONE_ACK_W,
)
from Host.autogen.interface import (
    RDMAN_CONTROL_RAMP_DITHER_B,
    RDMAN_CONTROL_RAMP_DITHER_W,
)
from Host.autogen.interface import RDMAN_STATUS_SHUTDOWN_B, RDMAN_STATUS_SHUTDOWN_W
from Host.autogen.interface import RDMAN_STATUS_RD_IRQ_B, RDMAN_STATUS_RD_IRQ_W
from Host.autogen.interface import RDMAN_STATUS_ACQ_DONE_B, RDMAN_STATUS_ACQ_DONE_W
from Host.autogen.interface import RDMAN_STATUS_BANK_B, RDMAN_STATUS_BANK_W
from Host.autogen.interface import (
    RDMAN_STATUS_BANK0_IN_USE_B,
    RDMAN_STATUS_BANK0_IN_USE_W,
)
from Host.autogen.interface import (
    RDMAN_STATUS_BANK1_IN_USE_B,
    RDMAN_STATUS_BANK1_IN_USE_W,
)
from Host.autogen.interface import RDMAN_STATUS_LAPPED_B, RDMAN_STATUS_LAPPED_W
from Host.autogen.interface import (
    RDMAN_STATUS_LASER_FREQ_LOCKED_B,
    RDMAN_STATUS_LASER_FREQ_LOCKED_W,
)
from Host.autogen.interface import RDMAN_STATUS_TIMEOUT_B, RDMAN_STATUS_TIMEOUT_W
from Host.autogen.interface import RDMAN_STATUS_ABORTED_B, RDMAN_STATUS_ABORTED_W
from Host.autogen.interface import RDMAN_STATUS_BUSY_B, RDMAN_STATUS_BUSY_W
from Host.autogen.interface import (
    RDMAN_OPTIONS_LOCK_ENABLE_B,
    RDMAN_OPTIONS_LOCK_ENABLE_W,
)
from Host.autogen.interface import (
    RDMAN_OPTIONS_UP_SLOPE_ENABLE_B,
    RDMAN_OPTIONS_UP_SLOPE_ENABLE_W,
)
from Host.autogen.interface import (
    RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B,
    RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W,
)
from Host.autogen.interface import (
    RDMAN_OPTIONS_DITHER_ENABLE_B,
    RDMAN_OPTIONS_DITHER_ENABLE_W,
)
from Host.autogen.interface import (
    RDMAN_OPTIONS_SIM_ACTUAL_B,
    RDMAN_OPTIONS_SIM_ACTUAL_W,
)
from Host.autogen.interface import (
    RDMAN_OPTIONS_SCOPE_MODE_B,
    RDMAN_OPTIONS_SCOPE_MODE_W,
)
from Host.autogen.interface import (
    RDMAN_OPTIONS_SCOPE_SLOPE_B,
    RDMAN_OPTIONS_SCOPE_SLOPE_W,
)

from MyHDL.Common.RdMan import RdMan

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
pulse_100k_in = Signal(LOW)
pulse_1M_in = Signal(LOW)
tuner_value_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta0_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta1_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta2_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta3_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta4_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta5_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta6_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
meta7_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rd_sim_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rd_data_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
tuner_slope_in = Signal(LOW)
tuner_window_in = Signal(LOW)
laser_freq_ok_in = Signal(LOW)
metadata_strobe_in = Signal(LOW)
ext_mode_in = Signal(LOW)
sel_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
ext_laser_current_in_window_in = Signal(intbv(0)[4:])
ext_laser_level_counter_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
ext_laser_sequence_id_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rd_trig_out = Signal(LOW)
laser_extra_out = Signal(LOW)
acc_en_out = Signal(LOW)
rd_irq_out = Signal(LOW)
acq_done_irq_out = Signal(LOW)
rd_adc_clk_out = Signal(LOW)
bank_out = Signal(LOW)
laser_locked_out = Signal(LOW)
data_addr_out = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
wr_data_out = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
data_we_out = Signal(LOW)
meta_addr_out = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
wr_meta_out = Signal(intbv(0)[RDMEM_META_WIDTH:])
meta_we_out = Signal(LOW)
param_addr_out = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH:])
wr_param_out = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
param_we_out = Signal(LOW)
map_base = FPGA_RDMAN


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
    rdman = RdMan(
        clk=clk,
        reset=reset,
        dsp_addr=dsp_addr,
        dsp_data_out=dsp_data_out,
        dsp_data_in=dsp_data_in,
        dsp_wr=dsp_wr,
        pulse_100k_in=pulse_100k_in,
        pulse_1M_in=pulse_1M_in,
        tuner_value_in=tuner_value_in,
        meta0_in=meta0_in,
        meta1_in=meta1_in,
        meta2_in=meta2_in,
        meta3_in=meta3_in,
        meta4_in=meta4_in,
        meta5_in=meta5_in,
        meta6_in=meta6_in,
        meta7_in=meta7_in,
        rd_sim_in=rd_sim_in,
        rd_data_in=rd_data_in,
        tuner_slope_in=tuner_slope_in,
        tuner_window_in=tuner_window_in,
        laser_freq_ok_in=laser_freq_ok_in,
        metadata_strobe_in=metadata_strobe_in,
        ext_mode_in=ext_mode_in,
        sel_fine_current_in=sel_fine_current_in,
        ext_laser_current_in_window_in=ext_laser_current_in_window_in,
        ext_laser_level_counter_in=ext_laser_level_counter_in,
        ext_laser_sequence_id_in=ext_laser_sequence_id_in,
        rd_trig_out=rd_trig_out,
        laser_extra_out=laser_extra_out,
        acc_en_out=acc_en_out,
        rd_irq_out=rd_irq_out,
        acq_done_irq_out=acq_done_irq_out,
        rd_adc_clk_out=rd_adc_clk_out,
        bank_out=bank_out,
        laser_locked_out=laser_locked_out,
        data_addr_out=data_addr_out,
        wr_data_out=wr_data_out,
        data_we_out=data_we_out,
        meta_addr_out=meta_addr_out,
        wr_meta_out=wr_meta_out,
        meta_we_out=meta_we_out,
        param_addr_out=param_addr_out,
        wr_param_out=wr_param_out,
        param_we_out=param_we_out,
        map_base=map_base,
    )

    @instance
    def stimulus():
        yield delay(10 * PERIOD)
        raise StopSimulation

    return instances()


def test_RdMan():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)


if __name__ == "__main__":
    test_RdMan()
