#!/usr/bin/python
#
# FILE:
#   LaserDac.py
#
# DESCRIPTION:
#   Driver for laser current DACs (DAC8552)
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   31-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH

LOW, HIGH = bool(0), bool(1)
t_State = enum("IDLE","WAIT_1","WAIT_0")

def  LaserDac(clk,reset,dac_clock_in,chanA_data_in,chanB_data_in,strobe_in,
               dac_sync_out,dac_din_out):
    # The DAC8552 is a dual 16-bit DAC with a serial interface. The
    #  dac clock runs at 50 times the strobe rate, which is 100ksps.
    # When the strobe signal goes high (for one clk cycle), chanA is
    #  first written to the DAC buffer, followed by chanB. After both
    #  are written, the data are sent simultaneously to the analog output.

    counter = Signal(intbv(0)[6:])
    state = Signal(t_State.IDLE)

    chanA_control = (0,0,0,0,0,0,0,0)
    chanB_control = (0,0,1,0,1,1,0,0)

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

    chanA_data = Signal(intbv(0)[DATA_LENGTH:])
    chanB_data = Signal(intbv(0)[DATA_LENGTH:])
    dac_din = Signal(LOW)
    
    @instance
    def  logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                counter.next = 0
                dac_sync_out.next = 0
                dac_din_out.next = 0
            else:
                if state == t_State.IDLE:
                    dac_sync_out.next = 0
                    if strobe_in:
                        chanA_data.next = chanA_data_in
                        chanB_data.next = chanB_data_in
                        counter.next = 0
                        dac_sync_out.next = 1
                        state.next = t_State.WAIT_1
                elif state == t_State.WAIT_1:
                    if dac_clock_in:
                        if counter < 49:
                            if counter == 24:
                                dac_sync_out.next = 0
                            counter.next = counter + 1
                            state.next = t_State.WAIT_0
                        else:
                            dac_sync_out.next = 0
                            state.next = t_State.IDLE
                elif state == t_State.WAIT_0:
                    if not dac_clock_in:
                        dac_sync_out.next = 1
                        state.next = t_State.WAIT_1
                else:
                    state.next = t_State.IDLE
                # Register the serial data 
                dac_din_out.next = dac_din

    @always_comb
    def  comb2():
        if CHANA_CONTROL_START<=counter and counter<CHANA_CONTROL_END:
            dac_din.next = chanA_control[CHANA_CONTROL_END-1-int(counter)]
        elif CHANA_DATA_START<=counter and counter<CHANA_DATA_END:
            dac_din.next = chanA_data[CHANA_DATA_END-1-int(counter)]
        elif CHANB_CONTROL_START<=counter and counter<CHANB_CONTROL_END:
            dac_din.next = chanB_control[CHANB_CONTROL_END-1-int(counter)]
        elif CHANB_DATA_START<=counter and counter<CHANB_DATA_END:
            dac_din.next = chanB_data[CHANB_DATA_END-1-int(counter)]
        else:
            dac_din.next = 0

    return instances()

if __name__ == "__main__":
    # Define the pinouts for VHDL synthesis
    clk, reset, dac_clock_in, strobe_in = [Signal(LOW) for i in range(4)]
    dac_sync_out, dac_din_out = [Signal(LOW) for i in range(2)]
    chanA_data_in = Signal(intbv(0)[16:])
    chanB_data_in = Signal(intbv(0)[16:])

    toVHDL(LaserDac, clk=clk, reset=reset,
                     dac_clock_in=dac_clock_in,
                     chanA_data_in=chanA_data_in,
                     chanB_data_in=chanB_data_in,
                     strobe_in=strobe_in,
                     dac_sync_out=dac_sync_out,
                     dac_din_out=dac_din_out)
