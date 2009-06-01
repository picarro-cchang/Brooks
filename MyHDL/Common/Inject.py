#!/usr/bin/python
#
# FILE:
#   Inject.py
#
# DESCRIPTION:
#   MyHDL for optical injection block
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   31-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#

Each DAC has two outputs (a coarse current and a fine current) which are updated on a 100kHz schedule. It takes 24 clock cycles to download each channel. By running the serial clock at  , it is possible to update both outputs every , interleaving the updates.

5.9.1 Inputs

MM laser_dac_clk  clock for driving DAC8522 at 50 times (needs to be at least 24 times per channel) 100kHz update rate

MM laser_fine_current_in Laser fine current setting.

MM laser_shutdown_in Turns off laser using shorting switch

MM soa_shutdown_in Turns off SOA, using shorting switch

5.9.2 Outputs

MM laser_dac_sclk Serial clock for laser current DACs

MM laser_sync_z Start of frame for laser current DACs

MM laser1_dac_din Laser 1 DAC data (coarse and fine current multiplexed)

MM laser2_dac_din Laser 2 DAC data (coarse and fine current multiplexed)

MM laser3_dac_din Laser 3 DAC data (coarse and fine current multiplexed)

MM laser4_dac_din Laser 4 DAC data (coarse and fine current multiplexed)

MM laser1_enable Laser 1 current source enable

MM laser2_enable Laser 2 current source enable

MM laser3_enable Laser 3 current source enable

MM laser4_enable Laser 4 current source enable

MM laser1_shutdown Activate laser 1 shorting switch

MM laser2_shutdown Activate laser 2 shorting switch

MM laser3_shutdown Activate laser 3 shorting switch

MM laser4_shutdown Activate laser 4 shorting switch

MM soa_shutdown Activate SOA shorting switch

5.9.3 Registers


from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import FPGA_TWGEN

from Host.autogen.interface import TWGEN_ACC
from Host.autogen.interface import TWGEN_CS
from Host.autogen.interface import TWGEN_SLOPE_DOWN
from Host.autogen.interface import TWGEN_SLOPE_UP
from Host.autogen.interface import TWGEN_SWEEP_LOW
from Host.autogen.interface import TWGEN_SWEEP_HIGH
from Host.autogen.interface import TWGEN_WINDOW_LOW
from Host.autogen.interface import TWGEN_WINDOW_HIGH

from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH, FPGA_REG_MASK
from Host.autogen.interface import TWGEN_CS_RUN_B, TWGEN_CS_CONT_B, TWGEN_CS_RESET_B

LOW, HIGH = bool(0), bool(1)

