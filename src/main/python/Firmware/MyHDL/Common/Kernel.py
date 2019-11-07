#!/usr/bin/python
#
# FILE:
#   Kernel.py
#
# DESCRIPTION:
#   MyHDL for kernel block. This block
#    1) Allows the host to discover if the FPGA has been programmed
#    2) Resets the Cypress FX2 if the USB cable is disconnected
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   27-May-2009  sze  Initial version.
#   03-Jun-2009  sze  Introduced general purpose output register gpreg_1 for selecting
#                      signals that are monitored by the Intronix Logic Probe
#   27-Jul-2009  sze  Support resetting Cypress FX2 and FPGA. Allow Intronix to monitor
#                      three waveform channels
#   25-Sep-2009  sze  Added register and I/O for overload conditions
#    5-Nov-2009  sze  Added I2C reset bit in control register
#   03-Jun-2010  sze  Added manual control of FPGA DIO lines
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import FPGA_MAGIC_CODE
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_KERNEL

from Host.autogen.interface import KERNEL_MAGIC_CODE, KERNEL_CONTROL
from Host.autogen.interface import KERNEL_DIAG_1, KERNEL_CONFIG
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL
from Host.autogen.interface import KERNEL_INTRONIX_1, KERNEL_INTRONIX_2
from Host.autogen.interface import KERNEL_INTRONIX_3, KERNEL_OVERLOAD
from Host.autogen.interface import KERNEL_DOUT_HI, KERNEL_DOUT_LO
from Host.autogen.interface import KERNEL_DIN, KERNEL_STATUS_LED
from Host.autogen.interface import KERNEL_FAN, KERNEL_SEL_DETECTOR_MODE

from Host.autogen.interface import KERNEL_CONTROL_CYPRESS_RESET_B, KERNEL_CONTROL_CYPRESS_RESET_W
from Host.autogen.interface import KERNEL_CONTROL_OVERLOAD_RESET_B, KERNEL_CONTROL_OVERLOAD_RESET_W
from Host.autogen.interface import KERNEL_CONTROL_I2C_RESET_B, KERNEL_CONTROL_I2C_RESET_W
from Host.autogen.interface import KERNEL_CONTROL_DOUT_MAN_B, KERNEL_CONTROL_DOUT_MAN_W
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL_DIVISOR_B, KERNEL_INTRONIX_CLKSEL_DIVISOR_W
from Host.autogen.interface import KERNEL_INTRONIX_1_CHANNEL_B, KERNEL_INTRONIX_1_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_2_CHANNEL_B, KERNEL_INTRONIX_2_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_3_CHANNEL_B, KERNEL_INTRONIX_3_CHANNEL_W
from Host.autogen.interface import KERNEL_STATUS_LED_RED_B, KERNEL_STATUS_LED_RED_W
from Host.autogen.interface import KERNEL_STATUS_LED_GREEN_B, KERNEL_STATUS_LED_GREEN_W
from Host.autogen.interface import KERNEL_FAN_FAN1_B, KERNEL_FAN_FAN1_W
from Host.autogen.interface import KERNEL_FAN_FAN2_B, KERNEL_FAN_FAN2_W
from Host.autogen.interface import KERNEL_SEL_DETECTOR_MODE_MODE_B, KERNEL_SEL_DETECTOR_MODE_MODE_W


t_State = enum("NORMAL","DISCONNECTED","RESETTING")

