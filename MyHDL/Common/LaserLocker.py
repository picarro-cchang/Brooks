#!/usr/bin/python
#
# FILE:
#   LaserLocker.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   02-Jul-2009  sze  Initial version.
#   23-Jul-2009  sze  Use offset binary for tuning offset and a signed fractional
#                      multiplier for applying "ratio multipliers"
#   17-Sep-2009  sze  Added control register to select between simulator and actual WLM
#   18-Sep-2009  sze  Removed sample dark current input (must now use register)
#   18-Mar-2010  sze  Added pid_out for unconditional output of laser locker PID and drive error
#                      input of locker PID from PRBS sequence
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
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
from Host.autogen.interface import LASERLOCKER_CS_SAMPLE_DARK_B, LASERLOCKER_CS_SAMPLE_DARK_W
from Host.autogen.interface import LASERLOCKER_CS_ADC_STROBE_B, LASERLOCKER_CS_ADC_STROBE_W
from Host.autogen.interface import LASERLOCKER_CS_TUNING_OFFSET_SEL_B, LASERLOCKER_CS_TUNING_OFFSET_SEL_W
from Host.autogen.interface import LASERLOCKER_CS_LASER_FREQ_OK_B, LASERLOCKER_CS_LASER_FREQ_OK_W
from Host.autogen.interface import LASERLOCKER_CS_CURRENT_OK_B, LASERLOCKER_CS_CURRENT_OK_W
from Host.autogen.interface import LASERLOCKER_OPTIONS_SIM_ACTUAL_B, LASERLOCKER_OPTIONS_SIM_ACTUAL_W
from Host.autogen.interface import LASERLOCKER_OPTIONS_DIRECT_TUNE_B, LASERLOCKER_OPTIONS_DIRECT_TUNE_W

from Divider import Divider
from SignedMultiplier import SignedMultiplier

LOW, HIGH = bool(0), bool(1)

def SignedFracMultiplier(a_in,b_in,p_out,o_out):
    # We create a 16*16 bit signed fractional multiplier out of the underlying SignedMultiplier block
    #  which is based on the MULT18x18 block in the Xilinx FPGA.
    #
    # a: Multiplier as signed binary fraction between -1<= a <1, of width 16 bits
    # b: Multiplicand as signed binary fraction between -1<= a <1, of width 16 bits
    # p: Product as signed binary fraction between -1<= a <1, of width 16 bits
    #     (i.e., binary point is immediately after the sign bit)
    # Note that we cannot multiply -1 x -1, since this causes an overflow (o bit set)
    
    # Signals for interfacing with SignedMultiplier block
    a_s = Signal(intbv(0,min=-0x20000,max=0x20000))
    b_s = Signal(intbv(0,min=-0x20000,max=0x20000))
    p_s = Signal(intbv(0,min=-0x800000000,max=0x800000000))

    sm = SignedMultiplier(p_s,a_s,b_s)
    
    @always_comb
    def comb():
        a_s.next = concat(a_in,LOW,LOW).signed()
        b_s.next = concat(b_in,LOW,LOW).signed()
        p_out.next = concat(p_s[35],p_s[34:19]) % 65536
        o_out.next = p_s[35] != p_s[34]
        
    return instances()

