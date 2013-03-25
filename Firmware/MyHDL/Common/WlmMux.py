#!/usr/bin/python
#
# FILE:
#   WlmMux.py
#
# DESCRIPTION:
#   Combinational logic multiplexer for selecting between the WLM simulator and the WLM ADC reader
#
# SEE ALSO:
#
# HISTORY:
#   17-Sep-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK

LOW, HIGH = bool(0), bool(1)
def WlmMux(sim_actual_in,eta1_sim_in,ref1_sim_in,eta2_sim_in,
           ref2_sim_in,data_available_sim_in,eta1_actual_in,
           ref1_actual_in,eta2_actual_in,ref2_actual_in,
           data_available_actual_in,eta1_out,ref1_out,eta2_out,ref2_out,
           data_available_out):
    """
    Parameters:
    sim_actual_in -- 0 to select simulator, 1 to select actual WLM
    eta1_sim_in   -- Etalon 1 photocurrent from simulator
    ref1_sim_in   -- Reference 1 photocurrent from simulator
    eta2_sim_in   -- Etalon 2 photocurrent from simulator
    ref2_sim_in   -- Reference 2 photocurrent from simulator
    data_available_sim_in -- Data available strobe from simulator
    eta1_actual_in -- Etalon 1 photocurrent from actual WLM
    ref1_actual_in -- Reference 1 photocurrent from actual WLM
    eta2_actual_in -- Etalon 2 photocurrent from actual WLM
    ref2_actual_in -- Reference 2 photocurrent from actual WLM
    data_available_actual_in -- Data available strobe from actual WLM
    eta1_out -- Selected etalon 1 photocurrent
    ref1_out -- Selected reference 1 photocurrent
    eta2_out -- Selected etalon 2 photocurrent
    ref2_out -- Selected reference 2 photocurrent
    data_available_out -- Selected data available strobe

    """
    @always_comb
    def logic():
        if sim_actual_in:
            eta1_out.next = eta1_actual_in
            ref1_out.next = ref1_actual_in
            eta2_out.next = eta2_actual_in
            ref2_out.next = ref2_actual_in
            data_available_out.next = data_available_actual_in
        else:
            eta1_out.next = eta1_sim_in
            ref1_out.next = ref1_sim_in
            eta2_out.next = eta2_sim_in
            ref2_out.next = ref2_sim_in
            data_available_out.next = data_available_sim_in
            
    return instances()

if __name__ == "__main__":
    sim_actual_in = Signal(LOW)
    eta1_sim_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_sim_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_sim_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_sim_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    data_available_sim_in = Signal(LOW)
    eta1_actual_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_actual_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_actual_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_actual_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    data_available_actual_in = Signal(LOW)
    eta1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    data_available_out = Signal(LOW)

    toVHDL(WlmMux, sim_actual_in=sim_actual_in, eta1_sim_in=eta1_sim_in,
                   ref1_sim_in=ref1_sim_in, eta2_sim_in=eta2_sim_in,
                   ref2_sim_in=ref2_sim_in,
                   data_available_sim_in=data_available_sim_in,
                   eta1_actual_in=eta1_actual_in,
                   ref1_actual_in=ref1_actual_in,
                   eta2_actual_in=eta2_actual_in,
                   ref2_actual_in=ref2_actual_in,
                   data_available_actual_in=data_available_actual_in,
                   eta1_out=eta1_out, ref1_out=ref1_out,
                   eta2_out=eta2_out, ref2_out=ref2_out,
                   data_available_out=data_available_out)
