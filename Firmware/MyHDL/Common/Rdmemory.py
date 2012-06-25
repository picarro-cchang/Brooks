#!/usr/bin/python
#
# FILE:
#   Rdmemory.py
#
# DESCRIPTION:
#   Dual ported memory for storing ringdown information
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   12-May-2009  sze  Initial version.
#   22-Jul-2009  sze  Moved parameter addresses to 0x3000 and 0x7000.
#                     Allow DSP read-only access to both metadata and data memory as 32-bit words 
#                      (MSW = metadata, LSW = data) in blocks starting at addresses 0x2000 and 0x6000. 
#                      This speeds up DMA but only low order 16 bits of the data are accessible in this way. 
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from DualPortRamRw import DualPortRamRw
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH, META_BANK_ADDR_WIDTH, PARAM_BANK_ADDR_WIDTH
from Host.autogen.interface import RDMEM_DATA_WIDTH, RDMEM_META_WIDTH, RDMEM_PARAM_WIDTH, RDMEM_RESERVED_BANK_ADDR_WIDTH
LOW, HIGH = bool(0), bool(1)

def  Rdmemory(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
               bank,data_addr,data,wr_data,data_we,
               meta_addr,meta,wr_meta,meta_we,
               param_addr,param,wr_param,param_we):
    # Ringdown memory appears to the DSP as two banks, each of 0x4000
    #  32-bit words. Each bank is divided into three regions, the
    #  "data", "metadata" and "parameters".
    # The base address of ringdown memory is at interface.RDMEM_ADDRESS
    # The following are word offsets (which must be multiplied by 4 to
    #  give byte offsets) relative to the base address
    # 0x0       Data area, bank 0
    # 0x1000    Metadata area, bank 0
    # 0x2000    Read-only access of bank 0 of both data (MSW) and metadata (LSW)
    # 0x3000    Parameter area, bank 0
    # 0x4000    Data area, bank 1
    # 0x5000    Metadata area, bank 1
    # 0x6000    Read-only access of bank 1 of both data (MSW) and metadata (LSW)
    # 0x7000    Parameter area, bank 1

    # From the FPGA side, the memory is write-only and organized as
    #  words of width RDMEM_DATA_WIDTH, RDMEM_META_WIDTH and
    #  RDMEM_PARAM_WIDTH. In order to write, the info is placed on
    #  wr_data, wr_meta or wr_param and the appropriate write enable
    #  pin is raised high during a positive edge of the clock.
    # The contents of the memory are continuously available on data,
    #  meta and param.

    # Following are sizes in words (16/18 bit on FPGA side, 32 bit on DSP side)
    DATA_BANK_SIZE = 2**DATA_BANK_ADDR_WIDTH
    META_BANK_SIZE = 2**META_BANK_ADDR_WIDTH
    PARAM_BANK_SIZE = 2**PARAM_BANK_ADDR_WIDTH

    enA_data = Signal(LOW)
    enB_data = Signal(HIGH)
    wr_enable = Signal(LOW)
    
    data_addrA = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH+1:])
    data_addrB = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH+1:])
    wr_dataA = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
    rd_dataA = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
    sel_data = LOW

    data_mem = DualPortRamRw(clockA=clk, enableA=enA_data, wr_enableA=wr_enable,
                            addressA=data_addrA, rd_dataA=rd_dataA,
                            wr_dataA=wr_dataA,
                            clockB=clk, enableB=enB_data, wr_enableB=data_we,
                            addressB=data_addrB, rd_dataB=data,
                            wr_dataB=wr_data,
                            addr_width=DATA_BANK_ADDR_WIDTH+1,
                            data_width=RDMEM_DATA_WIDTH)

    enA_meta = Signal(LOW)
    enB_meta = Signal(HIGH)
    meta_addrA = Signal(intbv(0)[META_BANK_ADDR_WIDTH+1:])
    meta_addrB = Signal(intbv(0)[META_BANK_ADDR_WIDTH+1:])
    wr_metaA = Signal(intbv(0)[RDMEM_META_WIDTH:])
    rd_metaA = Signal(intbv(0)[RDMEM_META_WIDTH:])
    sel_meta = LOW

    meta_mem = DualPortRamRw(clockA=clk, enableA=enA_meta, wr_enableA=wr_enable,
                            addressA=meta_addrA, rd_dataA=rd_metaA,
                            wr_dataA=wr_metaA,
                            clockB=clk, enableB=enB_meta, wr_enableB=meta_we,
                            addressB=meta_addrB, rd_dataB=meta,
                            wr_dataB=wr_meta,
                            addr_width=META_BANK_ADDR_WIDTH+1,
                            data_width=RDMEM_META_WIDTH)

    enA_param = Signal(LOW)
    enB_param = Signal(HIGH)
    param_addrA = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH+1:])
    param_addrB = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH+1:])
    wr_paramA = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    rd_paramA = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    sel_param = LOW

    param_mem = DualPortRamRw(clockA=clk, enableA=enA_param, wr_enableA=wr_enable,
                            addressA=param_addrA, rd_dataA=rd_paramA,
                            wr_dataA=wr_paramA,
                            clockB=clk, enableB=enB_param, wr_enableB=param_we,
                            addressB=param_addrB, rd_dataB=param,
                            wr_dataB=wr_param,
                            addr_width=PARAM_BANK_ADDR_WIDTH+1,
                            data_width=RDMEM_PARAM_WIDTH)

    @always_comb
    def  comb():
        # Selects both data and metadata for read-only access
        sel_data_and_metadata = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 6 or dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 2
        wr_enable.next = dsp_wr and not sel_data_and_metadata
        
        enB_data.next = 1
        sel_data = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 4 or dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 0 or sel_data_and_metadata
        data_addrA.next[DATA_BANK_ADDR_WIDTH:] = dsp_addr[DATA_BANK_ADDR_WIDTH:]
        # The bank is selected (on the DSP side) using dsp_addr[14]
        data_addrA.next[DATA_BANK_ADDR_WIDTH] = dsp_addr[RDMEM_RESERVED_BANK_ADDR_WIDTH+2]
        enA_data.next = sel_data
        # Compute the address from the FPGA side
        data_addrB.next[DATA_BANK_ADDR_WIDTH:] = data_addr
        data_addrB.next[DATA_BANK_ADDR_WIDTH] = bank
        # Handle data write from DSP
        wr_dataA.next = dsp_data_out[RDMEM_DATA_WIDTH:]

        enB_meta.next = 1
        sel_meta = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 5 or dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 1 or sel_data_and_metadata
        meta_addrA.next[META_BANK_ADDR_WIDTH:] = dsp_addr[META_BANK_ADDR_WIDTH:]
        # The bank is selected (on the DSP side) using dsp_addr[14]
        meta_addrA.next[META_BANK_ADDR_WIDTH] = dsp_addr[RDMEM_RESERVED_BANK_ADDR_WIDTH+2]
        enA_meta.next = sel_meta
        # Compute the address from the FPGA side
        meta_addrB.next[META_BANK_ADDR_WIDTH:] = meta_addr
        meta_addrB.next[META_BANK_ADDR_WIDTH] = bank
        # Handle data write from DSP
        wr_metaA.next = dsp_data_out[RDMEM_META_WIDTH:]

        enB_param.next = 1
        sel_param = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 7 or dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 3
        param_addrA.next[PARAM_BANK_ADDR_WIDTH:] = dsp_addr[PARAM_BANK_ADDR_WIDTH:]
        # The bank is selected (on the DSP side) using dsp_addr[14]
        param_addrA.next[PARAM_BANK_ADDR_WIDTH] = dsp_addr[RDMEM_RESERVED_BANK_ADDR_WIDTH+2]
        enA_param.next = sel_param
        # Compute the address from the FPGA side
        param_addrB.next[PARAM_BANK_ADDR_WIDTH:] = param_addr
        param_addrB.next[PARAM_BANK_ADDR_WIDTH] = bank
        # Handle data write from DSP
        wr_paramA.next = dsp_data_out[RDMEM_PARAM_WIDTH:]

        if sel_data_and_metadata:
            dsp_data_in.next[FPGA_REG_WIDTH:] = rd_dataA[FPGA_REG_WIDTH:]
            dsp_data_in.next[EMIF_DATA_WIDTH:FPGA_REG_WIDTH] = rd_metaA[FPGA_REG_WIDTH:]
        elif sel_data:
            dsp_data_in.next = rd_dataA[RDMEM_DATA_WIDTH:]
        elif sel_meta:
            dsp_data_in.next = rd_metaA[RDMEM_META_WIDTH:]
        elif sel_param:
            dsp_data_in.next = rd_paramA[RDMEM_PARAM_WIDTH:]
        else:
            dsp_data_in.next = 0
            
    return instances()

if __name__ == "__main__":
    # Define the pinouts for VHDL synthesis
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    clk, reset, dsp_wr = [Signal(LOW) for i in range(3)]
    bank, data_we, metadata_we, param_we = [Signal(LOW) for i in range(4)]
    data_addr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
    wr_data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
    meta_addr = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
    meta = Signal(intbv(0)[RDMEM_META_WIDTH:])
    wr_meta = Signal(intbv(0)[RDMEM_META_WIDTH:])
    param_addr = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH:])
    param = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    wr_param = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    data_we, meta_we, param_we = [Signal(LOW) for i in range(3)]

    toVHDL(Rdmemory, clk=clk, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                     dsp_wr=dsp_wr, bank=bank,
                     data_addr=data_addr, data=data, wr_data=wr_data, data_we=data_we,
                     meta_addr=meta_addr, meta=meta, wr_meta=wr_meta, meta_we=meta_we,
                     param_addr=param_addr, param=param, wr_param=wr_param, param_we=param_we)