def LaserLocker(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
                eta1_in,ref1_in,eta2_in,ref2_in,tuning_offset_in,
                acc_en_in,adc_strobe_in,ratio1_out,
                ratio2_out,lock_error_out,fine_current_out,
                tuning_offset_out,pid_out,laser_freq_ok_out,current_ok_out,
                sim_actual_out,map_base):
    """ Laser frequency locking using wavelength monitor

    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    eta1_in             -- Etalon 1 photodiode value
    ref1_in             -- Reference 1 photodiode value
    eta2_in             -- Etalon 2 photodiode value
    ref2_in             -- Reference 2 photodiode value
    tuning_offset_in    -- Tuning offset input. Used if TUNING_OFFSET_SEL
                        --  bit in CS register is 1
    acc_en_in           -- 0 to reset accumulator, 1 for locking
    adc_strobe_in       -- Strobe high for one cycle to indicate photodiode values are valid
                        --  May only be asserted when current_ok_out is high
    ratio1_out          -- Ratio 1 output
    ratio2_out          -- Ratio 2 output
    lock_error_out      -- Lock error output
    fine_current_out    -- Fine current output
    tuning_offset_out   -- Tuning offset used, whether from register or input
    pid_out             -- Output from laser locking PID loop
    laser_freq_ok_out   -- High once absolute value of lock error is within window
    current_ok_out      -- Goes high once fine current has been calculated
    sim_actual_out      -- Low for simulator, high to select actual WLM
    map_base

    Registers:
    LASERLOCKER_CS      -- Control/status register
    LASERLOCKER_OPTIONS -- Options register
    LASERLOCKER_ETA1    -- Etalon 1 reading. Used instead of input when in single step mode.
    LASERLOCKER_REF1    -- Reference 1 reading. Used instead of input when in single step mode.
    LASERLOCKER_ETA2    -- Etalon 2 reading. Used instead of input when in single step mode.
    LASERLOCKER_REF2    -- Reference 2 reading. Used instead of input when in single step mode.
    LASERLOCKER_ETA1_DARK -- Etalon 1 dark reading
    LASERLOCKER_REF1_DARK -- Reference 1 dark reading
    LASERLOCKER_ETA2_DARK -- Etalon 2 dark reading
    LASERLOCKER_REF2_DARK -- Reference 2 dark reading
    LASERLOCKER_ETA1_OFFSET -- Etalon 1 offset to be subtracted before finding ratios
    LASERLOCKER_REF1_OFFSET -- Reference 1 offset to be subtracted before finding ratios
    LASERLOCKER_ETA2_OFFSET -- Etalon 2 offset to be subtracted before finding ratios
    LASERLOCKER_REF2_OFFSET -- Reference 2 offset to be subtracted before finding ratios
    LASERLOCKER_RATIO1  -- Ratio 1
    LASERLOCKER_RATIO2  -- Ratio 2
    LASERLOCKER_RATIO1_CENTER   -- Center of ellipse for ratio 1
    LASERLOCKER_RATIO1_MULTIPLIER -- Multiplier for ratio 1 in locker
    LASERLOCKER_RATIO2_CENTER   -- Center of ellipse for ratio 2
    LASERLOCKER_RATIO2_MULTIPLIER -- Multiplier for ratio 2 in locker
    LASERLOCKER_TUNING_OFFSET   -- Offset to add to error (used when TUNING_OFFSET_SEL
                                --  bit in CS register is 0), specified as offset binary so that
                                --  32768 represents zero offset
    LASERLOCKER_LOCK_ERROR      -- Loop lock error
    LASERLOCKER_WM_LOCK_WINDOW  -- Defines when laser frequency is in range
    LASERLOCKER_WM_INT_GAIN     -- Integral gain for wavelength locking
    LASERLOCKER_WM_PROP_GAIN    -- Proportional gain for wavelength locking
    LASERLOCKER_WM_DERIV_GAIN   -- Derivative gain for wavelength locking
    LASERLOCKER_FINE_CURRENT    -- Fine laser current
    LASERLOCKER_CYCLE_COUNTER   -- Cycle counter

    Fields in LASERLOCKER_CS:
    LASERLOCKER_CS_RUN          -- 0 stops simulator from running, 1 allows running
    LASERLOCKER_CS_CONT         -- 0 for single-shot mode, 1 for continuous mode
    LASERLOCKER_CS_PRBS         -- Enable generation of PRBS for loop characterization
    LASERLOCKER_CS_ACC_EN       -- Enables fine current accumulator
    LASERLOCKER_CS_SAMPLE_DARK  -- Set high to sample dark current
    LASERLOCKER_CS_ADC_STROBE   -- Set high to read photocurrent inputs and start computation
    LASERLOCKER_CS_TUNING_OFFSET_SEL -- Selects register if 0, input if 1
    LASERLOCKER_CS_LASER_FREQ_OK -- Set high to indicate laser frequency is in range
    LASERLOCKER_CS_CURRENT_OK    -- Indicates that laser current has been computed

    Fields in LASERLOCKER_OPTIONS:
    LASERLOCKER_OPTIONS_SIM_ACTUAL
    """
    laserlocker_cs_addr = map_base + LASERLOCKER_CS
    laserlocker_options_addr = map_base + LASERLOCKER_OPTIONS
    laserlocker_eta1_addr = map_base + LASERLOCKER_ETA1
    laserlocker_ref1_addr = map_base + LASERLOCKER_REF1
    laserlocker_eta2_addr = map_base + LASERLOCKER_ETA2
    laserlocker_ref2_addr = map_base + LASERLOCKER_REF2
    laserlocker_eta1_dark_addr = map_base + LASERLOCKER_ETA1_DARK
    laserlocker_ref1_dark_addr = map_base + LASERLOCKER_REF1_DARK
    laserlocker_eta2_dark_addr = map_base + LASERLOCKER_ETA2_DARK
    laserlocker_ref2_dark_addr = map_base + LASERLOCKER_REF2_DARK
    laserlocker_eta1_offset_addr = map_base + LASERLOCKER_ETA1_OFFSET
    laserlocker_ref1_offset_addr = map_base + LASERLOCKER_REF1_OFFSET
    laserlocker_eta2_offset_addr = map_base + LASERLOCKER_ETA2_OFFSET
    laserlocker_ref2_offset_addr = map_base + LASERLOCKER_REF2_OFFSET
    laserlocker_ratio1_addr = map_base + LASERLOCKER_RATIO1
    laserlocker_ratio2_addr = map_base + LASERLOCKER_RATIO2
    laserlocker_ratio1_center_addr = map_base + LASERLOCKER_RATIO1_CENTER
    laserlocker_ratio1_multiplier_addr = map_base + LASERLOCKER_RATIO1_MULTIPLIER
    laserlocker_ratio2_center_addr = map_base + LASERLOCKER_RATIO2_CENTER
    laserlocker_ratio2_multiplier_addr = map_base + LASERLOCKER_RATIO2_MULTIPLIER
    laserlocker_tuning_offset_addr = map_base + LASERLOCKER_TUNING_OFFSET
    laserlocker_lock_error_addr = map_base + LASERLOCKER_LOCK_ERROR
    laserlocker_wm_lock_window_addr = map_base + LASERLOCKER_WM_LOCK_WINDOW
    laserlocker_wm_int_gain_addr = map_base + LASERLOCKER_WM_INT_GAIN
    laserlocker_wm_prop_gain_addr = map_base + LASERLOCKER_WM_PROP_GAIN
    laserlocker_wm_deriv_gain_addr = map_base + LASERLOCKER_WM_DERIV_GAIN
    laserlocker_fine_current_addr = map_base + LASERLOCKER_FINE_CURRENT
    laserlocker_cycle_counter_addr = map_base + LASERLOCKER_CYCLE_COUNTER
    cs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    options = Signal(intbv(0)[2:])
    eta1 = Signal(intbv(0)[WLM_ADC_WIDTH:])
    ref1 = Signal(intbv(0)[WLM_ADC_WIDTH:])
    eta2 = Signal(intbv(0)[WLM_ADC_WIDTH:])
    ref2 = Signal(intbv(0)[WLM_ADC_WIDTH:])
    eta1_dark = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_dark = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_dark = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_dark = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta1_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio1_center = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio1_multiplier = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio2_center = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio2_multiplier = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuning_offset = Signal(intbv(0x8000)[FPGA_REG_WIDTH:])
    lock_error = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wm_lock_window = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wm_int_gain = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wm_prop_gain = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wm_deriv_gain = Signal(intbv(0)[FPGA_REG_WIDTH:])
    fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    cycle_counter = Signal(intbv(0)[FPGA_REG_WIDTH:])

    FPGA_REG_MAXVAL = 1<<FPGA_REG_WIDTH
    M2 = FPGA_REG_MAXVAL//2
    
    # Signals interfacing to divider
    div_num, div_den, div_quot = [Signal(intbv(0)[FPGA_REG_WIDTH:]) for i in range(3)]
    div_rfd, div_ce = [Signal(LOW) for i in range(2)]

    # Signals to the signed fractional multiplier
    mult_a, mult_b, mult_p = [Signal(intbv(0)[FPGA_REG_WIDTH:]) for i in range(3)]
    mult_o = Signal(LOW)

    prev_lock_error = Signal(intbv(0)[FPGA_REG_WIDTH:])
    prev_lock_error_deriv = Signal(intbv(0)[FPGA_REG_WIDTH:])
    deriv = Signal(intbv(0)[FPGA_REG_WIDTH:])
    deriv2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    prbs_reg = Signal(intbv(0)[8:]) # Use for ALM sequence
    prbs_augment = Signal(LOW)
    awaiting_strobe = Signal(HIGH)

    DIV_LATENCY  = 19
    MULT_LATENCY = 2
    MAX_CYCLES = 2*DIV_LATENCY + 1 + 4*MULT_LATENCY + 4

    @always_comb
    def comb():
        tuning_offset_out.next = tuning_offset
        sim_actual_out.next = options[LASERLOCKER_OPTIONS_SIM_ACTUAL_B]
        
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                cs.next = 0
                options.next = 0
                eta1.next = 0
                ref1.next = 0
                eta2.next = 0
                ref2.next = 0
                eta1_dark.next = 0
                ref1_dark.next = 0
                eta2_dark.next = 0
                ref2_dark.next = 0
                eta1_offset.next = 0
                ref1_offset.next = 0
                eta2_offset.next = 0
                ref2_offset.next = 0
                ratio1.next = 0
                ratio2.next = 0
                ratio1_center.next = 0
                ratio1_multiplier.next = 0
                ratio2_center.next = 0
                ratio2_multiplier.next = 0
                tuning_offset.next = 0x8000
                lock_error.next = 0
                wm_lock_window.next = 0
                wm_int_gain.next = 0
                wm_prop_gain.next = 0
                wm_deriv_gain.next = 0
                fine_current.next = 0
                cycle_counter.next = MAX_CYCLES
                #
                div_ce.next = 0
                div_num.next = 0
                div_den.next = 0
                prev_lock_error.next = 0
                prev_lock_error_deriv.next = 0
                deriv.next = 0
                deriv2.next = 0
                laser_freq_ok_out.next = LOW
                current_ok_out.next = LOW
                prbs_reg.next = 1
                prbs_augment.next = 0
                awaiting_strobe.next = HIGH
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_cs_addr: # rw
                        if dsp_wr: cs.next = dsp_data_out
                        dsp_data_in.next = cs
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_options_addr: # rw
                        if dsp_wr: options.next = dsp_data_out
                        dsp_data_in.next = options
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_eta1_addr: # rw
                        if dsp_wr: eta1.next = dsp_data_out
                        dsp_data_in.next = eta1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ref1_addr: # rw
                        if dsp_wr: ref1.next = dsp_data_out
                        dsp_data_in.next = ref1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_eta2_addr: # rw
                        if dsp_wr: eta2.next = dsp_data_out
                        dsp_data_in.next = eta2
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ref2_addr: # rw
                        if dsp_wr: ref2.next = dsp_data_out
                        dsp_data_in.next = ref2
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_eta1_dark_addr: # r
                        dsp_data_in.next = eta1_dark
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ref1_dark_addr: # r
                        dsp_data_in.next = ref1_dark
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_eta2_dark_addr: # r
                        dsp_data_in.next = eta2_dark
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ref2_dark_addr: # r
                        dsp_data_in.next = ref2_dark
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_eta1_offset_addr: # rw
                        if dsp_wr: eta1_offset.next = dsp_data_out
                        dsp_data_in.next = eta1_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ref1_offset_addr: # rw
                        if dsp_wr: ref1_offset.next = dsp_data_out
                        dsp_data_in.next = ref1_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_eta2_offset_addr: # rw
                        if dsp_wr: eta2_offset.next = dsp_data_out
                        dsp_data_in.next = eta2_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ref2_offset_addr: # rw
                        if dsp_wr: ref2_offset.next = dsp_data_out
                        dsp_data_in.next = ref2_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ratio1_addr: # r
                        dsp_data_in.next = ratio1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ratio2_addr: # r
                        dsp_data_in.next = ratio2
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ratio1_center_addr: # rw
                        if dsp_wr: ratio1_center.next = dsp_data_out
                        dsp_data_in.next = ratio1_center
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ratio1_multiplier_addr: # rw
                        if dsp_wr: ratio1_multiplier.next = dsp_data_out
                        dsp_data_in.next = ratio1_multiplier
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ratio2_center_addr: # rw
                        if dsp_wr: ratio2_center.next = dsp_data_out
                        dsp_data_in.next = ratio2_center
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_ratio2_multiplier_addr: # rw
                        if dsp_wr: ratio2_multiplier.next = dsp_data_out
                        dsp_data_in.next = ratio2_multiplier
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_tuning_offset_addr: # rw
                        if dsp_wr: tuning_offset.next = dsp_data_out
                        dsp_data_in.next = tuning_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_lock_error_addr: # r
                        dsp_data_in.next = lock_error
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_wm_lock_window_addr: # rw
                        if dsp_wr: wm_lock_window.next = dsp_data_out
                        dsp_data_in.next = wm_lock_window
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_wm_int_gain_addr: # rw
                        if dsp_wr: wm_int_gain.next = dsp_data_out
                        dsp_data_in.next = wm_int_gain
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_wm_prop_gain_addr: # rw
                        if dsp_wr: wm_prop_gain.next = dsp_data_out
                        dsp_data_in.next = wm_prop_gain
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_wm_deriv_gain_addr: # rw
                        if dsp_wr: wm_deriv_gain.next = dsp_data_out
                        dsp_data_in.next = wm_deriv_gain
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_fine_current_addr: # r
                        dsp_data_in.next = fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == laserlocker_cycle_counter_addr: # r
                        dsp_data_in.next = cycle_counter
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                if cs[LASERLOCKER_CS_RUN_B]:
                    # Select either the input signal or the register
                    #  depending on whether we are single-stepping or running continuously
                    if cs[LASERLOCKER_CS_CONT_B]:
                        eta1.next = eta1_in
                        ref1.next = ref1_in
                        eta2.next = eta2_in
                        ref2.next = ref2_in
                        cs.next[LASERLOCKER_CS_ACC_EN_B] = acc_en_in
                        cs.next[LASERLOCKER_CS_ADC_STROBE_B] = adc_strobe_in

                    # If the tuning offset select bit is 1, use the input
                    #  rather than the register
                    if cs[LASERLOCKER_CS_TUNING_OFFSET_SEL_B]:
                        tuning_offset.next = tuning_offset_in

                    # Sample the dark readings if this is requested
                    if cs[LASERLOCKER_CS_SAMPLE_DARK_B]:
                        eta1_dark.next = eta1
                        ref1_dark.next = ref1
                        eta2_dark.next = eta2
                        ref2_dark.next = ref2

                    # Share the divider between the two etalon channels
                    div_ce.next = (cycle_counter == 1) or (cycle_counter == DIV_LATENCY+1)
                    if cycle_counter == 0:
                        div_num.next = eta1 - eta1_offset
                        div_den.next = ref1 - ref1_offset
                    elif cycle_counter == DIV_LATENCY:
                        div_num.next = eta2 - eta2_offset
                        div_den.next = ref2 - ref2_offset
                    # Load the multiplier inputs
                    elif cycle_counter == DIV_LATENCY+1:
                        # assert div_rfd == HIGH
                        ratio1.next = div_quot
                        ratio1_out.next = div_quot
                    elif cycle_counter == DIV_LATENCY+2:
                        mult_a.next = (ratio1 - ratio1_center) % FPGA_REG_MAXVAL
                        mult_b.next = ratio1_multiplier
                    elif cycle_counter == DIV_LATENCY+2+MULT_LATENCY:
                        lock_error.next = (lock_error + mult_p) % FPGA_REG_MAXVAL
                    elif cycle_counter == 2*DIV_LATENCY+1:
                        # assert div_rfd == HIGH
                        ratio2.next = div_quot
                        ratio2_out.next = div_quot
                    elif cycle_counter == 2*DIV_LATENCY+2:
                        mult_a.next = (ratio2 - ratio2_center) % FPGA_REG_MAXVAL
                        mult_b.next = ratio2_multiplier
                    elif cycle_counter == 2*DIV_LATENCY + 2 + MULT_LATENCY:
                        lock_error.next = (lock_error + mult_p) % FPGA_REG_MAXVAL
                    elif cycle_counter == 2*DIV_LATENCY + 2 + MULT_LATENCY + 1:
                        lock_error_out.next = lock_error
                        if cs[LASERLOCKER_CS_PRBS_B]:
                            # N.B. lock_error is a SIGNED quantity
                            if prbs_reg[0]:
                                lock_error.next = 0x0100
                            else:
                                lock_error.next = 0xFF00
                    elif cycle_counter == 2*DIV_LATENCY + 2 + MULT_LATENCY + 2:
                        if lock_error.signed() >= 0:
                            laser_freq_ok_out.next = (lock_error <= wm_lock_window)
                        else:
                            laser_freq_ok_out.next = (-lock_error.signed()) <= wm_lock_window

                        mult_a.next = lock_error
                        mult_b.next = wm_int_gain
                        deriv.next = (lock_error - prev_lock_error) % FPGA_REG_MAXVAL
                        prev_lock_error.next = lock_error
                    elif cycle_counter == 2*DIV_LATENCY + 1 + 2*MULT_LATENCY + 2:
                        mult_a.next = deriv
                        mult_b.next = wm_prop_gain
                        deriv2.next = (deriv - prev_lock_error_deriv) % FPGA_REG_MAXVAL
                        prev_lock_error_deriv.next = deriv
                        fine_current.next = (fine_current + mult_p) % FPGA_REG_MAXVAL
                        #t = fine_current + mult_p.signed()
                        #if t<0: fine_current.next = 0
                        #elif t>=fine_current.max: fine_current.next = 65535
                        #else: fine_current.next = t
                    elif cycle_counter == 2*DIV_LATENCY + 1 + 3*MULT_LATENCY + 2:
                        mult_a.next = deriv2
                        mult_b.next = wm_deriv_gain
                        fine_current.next = (fine_current + mult_p) % FPGA_REG_MAXVAL
                        #t = fine_current + mult_p.signed()
                        #if t<0: fine_current.next = 0
                        #elif t>=fine_current.max: fine_current.next = 65535
                        #else: fine_current.next = t
                    elif cycle_counter == 2*DIV_LATENCY + 1 + 4*MULT_LATENCY + 2:
                        fine_current.next = (fine_current + mult_p) % FPGA_REG_MAXVAL
                        #t = fine_current + mult_p.signed()
                        #if t<0: fine_current.next = 0
                        #elif t>=fine_current.max: fine_current.next = 65535
                        #else: fine_current.next = t
                    elif cycle_counter == 2*DIV_LATENCY + 1 + 4*MULT_LATENCY + 3:
                        pid_out.next = fine_current
                        if cs[LASERLOCKER_CS_PRBS_B]:
                            if prbs_reg[0]:
                                fine_current_out.next = 0x8100
                            else:
                                fine_current_out.next = 0x7F00
                            temp = prbs_reg == 0xEE and not prbs_augment
                            prbs_augment.next = temp
                            if not temp:
                                if prbs_reg[7]:
                                    prbs_reg.next = concat(prbs_reg[7:]^0x34,intbv(1)[1:])
                                else:
                                    prbs_reg.next = concat(prbs_reg[7:],intbv(0)[1:])
                        else:
                            fine_current_out.next = fine_current
                            prbs_reg.next = 1
                            prbs_augment.next = 0

                    # Update cycle_counter to indicate location in algorithm
                    if cycle_counter < MAX_CYCLES:
                        cycle_counter.next = cycle_counter + 1
                    else:
                        current_ok_out.next = 1
                        # Allow a new cycle if cycle_counter is at MAX_CYCLES
                        if cs[LASERLOCKER_CS_ADC_STROBE_B]:
                            if awaiting_strobe:
                                awaiting_strobe.next = LOW
                                lock_error_out.next = lock_error
                                cycle_counter.next = 0
                                current_ok_out.next = 0
                                # Perform a shift with sign extension
                                if tuning_offset[15]:
                                    lock_error.next = concat(LOW,LOW,LOW,LOW,tuning_offset[15:3])
                                else:
                                    lock_error.next = concat(HIGH,HIGH,HIGH,HIGH,tuning_offset[15:3])
                        else:
                            awaiting_strobe.next = HIGH

                    if not cs[LASERLOCKER_CS_ACC_EN_B]:
                        fine_current.next = 0x8000
                        fine_current_out.next = 0x8000
                        
                    if options[LASERLOCKER_OPTIONS_DIRECT_TUNE_B]:
                        fine_current_out.next = tuning_offset

                    # Reset the run bit if continuous mode is not selected
                    # Ensure this is within clause that cs[LASERLOCKER_CS_RUN_B] == 1
                    if not cs[LASERLOCKER_CS_CONT_B]:
                        cs.next[LASERLOCKER_CS_RUN_B] = 0

                    cs.next[LASERLOCKER_CS_CURRENT_OK_B] = current_ok_out
                    cs.next[LASERLOCKER_CS_LASER_FREQ_OK_B] = laser_freq_ok_out

    divider = Divider(clk=clk, reset=reset, N_in=div_num, D_in=div_den, Q_out=div_quot,
                      rfd_out=div_rfd, ce_in=div_ce, width=FPGA_REG_WIDTH)

    signedMultiplier = SignedFracMultiplier(a_in=mult_a, b_in=mult_b, p_out=mult_p, o_out=mult_o)

    return instances()

if __name__ == "__main__":
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

    toVHDL(LaserLocker, clk=clk, reset=reset, dsp_addr=dsp_addr,
                        dsp_data_out=dsp_data_out,
                        dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                        eta1_in=eta1_in, ref1_in=ref1_in,
                        eta2_in=eta2_in, ref2_in=ref2_in,
                        tuning_offset_in=tuning_offset_in,
                        acc_en_in=acc_en_in,
                        adc_strobe_in=adc_strobe_in,
                        ratio1_out=ratio1_out, ratio2_out=ratio2_out,
                        lock_error_out=lock_error_out,
                        fine_current_out=fine_current_out,
                        tuning_offset_out=tuning_offset_out,
                        pid_out=pid_out,
                        laser_freq_ok_out=laser_freq_ok_out,
                        current_ok_out=current_ok_out,
                        sim_actual_out=sim_actual_out, map_base=map_base)