LOW, HIGH = bool(0), bool(1)
def Kernel(clk, reset, dsp_addr, dsp_data_out, dsp_data_in, dsp_wr,
            sel_laser_in, usb_connected, cyp_reset, sel_detector_out,
            diag_1_out, config_out, intronix_clksel_out, intronix_1_out,
            intronix_2_out, intronix_3_out, overload_in, overload_out,
            i2c_reset_out, status_led_out, fan_out, dout_man_out,
            dout_out, din_in, map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    sel_laser_in        -- Two bits indicating selected actual laser (from INJECT block)
    usb_connected       -- input which is high if power is detected on the USB connector
    cyp_reset           -- output which interrupts power to the FX2 chip
    sel_detector_out    -- output to select detector using analog switch
    diag_1_out          -- DSP accessible register which may be monitored by the LogicPort
    config_out          -- DSP accessible register for configuring FPGA
    intronix_clksel_out -- selects speed of clock signal for LogicPort
    intronix_1_out      -- used to select quantity to display in channel 1 of LogicPort
    intronix_2_out      -- used to select quantity to display in channel 2 of LogicPort
    intronix_3_out      -- used to select quantity to display in channel 3 of LogicPort
    overload_in         -- Inputs from overload detection circuitry, readable via a register
    overload_out        -- Goes high if any bit in latched overload_in is high
    i2c_reset_out       -- Goes high to reset I2C multiplexers
    status_led_out      -- used to set tricolor LED on front panel
    fan_out             -- used to set dual fans
    dout_man_out        -- Goes high to indicate FPGA DOUT lines are driven manually
    dout_out            -- Values to write to FPGA DOUT lines when in manual mode
    din_in              -- Values from FPGA DIN lines
    map_base            -- Base of FPGA map for this block

    Registers:
    KERNEL_MAGIC_CODE   -- Magic code register. Read to check if FPGA is programmed.
    KERNEL_CONTROL      -- Control register for resetting FPGA and overload state
    KERNEL_DIAG_1       -- Register which may be monitored by the LogicPort
    KERNEL_CONFIG       -- Register for configuring FPGA
    KERNEL_INTRONIX_CLKSEL
    KERNEL_INTRONIX_1
    KERNEL_INTRONIX_2
    KERNEL_INTRONIX_3
    KERNEL_OVERLOAD     -- Latches any high overload inputs so they may be read by the DSP
                            The contents are reset when OVERLOAD_RESET bit in the kernel register is asserted
    KERNEL_DOUT_HI      -- High-order bits (39-32) for FPGA DOUT lines
    KERNEL_DOUT_LO      -- Low-order  bits (31-0)  for FPGA DOUT lines
    KERNEL_DIN          -- Readback for FPGA DIN lines
    KERNEL_STATUS_LED   -- state of LEDs (bit0 for red and bit1 for green)
    KERNEL_FAN          -- state of fans (bit0 for fan1 and bit1 for fan2)
    KERNEL_SEL_DETECTOR_MODE -- 4 bit code indicating which lasers map to which detector

    Fields in KERNEL_CONTROL:
    KERNEL_CONTROL_CYPRESS_RESET
    KERNEL_CONTROL_OVERLOAD_RESET
    KERNEL_CONTROL_I2C_RESET
    KERNEL_CONTROL_DOUT_MAN         -- Set to 1 to drive FPGA digital output lines manually

    Fields in KERNEL_INTRONIX_CLKSEL:
    KERNEL_INTRONIX_CLKSEL_DIVISOR

    Fields in KERNEL_INTRONIX_1:
    KERNEL_INTRONIX_1_CHANNEL

    Fields in KERNEL_INTRONIX_2:
    KERNEL_INTRONIX_2_CHANNEL

    Fields in KERNEL_INTRONIX_3:
    KERNEL_INTRONIX_3_CHANNEL

    Fields in KERNEL_STATUS_LED:
    KERNEL_STATUS_LED_RED
    KERNEL_STATUS_LED_GREEN

    Fields in KERNEL_FAN:
    KERNEL_FAN_FAN1
    KERNEL_FAN_FAN2

    A state machine is used to control resetting of the Cypress FX2. If
     a kernel reset is commanded, the FX2 reset is asserted for 1s. When
     this is removed, the FPGA is also reset, since the PROGB pin goes low.
     If the USB connection is broken for more than a certain length of time,
     we also reset the Cypress FX2 and FPGA.

    """
    NSTAGES = 26
    counter = Signal(intbv(0)[NSTAGES:])
    top_count = (1<<NSTAGES)-1

    kernel_magic_code_addr = map_base + KERNEL_MAGIC_CODE
    kernel_control_addr = map_base + KERNEL_CONTROL
    kernel_diag_1_addr = map_base + KERNEL_DIAG_1
    kernel_config_addr = map_base + KERNEL_CONFIG
    kernel_intronix_clksel_addr = map_base + KERNEL_INTRONIX_CLKSEL
    kernel_intronix_1_addr = map_base + KERNEL_INTRONIX_1
    kernel_intronix_2_addr = map_base + KERNEL_INTRONIX_2
    kernel_intronix_3_addr = map_base + KERNEL_INTRONIX_3
    kernel_overload_addr = map_base + KERNEL_OVERLOAD
    kernel_dout_hi_addr = map_base + KERNEL_DOUT_HI
    kernel_dout_lo_addr = map_base + KERNEL_DOUT_LO
    kernel_din_addr = map_base + KERNEL_DIN
    kernel_status_led_addr = map_base + KERNEL_STATUS_LED
    kernel_fan_addr = map_base + KERNEL_FAN
    kernel_sel_detector_mode_addr = map_base + KERNEL_SEL_DETECTOR_MODE
    magic_code = Signal(intbv(0)[FPGA_REG_WIDTH:])
    control = Signal(intbv(0)[FPGA_REG_WIDTH:])
    diag_1 = Signal(intbv(0)[8:])
    config = Signal(intbv(0)[FPGA_REG_WIDTH:])
    intronix_clksel = Signal(intbv(0)[5:])
    intronix_1 = Signal(intbv(0)[8:])
    intronix_2 = Signal(intbv(0)[8:])
    intronix_3 = Signal(intbv(0)[8:])
    overload = Signal(intbv(0)[FPGA_REG_WIDTH:])
    dout_hi = Signal(intbv(0)[8:])
    dout_lo = Signal(intbv(0)[32:])
    din = Signal(intbv(0)[24:])
    status_led = Signal(intbv(0)[FPGA_REG_WIDTH:])
    fan = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sel_detector_mode = Signal(intbv(0)[4:])

    state = Signal(t_State.NORMAL)
    control_init = 1 << KERNEL_CONTROL_I2C_RESET_B
    
    @always_comb
    def  comb():
        intronix_clksel_out.next = intronix_clksel
        intronix_1_out.next = intronix_1
        intronix_2_out.next = intronix_2
        intronix_3_out.next = intronix_3
        diag_1_out.next = diag_1
        config_out.next = config
        dout_out.next = concat(dout_hi,dout_lo)
        din.next = din_in
        status_led_out.next[0] = status_led[KERNEL_STATUS_LED_RED_B]
        status_led_out.next[1] = status_led[KERNEL_STATUS_LED_GREEN_B]
        fan_out.next[0] = fan[KERNEL_FAN_FAN1_B]
        fan_out.next[1] = fan[KERNEL_FAN_FAN2_B]
        sel_detector_out.next = (
            (sel_detector_mode[0] and (sel_laser_in == 0)) or
            (sel_detector_mode[1] and (sel_laser_in == 1)) or
            (sel_detector_mode[2] and (sel_laser_in == 2)) or
            (sel_detector_mode[3] and (sel_laser_in == 3))
        )
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                control.next = control_init
                diag_1.next = 0
                config.next = 0
                intronix_clksel.next = 0
                intronix_1.next = 0
                intronix_2.next = 0
                intronix_3.next = 0
                overload.next = 0
                i2c_reset_out.next = 1
                dout_hi.next = 0
                dout_lo.next = 0
                status_led.next = 0
                fan.next = 0
                sel_detector_mode.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_magic_code_addr: # r
                        dsp_data_in.next = FPGA_MAGIC_CODE
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_control_addr: # rw
                        if dsp_wr: control.next = dsp_data_out
                        dsp_data_in.next = control
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_diag_1_addr: # rw
                        if dsp_wr: diag_1.next = dsp_data_out
                        dsp_data_in.next = diag_1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_config_addr: # rw
                        if dsp_wr: config.next = dsp_data_out
                        dsp_data_in.next = config
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_intronix_clksel_addr: # rw
                        if dsp_wr: intronix_clksel.next = dsp_data_out
                        dsp_data_in.next = intronix_clksel
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_intronix_1_addr: # rw
                        if dsp_wr: intronix_1.next = dsp_data_out
                        dsp_data_in.next = intronix_1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_intronix_2_addr: # rw
                        if dsp_wr: intronix_2.next = dsp_data_out
                        dsp_data_in.next = intronix_2
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_intronix_3_addr: # rw
                        if dsp_wr: intronix_3.next = dsp_data_out
                        dsp_data_in.next = intronix_3
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_overload_addr: # r
                        dsp_data_in.next = overload
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_dout_hi_addr: # rw
                        if dsp_wr: dout_hi.next = dsp_data_out
                        dsp_data_in.next = dout_hi
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_dout_lo_addr: # rw
                        if dsp_wr: dout_lo.next = dsp_data_out
                        dsp_data_in.next = dout_lo
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_din_addr: # r
                        dsp_data_in.next = din
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_status_led_addr: # rw
                        if dsp_wr: status_led.next = dsp_data_out
                        dsp_data_in.next = status_led
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_fan_addr: # rw
                        if dsp_wr: fan.next = dsp_data_out
                        dsp_data_in.next = fan
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_sel_detector_mode_addr: # rw
                        if dsp_wr: sel_detector_mode.next = dsp_data_out
                        dsp_data_in.next = sel_detector_mode
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                
                # Allow DSP to read state of overload inputs and assert overload_out if any
                #  input is high
                if control[KERNEL_CONTROL_OVERLOAD_RESET_B]:
                    control.next[KERNEL_CONTROL_OVERLOAD_RESET_B] = 0
                    overload.next = overload_in
                else: # Latch set bits in overload_in
                    overload.next = overload | overload_in

                if overload != 0:
                    overload_out.next = 1
                else:
                    overload_out.next = 0
                    
                i2c_reset_out.next = control[KERNEL_CONTROL_I2C_RESET_B]
                dout_man_out.next =  control[KERNEL_CONTROL_DOUT_MAN_B]
                
                ## State machine for handling resetting of Cypress FX2 and FPGA
                #if state == t_State.NORMAL:
                    #cyp_reset.next = LOW
                    #if control[KERNEL_CONTROL_CYPRESS_RESET_B]:
                        #counter.next = 0
                        #control.next[KERNEL_CONTROL_CYPRESS_RESET_B] = 0
                        #state.next = t_State.RESETTING
                    #elif not usb_connected:
                        #counter.next = 0
                        #state.next = t_State.DISCONNECTED
                    #else:
                        #state.next = t_State.NORMAL
                #elif state == t_State.DISCONNECTED:
                    #cyp_reset.next = LOW
                    #if usb_connected:
                        #state.next = t_State.NORMAL
                    #elif control[KERNEL_CONTROL_CYPRESS_RESET_B]:
                        #counter.next = 0
                        #control.next[KERNEL_CONTROL_CYPRESS_RESET_B] = 0
                        #state.next = t_State.RESETTING
                    #else:
                        #counter.next = counter + 1
                        #if counter == top_count:
                            #counter.next = 0
                            #state.next = t_State.RESETTING
                        #else:
                            #state.next = t_State.DISCONNECTED
                #elif state == t_State.RESETTING:
                    #cyp_reset.next = HIGH
                    #counter.next = counter + 1
                    #if counter == top_count:
                        #control.next[KERNEL_CONTROL_CYPRESS_RESET_B] = 0
                        #state.next = t_State.NORMAL
                    #else:
                        #state.next = t_State.RESETTING
                #else:
                    #cyp_reset.next = LOW
                    #state.next = t_State.NORMAL


    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    sel_laser_in = Signal(intbv(0)[2:])
    usb_connected = Signal(LOW)
    cyp_reset = Signal(LOW)
    sel_detector_out = Signal(LOW)
    diag_1_out = Signal(intbv(0)[8:])
    config_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    intronix_clksel_out = Signal(intbv(0)[5:])
    intronix_1_out = Signal(intbv(0)[8:])
    intronix_2_out = Signal(intbv(0)[8:])
    intronix_3_out = Signal(intbv(0)[8:])
    overload_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    overload_out = Signal(LOW)
    i2c_reset_out = Signal(LOW)
    status_led_out = Signal(intbv(0)[2:])
    fan_out = Signal(intbv(0)[2:])
    dout_man_out = Signal(LOW)
    dout_out = Signal(intbv(0)[40:])
    din_in = Signal(intbv(0)[24:])
    map_base = FPGA_KERNEL

    toVHDL(Kernel, clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, sel_laser_in=sel_laser_in,
                   usb_connected=usb_connected, cyp_reset=cyp_reset,
                   sel_detector_out=sel_detector_out,
                   diag_1_out=diag_1_out, config_out=config_out,
                   intronix_clksel_out=intronix_clksel_out,
                   intronix_1_out=intronix_1_out,
                   intronix_2_out=intronix_2_out,
                   intronix_3_out=intronix_3_out,
                   overload_in=overload_in, overload_out=overload_out,
                   i2c_reset_out=i2c_reset_out,
                   status_led_out=status_led_out, fan_out=fan_out,
                   dout_man_out=dout_man_out, dout_out=dout_out,
                   din_in=din_in, map_base=map_base)
