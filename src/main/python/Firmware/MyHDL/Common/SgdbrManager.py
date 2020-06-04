#!/usr/bin/python
#
# FILE:
#   SgdbrManager.py
#
# DESCRIPTION:
#   Manages the generation of SGDBR current scans and the synchronous collection
# of wavelength monitor information by implementing a "recorder" with two playack
# channels and two record channels. The playback channels read data out of the
# analyzer metadata memory while the record channels write data into the analyzer
# data memory (which is normally used for storing ringdown waveforms).
#
# SEE ALSO:
#
# HISTORY:
#   06-Apr-2018  sze  Initial version.
#
#  Copyright (c) 2016 Picarro, Inc. All rights reserved
#
from myhdl import (Signal, always_comb, concat, enum, instance, instances, intbv, modbv,
                   toVHDL)

from EdgeDetectors import PosEdge
from Host.autogen import interface
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH, EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, RDMEM_DATA_WIDTH, RDMEM_META_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_SGDBRMANAGER

from Host.autogen.interface import SGDBRMANAGER_CSR
from Host.autogen.interface import SGDBRMANAGER_CONFIG
from Host.autogen.interface import SGDBRMANAGER_SCAN_SAMPLES
from Host.autogen.interface import SGDBRMANAGER_SAMPLE_TIME
from Host.autogen.interface import SGDBRMANAGER_DELAY_SAMPLES
from Host.autogen.interface import SGDBRMANAGER_SCAN_ADDRESS
from Host.autogen.interface import SGDBRMANAGER_SGDBR_PRESENT

from Host.autogen.interface import SGDBRMANAGER_CSR_START_SCAN_B, SGDBRMANAGER_CSR_START_SCAN_W
from Host.autogen.interface import SGDBRMANAGER_CSR_DONE_B, SGDBRMANAGER_CSR_DONE_W
from Host.autogen.interface import SGDBRMANAGER_CSR_SCAN_ACTIVE_B, SGDBRMANAGER_CSR_SCAN_ACTIVE_W
from Host.autogen.interface import SGDBRMANAGER_CONFIG_MODE_B, SGDBRMANAGER_CONFIG_MODE_W
from Host.autogen.interface import SGDBRMANAGER_CONFIG_SELECT_B, SGDBRMANAGER_CONFIG_SELECT_W
from Host.autogen.interface import SGDBRMANAGER_SGDBR_PRESENT_SGDBR_A_PRESENT_B, SGDBRMANAGER_SGDBR_PRESENT_SGDBR_A_PRESENT_W
from Host.autogen.interface import SGDBRMANAGER_SGDBR_PRESENT_SGDBR_B_PRESENT_B, SGDBRMANAGER_SGDBR_PRESENT_SGDBR_B_PRESENT_W

LOW, HIGH = bool(0), bool(1)

SeqState = enum("READ_PB_WFM0", "READ_PB_WFM1", "WRITE_PB_DATA",
                "AWAIT_REC_STROBE", "READ_REC_DATA", "WRITE_REC_WFM0",
                "WRITE_REC_WFM1", "ADVANCE_ADDRESS")


