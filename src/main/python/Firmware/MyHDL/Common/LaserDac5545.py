#!/usr/bin/python
#
# FILE:
#   LaserDac5545.py
#
# DESCRIPTION:
#   Driver for laser current DACs (AD5545)
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   1-Mar-2012  sze  Initial version.
#
#  Copyright (c) 2012 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH

LOW, HIGH = bool(0), bool(1)
t_State = enum("IDLE","WAIT_1","WAIT_0")

def  LaserDac(clk,reset,dac_clock_in,chanA_data_in,chanB_data_in,strobe_in,
               dac_cs_out,dac_din_out):
    # The DAC5545 is a dual 16-bit DAC with a serial interface. The
    #  dac clock runs at 50 times the strobe rate, which is 100ksps.
    # When the strobe signal goes high (for one clk cycle), chanA is
    #  first written to the DAC buffer, followed by chanB.
    # Outputs change on falling edge of DAC clock, so they are stable 
    #  on the positive clock edge. 
    # A counter is used for sequencing. When idle, the counter is reset 
    #  to zero and CS is low. The sequence of events is:

    # 1. Strobe arrives
    # 2. Wait for next negative clock edge, set counter to one
    # 3. Counts 1, 2: Send A1, A0
    # 4. Counts 3, 4, ..., 18:  Send D15, D14, ..., D0
    # 5. CS goes high (this is inverted before driving hardware) during 
    #     counts 1 through 18
    # Channel B is sent from a count of 21 through 38
    # 6. Counts 21, 22: Send A1, A0
    # 7. Counts 23, 24, ..., 38:  Send D15, D14, ..., D0
    # 8. CS goes high (this is inverted before driving hardware) during 
    #     counts 21 through 38
    
    counter = Signal(intbv(0)[6:])
    state = Signal(t_State.IDLE)
    dac_cs = Signal(LOW)
    dac_data = Signal(LOW)
    
    # These control bits are written in REVERSE ORDER, since the control[0] 
    #  is the LSB and the bits go down the wire MSB first
    chanA_control = (1,0)  
    chanB_control = (0,1)

    CONTROL_LENGTH = 2
    DATA_LENGTH = 16
    CHANA_CONTROL_START = 1
    CHANA_CONTROL_END = CHANA_CONTROL_START+CONTROL_LENGTH
    CHANA_DATA_START = CHANA_CONTROL_END
    CHANA_DATA_END = CHANA_DATA_START+DATA_LENGTH

    CHANB_CONTROL_START = 21
    CHANB_CONTROL_END = CHANB_CONTROL_START+CONTROL_LENGTH
    CHANB_DATA_START = CHANB_CONTROL_END
    CHANB_DATA_END = CHANB_DATA_START+DATA_LENGTH

    chanA_data = Signal(intbv(0)[DATA_LENGTH:])
    chanB_data = Signal(intbv(0)[DATA_LENGTH:])

    @instance
    def  logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                counter.next = 0
                dac_cs_out.next = 0
                dac_din_out.next = 0
            else:
                dac_cs_out.next = dac_cs
                dac_din_out.next = dac_data
                if state == t_State.IDLE:
                    counter.next = 0
                    if strobe_in:
                        chanA_data.next = chanA_data_in
                        chanB_data.next = chanB_data_in
                        state.next = t_State.WAIT_1
                elif state == t_State.WAIT_1:
                    if dac_clock_in:
                        state.next = t_State.WAIT_0
                elif state == t_State.WAIT_0:
                    if not dac_clock_in:
                        if counter == CHANB_DATA_END-1:
                            state.next = t_State.IDLE
                            counter.next = 0
                        else:
                            state.next = t_State.WAIT_1
                            counter.next = counter + 1
                else:
                    state.next = t_State.IDLE

    @always_comb
    def  comb2():
        if CHANA_CONTROL_START<=counter and counter<CHANA_CONTROL_END:
            dac_data.next = chanA_control[CHANA_CONTROL_END-1-int(counter)]
            dac_cs.next = 1
        elif CHANA_DATA_START<=counter and counter<CHANA_DATA_END:
            dac_data.next = chanA_data[CHANA_DATA_END-1-int(counter)]
            dac_cs.next = 1
        elif CHANB_CONTROL_START<=counter and counter<CHANB_CONTROL_END:
            dac_data.next = chanB_control[CHANB_CONTROL_END-1-int(counter)]
            dac_cs.next = 1
        elif CHANB_DATA_START<=counter and counter<CHANB_DATA_END:
            dac_data.next = chanB_data[CHANB_DATA_END-1-int(counter)]
            dac_cs.next = 1
        else:
            dac_data.next = 0
            dac_cs.next = 0

    return instances()

if __name__ == "__main__":
    # Define the pinouts for VHDL synthesis
    clk, reset, dac_clock_in, strobe_in = [Signal(LOW) for i in range(4)]
    dac_cs_out, dac_din_out = [Signal(LOW) for i in range(2)]
    chanA_data_in = Signal(intbv(0)[16:])
    chanB_data_in = Signal(intbv(0)[16:])

    toVHDL(LaserDac, clk=clk, reset=reset,
                     dac_clock_in=dac_clock_in,
                     chanA_data_in=chanA_data_in,
                     chanB_data_in=chanB_data_in,
                     strobe_in=strobe_in,
                     dac_cs_out=dac_cs_out,
                     dac_din_out=dac_din_out)
