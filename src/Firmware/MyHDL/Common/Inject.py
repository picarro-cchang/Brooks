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
#   24-Jul-2009  sze  Add selected laser outputs for use with WLM simulator.
#   16-Sep-2009  sze  Enable laser shutdown and enable SOA shutdown control bits cause the selected laser
#                      or SOA to be affected by the shutdown inputs in automatic mode. If the enable bit
#                      is reset, the selected laser or SOA remains on even when the shutdown input is asserted.
#   18-Sep-2009  sze  Handle 2 input CrystaLatch optical switch
#   05-Oct-2009  sze  In automatic mode, the selected fine current register is updated with laser_fine_current_in
#   29-Apr-2010  sze  Handle 4 input CrystaLatch optical switch
#   14-Feb-2011  sze  Allow use of two 2-input CrystalLatch optical switches
#   17-Jun-2011  sze  Remove support for two 2-input CrystalLatch optical switches because of damage to 4-way switch
#                      if the system is not properly configured
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_INJECT

from Host.autogen.interface import INJECT_CONTROL, INJECT_CONTROL2
from Host.autogen.interface import INJECT_LASER1_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER2_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER3_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER4_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER1_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER2_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER3_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER4_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER1_FINE_CURRENT_RANGE
from Host.autogen.interface import INJECT_LASER2_FINE_CURRENT_RANGE
from Host.autogen.interface import INJECT_LASER3_FINE_CURRENT_RANGE
from Host.autogen.interface import INJECT_LASER4_FINE_CURRENT_RANGE

from Host.autogen.interface import INJECT_CONTROL_MODE_B, INJECT_CONTROL_MODE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_LASER_CURRENT_ENABLE_B, INJECT_CONTROL_LASER_CURRENT_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_LASER_ENABLE_B, INJECT_CONTROL_MANUAL_LASER_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_SOA_ENABLE_B, INJECT_CONTROL_MANUAL_SOA_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_OPTICAL_SWITCH_SELECT_B, INJECT_CONTROL_OPTICAL_SWITCH_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_SOA_PRESENT_B, INJECT_CONTROL_SOA_PRESENT_W
from Host.autogen.interface import INJECT_CONTROL2_FIBER_AMP_PRESENT_B, INJECT_CONTROL2_FIBER_AMP_PRESENT_W
from Host.autogen.interface import INJECT_CONTROL2_EXTINGUISH_DESELECTED_B, INJECT_CONTROL2_EXTINGUISH_DESELECTED_W

from MyHDL.Common.LaserDac import LaserDac

OptSwitchState = enum("IDLE","PULSING_1","SELECTED_1","PULSING_2","SELECTED_2")
SwitchPulserState = enum("START","PULSING","WAITING")