def TWGen(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,synth_step_in,
            value_out,slope_out,in_window_out,map_base,extra=9):
    """Tuner waveform generator
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    synth_step_in       -- pulse to step waveform synthesizer
    value_out           -- waveform generator output
    slope_out           -- 1 on up slope, 0 on down slope
    in_window_out       -- 1 when value is within the window
    extra               -- Number of extra bits for high-resolution accumulator

    This block appears as several registers to the DSP, starting at map_base. The registers are:
    TWGEN_ACC           -- High-resolution accumulator
    TWGEN_CS            -- Control/status register
    TWGEN_SLOPE_DOWN    -- (unsigned) down slope value, subtracted from
                            hi-res accumulator on each step while on
                            down slope
    TWGEN_SLOPE_UP      -- (unsigned) up slope value, added to hi-res
                            accumulator on each step while on up slope
    TWGEN_SWEEP_HIGH    -- value above which down slope starts
    TWGEN_SWEEP_LOW     -- value below which up slope starts
    TWGEN_WINDOW_HIGH   -- value above which ringdowns are inhibited
    TWGEN_WINDOW_LOW    -- value below which ringdowns are inhibited

    Bits within the TWGEN_CS register are:
    TWGEN_CS_RUN        -- 0 stops the TWGEN from running, 1 allows running
    TWGEN_CS_CONT       -- 0 places TWGEN in single-shot mode. i.e., machine runs for one
                            clock cycle each time TWGEN_CS_RUN goes high. The RUN bit is reset
                            at end of cycle.
                           1 places TWGEN in continuous mode, which is started by writing 1 to TWGEN_CS_RUN.
    TWGEN_CS_RESET      -- resets the accumulator to mid-range and slope to 1 while asserted
    """

    TWGen_acc_addr = map_base + TWGEN_ACC
    TWGen_cs_addr = map_base + TWGEN_CS
    TWGen_slope_down_addr = map_base + TWGEN_SLOPE_DOWN
    TWGen_slope_up_addr = map_base + TWGEN_SLOPE_UP
    TWGen_sweep_low_addr = map_base + TWGEN_SWEEP_LOW
    TWGen_sweep_high_addr = map_base + TWGEN_SWEEP_HIGH
    TWGen_window_low_addr = map_base + TWGEN_WINDOW_LOW
    TWGen_window_high_addr = map_base + TWGEN_WINDOW_HIGH

    dsp_data_from_regs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    acc = Signal(intbv(0)[FPGA_REG_WIDTH+extra:])
    cs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    slope_down = Signal(intbv(0)[FPGA_REG_WIDTH:])
    slope_up = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sweep_low = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sweep_high = Signal(intbv(0)[FPGA_REG_WIDTH:])
    window_low = Signal(intbv(0)[FPGA_REG_WIDTH:])
    window_high = Signal(intbv(0)[FPGA_REG_WIDTH:])

    slope = Signal(LOW)
    value = Signal(intbv(0)[FPGA_REG_WIDTH:])

    @always_comb
    def comb1():
        value.next = acc[FPGA_REG_WIDTH+extra:extra]

    @always_comb
    def comb2():
        dsp_data_in.next = dsp_data_from_regs
        value_out.next = value
        in_window_out.next = (value >= window_low) and (value <= window_high)
        slope_out.next = slope

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                acc.next[FPGA_REG_WIDTH+extra-1] = 1
                acc.next[FPGA_REG_WIDTH+extra-1:] = 0
                cs.next = 0
                slope_down.next = 0
                slope_up.next = 0
                sweep_low.next = 0
                sweep_high.next = 0
                window_low.next = 0
                window_high.next = 0
                slope.next = 1
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_acc_addr:
                        if dsp_wr: acc.next = dsp_data_out
                        dsp_data_from_regs.next = acc
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_cs_addr:
                        if dsp_wr: cs.next = dsp_data_out
                        dsp_data_from_regs.next = cs
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_slope_down_addr:
                        if dsp_wr: slope_down.next = dsp_data_out
                        dsp_data_from_regs.next = slope_down
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_slope_up_addr:
                        if dsp_wr: slope_up.next = dsp_data_out
                        dsp_data_from_regs.next = slope_up
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_sweep_low_addr:
                        if dsp_wr: sweep_low.next = dsp_data_out
                        dsp_data_from_regs.next = sweep_low
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_sweep_high_addr:
                        if dsp_wr: sweep_high.next = dsp_data_out
                        dsp_data_from_regs.next = sweep_high
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_window_low_addr:
                        if dsp_wr: window_low.next = dsp_data_out
                        dsp_data_from_regs.next = window_low
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == TWGen_window_high_addr:
                        if dsp_wr: window_high.next = dsp_data_out
                        dsp_data_from_regs.next = window_high
                    else:
                        dsp_data_from_regs.next = 0
                else:
                    dsp_data_from_regs.next = 0

                if cs[TWGEN_CS_RUN_B]:
                    if not cs[TWGEN_CS_CONT_B]:
                        cs.next[TWGEN_CS_RUN_B] = 0
                    if cs[TWGEN_CS_RESET_B]:
                        acc.next[FPGA_REG_WIDTH+extra-1] = 1
                        acc.next[FPGA_REG_WIDTH+extra-1:] = 0
                        slope.next = 1
                    else:
                        if value >= sweep_high:
                            slope.next = 0
                        elif value <= sweep_low:
                            slope.next = 1
                        if synth_step_in:
                            if slope:
                                acc.next = acc + slope_up
                            else:
                                acc.next = acc - slope_down

    return instances()

if __name__ == "__main__":
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    value_out  = Signal(intbv(0)[FPGA_REG_WIDTH:])
    dsp_wr, clk, reset, synth_step_in, slope_out, in_window_out = [Signal(LOW) for i in range(6)]
    map_base = FPGA_TWGEN

    toVHDL(TWGen, clk=clk, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                  dsp_wr=dsp_wr, synth_step_in=synth_step_in,
                  value_out=value_out, slope_out=slope_out,
                  in_window_out=in_window_out,map_base=map_base)
