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
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import FPGA_MAGIC_CODE
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_KERNEL

from Host.autogen.interface import KERNEL_MAGIC_CODE, KERNEL_FPGA_RESET
from Host.autogen.interface import KERNEL_DIAG_1
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL
from Host.autogen.interface import KERNEL_INTRONIX_1, KERNEL_INTRONIX_2
from Host.autogen.interface import KERNEL_INTRONIX_3

from Host.autogen.interface import KERNEL_FPGA_RESET_RESET_B, KERNEL_FPGA_RESET_RESET_W
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL_DIVISOR_B, KERNEL_INTRONIX_CLKSEL_DIVISOR_W
from Host.autogen.interface import KERNEL_INTRONIX_1_CHANNEL_B, KERNEL_INTRONIX_1_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_2_CHANNEL_B, KERNEL_INTRONIX_2_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_3_CHANNEL_B, KERNEL_INTRONIX_3_CHANNEL_W


t_State = enum("NORMAL","DISCONNECTED","RESETTING")

LOW, HIGH = bool(0), bool(1)
def Kernel(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
           usb_connected,cyp_reset,diag_1_out,intronix_clksel_out,
           intronix_1_out,intronix_2_out,intronix_3_out,map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    usb_connected
    cyp_reset
    diag_1_out
    intronix_clksel_out
    intronix_1_out
    intronix_2_out
    intronix_3_out
    map_base            -- Base of FPGA map for this block

    Registers:
    KERNEL_MAGIC_CODE   -- Magic code register. Read to check if FPGA is programmed.
    KERNEL_FPGA_RESET   -- Writing "one" resets Cypress USB and FPGA
    KERNEL_DIAG_1
    KERNEL_INTRONIX_CLKSEL
    KERNEL_INTRONIX_1
    KERNEL_INTRONIX_2
    KERNEL_INTRONIX_3

    Fields in KERNEL_FPGA_RESET:
    KERNEL_FPGA_RESET_RESET

    Fields in KERNEL_INTRONIX_CLKSEL:
    KERNEL_INTRONIX_CLKSEL_DIVISOR

    Fields in KERNEL_INTRONIX_1:
    KERNEL_INTRONIX_1_CHANNEL

    Fields in KERNEL_INTRONIX_2:
    KERNEL_INTRONIX_2_CHANNEL

    Fields in KERNEL_INTRONIX_3:
    KERNEL_INTRONIX_3_CHANNEL

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
    kernel_fpga_reset_addr = map_base + KERNEL_FPGA_RESET
    kernel_diag_1_addr = map_base + KERNEL_DIAG_1
    kernel_intronix_clksel_addr = map_base + KERNEL_INTRONIX_CLKSEL
    kernel_intronix_1_addr = map_base + KERNEL_INTRONIX_1
    kernel_intronix_2_addr = map_base + KERNEL_INTRONIX_2
    kernel_intronix_3_addr = map_base + KERNEL_INTRONIX_3
    magic_code = Signal(intbv(0)[FPGA_REG_WIDTH:])
    fpga_reset = Signal(intbv(0)[1:])
    diag_1 = Signal(intbv(0)[8:])
    intronix_clksel = Signal(intbv(0)[5:])
    intronix_1 = Signal(intbv(0)[8:])
    intronix_2 = Signal(intbv(0)[8:])
    intronix_3 = Signal(intbv(0)[8:])

    state = Signal(t_State.NORMAL)

    @always_comb
    def  comb():
        intronix_clksel_out.next = intronix_clksel
        intronix_1_out.next = intronix_1
        intronix_2_out.next = intronix_2
        intronix_3_out.next = intronix_3
        diag_1_out.next = diag_1

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                fpga_reset.next = 0
                diag_1.next = 0
                intronix_clksel.next = 0
                intronix_1.next = 0
                intronix_2.next = 0
                intronix_3.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_magic_code_addr: # r
                        dsp_data_in.next = FPGA_MAGIC_CODE
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_fpga_reset_addr: # rw
                        if dsp_wr: fpga_reset.next = dsp_data_out
                        dsp_data_in.next = fpga_reset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_diag_1_addr: # rw
                        if dsp_wr: diag_1.next = dsp_data_out
                        dsp_data_in.next = diag_1
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
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                # State machine for handling resetting of Cypress FX2 and FPGA
                if state == t_State.NORMAL:
                    cyp_reset.next = LOW
                    if fpga_reset:
                        counter.next = 0
                        fpga_reset.next = 0
                        state.next = t_State.RESETTING
                    elif not usb_connected:
                        counter.next = 0
                        state.next = t_State.DISCONNECTED
                    else:
                        state.next = t_State.NORMAL
                elif state == t_State.DISCONNECTED:
                    cyp_reset.next = LOW
                    if usb_connected:
                        state.next = t_State.NORMAL
                    elif fpga_reset:
                        counter.next = 0
                        fpga_reset.next = 0
                        state.next = t_State.RESETTING
                    else:
                        counter.next = counter + 1
                        if counter == top_count:
                            counter.next = 0
                            state.next = t_State.RESETTING
                        else:
                            state.next = t_State.DISCONNECTED
                elif state == t_State.RESETTING:
                    cyp_reset.next = HIGH
                    counter.next = counter + 1
                    if counter == top_count:
                        fpga_reset.next = 0
                        state.next = t_State.NORMAL
                    else:
                        state.next = t_State.RESETTING
                else:
                    cyp_reset.next = LOW
                    state.next = t_State.NORMAL


    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    usb_connected = Signal(LOW)
    cyp_reset = Signal(LOW)
    diag_1_out = Signal(intbv(0)[8:])
    intronix_clksel_out = Signal(intbv(0)[5:])
    intronix_1_out = Signal(intbv(0)[8:])
    intronix_2_out = Signal(intbv(0)[8:])
    intronix_3_out = Signal(intbv(0)[8:])
    map_base = FPGA_KERNEL

    toVHDL(Kernel, clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, usb_connected=usb_connected,
                   cyp_reset=cyp_reset, diag_1_out=diag_1_out,
                   intronix_clksel_out=intronix_clksel_out,
                   intronix_1_out=intronix_1_out,
                   intronix_2_out=intronix_2_out,
                   intronix_3_out=intronix_3_out, map_base=map_base)
