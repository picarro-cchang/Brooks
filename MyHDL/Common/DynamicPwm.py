#!/usr/bin/python
#
# FILE:
#   DynamicPwm.py
#
# DESCRIPTION:
#   Control of PWM for proportional valves. The PWM signal excites the coil of the
#  valve, and the average current through the coil is monitored and compared with
#  the output of a DAC. The comparator output is fed to this block to adjust the
#  pulse width dynamically. The pulse width is stored in a register which is either
#  incremented or decremented by +/- a specified (signed) amount "delta" depending
#  on the comparator value. The comparator signal is sampled and the pulse width 
#  register is updated on each occurrence of the "update" pulse.
#
# SEE ALSO:
#
# HISTORY:
#   16-Sep-2009  sze  Initial version
#   19-Sep-2009  sze  Add dither waveform generation
#   20-Sep-2009  sze  Added pwm_enable bit in CS register
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_DYNAMICPWM_INLET, FPGA_DYNAMICPWM_OUTLET

from Host.autogen.interface import DYNAMICPWM_CS, DYNAMICPWM_DELTA
from Host.autogen.interface import DYNAMICPWM_HIGH, DYNAMICPWM_LOW
from Host.autogen.interface import DYNAMICPWM_SLOPE

from Host.autogen.interface import DYNAMICPWM_CS_RUN_B, DYNAMICPWM_CS_RUN_W
from Host.autogen.interface import DYNAMICPWM_CS_CONT_B, DYNAMICPWM_CS_CONT_W
from Host.autogen.interface import DYNAMICPWM_CS_PWM_ENABLE_B, DYNAMICPWM_CS_PWM_ENABLE_W
from Host.autogen.interface import DYNAMICPWM_CS_PWM_OUT_B, DYNAMICPWM_CS_PWM_OUT_W


