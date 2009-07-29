#!/usr/bin/python
#
# FILE:
#   RdSim.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Jun-2009  sze  Initial version.
#   28-Jul-2009  sze  Calculate the distance from the tuner center modulo 16384, so that
#                      we simulate the periodicity of the cavity resonance
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import RDSIM_EXTRA
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_RDSIM

from Host.autogen.interface import RDSIM_OPTIONS, RDSIM_TUNER_CENTER
from Host.autogen.interface import RDSIM_TUNER_WINDOW_HALF_WIDTH
from Host.autogen.interface import RDSIM_FILLING_RATE, RDSIM_DECAY
from Host.autogen.interface import RDSIM_DECAY_IN_SHIFT
from Host.autogen.interface import RDSIM_DECAY_IN_OFFSET
from Host.autogen.interface import RDSIM_ACCUMULATOR

from Host.autogen.interface import RDSIM_OPTIONS_INPUT_SEL_B, RDSIM_OPTIONS_INPUT_SEL_W

from MyHDL.Common.UnsignedMultiplier import UnsignedMultiplier

LOW, HIGH = bool(0), bool(1)
t_State = enum("INIT","GENVALUE")

def RdSim(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,rd_trig_in,
          tuner_value_in,rd_adc_clk_in,pzt_center_in,decay_in,
          rdsim_value_out,map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    rd_trig_in          -- Goes high to turn off injection into cavity
    tuner_value_in      -- Tuner value
    rd_adc_clk_in       -- Clock for ring-down ADC. Data loaded on negative transitions
    pzt_center_in       -- Input for tuner value at ringdown (selected using input_sel)
    decay_in            -- Input for decay rate (selected using input_sel)
    rdsim_value_out     -- Simulated ring-down signal value
    map_base

    Registers:
    RDSIM_OPTIONS       -- Options register
    RDSIM_TUNER_CENTER  -- Specifies center of tuner window for cavity filling
    RDSIM_TUNER_WINDOW_HALF_WIDTH   -- Specifies half-width of tuner window for cavity filling
    RDSIM_FILLING_RATE  -- Specifies amount added to accumulator on each adc_clk when cavity is filling
    RDSIM_DECAY         -- Specifies decay rate as a binary fraction. Accumulator is multiplied by (1-decay/16) every adc_clk
    RDSIM_DECAY_IN_SHIFT -- Decay input is shifted by this number of bits
    RDSIM_DECAY_IN_OFFSET -- This offset is added to the shifted decay input
    RDSIM_ACCUMULATOR   -- High resolution accumulator. Simulator value discards low order four bits of accumulator.

    Fields in RDSIM_OPTIONS:
    RDSIM_OPTIONS_INPUT_SEL -- 0 for register, 1 for input ports
    """
    rdsim_options_addr = map_base + RDSIM_OPTIONS
    rdsim_tuner_center_addr = map_base + RDSIM_TUNER_CENTER
    rdsim_tuner_window_half_width_addr = map_base + RDSIM_TUNER_WINDOW_HALF_WIDTH
    rdsim_filling_rate_addr = map_base + RDSIM_FILLING_RATE
    rdsim_decay_addr = map_base + RDSIM_DECAY
    rdsim_decay_in_shift_addr = map_base + RDSIM_DECAY_IN_SHIFT
    rdsim_decay_in_offset_addr = map_base + RDSIM_DECAY_IN_OFFSET
    rdsim_accumulator_addr = map_base + RDSIM_ACCUMULATOR
    options = Signal(intbv(0)[1:])
    tuner_center = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuner_window_half_width = Signal(intbv(0)[FPGA_REG_WIDTH:])
    filling_rate = Signal(intbv(0)[FPGA_REG_WIDTH:])
    decay = Signal(intbv(0)[FPGA_REG_WIDTH:])
    decay_in_shift = Signal(intbv(0)[4:])
    decay_in_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    accumulator = Signal(intbv(0)[FPGA_REG_WIDTH+RDSIM_EXTRA:])

    a = Signal(intbv(0)[17:])
    b = Signal(intbv(0)[17:])
    p = Signal(intbv(0)[34:])
    state = Signal(t_State.INIT)
    residual = Signal(intbv(0)[14:])
    rmask = residual.max - 1
    
    mult = UnsignedMultiplier(p=p,a=a,b=b)

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                options.next = 0
                tuner_center.next = 0
                tuner_window_half_width.next = 0
                filling_rate.next = 0
                decay.next = 0
                decay_in_shift.next = 0
                decay_in_offset.next = 0
                accumulator.next = 0
                state.next = t_State.INIT
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_options_addr: # rw
                        if dsp_wr: options.next = dsp_data_out
                        dsp_data_in.next = options
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_tuner_center_addr: # rw
                        if dsp_wr: tuner_center.next = dsp_data_out
                        dsp_data_in.next = tuner_center
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_tuner_window_half_width_addr: # rw
                        if dsp_wr: tuner_window_half_width.next = dsp_data_out
                        dsp_data_in.next = tuner_window_half_width
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_filling_rate_addr: # rw
                        if dsp_wr: filling_rate.next = dsp_data_out
                        dsp_data_in.next = filling_rate
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_decay_addr: # rw
                        if dsp_wr: decay.next = dsp_data_out
                        dsp_data_in.next = decay
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_decay_in_shift_addr: # rw
                        if dsp_wr: decay_in_shift.next = dsp_data_out
                        dsp_data_in.next = decay_in_shift
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_decay_in_offset_addr: # rw
                        if dsp_wr: decay_in_offset.next = dsp_data_out
                        dsp_data_in.next = decay_in_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_accumulator_addr: # r
                        dsp_data_in.next = accumulator
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                    
                if options[RDSIM_OPTIONS_INPUT_SEL_B]:
                    decay.next = decay_in_offset + (decay_in >> decay_in_shift)
                    tuner_center.next = pzt_center_in
                    
                residual.next = (tuner_value_in - tuner_center) & rmask
                if state == t_State.INIT:
                    if rd_adc_clk_in:
                        if (residual.signed() < tuner_window_half_width) and \
                           (residual.signed() > -tuner_window_half_width) and not rd_trig_in:
                            # Cavity filling
                            accumulator.next = accumulator + filling_rate
                        else:
                            # Cavity decay
                            accumulator.next = accumulator - concat(intbv(0)[RDSIM_EXTRA:],p[34:34-FPGA_REG_WIDTH])
                        state.next = t_State.GENVALUE
                elif state == t_State.GENVALUE:
                    if not rd_adc_clk_in:
                        state.next = t_State.INIT
                else:
                    state.next = t_State.INIT    
                
                rdsim_value_out.next = accumulator[FPGA_REG_WIDTH+RDSIM_EXTRA:RDSIM_EXTRA]
                a.next = accumulator[FPGA_REG_WIDTH+RDSIM_EXTRA:FPGA_REG_WIDTH+RDSIM_EXTRA-17]
                b.next = concat(decay,intbv(0)[1:])
                    
    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    rd_trig_in = Signal(LOW)
    tuner_value_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rd_adc_clk_in = Signal(LOW)
    pzt_center_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    decay_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rdsim_value_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    map_base = FPGA_RDSIM

    toVHDL(RdSim, clk=clk, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                  dsp_wr=dsp_wr, rd_trig_in=rd_trig_in,
                  tuner_value_in=tuner_value_in,
                  rd_adc_clk_in=rd_adc_clk_in,
                  pzt_center_in=pzt_center_in, decay_in=decay_in,
                  rdsim_value_out=rdsim_value_out, map_base=map_base)
