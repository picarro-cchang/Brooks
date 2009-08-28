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
#   26-Aug-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_DYNAMICPWM_INLET, FPGA_DYNAMICPWM_OUTLET

from Host.autogen.interface import DYNAMICPWM_CS, DYNAMICPWM_DELTA

from Host.autogen.interface import DYNAMICPWM_CS_RUN_B, DYNAMICPWM_CS_RUN_W
from Host.autogen.interface import DYNAMICPWM_CS_CONT_B, DYNAMICPWM_CS_CONT_W
from Host.autogen.interface import DYNAMICPWM_CS_PWM_OUT_B, DYNAMICPWM_CS_PWM_OUT_W


LOW, HIGH = bool(0), bool(1)
def DynamicPwm(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
               comparator_in,update_in,pwm_out,map_base,
               width=16,main_width=8,MIN_WIDTH=0,MAX_WIDTH=65535):
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
    map_base            -- Base of FPGA map for this block
    width               -- 1<<width is period of output waveform
    main_width          -- Number of bits for coarse (main) PWM counter
    MIN_WIDTH           -- Minimum value of pulse_width
    MAX_WIDTH           -- Maximum value of pulse_width
    
    Registers:
    DYNAMICPWM_CS       -- Control/status register
    DYNAMICPWM_DELTA    -- Signed quantity added or subtracted from pulse width on each update

    Fields in DYNAMICPWM_CS:
    DYNAMICPWM_CS_RUN   -- 0 stops the PWM from running, 1 allows running
    DYNAMICPWM_CS_CONT  -- 0 places system in single-shot mode. i.e., machine runs for one
                            clock cycle each time CS_RUN goes high. The RUN bit is reset
                            at end of cycle.
                           1 places system in continuous mode, which is started by writing 1 to CS_RUN.
    DYNAMICPWM_CS_PWM_OUT -- A (read-only) copy of the output of the PWM.
    """
    dynamicpwm_cs_addr = map_base + DYNAMICPWM_CS
    dynamicpwm_delta_addr = map_base + DYNAMICPWM_DELTA
    cs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    delta = Signal(intbv(0,min=-32768,max=32768))
    pulse_width = Signal(intbv(0)[FPGA_REG_WIDTH:])
    
    dither_width = width-main_width
    mod_dither = 1 << dither_width
    mod_main = 1 << main_width

    main_cntr = Signal(intbv(0)[main_width:])
    dither_cntr = Signal(intbv(0)[dither_width:])
    temp = Signal(intbv(0)[dither_width+1:])
    pwm = Signal(LOW)
    
    EMIF_DATA_MASK = (1 << EMIF_DATA_WIDTH) - 1

    @always_comb
    def comb():
        pwm_out.next = pwm
        temp.next = dither_cntr + pulse_width[dither_width:0]
    
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                cs.next = 0
                delta.next = 0
                pulse_width.next = 32768
                main_cntr.next = 0
                dither_cntr.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == dynamicpwm_cs_addr: # rw
                        if dsp_wr: cs.next = dsp_data_out
                        dsp_data_in.next = cs
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == dynamicpwm_delta_addr: # rw
                        if dsp_wr: delta.next = dsp_data_out.signed()
                        dsp_data_in.next = delta & EMIF_DATA_MASK
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                if cs[DYNAMICPWM_CS_RUN_B]:
                    # Reset the run bit if continuous mode is not selected
                    if not cs[DYNAMICPWM_CS_CONT_B]:
                        cs.next[DYNAMICPWM_CS_RUN_B] = 0
                    # Handle update of width by adding or subtracting delta, depending on the
                    #  value of comparator_in. We want the width to saturate at MIN_WIDTH and
                    #  MAX_WIDTH and not to wrap around. Delta can be of either sign, depending
                    #  on the sense of the comparator.
                    if update_in:
                        if delta > 0:
                            if comparator_in:
                                if pulse_width < MAX_WIDTH - delta:
                                    pulse_width.next = pulse_width + delta
                                else:
                                    pulse_width.next = MAX_WIDTH
                            else:
                                if pulse_width > MIN_WIDTH + delta:
                                    pulse_width.next = pulse_width - delta
                                else:
                                    pulse_width.next = MIN_WIDTH
                        else:
                            if comparator_in:
                                if pulse_width > MIN_WIDTH - delta:
                                    pulse_width.next = pulse_width + delta
                                else:
                                    pulse_width.next = MIN_WIDTH
                            else:
                                if pulse_width < MAX_WIDTH + delta:
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
    map_base = FPGA_DYNAMICPWM_INLET

    toVHDL(DynamicPwm, clk=clk, reset=reset, dsp_addr=dsp_addr,
                       dsp_data_out=dsp_data_out,
                       dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                       comparator_in=comparator_in, update_in=update_in,
                       pwm_out=pwm_out, map_base=map_base)