LOW, HIGH = bool(0), bool(1)
def Inject(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
           laser_dac_clk_in,strobe_in,laser_fine_current_in,
           laser_shutdown_in,soa_shutdown_in,fiber_amp_pwm_in,
           laser1_dac_sync_out,laser2_dac_sync_out,laser3_dac_sync_out,
           laser4_dac_sync_out,laser1_dac_din_out,laser2_dac_din_out,
           laser3_dac_din_out,laser4_dac_din_out,laser1_disable_out,
           laser2_disable_out,laser3_disable_out,laser4_disable_out,
           laser1_shutdown_out,laser2_shutdown_out,laser3_shutdown_out,
           laser4_shutdown_out,soa_shutdown_out,sel_laser_out,
           sel_coarse_current_out,sel_fine_current_out,
           optical_switch1_out,optical_switch2_out,optical_switch4_out,
           map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    laser_dac_clk_in    -- 5MHz clock to drive laser current DAC
    strobe_in           -- 100kHz strobe for DACs. N.B. This strobe may remain high for multiple clocks
    laser_fine_current_in -- Sets fine current for selected laser in automatic mode
    laser_shutdown_in   -- Shuts down selected laser in automatic mode
    soa_shutdown_in     -- Shuts down SOA in automatic mode
    fiber_amp_pwm_in    -- PWM signal for fiber amplifier TEC
    laser1_dac_sync_out  -- Synchronization signal for laser 1 current DAC
    laser2_dac_sync_out  -- Synchronization signal for laser 2 current DAC
    laser3_dac_sync_out  -- Synchronization signal for laser 3 current DAC
    laser4_dac_sync_out  -- Synchronization signal for laser 4 current DAC
    laser1_dac_din_out  -- Serial data in for laser 1 current DAC
    laser2_dac_din_out  -- Serial data in for laser 2 current DAC
    laser3_dac_din_out  -- Serial data in for laser 3 current DAC
    laser4_dac_din_out  -- Serial data in for laser 4 current DAC
    laser1_disable_out  -- Disable laser 1 current source
    laser2_disable_out  -- Disable laser 2 current source
    laser3_disable_out  -- Disable laser 3 current source
    laser4_disable_out  -- Disable laser 4 current source
    laser1_shutdown_out  -- Short across laser 1
    laser2_shutdown_out  -- Short across laser 2
    laser3_shutdown_out  -- Short across laser 3
    laser4_shutdown_out  -- Short across laser 4
    soa_shutdown_out     -- Short across SOA
    sel_laser_out
    sel_coarse_current_out
    sel_fine_current_out

    Depending on the state of optical_switch_select in the control register, the
    following three outputs drive either a four-way optical switch or a two-way
    optical switch.

    optical_switch1_out  -- For 2 way switch, goes high for 1ms when laser 1 or 3 selected. Used for laser select for 4 way switch.
    optical_switch2_out  -- For 2 way switch, goes high for 1ms when laser 2 or 4 selected. Used for laser select for 4 way switch.
    optical_switch4_out  -- For 4-way switch, goes low for 1ms when any laser is selected.
    If INJECT_CONTROL2_FIBER_AMP_PRESENT is asserted, optical_switch4_out is connected to
    fiber_amp_pwm_in, since this signal is also used for the PWM of the fiber amplifier

    map_base             -- Base of FPGA map for this block

    Registers:
    INJECT_CONTROL        -- Control register
    LASER1_COARSE_CURRENT -- Laser 1 coarse current DAC setting
    LASER2_COARSE_CURRENT -- Laser 2 coarse current DAC setting
    LASER3_COARSE_CURRENT -- Laser 3 coarse current DAC setting
    LASER4_COARSE_CURRENT -- Laser 4 coarse current DAC setting
    LASER1_FINE_CURRENT   -- Laser 1 manual fine current DAC setting
    LASER2_FINE_CURRENT   -- Laser 2 manual fine current DAC setting
    LASER3_FINE_CURRENT   -- Laser 3 manual fine current DAC setting
    LASER4_FINE_CURRENT   -- Laser 4 manual fine current DAC setting
    LASER1_FINE_CURRENT_RANGE -- When set to v, limits fine current range of laser 1 from 32768-v to 32768+v
    LASER2_FINE_CURRENT_RANGE -- When set to v, limits fine current range of laser 2 from 32768-v to 32768+v
    LASER3_FINE_CURRENT_RANGE -- When set to v, limits fine current range of laser 3 from 32768-v to 32768+v
    LASER4_FINE_CURRENT_RANGE -- When set to v, limits fine current range of laser 4 from 32768-v to 32768+v

    Fields in INJECT_CONTROL:
    INJECT_CONTROL_MODE         -- Selects manual (0) or automatic (1) mode
    INJECT_CONTROL_LASER_SELECT -- Selects laser for automatic control 00 -> 11
    INJECT_CONTROL_LASER_CURRENT_ENABLE -- 4 bits controlling laser current regulators
    INJECT_CONTROL_MANUAL_LASER_ENABLE  -- 4 bits controlling laser shorting transistors in manual mode
    INJECT_CONTROL_MANUAL_SOA_ENABLE    -- Controls SOA current in manual mode
    INJECT_CONTROL_LASER_SHUTDOWN_ENABLE -- enables laser shutdown in automatic mode
    INJECT_CONTROL_SOA_SHUTDOWN_ENABLE   -- enables SOA shutdown in automatic mode.
    INJECT_CONTROL_OPTICAL_SWITCH_SELECT -- 0 for 2-way switch, 1 for 4-way switch
    INJECT_CONTROL_MANUAL_SOA_PRESENT -- if False, SOA is always shorted

    Note: If MODE is automatic, only the SOA and the selected laser are in automatic mode,
           the other lasers remain in manual mode.

    INJECT_CONTROL2        -- Second control register
    Fields in INJECT_CONTROL2:
    INJECT_CONTROL2_FIBER_AMP_PRESENT -- Indicates if fiber amplifier is present (1) or absent (0)
                                      -- Connects laser 4 PWM to SW4 output

    """
    inject_control_addr = map_base + INJECT_CONTROL
    inject_control2_addr = map_base + INJECT_CONTROL2
    inject_laser1_coarse_current_addr = map_base + INJECT_LASER1_COARSE_CURRENT
    inject_laser2_coarse_current_addr = map_base + INJECT_LASER2_COARSE_CURRENT
    inject_laser3_coarse_current_addr = map_base + INJECT_LASER3_COARSE_CURRENT
    inject_laser4_coarse_current_addr = map_base + INJECT_LASER4_COARSE_CURRENT
    inject_laser1_fine_current_addr = map_base + INJECT_LASER1_FINE_CURRENT
    inject_laser2_fine_current_addr = map_base + INJECT_LASER2_FINE_CURRENT
    inject_laser3_fine_current_addr = map_base + INJECT_LASER3_FINE_CURRENT
    inject_laser4_fine_current_addr = map_base + INJECT_LASER4_FINE_CURRENT
    inject_laser1_fine_current_range_addr = map_base + INJECT_LASER1_FINE_CURRENT_RANGE
    inject_laser2_fine_current_range_addr = map_base + INJECT_LASER2_FINE_CURRENT_RANGE
    inject_laser3_fine_current_range_addr = map_base + INJECT_LASER3_FINE_CURRENT_RANGE
    inject_laser4_fine_current_range_addr = map_base + INJECT_LASER4_FINE_CURRENT_RANGE
    control = Signal(intbv(0)[FPGA_REG_WIDTH:])
    control2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser1_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser1_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser1_fine_current_range = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_fine_current_range = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_fine_current_range = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_fine_current_range = Signal(intbv(0)[FPGA_REG_WIDTH:])

    extinguish_deselected = Signal(LOW)
    mode = Signal(LOW)
    sel  = Signal(intbv(0)[2:])
    laser_current_en = Signal(intbv(0)[4:])
    manual_laser_en = Signal(intbv(0)[4:])
    manual_soa_en = Signal(LOW)
    laser_shutdown_en = Signal(LOW)
    soa_shutdown_en = Signal(LOW)
    soa_present = Signal(LOW)
    laser1_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser1_coarse = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_coarse = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_coarse = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_coarse = Signal(intbv(0)[FPGA_REG_WIDTH:])
    strobe_prev = Signal(LOW)
    dac_strobe = Signal(LOW)
    sw1_2way = Signal(LOW)
    sw2_2way = Signal(LOW)
    sw4_4way = Signal(LOW)
    last_sel = Signal(intbv(0)[2:])

    OPTICAL_SWITCH_WIDTH = 100 # Units of 10us
    optical_switch_counter = Signal(intbv(0,min=0,max=OPTICAL_SWITCH_WIDTH))
    optSwitchState = Signal(OptSwitchState.IDLE)
    switchPulserState = Signal(SwitchPulserState.START)
    pulse_counter = Signal(intbv(0,min=0,max=OPTICAL_SWITCH_WIDTH))

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                control.next = 0
                control2.next = 0
                laser1_coarse_current.next = 0
                laser2_coarse_current.next = 0
                laser3_coarse_current.next = 0
                laser4_coarse_current.next = 0
                laser1_fine_current.next = 0x8000
                laser2_fine_current.next = 0x8000
                laser3_fine_current.next = 0x8000
                laser4_fine_current.next = 0x8000
                laser1_fine_current_range.next = 0x7FFF
                laser2_fine_current_range.next = 0x7FFF
                laser3_fine_current_range.next = 0x7FFF
                laser4_fine_current_range.next = 0x7FFF
                strobe_prev.next = strobe_in
                dac_strobe.next = LOW
                optical_switch_counter.next = 0
                pulse_counter.next = 0
                optSwitchState.next = OptSwitchState.IDLE
                switchPulserState.next = SwitchPulserState.START
                sw4_4way.next = 1
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_control_addr: # rw
                        if dsp_wr: control.next = dsp_data_out
                        dsp_data_in.next = control
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_control2_addr: # rw
                        if dsp_wr: control2.next = dsp_data_out
                        dsp_data_in.next = control2
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser1_coarse_current_addr: # rw
                        if dsp_wr: laser1_coarse_current.next = dsp_data_out
                        dsp_data_in.next = laser1_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser2_coarse_current_addr: # rw
                        if dsp_wr: laser2_coarse_current.next = dsp_data_out
                        dsp_data_in.next = laser2_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser3_coarse_current_addr: # rw
                        if dsp_wr: laser3_coarse_current.next = dsp_data_out
                        dsp_data_in.next = laser3_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser4_coarse_current_addr: # rw
                        if dsp_wr: laser4_coarse_current.next = dsp_data_out
                        dsp_data_in.next = laser4_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser1_fine_current_addr: # rw
                        if dsp_wr: laser1_fine_current.next = dsp_data_out
                        dsp_data_in.next = laser1_fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser2_fine_current_addr: # rw
                        if dsp_wr: laser2_fine_current.next = dsp_data_out
                        dsp_data_in.next = laser2_fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser3_fine_current_addr: # rw
                        if dsp_wr: laser3_fine_current.next = dsp_data_out
                        dsp_data_in.next = laser3_fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser4_fine_current_addr: # rw
                        if dsp_wr: laser4_fine_current.next = dsp_data_out
                        dsp_data_in.next = laser4_fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser1_fine_current_range_addr: # rw
                        if dsp_wr: laser1_fine_current_range.next = dsp_data_out
                        dsp_data_in.next = laser1_fine_current_range
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser2_fine_current_range_addr: # rw
                        if dsp_wr: laser2_fine_current_range.next = dsp_data_out
                        dsp_data_in.next = laser2_fine_current_range
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser3_fine_current_range_addr: # rw
                        if dsp_wr: laser3_fine_current_range.next = dsp_data_out
                        dsp_data_in.next = laser3_fine_current_range
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == inject_laser4_fine_current_range_addr: # rw
                        if dsp_wr: laser4_fine_current_range.next = dsp_data_out
                        dsp_data_in.next = laser4_fine_current_range
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                # Produce a single clock width pulse for dac_strobe whenever strobe_in goes high
                dac_strobe.next = strobe_in and not strobe_prev
                strobe_prev.next = strobe_in
                # Store laser_fine_current input to register of selected laser in automatic mode
                if mode:
                    if sel==0:
                        if laser_fine_current_in > 32768 + laser1_fine_current_range:
                            laser1_fine.next = 32768 + laser1_fine_current_range
                        elif laser_fine_current_in < 32768 - laser1_fine_current_range:
                            laser1_fine.next = 32768 - laser1_fine_current_range
                        else:
                            laser1_fine.next = laser_fine_current_in
                        if extinguish_deselected:
                            laser2_fine.next = 0
                            laser3_fine.next = 0
                            laser4_fine.next = 0
                    elif sel==1:
                        if laser_fine_current_in > 32768 + laser2_fine_current_range:
                            laser2_fine.next = 32768 + laser2_fine_current_range
                        elif laser_fine_current_in < 32768 - laser2_fine_current_range:
                            laser2_fine.next = 32768 - laser2_fine_current_range
                        else:
                            laser2_fine.next = laser_fine_current_in
                        if extinguish_deselected:
                            laser1_fine.next = 0
                            laser3_fine.next = 0
                            laser4_fine.next = 0
                    elif sel==2:
                        if laser_fine_current_in > 32768 + laser3_fine_current_range:
                            laser3_fine.next = 32768 + laser3_fine_current_range
                        elif laser_fine_current_in < 32768 - laser3_fine_current_range:
                            laser3_fine.next = 32768 - laser3_fine_current_range
                        else:
                            laser3_fine.next = laser_fine_current_in
                        if extinguish_deselected:
                            laser1_fine.next = 0
                            laser2_fine.next = 0
                            laser4_fine.next = 0
                    else:
                        if laser_fine_current_in > 32768 + laser4_fine_current_range:
                            laser4_fine.next = 32768 + laser4_fine_current_range
                        elif laser_fine_current_in < 32768 - laser4_fine_current_range:
                            laser4_fine.next = 32768 - laser4_fine_current_range
                        else:
                            laser4_fine.next = laser_fine_current_in
                        if extinguish_deselected:
                            laser1_fine.next = 0
                            laser2_fine.next = 0
                            laser3_fine.next = 0
                else:
                    laser1_fine.next = laser1_fine_current
                    laser2_fine.next = laser2_fine_current
                    laser3_fine.next = laser3_fine_current
                    laser4_fine.next = laser4_fine_current

                # State machine for generating 2-way optical switch signals
                if optSwitchState == OptSwitchState.IDLE:
                    sw1_2way.next = 0
                    sw2_2way.next = 0
                    if sel[0] == 0:
                        optSwitchState.next = OptSwitchState.PULSING_1
                        optical_switch_counter.next = 0
                    else:
                        optSwitchState.next = OptSwitchState.PULSING_2
                        optical_switch_counter.next = 0
                elif optSwitchState == OptSwitchState.PULSING_1:
                    sw1_2way.next = 1
                    sw2_2way.next = 0
                    if dac_strobe: # This goes high for one clock cycle every 10us
                        if optical_switch_counter >= OPTICAL_SWITCH_WIDTH-1:
                            optSwitchState.next = OptSwitchState.SELECTED_1
                            optical_switch_counter.next = 0
                        else:
                            optical_switch_counter.next = optical_switch_counter + 1
                elif optSwitchState == OptSwitchState.SELECTED_1:
                    sw1_2way.next = 0
                    sw2_2way.next = 0
                    if sel[0] == 1:
                        optSwitchState.next = OptSwitchState.PULSING_2
                        optical_switch_counter.next = 0
                elif optSwitchState == OptSwitchState.PULSING_2:
                    sw1_2way.next = 0
                    sw2_2way.next = 1
                    if dac_strobe: # This goes high for one clock cycle every 10us
                        if optical_switch_counter >= OPTICAL_SWITCH_WIDTH-1:
                            optSwitchState.next = OptSwitchState.SELECTED_2
                            optical_switch_counter.next = 0
                        else:
                            optical_switch_counter.next = optical_switch_counter + 1
                elif optSwitchState == OptSwitchState.SELECTED_2:
                    sw1_2way.next = 0
                    sw2_2way.next = 0
                    if sel[0] == 0:
                        optSwitchState.next = OptSwitchState.PULSING_1
                        optical_switch_counter.next = 0

                # State machine for generating low-going pulse on laser change for 4-way optical switch

                if control[INJECT_CONTROL_OPTICAL_SWITCH_SELECT_B]:
                    if switchPulserState == SwitchPulserState.START:
                        sw4_4way.next = 1
                        switchPulserState.next = SwitchPulserState.PULSING
                        pulse_counter.next = 0

                    elif switchPulserState == SwitchPulserState.PULSING:
                        sw4_4way.next = 0
                        last_sel.next = sel
                        if dac_strobe: # This goes high for one clock cycle every 10us
                            if pulse_counter >= OPTICAL_SWITCH_WIDTH-1:
                                switchPulserState.next = SwitchPulserState.WAITING
                                pulse_counter.next = 0
                            else:
                                pulse_counter.next = pulse_counter + 1

                    elif switchPulserState == SwitchPulserState.WAITING:
                        sw4_4way.next = 1
                        if sel != last_sel:
                            switchPulserState.next = SwitchPulserState.PULSING
                            pulse_counter.next = 0

    @always_comb
    def  comb1():
        s = control[INJECT_CONTROL_LASER_SELECT_B+INJECT_CONTROL_LASER_SELECT_W:INJECT_CONTROL_LASER_SELECT_B]
        m = control[INJECT_CONTROL_MODE_B]
        e = control2[INJECT_CONTROL2_EXTINGUISH_DESELECTED_B]
        mode.next = m
        sel.next  = s
        extinguish_deselected.next = e

        if control[INJECT_CONTROL_OPTICAL_SWITCH_SELECT_B]:
            optical_switch1_out.next = s[0]
            optical_switch2_out.next = s[1]
            # optical_switch4_out.next = sw4_4way
        else:
            optical_switch1_out.next = sw1_2way
            optical_switch2_out.next = sw2_2way
            # optical_switch4_out.next = not s[1]

        optical_switch4_out.next = sw4_4way

        if control2[INJECT_CONTROL2_FIBER_AMP_PRESENT_B]:
            optical_switch4_out.next = fiber_amp_pwm_in

        laser_current_en.next = control[INJECT_CONTROL_LASER_CURRENT_ENABLE_B+INJECT_CONTROL_LASER_CURRENT_ENABLE_W:INJECT_CONTROL_LASER_CURRENT_ENABLE_B]
        manual_laser_en.next  = control[INJECT_CONTROL_MANUAL_LASER_ENABLE_B+INJECT_CONTROL_MANUAL_LASER_ENABLE_W:INJECT_CONTROL_MANUAL_LASER_ENABLE_B]
        manual_soa_en.next = control[INJECT_CONTROL_MANUAL_SOA_ENABLE_B]
        laser_shutdown_en.next = control[INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B]
        soa_shutdown_en.next = control[INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B]
        soa_present.next = control[INJECT_CONTROL_SOA_PRESENT_B]
        sel_laser_out.next = s

        if s == 0:
            sel_coarse_current_out.next = laser1_coarse_current
            sel_fine_current_out.next = laser1_fine
        elif s == 1:
            sel_coarse_current_out.next = laser2_coarse_current
            sel_fine_current_out.next = laser2_fine
        elif s == 2:
            sel_coarse_current_out.next = laser3_coarse_current
            sel_fine_current_out.next = laser3_fine
        elif s == 3:
            sel_coarse_current_out.next = laser4_coarse_current
            sel_fine_current_out.next = laser4_fine

    @always_comb
    def  comb2():
        laser1_disable_out.next = not laser_current_en[0]
        laser2_disable_out.next = not laser_current_en[1]
        laser3_disable_out.next = not laser_current_en[2]
        laser4_disable_out.next = not laser_current_en[3]
        laser1_shutdown_out.next = not manual_laser_en[0]
        laser2_shutdown_out.next = not manual_laser_en[1]
        laser3_shutdown_out.next = not manual_laser_en[2]
        laser4_shutdown_out.next = not manual_laser_en[3]
        laser1_coarse.next = laser1_coarse_current
        laser2_coarse.next = laser2_coarse_current
        laser3_coarse.next = laser3_coarse_current
        laser4_coarse.next = laser4_coarse_current
        soa_shutdown_out.next = not manual_soa_en

        if mode:
            soa_shutdown_out.next = soa_shutdown_in and soa_shutdown_en
            if sel==0:
                laser1_shutdown_out.next = laser_shutdown_in and laser_shutdown_en
                if extinguish_deselected:
                    laser2_coarse.next = 0
                    laser3_coarse.next = 0
                    laser4_coarse.next = 0
            elif sel==1:
                laser2_shutdown_out.next = laser_shutdown_in and laser_shutdown_en
                if extinguish_deselected:
                    laser1_coarse.next = 0
                    laser3_coarse.next = 0
                    laser4_coarse.next = 0
            elif sel==2:
                laser3_shutdown_out.next = laser_shutdown_in and laser_shutdown_en
                if extinguish_deselected:
                    laser1_coarse.next = 0
                    laser2_coarse.next = 0
                    laser4_coarse.next = 0
            else:
                laser4_shutdown_out.next = laser_shutdown_in and laser_shutdown_en
                if extinguish_deselected:
                    laser1_coarse.next = 0
                    laser2_coarse.next = 0
                    laser3_coarse.next = 0

        if not soa_present:
            soa_shutdown_out.next = True

    laser1_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser1_coarse,chanB_data_in=laser1_fine,
        strobe_in=dac_strobe,dac_sync_out=laser1_dac_sync_out,
        dac_din_out=laser1_dac_din_out)

    laser2_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser2_coarse,chanB_data_in=laser2_fine,
        strobe_in=dac_strobe,dac_sync_out=laser2_dac_sync_out,
        dac_din_out=laser2_dac_din_out)

    laser3_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser3_coarse,chanB_data_in=laser3_fine,
        strobe_in=dac_strobe,dac_sync_out=laser3_dac_sync_out,
        dac_din_out=laser3_dac_din_out)

    laser4_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser4_coarse,chanB_data_in=laser4_fine,
        strobe_in=dac_strobe,dac_sync_out=laser4_dac_sync_out,
        dac_din_out=laser4_dac_din_out)

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    laser_dac_clk_in = Signal(LOW)
    strobe_in = Signal(LOW)
    laser_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser_shutdown_in = Signal(LOW)
    soa_shutdown_in = Signal(LOW)
    fiber_amp_pwm_in = Signal(LOW)
    laser1_dac_sync_out = Signal(LOW)
    laser2_dac_sync_out = Signal(LOW)
    laser3_dac_sync_out = Signal(LOW)
    laser4_dac_sync_out = Signal(LOW)
    laser1_dac_din_out = Signal(LOW)
    laser2_dac_din_out = Signal(LOW)
    laser3_dac_din_out = Signal(LOW)
    laser4_dac_din_out = Signal(LOW)
    laser1_disable_out = Signal(LOW)
    laser2_disable_out = Signal(LOW)
    laser3_disable_out = Signal(LOW)
    laser4_disable_out = Signal(LOW)
    laser1_shutdown_out = Signal(LOW)
    laser2_shutdown_out = Signal(LOW)
    laser3_shutdown_out = Signal(LOW)
    laser4_shutdown_out = Signal(LOW)
    soa_shutdown_out = Signal(LOW)
    sel_laser_out = Signal(intbv(0)[2:])
    sel_coarse_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sel_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    optical_switch1_out = Signal(LOW)
    optical_switch2_out = Signal(LOW)
    optical_switch4_out = Signal(LOW)
    map_base = FPGA_INJECT

    toVHDL(Inject, clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, laser_dac_clk_in=laser_dac_clk_in,
                   strobe_in=strobe_in,
                   laser_fine_current_in=laser_fine_current_in,
                   laser_shutdown_in=laser_shutdown_in,
                   soa_shutdown_in=soa_shutdown_in,
                   fiber_amp_pwm_in=fiber_amp_pwm_in,
                   laser1_dac_sync_out=laser1_dac_sync_out,
                   laser2_dac_sync_out=laser2_dac_sync_out,
                   laser3_dac_sync_out=laser3_dac_sync_out,
                   laser4_dac_sync_out=laser4_dac_sync_out,
                   laser1_dac_din_out=laser1_dac_din_out,
                   laser2_dac_din_out=laser2_dac_din_out,
                   laser3_dac_din_out=laser3_dac_din_out,
                   laser4_dac_din_out=laser4_dac_din_out,
                   laser1_disable_out=laser1_disable_out,
                   laser2_disable_out=laser2_disable_out,
                   laser3_disable_out=laser3_disable_out,
                   laser4_disable_out=laser4_disable_out,
                   laser1_shutdown_out=laser1_shutdown_out,
                   laser2_shutdown_out=laser2_shutdown_out,
                   laser3_shutdown_out=laser3_shutdown_out,
                   laser4_shutdown_out=laser4_shutdown_out,
                   soa_shutdown_out=soa_shutdown_out,
                   sel_laser_out=sel_laser_out,
                   sel_coarse_current_out=sel_coarse_current_out,
                   sel_fine_current_out=sel_fine_current_out,
                   optical_switch1_out=optical_switch1_out,
                   optical_switch2_out=optical_switch2_out,
                   optical_switch4_out=optical_switch4_out,
                   map_base=map_base)
