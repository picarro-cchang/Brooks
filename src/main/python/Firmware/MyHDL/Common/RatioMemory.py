#!/usr/bin/python
#
# FILE:
#   RatioMemory.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   01-Aug-2017  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import RATIO_MEM_ADDR_WIDTH
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_RATIOMEMORY

from Host.autogen.interface import RATIOMEMORY_CS
from Host.autogen.interface import RATIOMEMORY_RATIO_ADDRESS
from Host.autogen.interface import RATIOMEMORY_DIVISOR

from Host.autogen.interface import RATIOMEMORY_CS_RUN_B, RATIOMEMORY_CS_RUN_W
from Host.autogen.interface import RATIOMEMORY_CS_CONT_B, RATIOMEMORY_CS_CONT_W
from Host.autogen.interface import RATIOMEMORY_CS_ACQUIRE_B, RATIOMEMORY_CS_ACQUIRE_W
from Host.autogen.interface import RATIOMEMORY_CS_DONE_B, RATIOMEMORY_CS_DONE_W


LOW, HIGH = bool(0), bool(1)
MAX_ADDR = (1 << RATIO_MEM_ADDR_WIDTH) - 1


def RatioMemory(clk, reset, dsp_addr, dsp_data_out, dsp_data_in, dsp_wr,
                strobe_in, wlm_ratio_we_out, wlm_ratio_addr_out,
                map_base):
    """
    Parameters:
    clk
    reset
    dsp_addr
    dsp_data_out
    dsp_data_in
    dsp_wr
    strobe_in
    wlm_ratio_we_out
    wlm_ratio_addr_out
    map_base

    Registers:
    RATIOMEMORY_CS
    RATIOMEMORY_RATIO_ADDRESS
    RATIOMEMORY_DIVISOR

    Fields in RATIOMEMORY_CS:
    RATIOMEMORY_CS_RUN
    RATIOMEMORY_CS_CONT
    RATIOMEMORY_CS_ACQUIRE
    RATIOMEMORY_CS_DONE
    """
    ratiomemory_cs_addr = map_base + RATIOMEMORY_CS
    ratiomemory_ratio_address_addr = map_base + RATIOMEMORY_RATIO_ADDRESS
    ratiomemory_divisor_addr = map_base + RATIOMEMORY_DIVISOR
    cs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio_address = Signal(intbv(0)[FPGA_REG_WIDTH:])
    divisor = Signal(intbv(0)[FPGA_REG_WIDTH:])

    sample_counter = Signal(intbv(0)[RATIO_MEM_ADDR_WIDTH:])
    divisor_counter = Signal(intbv(0)[FPGA_REG_WIDTH:])
    strobe_prev = Signal(LOW)
    acq_strobe = Signal(LOW)

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                cs.next = 0
                ratio_address.next = 0
                divisor.next = 0
                sample_counter.next = 0
                divisor_counter.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH - 1] == FPGA_REG_MASK:
                    if False:
                        pass
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == ratiomemory_cs_addr:  # rw
                        if dsp_wr:
                            cs.next = dsp_data_out
                        dsp_data_in.next = cs
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == ratiomemory_ratio_address_addr:  # r
                        dsp_data_in.next = ratio_address
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == ratiomemory_divisor_addr:  # rw
                        if dsp_wr:
                            divisor.next = dsp_data_out
                        dsp_data_in.next = divisor
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                strobe_prev.next = strobe_in
                acq_strobe.next = strobe_in and not strobe_prev

                if cs[RATIOMEMORY_CS_RUN_B]:
                    wlm_ratio_we_out.next = LOW
                    if not cs[RATIOMEMORY_CS_CONT_B]:
                        cs.next[RATIOMEMORY_CS_RUN_B] = 0
                    if not cs[RATIOMEMORY_CS_ACQUIRE_B]:
                        sample_counter.next = 0
                        ratio_address.next = 0
                        divisor_counter.next = 0
                        cs.next[RATIOMEMORY_CS_DONE_B] = LOW
                    elif not cs[RATIOMEMORY_CS_DONE_B]:
                        if acq_strobe:
                            if divisor_counter < divisor:
                                divisor_counter.next = divisor_counter + 1
                            else:
                                divisor_counter.next = 0
                                wlm_ratio_we_out.next = HIGH
                                if sample_counter == MAX_ADDR:
                                    sample_counter.next = 0
                                    ratio_address.next = 0
                                    cs.next[RATIOMEMORY_CS_DONE_B] = HIGH
                                else:
                                    sample_counter.next = sample_counter + 1
                                    ratio_address.next = sample_counter + 1
                    wlm_ratio_addr_out.next = sample_counter

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    strobe_in = Signal(LOW)
    wlm_ratio_we_out = Signal(LOW)
    wlm_ratio_addr_out = Signal(intbv(0)[RATIO_MEM_ADDR_WIDTH:])
    map_base = FPGA_RATIOMEMORY

    toVHDL(RatioMemory, clk=clk, reset=reset, dsp_addr=dsp_addr,
           dsp_data_out=dsp_data_out,
           dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
           strobe_in=strobe_in,
           wlm_ratio_we_out=wlm_ratio_we_out,
           wlm_ratio_addr_out=wlm_ratio_addr_out,
           map_base=map_base)
