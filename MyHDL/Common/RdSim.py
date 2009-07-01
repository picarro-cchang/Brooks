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
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import RDSIM_EXTRA
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_RDSIM

from Host.autogen.interface import RDSIM_TUNER_CENTER
from Host.autogen.interface import RDSIM_TUNER_WINDOW_HALF_WIDTH
from Host.autogen.interface import RDSIM_FILLING_RATE, RDSIM_DECAY
from Host.autogen.interface import RDSIM_ACCUMULATOR

LOW, HIGH = bool(0), bool(1)
t_State = enum("INIT","GENVALUE")

VHDL_CODE = \
"""
unsigned_mult18x18 : entity work.UnsignedMult18x18_e(Behavioral) 
    port map (
    A => %(a)s, B => %(b)s, P => %(p)s 
    );
"""
def multiplier(p,a,b):
    # Multiplies a and b to yield p
    __vhdl__ = VHDL_CODE
    p.driven = "wire"

    @always_comb
    def logic():
        p.next = int(a)*int(b)
    return instances()

def RdSim(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,rd_trig_in,
          tuner_value_in,rd_adc_clk_in,rdsim_value_out,map_base):
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
    rdsim_value_out     -- Simulated ring-down signal value
    map_base

    Registers:
    RDSIM_TUNER_CENTER  -- Specifies center of tuner window for cavity filling
    RDSIM_TUNER_WINDOW_HALF_WIDTH   -- Specifies half-width of tuner window for cavity filling
    RDSIM_FILLING_RATE  -- Specifies amount added to accumulator on each adc_clk when cavity is filling
    RDSIM_DECAY         -- Specifies decay rate as a binary fraction. Accumulator is multiplied by (1-decay/16) every adc_clk
    RDSIM_ACCUMULATOR   -- High resolution accumulator. Simulator value discards low order four bits of accumulator.
    """
    rdsim_tuner_center_addr = map_base + RDSIM_TUNER_CENTER
    rdsim_tuner_window_half_width_addr = map_base + RDSIM_TUNER_WINDOW_HALF_WIDTH
    rdsim_filling_rate_addr = map_base + RDSIM_FILLING_RATE
    rdsim_decay_addr = map_base + RDSIM_DECAY
    rdsim_accumulator_addr = map_base + RDSIM_ACCUMULATOR
    tuner_center = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuner_window_half_width = Signal(intbv(0)[FPGA_REG_WIDTH:])
    filling_rate = Signal(intbv(0)[FPGA_REG_WIDTH:])
    decay = Signal(intbv(0)[FPGA_REG_WIDTH:])
    accumulator = Signal(intbv(0)[FPGA_REG_WIDTH+RDSIM_EXTRA:])

    a = Signal(intbv(0)[18:])
    b = Signal(intbv(0)[18:])
    p = Signal(intbv(0)[36:])
    state = Signal(t_State.INIT)
    
    mult18x18_inst = multiplier(p=p,a=a,b=b)

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                tuner_center.next = 0
                tuner_window_half_width.next = 0
                filling_rate.next = 0
                decay.next = 0
                accumulator.next = 0
                state.next = t_State.INIT
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
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
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdsim_accumulator_addr: # r
                        dsp_data_in.next = accumulator
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                if state == t_State.INIT:
                    if rd_adc_clk_in:
                        if (tuner_value_in < tuner_center+tuner_window_half_width) and \
                           (tuner_value_in > tuner_center-tuner_window_half_width) and not rd_trig_in:
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
                a.next = concat(intbv(0)[1:],accumulator[FPGA_REG_WIDTH+RDSIM_EXTRA:FPGA_REG_WIDTH+RDSIM_EXTRA-17])
                b.next = concat(intbv(0)[1:],decay,intbv(0)[1:])
                    
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
    rdsim_value_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    map_base = FPGA_RDSIM

    toVHDL(RdSim, clk=clk, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                  dsp_wr=dsp_wr, rd_trig_in=rd_trig_in,
                  tuner_value_in=tuner_value_in,
                  rd_adc_clk_in=rd_adc_clk_in,
                  rdsim_value_out=rdsim_value_out, map_base=map_base)
