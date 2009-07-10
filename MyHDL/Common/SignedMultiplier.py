#!/usr/bin/python
#
# FILE:
#   SignedMultiplier.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   02-Jul-2008  sze  Initial version.
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_MASK
from myhdl import *

LOW, HIGH = bool(0), bool(1)

VHDL_CODE = \
"""
unsigned_mult18x18 : entity work.UnsignedMult18x18_e(Behavioral)
    port map (
    A => %(a)s, B => %(b)s, P => %(p)s
    );
"""
def Multiplier(p,a,b):
    # Multiplies a and b to yield p
    __vhdl__ = VHDL_CODE
    p.driven = "wire"

    @always_comb
    def logic():
        p.next = int(a)*int(b)
    return instances()

def SignedMultiplier(p,a,b,overflow,MULT_WIDTH=18):
    # Multiplies a and b to yield p, where each of a, b and p is a
    #  twos complement number representing a number between -1.0 and
    #  (slightly less than) 1.0. Overflow is set if result does not fit.
    #
    aLen = len(a)
    bLen = len(b)
    pLen = len(p)
    assert aLen <= MULT_WIDTH and bLen <= MULT_WIDTH and pLen <= 2*MULT_WIDTH,"Invalid widths for arguments"
    amag = Signal(intbv(0)[MULT_WIDTH:])
    bmag = Signal(intbv(0)[MULT_WIDTH:])
    pmag = Signal(intbv(0)[2*MULT_WIDTH:])

    pSign = Signal(LOW)
    in_mod = 1<<len(a)
    out_mod = 1<<pLen
    mult_inst = Multiplier(pmag,amag,bmag)

    @always_comb
    def input():
        pSign_v = LOW
        if a.signed()<0:
            pSign_v = not pSign_v
            amag.next[MULT_WIDTH:MULT_WIDTH-aLen] = -a.signed()
        else:
            amag.next[MULT_WIDTH:MULT_WIDTH-aLen] = a
        if b.signed()<0:
            pSign_v = not pSign_v
            bmag.next[MULT_WIDTH:MULT_WIDTH-bLen] = -b.signed()
        else:
            bmag.next[MULT_WIDTH:MULT_WIDTH-bLen] = b
        pSign.next = pSign_v

    @always_comb
    def output():
        p_v = intbv(0)[pLen:]
        p_v[:] = pmag[2*MULT_WIDTH-1:2*MULT_WIDTH-1-pLen]
        overflow.next = p_v.signed() < 0
        if pSign:
            p.next = (-p_v) % out_mod
        else:
            p.next = p_v

    return instances()

def SignedMultiplierHarness(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,product,overflow,map_base):
    """ Tests operation of signed multiplier
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    adc_clk             -- ADC clock input. Data are valid on the falling edge
    value               -- output with ringdown waveform value
    map_base            -- Base of FPGA map for this block
    """

    a_addr = map_base + 0
    b_addr = map_base + 1
    p_addr = map_base + 2
    o_addr = map_base + 3

    a = Signal(intbv(0)[16:])
    b = Signal(intbv(0)[16:])
    p = Signal(intbv(0)[16:])
    o = Signal(LOW)

    sm = SignedMultiplier(p,a,b,o)

    @instance
    def logic():
        # FPGA registers stored in variables
        a_v = intbv(0)[16:]
        b_v = intbv(0)[16:]
        p_v = intbv(0)[16:]
        o_v = intbv(0)[16:]

        while True:
            yield clk.posedge, reset.posedge
            if reset:
                a_v[:] = 0
                b_v[:] = 0
                p_v[:] = 0
                o_v[:] = 0
            else:
                # Handle register access
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if dsp_addr[EMIF_ADDR_WIDTH-1:]   == a_addr:
                        if dsp_wr: a_v[:]=dsp_data_out
                        dsp_data_in.next = a_v
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == b_addr:
                        if dsp_wr: b_v[:]=dsp_data_out
                        dsp_data_in.next = b_v
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == p_addr:
                        dsp_data_in.next = p_v
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == o_addr:
                        dsp_data_in.next = o_v
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                # Actually do stuff, changing registers if necessary

                # Notice that we are expanding the inputs from 16 bits to 18 bits,
                #  obtaining a signed 18 bit product and then reducing the result to
                #  16 bits. Since the signed integer a_v represents a_v/32768.0 and b_v
                #  represents b_v/32768.0, the product as a signed 18-bit integer is
                # int((a_v/32768.0)*(b_v/32768.0)*(262144.0)). Reducing this to 16 bits
                # yields int((a_v/32768.0)*(b_v/32768.0)*(131072.0))//4. This is NOT
                # the same as int((a_v/32768.0)*(b_v/32768.0)*(32768.0)).

                a.next = a_v
                b.next = b_v
                p_v[:] = p
                o_v[:] = o
                product.next = p
                overflow.next = o

    return instances()

if __name__ == "__main__":
    clk, reset, overflow, dsp_wr = [Signal(LOW) for i in range(4)]
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out, dsp_data_in, product = [Signal(intbv(0)[16:]) for i in range(3)]
    toVHDL(SignedMultiplierHarness, clk=clk, reset=reset, dsp_addr=dsp_addr, dsp_data_out=dsp_data_out,
            dsp_data_in=dsp_data_in, dsp_wr=dsp_wr, product=product, overflow=overflow, map_base=0)
