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
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK
from Host.autogen.interface import KERNEL_MAGIC_CODE, FPGA_MAGIC_CODE
from Host.autogen.interface import FPGA_KERNEL, KERNEL_RESET

LOW, HIGH = bool(0), bool(1)

t_State = enum("NORMAL","DISCONNECTED","RESETTING")

def Kernel(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,map_base,
        usb_connected,cyp_reset):
    """
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    map_base            -- Base of FPGA map for this block

    This block appears as two registers to the DSP, starting at map_base. The registers are:
    KERNEL_MAGIC_CODE   -- Magic code register. Read to check if FPGA is programmed.
    KERNEL_RESET        -- Writing "one" resets Cypress USB and FPGA

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
    kernel_reset_addr = map_base + KERNEL_RESET

    kernel_reset = Signal(intbv(0)[1:])
    state = Signal(t_State.NORMAL)

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                cyp_reset.next = LOW
                counter.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_magic_code_addr:
                        dsp_data_in.next = FPGA_MAGIC_CODE
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == kernel_reset_addr:
                        if dsp_wr: kernel_reset.next = dsp_data_out
                        dsp_data_in.next = kernel_reset
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                # State machine for handling resetting of Cypress FX2 and FPGA
                if state == t_State.NORMAL:
                    cyp_reset.next = LOW
                    if kernel_reset:
                        counter.next = 0
                        kernel_reset.next = 0
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
                    elif kernel_reset:
                        counter.next = 0
                        kernel_reset.next = 0
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
                        kernel_reset.next = 0
                        state.next = t_State.NORMAL
                    else:
                        state.next = t_State.RESETTING
                else:
                    cyp_reset.next = LOW
                    state.next = t_State.NORMAL

    return instances()

if __name__ == "__main__":
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr, clk, reset = [Signal(LOW) for i in range(3)]
    usb_connected, cyp_reset = [Signal(LOW) for i in range(2)]
    map_base = FPGA_KERNEL

    toVHDL(Kernel, clk=clk, reset=reset, dsp_addr=dsp_addr, dsp_data_out=dsp_data_out,
                   dsp_data_in=dsp_data_in, dsp_wr=dsp_wr, map_base=map_base,
                   usb_connected=usb_connected, cyp_reset=cyp_reset)
