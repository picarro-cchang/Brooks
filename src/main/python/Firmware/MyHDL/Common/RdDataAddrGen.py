#!/usr/bin/python
#
# FILE:
#   RdDataAddrGen.py
#
# DESCRIPTION:
#   Address generator for ringdown data waveform
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   15-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH

LOW, HIGH = bool(0), bool(1)

def  RdDataAddrGen(clk,addr_reset,enable,addr_div,
                    data_addr,data_we,adc_clk):
    # The ringdown data address generator is involved in the storage of
    #  ringdown ADC data. The 50 MHz clock is divided by two to give
    #  adc_clk, and this is further divided by (addr_div+1) to give
    #  the rate at which the data_addr is incremented.
    # The value of data_addr is reset in response to addr_reset
    #  and increments while enable is high. The reset value is actually
    #  one less than zero, so that the first clock pulse that occrus
    #  when enable goes high writes data to location zero.
    # The data_we signal goes high for one cycle whenever the data
    #  address is incremented.

    mod_data_addr = 1<<DATA_BANK_ADDR_WIDTH
    max_data_addr = mod_data_addr-1
    DIVIDER_WIDTH = 5
    mod_divider = 1<<DIVIDER_WIDTH
    divider = Signal(intbv(0)[DIVIDER_WIDTH:])  # ADC does not work below 1MHz, so
                                                # cannot divide by more than 25
    data_addr_i = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    adc_clk_i = Signal(LOW)

    @always(clk.posedge)
    def  seq():
        data_we.next = 0
        adc_clk_i.next = not adc_clk_i
        if addr_reset:
            divider.next = addr_div
            data_addr_i.next = max_data_addr
        elif enable and adc_clk_i:
            if divider == addr_div:
                divider.next = 0
                data_addr_i.next = (data_addr_i + 1) % mod_data_addr
                data_we.next = 1
            else:
                divider.next = (divider.next+1) % mod_divider

    @always_comb
    def  comb():
        adc_clk.next = adc_clk_i
        data_addr.next = data_addr_i

    return instances()

if __name__ == "__main__":
    # Define the pinouts for VHDL synthesis
    clk, addr_reset, enable = [Signal(LOW) for i in range(3)]
    addr_div = Signal(intbv(0)[5:])
    data_addr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    data_we, adc_clk = [Signal(LOW) for i in range(2)]

    toVHDL(RdDataAddrGen, clk=clk, addr_reset=addr_reset,
                          enable=enable, addr_div=addr_div,
                          data_addr=data_addr, data_we=data_we,
                          adc_clk=adc_clk)