def SgdbrManager(clk, reset, dsp_addr, dsp_data_out, dsp_data_in,
                 dsp_wr, rec0_in, rec1_in, rec_strobe_in, pb0_out,
                 pb1_out, pb_strobe_out, rec_addr_out, rec_data_out,
                 rec_wfm_sel_out, rec_we_out, pb_data_in,
                 pb_wfm_sel_out, mode_out, scan_active_out,
                 sgdbr_present_out, sgdbr_select_out, map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    rec0_in             -- record channel 0 input
    rec1_in             -- record channel 1 input
    rec_strobe_in       -- record strobe input
    pb0_out             -- playback channel 0 output
    pb1_out             -- playback channel 1 output
    pb_strobe_out       -- playback strobe output
    rec_addr_out        -- recorder address output
    rec_data_out        -- record data output
    rec_wfm_sel_out     -- record waveform (channel) select output
    rec_we_out          -- record write enable output
    pb_data_in          -- playback data input
    pb_wfm_sel_out      -- playback waveform (channel) select output
    mode_out            -- mode output (0=>ringdown, 1=>recorder)
    scan_active_out     -- high while scan is in progress
    sgdbr_present_out   -- indicates which SGDBR lasers are present (2 bits)
    sgdbr_select_out    -- indicates which SDBR laser is selected for synchronous updates
    map_base

    Registers:
    SGDBRMANAGER_CSR            -- control/status register
    SGDBRMANAGER_CONFIG         -- configures analyzer memory mode and which laser is controlled
    SGDBRMANAGER_SCAN_SAMPLES   -- number of samples in scan
    SGDBRMANAGER_SAMPLE_TIME    -- inter sample interval (units of 10us)
    SGDBRMANAGER_DELAY_SAMPLES  -- number of samples to delay at start of scan
    SGDBRMANAGER_SCAN_ADDRESS   -- memory address currently used in scan
    SGDBRMANAGER_SGDBR_PRESENT  -- indicates which SGDBR lasers are present

    Fields in SGDBRMANAGER_CSR:
    SGDBRMANAGER_CSR_START_SCAN -- assert to start scan
    SGDBRMANAGER_CSR_DONE       -- goes high to indicate scan is done
    SGDBRMANAGER_CSR_SCAN_ACTIVE -- indicates scan is in progress

    Fields in SGDBRMANAGER_CONFIG:
    SGDBRMANAGER_CONFIG_MODE -- Set analyzer memory mode: 0 for ringdown mode, 1 for SGDBR laser recorder mode
    SGDBRMANAGER_CONFIG_SELECT -- Select SGDBR laser for control: 0 for laser A, 1 for laser B

    Fields in SGDBRMANAGER_SGDBR_PRESENT:
    SGDBRMANAGER_SGDBR_PRESENT_SGDBR_A_PRESENT -- Indicates SGDBR_A is installed in slot for laser 1
    SGDBRMANAGER_SGDBR_PRESENT_SGDBR_B_PRESENT -- Indicates SGDBR_B is installed in slot for laser 3
    """
    sgdbrmanager_csr_addr = map_base + SGDBRMANAGER_CSR
    sgdbrmanager_config_addr = map_base + SGDBRMANAGER_CONFIG
    sgdbrmanager_scan_samples_addr = map_base + SGDBRMANAGER_SCAN_SAMPLES
    sgdbrmanager_sample_time_addr = map_base + SGDBRMANAGER_SAMPLE_TIME
    sgdbrmanager_delay_samples_addr = map_base + SGDBRMANAGER_DELAY_SAMPLES
    sgdbrmanager_scan_address_addr = map_base + SGDBRMANAGER_SCAN_ADDRESS
    sgdbrmanager_sgdbr_present_addr = map_base + SGDBRMANAGER_SGDBR_PRESENT
    csr = Signal(intbv(0)[3:])
    config = Signal(intbv(0)[2:])
    scan_samples = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH+1:])
    sample_time = Signal(intbv(0)[7:])
    delay_samples = Signal(intbv(0)[16:])
    scan_address = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    sgdbr_present = Signal(intbv(0)[2:])
    scan_address = Signal(modbv(0)[DATA_BANK_ADDR_WIDTH:])
    holdoff_counter = Signal(modbv(0)[16:])
    seq_state = Signal(SeqState.AWAIT_REC_STROBE)
    pb0 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pb1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rec_strobe_edge = Signal(LOW)
    mem_flag = Signal(LOW)
    sample_time_counter = Signal(intbv(0)[7:])

    posEdge = PosEdge(clk=clk, reset=reset, input=rec_strobe_in,
                      output=rec_strobe_edge)

    @always_comb
    def comb():
        rec_addr_out.next = scan_address
        pb0_out.next = pb0
        pb1_out.next = pb1
        scan_active_out.next = csr[SGDBRMANAGER_CSR_SCAN_ACTIVE_B]
        sgdbr_select_out.next = config[SGDBRMANAGER_CONFIG_SELECT_B]
        sgdbr_present_out.next = concat(
            sgdbr_present[SGDBRMANAGER_SGDBR_PRESENT_SGDBR_B_PRESENT_B],  
            sgdbr_present[SGDBRMANAGER_SGDBR_PRESENT_SGDBR_A_PRESENT_B])

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                csr.next = 0
                config.next = 0
                scan_samples.next = 0
                sample_time.next = 0
                delay_samples.next = 0
                scan_address.next = 0
                sgdbr_present.next = 0
                seq_state.next = SeqState.ADVANCE_ADDRESS
                holdoff_counter.next = 0
                pb0.next = 0
                pb1.next = 0
                sample_time_counter.next = 0

            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False:
                        pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == sgdbrmanager_csr_addr:  # rw
                        if dsp_wr:
                            csr.next = dsp_data_out
                        dsp_data_in.next = csr
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == sgdbrmanager_config_addr:  # rw
                        if dsp_wr:
                            config.next = dsp_data_out
                        dsp_data_in.next = config
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == sgdbrmanager_scan_samples_addr:  # rw
                        if dsp_wr:
                            scan_samples.next = dsp_data_out
                            scan_address.next = dsp_data_out - 1
                        dsp_data_in.next = scan_samples
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == sgdbrmanager_sample_time_addr:  # rw
                        if dsp_wr:
                            sample_time.next = dsp_data_out
                        dsp_data_in.next = sample_time
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == sgdbrmanager_delay_samples_addr:  # rw
                        if dsp_wr:
                            delay_samples.next = dsp_data_out
                            holdoff_counter.next = dsp_data_out - 1
                        dsp_data_in.next = delay_samples
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == sgdbrmanager_scan_address_addr:  # r
                        dsp_data_in.next = scan_address
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == sgdbrmanager_sgdbr_present_addr:  # rw
                        if dsp_wr:
                            sgdbr_present.next = dsp_data_out
                        dsp_data_in.next = sgdbr_present
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                pb_strobe_out.next = 0
                rec_we_out.next = 0

                if seq_state == SeqState.ADVANCE_ADDRESS:
                    # While memory mode is 1, the state machine keeps updating the
                    #  playback data at the same rate as record strobes arrive.
                    # The scan_address in memory starts at zero. At each sample
                    #  interval (expressed in multiples of the record strobe interval),
                    #  we either increment the holdoff counter (at the start of the scan)
                    #  for the specified number of delay samples, or we increment the
                    #  scan address
                    mode_out.next = config[SGDBRMANAGER_CONFIG_MODE_B]
                    if config[SGDBRMANAGER_CONFIG_MODE_B]:
                        if not csr[SGDBRMANAGER_CSR_SCAN_ACTIVE_B]:
                            scan_address.next = 0
                            holdoff_counter.next = 0
                            sample_time_counter.next = 0
                            if csr[SGDBRMANAGER_CSR_START_SCAN_B]:
                                csr.next[SGDBRMANAGER_CSR_START_SCAN_B] = 0
                                csr.next[SGDBRMANAGER_CSR_DONE_B] = 0
                                csr.next[SGDBRMANAGER_CSR_SCAN_ACTIVE_B] = 1
                        else:
                            if sample_time_counter < sample_time - 1:
                                sample_time_counter.next = sample_time_counter + 1
                            else:
                                sample_time_counter.next = 0
                                if holdoff_counter < delay_samples - 1:
                                    holdoff_counter.next = holdoff_counter + 1
                                else:
                                    if scan_address < scan_samples - 1:
                                        scan_address.next = scan_address + 1
                                    else:
                                        csr.next[SGDBRMANAGER_CSR_DONE_B] = 1
                                        csr.next[
                                            SGDBRMANAGER_CSR_SCAN_ACTIVE_B] = 0
                        mem_flag.next = 1
                        seq_state.next = SeqState.READ_PB_WFM0
                    else:
                        csr.next[SGDBRMANAGER_CSR_SCAN_ACTIVE_B] = 0

                elif seq_state == SeqState.READ_PB_WFM0:
                    # Read playback data for waveform 0
                    if mem_flag:
                        mem_flag.next = 0
                    else:
                        mem_flag.next = 1
                        pb0.next = pb_data_in
                        pb_wfm_sel_out.next = 1
                        seq_state.next = SeqState.READ_PB_WFM1

                elif seq_state == SeqState.READ_PB_WFM1:
                    # Read playback data for waveform 1
                    if mem_flag:
                        mem_flag.next = 0
                    else:
                        pb1.next = pb_data_in
                        pb_wfm_sel_out.next = 0
                        seq_state.next = SeqState.WRITE_PB_DATA

                elif seq_state == SeqState.WRITE_PB_DATA:
                    # Send playback strobe pulse to current source
                    pb_strobe_out.next = 1
                    seq_state.next = SeqState.AWAIT_REC_STROBE

                elif seq_state == SeqState.AWAIT_REC_STROBE:
                    # Wait for sample_time (by couting rec_strobe edges)
                    #  then proceed to read record data
                    if rec_strobe_edge:
                        rec_wfm_sel_out.next = 0
                        rec_data_out.next = rec0_in
                        seq_state.next = SeqState.WRITE_REC_WFM0
                        mem_flag.next = 1

                elif seq_state == SeqState.WRITE_REC_WFM0:
                    # Write the record wavefom 0, waiting for a cycle
                    if mem_flag:
                        mem_flag.next = 0
                        rec_we_out.next = 1
                    else:
                        rec_data_out.next = rec1_in
                        rec_wfm_sel_out.next = 1
                        mem_flag.next = 1
                        seq_state.next = SeqState.WRITE_REC_WFM1

                elif seq_state == SeqState.WRITE_REC_WFM1:
                    # Write the record wavefom 1, waiting for a cycle
                    if mem_flag:
                        mem_flag.next = 0
                        rec_we_out.next = 1
                    else:
                        seq_state.next = SeqState.ADVANCE_ADDRESS
                else:
                    seq_state.next = SeqState.ADVANCE_ADDRESS

    return instances()


if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    rec0_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rec1_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rec_strobe_in = Signal(LOW)
    pb0_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pb1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pb_strobe_out = Signal(LOW)
    rec_addr_out = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    rec_data_out = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
    rec_wfm_sel_out = Signal(LOW)
    rec_we_out = Signal(LOW)
    pb_data_in = Signal(intbv(0)[RDMEM_META_WIDTH:])
    pb_wfm_sel_out = Signal(LOW)
    mode_out = Signal(LOW)
    scan_active_out = Signal(LOW)
    sgdbr_present_out = Signal(intbv(0)[2:])
    sgdbr_select_out = Signal(LOW)
    map_base = FPGA_SGDBRMANAGER

    toVHDL(SgdbrManager, clk=clk, reset=reset, dsp_addr=dsp_addr,
                         dsp_data_out=dsp_data_out,
                         dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                         rec0_in=rec0_in, rec1_in=rec1_in,
                         rec_strobe_in=rec_strobe_in, pb0_out=pb0_out,
                         pb1_out=pb1_out, pb_strobe_out=pb_strobe_out,
                         rec_addr_out=rec_addr_out,
                         rec_data_out=rec_data_out,
                         rec_wfm_sel_out=rec_wfm_sel_out,
                         rec_we_out=rec_we_out, pb_data_in=pb_data_in,
                         pb_wfm_sel_out=pb_wfm_sel_out,
                         mode_out=mode_out,
                         scan_active_out=scan_active_out,
                         sgdbr_present_out=sgdbr_present_out,
                         sgdbr_select_out=sgdbr_select_out,
                         map_base=map_base)
