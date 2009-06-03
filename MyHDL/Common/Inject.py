#!/usr/bin/python
#
# FILE:
#   Inject.py
#
# DESCRIPTION:
#   MyHDL for optical injection block
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   31-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import FPGA_INJECT

from Host.autogen.interface import INJECT_CONTROL
from Host.autogen.interface import INJECT_LASER1_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER2_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER3_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER4_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER1_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER2_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER3_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER4_FINE_CURRENT

from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH, FPGA_REG_MASK
from Host.autogen.interface import INJECT_CONTROL_MODE_B, INJECT_CONTROL_MODE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_LASER_CURRENT_ENABLE_B, INJECT_CONTROL_LASER_CURRENT_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_LASER_ENABLE_B, INJECT_CONTROL_MANUAL_LASER_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_SOA_ENABLE_B, INJECT_CONTROL_MANUAL_SOA_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W
from MyHDL.Common.LaserDac import LaserDac

LOW, HIGH = bool(0), bool(1)

def Inject(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
            laser_dac_clk_in, strobe_in, laser_fine_current_in,
            laser_shutdown_in, soa_shutdown_in,
            laser1_dac_sync_out, laser2_dac_sync_out,
            laser3_dac_sync_out, laser4_dac_sync_out,
            laser1_dac_din_out, laser2_dac_din_out,
            laser3_dac_din_out, laser4_dac_din_out,
            laser1_disable_out, laser2_disable_out,
            laser3_disable_out, laser4_disable_out,
            laser1_shutdown_out, laser2_shutdown_out,
            laser3_shutdown_out, laser4_shutdown_out,
            soa_shutdown_out, map_base):

    """Optical Injection Subsystem
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    laser_dac_clk_in    -- 5MHz clock to drive laser current DAC
    strobe_in           -- 100kHz strobe for DACs
    laser_fine_current_in -- Sets fine current for selected laser in automatic mode
    laser_shutdown_in   -- Shuts down selected laser in automatic mode
    soa_shutdown_in     -- Shuts down SOA in automatic mode
    laser1_dac_sync_out  -- Synchronization signal for laser 1 current DAC
    laser2_dac_sync_out  -- Synchronization signal for laser 2 current DAC
    laser3_dac_sync_out  -- Synchronization signal for laser 3 current DAC
    laser4_dac_sync_out  -- Synchronization signal for laser 4 current DAC
    laser1_dac_din_out  -- Serial data in for laser 1 current DAC
    laser2_dac_din_out  -- Serial data in for laser 2 current DAC
    laser3_dac_din_out  -- Serial data in for laser 3 current DAC
    laser4_dac_din_out  -- Serial data in for laser 4 current DAC
    laser1_disable_out  -- Disable laser 1 current source
    laser2_disable_out  -- Disable laser 2 current source
    laser3_disable_out  -- Disable laser 3 current source
    laser4_disable_out  -- Disable laser 4 current source
    laser1_shutdown_out  -- Short across laser 1
    laser2_shutdown_out  -- Short across laser 2
    laser3_shutdown_out  -- Short across laser 3
    laser4_shutdown_out  -- Short across laser 4
    soa_shutdown_out     -- Short across SOA

    map_base            -- Base of FPGA map for this block

    This block appears as several registers to the DSP, starting at map_base.
    The registers are:
    INJECT_CONTROL        -- Control register
    LASER1_COARSE_CURRENT -- Laser 1 coarse current DAC setting
    LASER2_COARSE_CURRENT -- Laser 2 coarse current DAC setting
    LASER3_COARSE_CURRENT -- Laser 3 coarse current DAC setting
    LASER4_COARSE_CURRENT -- Laser 4 coarse current DAC setting
    LASER1_FINE_CURRENT   -- Laser 1 manual fine current DAC setting
    LASER2_FINE_CURRENT   -- Laser 2 manual fine current DAC setting
    LASER3_FINE_CURRENT   -- Laser 3 manual fine current DAC setting
    LASER4_FINE_CURRENT   -- Laser 4 manual fine current DAC setting

    Fields within the INJECT_CONTROL register are:

    INJECT_CONTROL_MODE         -- Selects manual (0) or automatic (1) mode
    INJECT_CONTROL_LASER_SELECT -- Selects laser for automatic control 00 -> 11
    INJECT_CONTROL_LASER_CURRENT_ENABLE -- 4 bits controlling laser current regulators
    INJECT_CONTROL_MANUAL_LASER_ENABLE  -- 4 bits controlling laser shorting transistors in manual mode
    INJECT_CONTROL_MANUAL_SOA_ENABLE    -- controls SOA shorting transistor in manual mode
    INJECT_CONTROL_LASER_SHUTDOWN_ENABLE -- enables laser shutdown in automatic mode
    INJECT_CONTROL_SOA_SHUTDOWN_ENABLE   -- enables SOA shutdown in automatic mode.

    Note: If MODE is automatic, only the SOA and the selected laser are in automatic mode,
           the other lasers remain in manual mode.
    """
    Inject_control_addr = map_base + INJECT_CONTROL
    Inject_laser1_coarse_current_addr = map_base + INJECT_LASER1_COARSE_CURRENT
    Inject_laser2_coarse_current_addr = map_base + INJECT_LASER2_COARSE_CURRENT
    Inject_laser3_coarse_current_addr = map_base + INJECT_LASER3_COARSE_CURRENT
    Inject_laser4_coarse_current_addr = map_base + INJECT_LASER4_COARSE_CURRENT
    Inject_laser1_fine_current_addr = map_base + INJECT_LASER1_FINE_CURRENT
    Inject_laser2_fine_current_addr = map_base + INJECT_LASER2_FINE_CURRENT
    Inject_laser3_fine_current_addr = map_base + INJECT_LASER3_FINE_CURRENT
    Inject_laser4_fine_current_addr = map_base + INJECT_LASER4_FINE_CURRENT
    dsp_data_from_regs = Signal(intbv(0)[FPGA_REG_WIDTH:])
    control = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser1_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser1_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])

    mode = Signal(LOW)
    sel  = Signal(intbv(0)[2:])
    laser_current_en = Signal(intbv(0)[4:])
    manual_laser_en = Signal(intbv(0)[4:])
    manual_soa_en = Signal(LOW)
    laser_shutdown_en = Signal(LOW)
    soa_shutdown_en = Signal(LOW)
    laser1_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_fine = Signal(intbv(0)[FPGA_REG_WIDTH:])

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                control.next = 0
                laser1_coarse_current.next = 0
                laser2_coarse_current.next = 0
                laser3_coarse_current.next = 0
                laser4_coarse_current.next = 0
                laser1_fine_current.next = 0x8000
                laser2_fine_current.next = 0x8000
                laser3_fine_current.next = 0x8000
                laser4_fine_current.next = 0x8000
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_control_addr:
                        if dsp_wr: control.next = dsp_data_out
                        dsp_data_from_regs.next = control
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser1_coarse_current_addr:
                        if dsp_wr: laser1_coarse_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser1_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser2_coarse_current_addr:
                        if dsp_wr: laser2_coarse_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser2_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser3_coarse_current_addr:
                        if dsp_wr: laser3_coarse_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser3_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser4_coarse_current_addr:
                        if dsp_wr: laser4_coarse_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser4_coarse_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser1_fine_current_addr:
                        if dsp_wr: laser1_fine_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser1_fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser2_fine_current_addr:
                        if dsp_wr: laser2_fine_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser2_fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser3_fine_current_addr:
                        if dsp_wr: laser3_fine_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser3_fine_current
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == Inject_laser4_fine_current_addr:
                        if dsp_wr: laser4_fine_current.next = dsp_data_out
                        dsp_data_from_regs.next = laser4_fine_current
                    else:
                        dsp_data_from_regs.next = 0
                else:
                    dsp_data_from_regs.next = 0

    @always_comb
    def  comb1():
        mode.next = control[INJECT_CONTROL_MODE_B]
        sel.next  = control[INJECT_CONTROL_LASER_SELECT_B+INJECT_CONTROL_LASER_SELECT_W:INJECT_CONTROL_LASER_SELECT_B]
        laser_current_en.next = control[INJECT_CONTROL_LASER_CURRENT_ENABLE_B+INJECT_CONTROL_LASER_CURRENT_ENABLE_W:INJECT_CONTROL_LASER_CURRENT_ENABLE_B]
        manual_laser_en.next  = control[INJECT_CONTROL_MANUAL_LASER_ENABLE_B+INJECT_CONTROL_MANUAL_LASER_ENABLE_W:INJECT_CONTROL_MANUAL_LASER_ENABLE_B]
        manual_soa_en.next = control[INJECT_CONTROL_MANUAL_SOA_ENABLE_B]
        laser_shutdown_en.next = control[INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B]
        soa_shutdown_en.next = control[INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B]

    @always_comb
    def  comb2():
        laser1_fine.next = laser1_fine_current
        laser2_fine.next = laser2_fine_current
        laser3_fine.next = laser3_fine_current
        laser4_fine.next = laser4_fine_current
        laser1_disable_out.next = not laser_current_en[0]
        laser2_disable_out.next = not laser_current_en[1]
        laser3_disable_out.next = not laser_current_en[2]
        laser4_disable_out.next = not laser_current_en[3]
        laser1_shutdown_out.next = not manual_laser_en[0]
        laser2_shutdown_out.next = not manual_laser_en[1]
        laser3_shutdown_out.next = not manual_laser_en[2]
        laser4_shutdown_out.next = not manual_laser_en[3]
        soa_shutdown_out.next = not manual_soa_en

        if mode:
            soa_shutdown_out.next = soa_shutdown_in
            if sel==0:
                laser1_fine.next = laser_fine_current_in
                laser1_shutdown_out.next = laser_shutdown_in
            elif sel==1:
                laser2_fine.next = laser_fine_current_in
                laser2_shutdown_out.next = laser_shutdown_in
            elif sel==2:
                laser3_fine.next = laser_fine_current_in
                laser3_shutdown_out.next = laser_shutdown_in
            else:
                laser4_fine.next = laser_fine_current_in
                laser4_shutdown_out.next = laser_shutdown_in

    laser1_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser1_coarse_current,chanB_data_in=laser1_fine,
        strobe_in=strobe_in,dac_sync_out=laser1_dac_sync_out,
        dac_din_out=laser1_dac_din_out)

    laser2_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser2_coarse_current,chanB_data_in=laser2_fine,
        strobe_in=strobe_in,dac_sync_out=laser2_dac_sync_out,
        dac_din_out=laser2_dac_din_out)

    laser3_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser3_coarse_current,chanB_data_in=laser3_fine,
        strobe_in=strobe_in,dac_sync_out=laser3_dac_sync_out,
        dac_din_out=laser3_dac_din_out)

    laser4_dac = LaserDac(clk=clk, reset=reset, dac_clock_in=laser_dac_clk_in,
        chanA_data_in=laser4_coarse_current,chanB_data_in=laser4_fine,
        strobe_in=strobe_in,dac_sync_out=laser4_dac_sync_out,
        dac_din_out=laser4_dac_din_out)

    return instances()

