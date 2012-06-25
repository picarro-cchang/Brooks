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
#   22-Jul-2009  sze  Initial version, using Xilinx block multiplier
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_MASK
from myhdl import *

VHDL_CODE = \
"""
signed_mult18x18_%(instance_count)s : entity work.SignedMult18x18_e(Behavioral)
    port map (
    A => %(a)s, B => %(b)s, P => %(p)s
    );
"""

instance_count = 0

def SignedMultiplier(p,a,b):
    global instance_count
    # Multiplies a and b to yield p
    instance_count += 1
    __vhdl__ = VHDL_CODE
    p.driven = "wire"

    @always_comb
    def logic():
        a_s = intbv(a.signed(),min=-0x40000,max=0x40000)
        b_s = intbv(b.signed(),min=-0x40000,max=0x40000)
        p.next = a_s * b_s
    return instances()