LOW, HIGH = bool(0), bool(1)
def DynamicPwm(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
               comparator_in,update_in,pwm_out,value_out,map_base,
               extra=8,width=16,main_width=8,MIN_WIDTH=0,MAX_WIDTH=65535):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    comparator_in       -- input from comparator
    update_in           -- strobe which causes an update whenever it is high
    pwm_out             -- output pulse-width modulated signal
    value_out           -- dither waveform output
    extra               -- number of additional bits for high-resolution accumulator
    map_base            -- Base of FPGA map for this block
    width               -- 1<<width is period of output waveform
    main_width          -- Number of bits for coarse (main) PWM counter
    MIN_WIDTH           -- Minimum value of pulse_width
    MAX_WIDTH           -- Maximum value of pulse_width
    
    Registers:
    DYNAMICPWM_CS       -- Control/status register
    DYNAMICPWM_DELTA    -- Signed quantity added or subtracted from pulse width on each update
    DYNAMICPWM_HIGH     -- Upper limit of dither waveform
    DYNAMICPWM_LOW      -- Lower limit of dither waveform
    DYNAMICPWM_SLOPE    -- Absolute slope of dither waveform

    Fields in DYNAMICPWM_CS:
    DYNAMICPWM_CS_RUN   -- 0 stops the PWM from running, 1 allows running
    DYNAMICPWM_CS_CONT  -- 0 places system in single-shot mode. i.e., machine runs for one
                            clock cycle each time CS_RUN goes high. The RUN bit is reset
                            at end of cycle.
                           1 places system in continuous mode, which is started by writing 1 to CS_RUN.
    DYNAMICPWM_CS_PWM_ENABLE -- 1 to enable generation of PWM signal
    DYNAMICPWM_CS_PWM_OUT -- A (read-only) copy of the output of the PWM.
    """
    dynamicpwm_cs_addr = map_base + DYNAMICPWM_CS
    dynamicpwm_delta_addr = map_base + DYNAMICPWM_DELTA
    dynamicpwm_high_addr = map_base + DYNAMICPWM_HIGH
    dynamicpwm_low_addr = map_base + DYNAMICPWM_LOW
    dynamicpwm_slope_addr = map_base + DYNAMICPWM_SLOPE
    cs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    delta = Signal(intbv(0,min=-32768,max=32768))
    high = Signal(intbv(0)[FPGA_REG_WIDTH:])
    low = Signal(intbv(0)[FPGA_REG_WIDTH:])
    slope = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pulse_width = Signal(intbv(0)[FPGA_REG_WIDTH:])
    dither_width = width-main_width
    mod_dither = 1 << dither_width
    mod_main = 1 << main_width

    acc = Signal(intbv(0)[FPGA_REG_WIDTH+extra:])
    main_cntr = Signal(intbv(0)[main_width:])
    dither_cntr = Signal(intbv(0)[dither_width:])
    temp = Signal(intbv(0)[dither_width+1:])
    pwm = Signal(LOW)
    up = Signal(LOW) # Current sign of slope
    
    mod_emif_data = 1 << EMIF_DATA_WIDTH

    @always_comb
    def comb():
        if cs[DYNAMICPWM_CS_PWM_ENABLE_B]:
            pwm_out.next = pwm
        else:
            pwm_out.next = 0
        temp.next = dither_cntr + pulse_width[dither_width:0]
    
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                cs.next = 0
                delta.next = 0
                high.next = 0
                low.next = 0
                slope.next = 0
                pulse_width.next = 32768
                main_cntr.next = 0
                dither_cntr.next = 0
                acc.next[FPGA_REG_WIDTH+extra:] = 0
                up.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == dynamicpwm_cs_addr: # rw
                        if dsp_wr: cs.next = dsp_data_out
                        dsp_data_in.next = cs
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == dynamicpwm_delta_addr: # rw
                        if dsp_wr: delta.next = dsp_data_out.signed()
                        dsp_data_in.next = delta[FPGA_REG_WIDTH:]
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == dynamicpwm_high_addr: # rw
                        if dsp_wr: high.next = dsp_data_out
                        dsp_data_in.next = high
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == dynamicpwm_low_addr: # rw
                        if dsp_wr: low.next = dsp_data_out
                        dsp_data_in.next = low
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == dynamicpwm_slope_addr: # rw
                        if dsp_wr: slope.next = dsp_data_out
                        dsp_data_in.next = slope
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                if cs[DYNAMICPWM_CS_RUN_B]:
                    # Reset the run bit if continuous mode is not selected
                    if not cs[DYNAMICPWM_CS_CONT_B]:
                        cs.next[DYNAMICPWM_CS_RUN_B] = 0
                    # Increment the accumulator as needed
                    value = acc[FPGA_REG_WIDTH+extra:extra]
                    if value >= high:
                        up.next = 0
                    elif value <= low:
                        up.next = 1
                    # Handle update of accumulator by adding or subtracting the slope, depending
                    #  on the state of "up". Handle update of width by adding or subtracting delta, 
                    #  depending on the value of comparator_in. We want the width to saturate at 
                    #  MIN_WIDTH and MAX_WIDTH and not to wrap around. Delta can be of either sign, 
                    #  depending on the sense of the comparator. 
                    if update_in:
                        if up:
                            acc.next = acc + slope
                        else:
                            acc.next = acc - slope
                        if delta > 0:
                            if comparator_in:
                                if pulse_width + delta < MAX_WIDTH:
                                    pulse_width.next = pulse_width + delta
                                else:
                                    pulse_width.next = MAX_WIDTH
                            else:
                                if pulse_width - delta > MIN_WIDTH:
                                    pulse_width.next = pulse_width - delta
                                else:
                                    pulse_width.next = MIN_WIDTH
                        else:
                            if comparator_in:
                                if pulse_width + delta > MIN_WIDTH:
                                    pulse_width.next = pulse_width + delta
                                else:
                                    pulse_width.next = MIN_WIDTH
                            else:
                                if pulse_width - delta < MAX_WIDTH:
                                    pulse_width.next = pulse_width - delta
                                else:
                                    pulse_width.next = MAX_WIDTH

                    # The pwm_out is high unconditionally if the main_cntr is less
                    #  than the width.
                    pwm.next = 0
                    if main_cntr < pulse_width[width:width-main_width]:
                        pwm.next = 1
                    # When main_cntr is equal to the width, we need to look at dither_cntr
                    #  and increment the dither counter appropriately
                    elif main_cntr == pulse_width[width:dither_width]:
                        if temp >= mod_dither:
                            pwm.next = 1
                            cs.next[DYNAMICPWM_CS_PWM_OUT_B] = 1
                            dither_cntr.next = temp - mod_dither
                        else:
                            dither_cntr.next = temp
                    main_cntr.next = (main_cntr + 1) % mod_main
                    value_out.next = value
                cs.next[DYNAMICPWM_CS_PWM_OUT_B] = pwm
    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    comparator_in = Signal(LOW)
    update_in = Signal(LOW)
    pwm_out = Signal(LOW)
    value_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    map_base = FPGA_DYNAMICPWM_INLET

    toVHDL(DynamicPwm, clk=clk, reset=reset, dsp_addr=dsp_addr,
                       dsp_data_out=dsp_data_out,
                       dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                       comparator_in=comparator_in, update_in=update_in,
                       pwm_out=pwm_out, value_out=value_out,
                       map_base=map_base)
