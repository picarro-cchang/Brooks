#!/usr/bin/python
#
# FILE:
#   UnsignedMultiplier.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   22-Jul-2009  sze  Initial version, using Xilinx block multiplier
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_MASK
from MyHDL.Common.SignedMultiplier import SignedMultiplier
from myhdl import *

def UnsignedMultiplier(p,a,b):
    # Multiplies a and b to yield p
    # Each of a and b is a 17 bit unsigned quantity
    #  p is a 34 bit unsigned quantity

    a_s = Signal(intbv(0,min=-0x20000,max=0x20000))
    b_s = Signal(intbv(0,min=-0x20000,max=0x20000))
    p_s = Signal(intbv(0,min=-0x800000000,max=0x800000000))

    sm = SignedMultiplier(p=p_s,a=a_s,b=b_s)
        
    @always_comb
    def comb():
        a_s.next[17:] = a
        a_s.next[17] = 0
        b_s.next[17:] = b
        b_s.next[17] = 0
        p.next = p_s[34:]
        
    return instances()