#!/usr/bin/python
#
# FILE:
#   Scaler.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   16-Aug-2010  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_SCALER

from MyHDL.Common.UnsignedMultiplier import UnsignedMultiplier
from Host.autogen.interface import SCALER_SCALE1

LOW, HIGH = bool(0), bool(1)
def Scaler(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,x1_in,
           y1_out,map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    x1_in               -- input 1 (PZT from waveform generator)
    y1_out              -- output 1 (PZT to DAC)
    map_base

    Registers:
    SCALER_SCALE1       -- Specifies number to multiply input 1 by to give output 1
    
    Multiplies the u16 quantity x1_in by a scale factor (stored in a register) to give
    the value of y1_out
    """
    scaler_scale1_addr = map_base + SCALER_SCALE1
    scale1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    
    a = Signal(intbv(0)[17:])
    b = Signal(intbv(0)[17:])
    p = Signal(intbv(0)[34:])
    mult = UnsignedMultiplier(p=p,a=a,b=b)

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                scale1.next = intbv(40000)[16:]
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == scaler_scale1_addr: # rw
                        if dsp_wr: scale1.next = dsp_data_out
                        dsp_data_in.next = scale1
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                a.next = concat(x1_in,intbv(0)[1:])
                b.next = concat(scale1,intbv(0)[1:])
                y1_out.next = p[34:18]
    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    x1_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    y1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    map_base = FPGA_SCALER

    toVHDL(Scaler, clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, x1_in=x1_in, y1_out=y1_out,
                   map_base=map_base)
