# FILE:
#   DualPortRamRw.py
#
# DESCRIPTION:
#   Dual ported memory block. MyHDL wrapper for VHDL component.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   12-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *

LOW, HIGH = bool(0), bool(1)

VHDL_CODE = \
"""
dual_port_ram : entity work.DualPortRamRw_e(Behavioral)
    generic map(ADDR_WIDTH => %(addr_width)s, DATA_WIDTH => %(data_width)s)
    port map (
    clockA => %(clockA)s, enableA => %(enableA)s, wr_enableA => %(wr_enableA)s,
    addressA => %(addressA)s, rd_dataA => %(rd_dataA)s, wr_dataA => %(wr_dataA)s,
    clockB => %(clockB)s, enableB => %(enableB)s, wr_enableB => %(wr_enableB)s,
    addressB => %(addressB)s, rd_dataB => %(rd_dataB)s, wr_dataB => %(wr_dataB)s
    );
"""

def DualPortRamRw(clockA, enableA, wr_enableA, addressA, rd_dataA, wr_dataA,
                  clockB, enableB, wr_enableB, addressB, rd_dataB, wr_dataB,
                  addr_width, data_width):
    """Dual ported RAM
    clockA          -- clock for port A
    enableA         -- enable for port A
    wr_enableA      -- write enable for port A
    addressA        -- address for port A
    rd_dataA        -- read data for port A
    wr_dataA        -- write data for port A
    clockB          -- clock for port B
    enableB         -- enable for port B
    wr_enableB      -- write enable for port B
    addressB        -- address for port B
    rd_dataB        -- read data for port B
    wr_dataB        -- write data for port B
    addr_width      -- width of address (both ports)
    data_width      -- width of data (both ports)

    The Python code is a behavioral simulation which is replaced by VHDL code
    during implementation.
    """

    __vhdl__ = VHDL_CODE
    rd_dataA.driven = "wire"
    rd_dataB.driven = "wire"

    RAM = {}
    maxAddress = 2**addr_width
    maxData = 2**data_width

    @instance
    def portA():
        while True:
            yield clockA.posedge
            if enableA:
                a = addressA % maxAddress
                if wr_enableA:
                    RAM[a] = wr_dataA % maxData
                rd_dataA.next = RAM.get(a,0)

    @instance
    def portB():
        while True:
            yield clockB.posedge
            if enableB:
                b = addressB % maxAddress
                if wr_enableB:
                    RAM[b] = wr_dataB % maxData
                rd_dataB.next = RAM.get(b,0)

    return portA, portB
