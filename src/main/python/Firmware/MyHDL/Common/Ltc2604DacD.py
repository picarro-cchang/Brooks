#!/usr/bin/python
#
# FILE:
#   Ltc2604DacD.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Aug-2009  sze  Initial version.
#   20-Sep-2009  sze  Register DAC lines to deglitch them
#   16-Feb-2010  sze  Only convert channel D for PZT, since prop valve DACs are no longer 
#                      needed, drop dac_clock_in frequency to 2.5 MHz.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK

LOW, HIGH = bool(0), bool(1)
t_State = enum("IDLE","WAIT_1","WAIT_0")

def Ltc2604DacD(clk,reset,dac_clock_in,chanD_data_in,strobe_in,dac_sck_out,
               dac_sdi_out,dac_ld_out):
    """
    Parameters:
    clk             -- 50MHz clock
    reset           -- reset
    dac_clock_in    -- 2.5MHz clock
    chanD_data_in   -- Data for channel D
    strobe_in       -- Strobe to start loading information into DAC
    dac_sck_out     -- Clock output to DAC
    dac_sdi_out     -- Serial data to DAC
    dac_ld_out      -- Signal for LD pin of DAC

    When strobe_in goes high, data are latched and transferred serially 
    to the DAC over the following 10us, channel D is updated at the end.
    
    """
    counter = Signal(intbv(0)[5:])
    state = Signal(t_State.IDLE)

    chanD_control = (1,1,0,0,1,1,0,0)

    CONTROL_LENGTH = 8
    DATA_LENGTH = 16

    CHAND_CONTROL_START = 1
    CHAND_CONTROL_END = CHAND_CONTROL_START+CONTROL_LENGTH
    CHAND_DATA_START = CHAND_CONTROL_END
    CHAND_DATA_END = CHAND_DATA_START+DATA_LENGTH

    chanD_data = Signal(intbv(0)[DATA_LENGTH:])
    dac_sdi = Signal(LOW)
    dac_ld = Signal(LOW)
    
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                chanD_data.next = 0
                dac_ld.next = 1
            else:
                if state == t_State.IDLE:
                    if strobe_in:
                        chanD_data.next = chanD_data_in
                        counter.next = 0
                        dac_ld.next = 0
                        state.next = t_State.WAIT_0
                elif state == t_State.WAIT_0:
                    if not dac_clock_in:
                        if counter < CHAND_DATA_END-1:
                            counter.next = counter + 1
                            state.next = t_State.WAIT_1
                        else:
                            dac_ld.next = 1
                            state.next = t_State.IDLE
                elif state == t_State.WAIT_1:
                    if dac_clock_in:
                        dac_ld.next = 0
                        state.next = t_State.WAIT_0
                else:
                    state.next = t_State.IDLE
                # Register the outputs
                dac_sdi_out.next = dac_sdi
                dac_ld_out.next = dac_ld
                dac_sck_out.next = dac_clock_in


    @always_comb
    def  comb2():
        dac_sdi.next = 1
        if CHAND_CONTROL_START<=counter and counter<CHAND_CONTROL_END:
            dac_sdi.next = chanD_control[CHAND_CONTROL_END-1-int(counter)]
        elif CHAND_DATA_START<=counter and counter<CHAND_DATA_END:
            dac_sdi.next = chanD_data[CHAND_DATA_END-1-int(counter)]
        else:
            dac_sdi.next = 0

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dac_clock_in = Signal(LOW)
    chanD_data_in = Signal(intbv(0)[16:])
    strobe_in = Signal(LOW)
    dac_sck_out = Signal(LOW)
    dac_sdi_out = Signal(LOW)
    dac_ld_out = Signal(LOW)

    toVHDL(Ltc2604DacD, clk=clk, reset=reset, dac_clock_in=dac_clock_in,
                        chanD_data_in=chanD_data_in, strobe_in=strobe_in,
                        dac_sck_out=dac_sck_out, dac_sdi_out=dac_sdi_out,
                        dac_ld_out=dac_ld_out)
