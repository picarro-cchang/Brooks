#!/usr/bin/python
#
# FILE:
#   Ltc2604Dac.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Aug-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK

LOW, HIGH = bool(0), bool(1)
t_State = enum("IDLE","WAIT_1","WAIT_0")

def Ltc2604Dac(clk,reset,dac_clock_in,chanA_data_in,chanB_data_in,
               chanC_data_in,chanD_data_in,strobe_in,dac_sdi_out,
               dac_ld_out):
    """
    Parameters:
    clk             -- 50MHz clock
    reset           -- reset
    dac_clock_in    -- 10MHz clock, also connected to DAC SCK
    chanA_data_in   -- Data for channel A
    chanB_data_in   -- Data for channel B
    chanC_data_in   -- Data for channel C
    chanD_data_in   -- Data for channel D
    strobe_in       -- Strobe to start loading information into DAC
    dac_sdi_out     -- Serial data to DAC
    dac_ld_out      -- Signal for LD pin of DAC

    When strobe_in goes high, data from all channels are latched. They
    are transferred serially to the DAC over the following 10us, and
    all four channels are updated simultaneously at the end.
    
    """
    counter = Signal(intbv(0)[7:])
    state = Signal(t_State.IDLE)

    chanA_control = (0,0,0,0,0,0,0,0)
    chanB_control = (1,0,0,0,0,0,0,0)
    chanC_control = (0,1,0,0,0,0,0,0)
    chanD_control = (1,1,0,0,0,1,0,0)

    CONTROL_LENGTH = 8
    DATA_LENGTH = 16
    CHANA_CONTROL_START = 1
    CHANA_CONTROL_END = CHANA_CONTROL_START+CONTROL_LENGTH
    CHANA_DATA_START = CHANA_CONTROL_END
    CHANA_DATA_END = CHANA_DATA_START+DATA_LENGTH

    CHANB_CONTROL_START = 26
    CHANB_CONTROL_END = CHANB_CONTROL_START+CONTROL_LENGTH
    CHANB_DATA_START = CHANB_CONTROL_END
    CHANB_DATA_END = CHANB_DATA_START+DATA_LENGTH

    CHANC_CONTROL_START = 51
    CHANC_CONTROL_END = CHANC_CONTROL_START+CONTROL_LENGTH
    CHANC_DATA_START = CHANC_CONTROL_END
    CHANC_DATA_END = CHANC_DATA_START+DATA_LENGTH

    CHAND_CONTROL_START = 76
    CHAND_CONTROL_END = CHAND_CONTROL_START+CONTROL_LENGTH
    CHAND_DATA_START = CHAND_CONTROL_END
    CHAND_DATA_END = CHAND_DATA_START+DATA_LENGTH

    chanA_data = Signal(intbv(0)[DATA_LENGTH:])
    chanB_data = Signal(intbv(0)[DATA_LENGTH:])
    chanC_data = Signal(intbv(0)[DATA_LENGTH:])
    chanD_data = Signal(intbv(0)[DATA_LENGTH:])
    
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                chanA_data.next = 0
                chanB_data.next = 0
                chanC_data.next = 0
                chanD_data.next = 0
                dac_ld_out.next = 1
            else:
                if state == t_State.IDLE:
                    if strobe_in:
                        chanA_data.next = chanA_data_in
                        chanB_data.next = chanB_data_in
                        chanC_data.next = chanC_data_in
                        chanD_data.next = chanD_data_in
                        counter.next = 0
                        dac_ld_out.next = 0
                        state.next = t_State.WAIT_0
                elif state == t_State.WAIT_0:
                    if not dac_clock_in:
                        if counter < CHAND_DATA_END-1:
                            if counter == CHANA_DATA_END-1 or counter == CHANB_DATA_END-1 or counter == CHANC_DATA_END-1:
                                dac_ld_out.next = 1
                            counter.next = counter + 1
                            state.next = t_State.WAIT_1
                        else:
                            dac_ld_out.next = 1
                            state.next = t_State.IDLE
                elif state == t_State.WAIT_1:
                    if dac_clock_in:
                        dac_ld_out.next = 0
                        state.next = t_State.WAIT_0
                else:
                    state.next = t_State.IDLE

    @always_comb
    def  comb2():
        dac_sdi_out.next = 1
        if CHANA_CONTROL_START<=counter and counter<CHANA_CONTROL_END:
            dac_sdi_out.next = chanA_control[CHANA_CONTROL_END-1-int(counter)]
        elif CHANA_DATA_START<=counter and counter<CHANA_DATA_END:
            dac_sdi_out.next = chanA_data[CHANA_DATA_END-1-int(counter)]
        elif CHANB_CONTROL_START<=counter and counter<CHANB_CONTROL_END:
            dac_sdi_out.next = chanB_control[CHANB_CONTROL_END-1-int(counter)]
        elif CHANB_DATA_START<=counter and counter<CHANB_DATA_END:
            dac_sdi_out.next = chanB_data[CHANB_DATA_END-1-int(counter)]
        elif CHANC_CONTROL_START<=counter and counter<CHANC_CONTROL_END:
            dac_sdi_out.next = chanC_control[CHANC_CONTROL_END-1-int(counter)]
        elif CHANC_DATA_START<=counter and counter<CHANC_DATA_END:
            dac_sdi_out.next = chanC_data[CHANC_DATA_END-1-int(counter)]
        elif CHAND_CONTROL_START<=counter and counter<CHAND_CONTROL_END:
            dac_sdi_out.next = chanD_control[CHAND_CONTROL_END-1-int(counter)]
        elif CHAND_DATA_START<=counter and counter<CHAND_DATA_END:
            dac_sdi_out.next = chanD_data[CHAND_DATA_END-1-int(counter)]
        else:
            dac_sdi_out.next = 0

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dac_clock_in = Signal(LOW)
    chanA_data_in = Signal(intbv(0)[16:])
    chanB_data_in = Signal(intbv(0)[16:])
    chanC_data_in = Signal(intbv(0)[16:])
    chanD_data_in = Signal(intbv(0)[16:])
    strobe_in = Signal(LOW)
    dac_sdi_out = Signal(LOW)
    dac_ld_out = Signal(LOW)

    toVHDL(Ltc2604Dac, clk=clk, reset=reset, dac_clock_in=dac_clock_in,
                       chanA_data_in=chanA_data_in,
                       chanB_data_in=chanB_data_in,
                       chanC_data_in=chanC_data_in,
                       chanD_data_in=chanD_data_in, strobe_in=strobe_in,
                       dac_sdi_out=dac_sdi_out, dac_ld_out=dac_ld_out)
