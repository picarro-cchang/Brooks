#!/usr/bin/python
#
# FILE:
#   Pwm1.py
#
# DESCRIPTION:
#   MyHDL for pulse width modulator
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   12-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH, FPGA_REG_MASK
from Host.autogen.interface import FPGA_LASER1_PWM, FPGA_LASER2_PWM, FPGA_LASER3_PWM, FPGA_LASER4_PWM
from Host.autogen.interface import PWM_CS
from Host.autogen.interface import PWM_PULSE_WIDTH
from Host.autogen.interface import PWM_CS_RUN_B, PWM_CS_CONT_B, PWM_CS_PWM_OUT_B

LOW, HIGH = bool(0), bool(1)

def Pwm(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,pwm_out,pwm_inv_out,map_base,
        width=16,main_width=8):
    """Pulse generator with variable mark-space ratio
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    pwm_out             -- Output of PWM
    pwm_inv_out         -- Inverted output of PWM
    map_base            -- Base of FPGA map for this block
    width               -- 1<<width is period of output waveform
    main_width          -- Number of bits for coarse (main) PWM counter

    This block appears as two registers to the DSP, starting at map_base. The registers are:
    PWM_CS              -- Control/status register
    PWM_PULSE_WIDTH     -- PWM pulse width register

    Bits within the PWM_CS register are:
    PWM_CS_RUN          -- 0 stops the PWM from running, 1 allows running
    PWM_CS_CONT         -- 0 places PWM in single-shot mode. i.e., machine runs for one
                            clock cycle each time PWM_CS_RUN goes high. The RUN bit is reset
                            at end of cycle.
                           1 places PWM in continuous mode, which is started by writing 1 to PWM_CS_RUN.
    PWM_CS_PWM_OUT      -- A (read-only) copy of the output of the PWM.

    When PWM_CS_CONT is low, pwm_inv_out = pwm_out (so that the output is disabled). When PWM_CS_CONT
    is high, pwm_inv_out is the inverse of pwm_out.
    """

    dither_width = width-main_width
    mod_dither = 2**dither_width
    mod_main = 2**main_width

    pwm_cs_addr = map_base + PWM_CS
    pwm_pulse_width_addr = map_base + PWM_PULSE_WIDTH

    cs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pulse_width = Signal(intbv(0)[FPGA_REG_WIDTH:])

    main_cntr = Signal(intbv(0)[main_width:])
    dither_cntr = Signal(intbv(0)[dither_width:])
    temp = Signal(intbv(0)[dither_width+1:])
    pwm = Signal(LOW)

    @always_comb
    def comb():
        pwm_out.next = pwm
        pwm_inv_out.next = pwm ^ cs[PWM_CS_CONT_B]
        temp.next = dither_cntr + pulse_width[dither_width:0]

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                cs.next = 0
                pulse_width.next = 0
                main_cntr.next = 0
                dither_cntr.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == pwm_cs_addr:
                        if dsp_wr: cs.next = dsp_data_out
                        dsp_data_in.next = cs
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == pwm_pulse_width_addr:
                        if dsp_wr: pulse_width.next = dsp_data_out
                        dsp_data_in.next = pulse_width
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                if cs[PWM_CS_RUN_B]:
                    if not cs[PWM_CS_CONT_B]:
                        cs.next[PWM_CS_RUN_B] = 0

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
                            cs.next[PWM_CS_PWM_OUT_B] = 1
                            dither_cntr.next = temp - mod_dither
                        else:
                            dither_cntr.next = temp
                    main_cntr.next = (main_cntr + 1) % mod_main
                cs.next[PWM_CS_PWM_OUT_B] = pwm
    return instances()

if __name__ == "__main__":
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr, clk, reset, pwm_out, pwm_inv_out = [Signal(LOW) for i in range(5)]
    map_base = FPGA_PWMA

    toVHDL(Pwm, clk=clk, reset=reset, dsp_addr=dsp_addr, dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                pwm_out=pwm_out, pwm_inv_out=pwm_inv_out, map_base=map_base, width=16, main_width=8)