if __name__ == "__main__":
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr, clk, reset = [Signal(LOW) for i in range(3)]
    laser_dac_clk_in, strobe_in, laser_shutdown_in, soa_shutdown_in =\
        [Signal(LOW) for i in range(4)]
    laser_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser1_dac_sync_out, laser2_dac_sync_out, \
        laser3_dac_sync_out, laser4_dac_sync_out = \
        [Signal(LOW) for i in range(4)]
    laser1_dac_din_out = Signal(LOW)
    laser2_dac_din_out = Signal(LOW)
    laser3_dac_din_out = Signal(LOW)
    laser4_dac_din_out = Signal(LOW)
    laser1_disable_out,laser2_disable_out,laser3_disable_out,laser4_disable_out=\
        [Signal(LOW) for i in range(4)]
    laser1_shutdown_out,laser2_shutdown_out,laser3_shutdown_out,laser4_shutdown_out=\
        [Signal(LOW) for i in range(4)]
    soa_shutdown_out = Signal(LOW)
    map_base = FPGA_INJECT

    toVHDL(Inject, clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, laser_dac_clk_in=laser_dac_clk_in,
                   strobe_in=strobe_in,
                   laser_fine_current_in=laser_fine_current_in,
                   laser_shutdown_in=laser_shutdown_in,
                   soa_shutdown_in=soa_shutdown_in,
                   laser1_dac_sync_out=laser1_dac_sync_out,
                   laser2_dac_sync_out=laser2_dac_sync_out,
                   laser3_dac_sync_out=laser3_dac_sync_out,
                   laser4_dac_sync_out=laser4_dac_sync_out,
                   laser1_dac_din_out=laser1_dac_din_out,
                   laser2_dac_din_out=laser2_dac_din_out,
                   laser3_dac_din_out=laser3_dac_din_out,
                   laser4_dac_din_out=laser4_dac_din_out,
                   laser1_disable_out=laser1_disable_out,
                   laser2_disable_out=laser2_disable_out,
                   laser3_disable_out=laser3_disable_out,
                   laser4_disable_out=laser4_disable_out,
                   laser1_shutdown_out=laser1_shutdown_out,
                   laser2_shutdown_out=laser2_shutdown_out,
                   laser3_shutdown_out=laser3_shutdown_out,
                   laser4_shutdown_out=laser4_shutdown_out,
                   soa_shutdown_out=soa_shutdown_out,
                   map_base=map_base)
