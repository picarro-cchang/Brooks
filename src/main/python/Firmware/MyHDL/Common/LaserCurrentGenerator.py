#!/usr/bin/python
#
# FILE:
#   LaserCurrentGenerator.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   05-Feb-2015  sze  Initial version.
#   01-Oct-2015  sze  Add output for level counter
#   11-Oct-2015  sze  Added sequence identifiers
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import LASER_CURRENT_GEN_ACC_WIDTH
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_LASERCURRENTGENERATOR

from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS
from Host.autogen.interface import LASERCURRENTGENERATOR_SLOW_SLOPE
from Host.autogen.interface import LASERCURRENTGENERATOR_FAST_SLOPE
from Host.autogen.interface import LASERCURRENTGENERATOR_FIRST_OFFSET
from Host.autogen.interface import LASERCURRENTGENERATOR_SECOND_OFFSET
from Host.autogen.interface import LASERCURRENTGENERATOR_FIRST_BREAKPOINT
from Host.autogen.interface import LASERCURRENTGENERATOR_SECOND_BREAKPOINT
from Host.autogen.interface import LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT
from Host.autogen.interface import LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT
from Host.autogen.interface import LASERCURRENTGENERATOR_LOWER_WINDOW
from Host.autogen.interface import LASERCURRENTGENERATOR_UPPER_WINDOW
from Host.autogen.interface import LASERCURRENTGENERATOR_SEQUENCE_ID

from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B, LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_W
from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B, LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_W
from Host.autogen.interface import LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B, LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_W

from Host.autogen.interface import RDMEM_RESERVED_BANK_ADDR_WIDTH

from DualPortRamRw import DualPortRamRw
from Interpolator import linear_interpolator

LOW, HIGH = bool(0), bool(1)
def LaserCurrentGenerator(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,
                          dsp_wr,strobe_in,sel_laser_in,
                          laser1_fine_current_out,
                          laser2_fine_current_out,
                          laser3_fine_current_out,
                          laser4_fine_current_out,
                          laser_current_in_window_out,level_counter_out,
                          sequence_id_out,map_base):
    """
    Parameters:
    clk                     -- Clock input
    reset                   -- Reset input
    dsp_addr                -- address from dsp_interface block
    dsp_data_out            -- write data from dsp_interface block
    dsp_data_in             -- read data to dsp_interface_block
    dsp_wr                  -- single-cycle write command from dsp_interface block
    strobe_in               -- single cycle pulse every 10us
    sel_laser_in            -- selected laser
    laser1_fine_current_out -- laser 1 fine current output
    laser2_fine_current_out -- laser 2 fine current output
    laser3_fine_current_out -- laser 3 fine current output
    laser4_fine_current_out -- laser 4 fine current output
    laser_current_in_window_out -- high if current for selected laser is within the window
    level_counter_out       -- value of level counter for selected laser
    sequence_id_out         -- sequence identifier for selected laser
    map_base

    Registers:
    LASERCURRENTGENERATOR_CONTROL_STATUS -- Control/status register
    LASERCURRENTGENERATOR_SLOW_SLOPE -- Slope of slowly changing portion (tread) of staircase
    LASERCURRENTGENERATOR_FAST_SLOPE -- Slope of rapidly changing portion (rise) of staircase
    LASERCURRENTGENERATOR_FIRST_OFFSET -- Initial value of rise counter
    LASERCURRENTGENERATOR_SECOND_OFFSET -- Effective initial value of upper tread counter
    LASERCURRENTGENERATOR_FIRST_BREAKPOINT -- Time between lower tread and rise
    LASERCURRENTGENERATOR_SECOND_BREAKPOINT -- Time between rise and upper tread
    LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT -- Time (units of 10us) for one stair step
    LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT -- Number of stair steps in a period
    LASERCURRENTGENERATOR_LOWER_WINDOW -- Lower value of the window for the laser current
    LASERCURRENTGENERATOR_UPPER_WINDOW -- Upper value of the window for the laser current
    LASERCURRENTGENERATOR_SEQUENCE_ID -- Sequence identifier for the set of levels

    Fields in LASERCURRENTGENERATOR_CONTROL_STATUS:
    LASERCURRENTGENERATOR_CONTROL_STATUS_MODE -- Zero indicates registers may be changed, one indicates current
        register values are to be latched
    LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT -- Index (2-bits) of the selected laser
    LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT -- Index of memory bank to use
    """
    lasercurrentgenerator_control_status_addr = map_base + LASERCURRENTGENERATOR_CONTROL_STATUS
    lasercurrentgenerator_slow_slope_addr = map_base + LASERCURRENTGENERATOR_SLOW_SLOPE
    lasercurrentgenerator_fast_slope_addr = map_base + LASERCURRENTGENERATOR_FAST_SLOPE
    lasercurrentgenerator_first_offset_addr = map_base + LASERCURRENTGENERATOR_FIRST_OFFSET
    lasercurrentgenerator_second_offset_addr = map_base + LASERCURRENTGENERATOR_SECOND_OFFSET
    lasercurrentgenerator_first_breakpoint_addr = map_base + LASERCURRENTGENERATOR_FIRST_BREAKPOINT
    lasercurrentgenerator_second_breakpoint_addr = map_base + LASERCURRENTGENERATOR_SECOND_BREAKPOINT
    lasercurrentgenerator_transition_counter_limit_addr = map_base + LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT
    lasercurrentgenerator_period_counter_limit_addr = map_base + LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT
    lasercurrentgenerator_lower_window_addr = map_base + LASERCURRENTGENERATOR_LOWER_WINDOW
    lasercurrentgenerator_upper_window_addr = map_base + LASERCURRENTGENERATOR_UPPER_WINDOW
    lasercurrentgenerator_sequence_id_addr = map_base + LASERCURRENTGENERATOR_SEQUENCE_ID
    control_status = Signal(intbv(0)[FPGA_REG_WIDTH:])
    slow_slope = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_slope = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_offset = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    second_offset = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_breakpoint = Signal(intbv(0)[FPGA_REG_WIDTH:])
    second_breakpoint = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_limit = Signal(intbv(0)[FPGA_REG_WIDTH:])
    period_counter_limit = Signal(intbv(0)[FPGA_REG_WIDTH:])
    lower_window = Signal(intbv(0)[FPGA_REG_WIDTH:])
    upper_window = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sequence_id = Signal(intbv(0)[FPGA_REG_WIDTH:])

    PERIOD_COUNTER_WIDTH = 9
    TRANSITION_COUNTER_WIDTH = 16
    ACCUMULATOR_MODULO = 1 << LASER_CURRENT_GEN_ACC_WIDTH

    slow_slope_1 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_slope_1 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_offset_1 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    second_offset_1 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_breakpoint_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    second_breakpoint_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_limit_1 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_limit_1 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    lower_window_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    upper_window_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sequence_id_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_1 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_1 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    slow_accumulator_1 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_accumulator_1 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    interp_1 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    bank_1 = Signal(LOW)
    current_level_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    prev_level_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])


    slow_slope_2 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_slope_2 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_offset_2 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    second_offset_2 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_breakpoint_2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    second_breakpoint_2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_limit_2 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_limit_2 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    lower_window_2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    upper_window_2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sequence_id_2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_2 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_2 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    slow_accumulator_2 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_accumulator_2 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    interp_2 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    bank_2 = Signal(LOW)
    current_level_2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    prev_level_2 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    slow_slope_3 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_slope_3 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_offset_3 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    second_offset_3 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_breakpoint_3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    second_breakpoint_3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_limit_3 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_limit_3 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    lower_window_3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    upper_window_3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sequence_id_3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_3 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_3 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    slow_accumulator_3 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_accumulator_3 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    interp_3 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    bank_3 = Signal(LOW)
    current_level_3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    prev_level_3 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    slow_slope_4 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_slope_4 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_offset_4 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    second_offset_4 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    first_breakpoint_4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    second_breakpoint_4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    transition_counter_limit_4 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_limit_4 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    transition_counter_4 = Signal(intbv(0)[TRANSITION_COUNTER_WIDTH:])
    period_counter_4 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH:])
    lower_window_4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    upper_window_4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sequence_id_4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    slow_accumulator_4 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    fast_accumulator_4 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    interp_4 = Signal(intbv(0)[LASER_CURRENT_GEN_ACC_WIDTH:])
    bank_4 = Signal(LOW)
    current_level_4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    prev_level_4 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    enA_laser1 = Signal(LOW)
    addrA_laser1 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataA_laser1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataA_laser1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    enB_laser1 = Signal(HIGH)
    wr_enB_laser1 = Signal(LOW)
    addrB_laser1 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataB_laser1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataB_laser1 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    enA_laser2 = Signal(LOW)
    addrA_laser2 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataA_laser2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataA_laser2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    enB_laser2 = Signal(HIGH)
    wr_enB_laser2 = Signal(LOW)
    addrB_laser2 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataB_laser2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataB_laser2 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    enA_laser3 = Signal(LOW)
    addrA_laser3 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataA_laser3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataA_laser3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    enB_laser3 = Signal(HIGH)
    wr_enB_laser3 = Signal(LOW)
    addrB_laser3 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataB_laser3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataB_laser3 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    enA_laser4 = Signal(LOW)
    addrA_laser4 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataA_laser4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataA_laser4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    enB_laser4 = Signal(HIGH)
    wr_enB_laser4 = Signal(LOW)
    addrB_laser4 = Signal(intbv(0)[PERIOD_COUNTER_WIDTH + 1:])
    rd_dataB_laser4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wr_dataB_laser4 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    dsp_wr_delayed = Signal(LOW)

    output_counter = Signal(intbv(0,min=0,max= 9))

    interp_y0 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    interp_y1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    interp_beta = Signal(intbv(0)[FPGA_REG_WIDTH:])
    interp_yout = Signal(intbv(0)[FPGA_REG_WIDTH:])

    interpolator = linear_interpolator(y0=interp_y0, y1=interp_y1, beta=interp_beta, y_out=interp_yout)

    # The following blocks of memory are used to store the fine laser current levels for each physical
    #  laser. The current generator makes transitions between consecutive levels by interpolating between
    #  them according to a template function. The number of 10us ticks to transition from one level to
    #  the next is transition_counter_limit, and the number of levels before the cycle repeats
    #  is given by period_counter_limit.
    # There are PERIOD_COUNTER_WIDTH + 1 bits in the address within the block because there are two
    #  banks of levels which can be selected.
    # The parameters of the template waveform can be defined for each laser. They are set by the values
    #  in the following registers:
    # slow_slope, fast_slope, first_offset, second_offset, first_breakpoint, second_breakpoint
    #  transition_counter_limit, period_counter_limit, lower_window, upper_window, bank

    laser1_mem = DualPortRamRw(clockA=clk, enableA=enA_laser1, wr_enableA=dsp_wr_delayed,
                               addressA=addrA_laser1, rd_dataA=rd_dataA_laser1,
                               wr_dataA=wr_dataA_laser1,
                               clockB=clk, enableB=enB_laser1, wr_enableB=wr_enB_laser1,
                               addressB=addrB_laser1, rd_dataB=rd_dataB_laser1,
                               wr_dataB=wr_dataB_laser1,
                               addr_width=PERIOD_COUNTER_WIDTH + 1,
                               data_width=FPGA_REG_WIDTH)

    laser2_mem = DualPortRamRw(clockA=clk, enableA=enA_laser2, wr_enableA=dsp_wr_delayed,
                               addressA=addrA_laser2, rd_dataA=rd_dataA_laser2,
                               wr_dataA=wr_dataA_laser2,
                               clockB=clk, enableB=enB_laser2, wr_enableB=wr_enB_laser2,
                               addressB=addrB_laser2, rd_dataB=rd_dataB_laser2,
                               wr_dataB=wr_dataB_laser2,
                               addr_width=PERIOD_COUNTER_WIDTH + 1,
                               data_width=FPGA_REG_WIDTH)

    laser3_mem = DualPortRamRw(clockA=clk, enableA=enA_laser3, wr_enableA=dsp_wr_delayed,
                               addressA=addrA_laser3, rd_dataA=rd_dataA_laser3,
                               wr_dataA=wr_dataA_laser3,
                               clockB=clk, enableB=enB_laser3, wr_enableB=wr_enB_laser3,
                               addressB=addrB_laser3, rd_dataB=rd_dataB_laser3,
                               wr_dataB=wr_dataB_laser3,
                               addr_width=PERIOD_COUNTER_WIDTH + 1,
                               data_width=FPGA_REG_WIDTH)

    laser4_mem = DualPortRamRw(clockA=clk, enableA=enA_laser4, wr_enableA=dsp_wr_delayed,
                               addressA=addrA_laser4, rd_dataA=rd_dataA_laser4,
                               wr_dataA=wr_dataA_laser4,
                               clockB=clk, enableB=enB_laser4, wr_enableB=wr_enB_laser4,
                               addressB=addrB_laser4, rd_dataB=rd_dataB_laser4,
                               wr_dataB=wr_dataB_laser4,
                               addr_width=PERIOD_COUNTER_WIDTH + 1,
                               data_width=FPGA_REG_WIDTH)

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                control_status.next = 0
                slow_slope.next = 0
                fast_slope.next = 0
                first_offset.next = 0
                second_offset.next = 0
                first_breakpoint.next = 0
                second_breakpoint.next = 0
                transition_counter_limit.next = 0
                period_counter_limit.next = 0
                lower_window.next = 0
                upper_window.next = 0
                sequence_id.next = 0

                slow_slope_1.next = 0
                fast_slope_1.next = 0
                first_offset_1.next = 0
                second_offset_1.next = 0
                first_breakpoint_1.next = 0
                second_breakpoint_1.next = 0
                transition_counter_limit_1.next = 32
                period_counter_limit_1.next = 16
                lower_window_1.next = 20000
                upper_window_1.next = 40000
                sequence_id_1.next = 0
                transition_counter_1.next = 0
                period_counter_1.next = 0
                slow_accumulator_1.next = 0
                fast_accumulator_1.next = 0
                bank_1.next = 0
                current_level_1.next = 0
                prev_level_1.next = 0

                slow_slope_2.next = 0
                fast_slope_2.next = 0
                first_offset_2.next = 0
                second_offset_2.next = 0
                first_breakpoint_2.next = 0
                second_breakpoint_2.next = 0
                transition_counter_limit_2.next = 32
                period_counter_limit_2.next = 16
                lower_window_2.next = 20000
                upper_window_2.next = 40000
                sequence_id_2.next = 0
                transition_counter_2.next = 0
                period_counter_2.next = 0
                slow_accumulator_2.next = 0
                fast_accumulator_2.next = 0
                bank_2.next = 0
                current_level_2.next = 0
                prev_level_2.next = 0

                slow_slope_3.next = 0
                fast_slope_3.next = 0
                first_offset_3.next = 0
                second_offset_3.next = 0
                first_breakpoint_3.next = 0
                second_breakpoint_3.next = 0
                transition_counter_limit_3.next = 32
                period_counter_limit_3.next = 16
                lower_window_3.next = 20000
                upper_window_3.next = 40000
                sequence_id_3.next = 0
                transition_counter_3.next = 0
                period_counter_3.next = 0
                slow_accumulator_3.next = 0
                fast_accumulator_3.next = 0
                bank_3.next = 0
                current_level_3.next = 0
                prev_level_3.next = 0

                slow_slope_4.next = 0
                fast_slope_4.next = 0
                first_offset_4.next = 0
                second_offset_4.next = 0
                first_breakpoint_4.next = 0
                second_breakpoint_4.next = 0
                transition_counter_limit_4.next = 32
                period_counter_limit_4.next = 16
                lower_window_4.next = 20000
                upper_window_4.next = 40000
                sequence_id_4.next = 0
                transition_counter_4.next = 0
                period_counter_4.next = 0
                slow_accumulator_4.next = 0
                fast_accumulator_4.next = 0
                bank_4.next = 0
                current_level_4.next = 0
                prev_level_4.next = 0

                output_counter.next = 0
                dsp_wr_delayed.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_control_status_addr: # rw
                        if dsp_wr: control_status.next = dsp_data_out
                        dsp_data_in.next = control_status
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_slow_slope_addr: # rw
                        if dsp_wr: slow_slope.next = dsp_data_out
                        dsp_data_in.next = slow_slope
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_fast_slope_addr: # rw
                        if dsp_wr: fast_slope.next = dsp_data_out
                        dsp_data_in.next = fast_slope
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_first_offset_addr: # rw
                        if dsp_wr: first_offset.next = dsp_data_out
                        dsp_data_in.next = first_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_second_offset_addr: # rw
                        if dsp_wr: second_offset.next = dsp_data_out
                        dsp_data_in.next = second_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_first_breakpoint_addr: # rw
                        if dsp_wr: first_breakpoint.next = dsp_data_out
                        dsp_data_in.next = first_breakpoint
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_second_breakpoint_addr: # rw
                        if dsp_wr: second_breakpoint.next = dsp_data_out
                        dsp_data_in.next = second_breakpoint
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_transition_counter_limit_addr: # rw
                        if dsp_wr: transition_counter_limit.next = dsp_data_out
                        dsp_data_in.next = transition_counter_limit
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_period_counter_limit_addr: # rw
                        if dsp_wr: period_counter_limit.next = dsp_data_out
                        dsp_data_in.next = period_counter_limit
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_lower_window_addr: # rw
                        if dsp_wr: lower_window.next = dsp_data_out
                        dsp_data_in.next = lower_window
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_upper_window_addr: # rw
                        if dsp_wr: upper_window.next = dsp_data_out
                        dsp_data_in.next = upper_window
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == lasercurrentgenerator_sequence_id_addr: # rw
                        if dsp_wr: sequence_id.next = dsp_data_out
                        dsp_data_in.next = sequence_id
                    else:
                        dsp_data_in.next = 0
                else:
                    # Handle accessing of block RAM
                    sel_laser1 = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 0x8
                    sel_laser2 = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 0x9
                    sel_laser3 = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 0xA
                    sel_laser4 = dsp_addr[:RDMEM_RESERVED_BANK_ADDR_WIDTH] == 0xB

                    # Access from DSP side
                    dsp_wr_delayed.next = dsp_wr
                    enA_laser1.next = sel_laser1
                    addrA_laser1.next = dsp_addr[PERIOD_COUNTER_WIDTH + 1:]
                    wr_dataA_laser1.next = dsp_data_out[FPGA_REG_WIDTH:]
                    enA_laser2.next = sel_laser2
                    addrA_laser2.next = dsp_addr[PERIOD_COUNTER_WIDTH + 1:]
                    wr_dataA_laser2.next = dsp_data_out[FPGA_REG_WIDTH:]
                    enA_laser3.next = sel_laser3
                    addrA_laser3.next = dsp_addr[PERIOD_COUNTER_WIDTH + 1:]
                    wr_dataA_laser3.next = dsp_data_out[FPGA_REG_WIDTH:]
                    enA_laser4.next = sel_laser4
                    addrA_laser4.next = dsp_addr[PERIOD_COUNTER_WIDTH + 1:]
                    wr_dataA_laser4.next = dsp_data_out[FPGA_REG_WIDTH:]

                    if sel_laser1:
                        dsp_data_in.next = rd_dataA_laser1
                    elif sel_laser2:
                        dsp_data_in.next = rd_dataA_laser2
                    elif sel_laser3:
                        dsp_data_in.next = rd_dataA_laser3
                    elif sel_laser4:
                        dsp_data_in.next = rd_dataA_laser4
                    else:
                        dsp_data_in.next = 0

                laser_select_b = LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B
                laser_select_w = LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_W
                laser_selected = control_status[laser_select_b + laser_select_w:laser_select_b]
                mode = control_status[LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B]
                bank = control_status[LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B]

                # Set up the level_counter_out and sequence_id_out signals, depending on the selected laser and its
                #  associated period counter and sequence_id register
                level_counter_out.next = 0
                sequence_id_out.next = 0
                if sel_laser_in == 0:
                    level_counter_out.next[FPGA_REG_WIDTH:FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH] = period_counter_1
                    level_counter_out.next[FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH-1] = transition_counter_1 >= (transition_counter_limit >> 1)
                    sequence_id_out.next = sequence_id_1
                elif sel_laser_in == 1:
                    level_counter_out.next[FPGA_REG_WIDTH:FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH] = period_counter_2
                    level_counter_out.next[FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH-1] = transition_counter_2 >= (transition_counter_limit >> 1)
                    sequence_id_out.next = sequence_id_2
                elif sel_laser_in == 2:
                    level_counter_out.next[FPGA_REG_WIDTH:FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH] = period_counter_3
                    level_counter_out.next[FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH-1] = transition_counter_3 >= (transition_counter_limit >> 1)
                    sequence_id_out.next = sequence_id_3
                elif sel_laser_in == 3:
                    level_counter_out.next[FPGA_REG_WIDTH:FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH] = period_counter_4
                    level_counter_out.next[FPGA_REG_WIDTH-PERIOD_COUNTER_WIDTH-1] = transition_counter_4 >= (transition_counter_limit >> 1)
                    sequence_id_out.next = sequence_id_4

                # The waveform generators for all four lasers run simultaneously and independently
                #  so there is a set of waveform parameter registers for each laser. The registers
                #  for a particular laser can only be updated when that laser is selected.

                # Advance the transition counters once every 10us and the
                #  period counters whenever these overflow. The transition counter
                #  steps through the template and the period counter steps through
                #  the levels that make up the laser current waveform.
                # When the transition counter overflows, check the mode to see if
                #  we need to update the registers of the selected laser.
                # After latching the register values for the selected laser, turn the
                #  mode bit back to zero.

                # The normalized transition template waveform beta(x) takes on values from zero to one
                #  as the normalized time x increases from zero to one. It is defined as the piecewise
                #  linear function:
                #
                # For 0 <= x < 0.5*(1-alpha), beta(x) = (alpha * x)/(1 - alpha)
                # For 0.5*(1-alpha) <= x < 0.5*(1+alpha), beta(x) = ((1-alpha) * x)/alpha + (2*alpha-1)/(2*alpha)
                # For 0.5*(1+alpha) <= x < 1, beta(x) = (alpha * x)/(1 - alpha) + (1-2*alpha)/(1-alpha)
                #
                # When alpha=0.5, this is beta(x)=x, corresponding to linear interpolation. For smaller
                #  values of alpha, we spend more time (by reducing the slopes) close to zero and one,
                #  and less time between the levels.

                # When implemented in the FPGA in de-normalized form x = k/T, where k is the transition
                #  counter value and T is the transition counter limit.
                # The value of the template is represented by an unsigned 16-bit integer (so 65536
                #  represents 1.0) but these are actually the high order bits of a 24-bit accumulator
                #  which synthesizes the waveform from the slope parameters. Setting M=2**24 a normalized
                #  slope of s is represented by the integer (M/T)*s

                # The following state machine implements the following for each laser:
                # There are two 24-bit accumulators, both of which start at zero at k=0. Every 10us, the
                #  "slow" accumulator is incremented by slow_slope and the "fast" accumulator is incremented
                #  by fast_slope.
                # For 0 <= k < first_breakpoint, the output comes from the slow accumulator
                # For first_breakpoint <= k < second_breakpoint, the output is the sum of the fast
                #  accumulator and the first offset.
                # For second_breakpoint <= k < T, the output is the sum of the slow accumulator and
                #  the second offset.

                # In order to implement the linear piecewise function above, we need to set
                # slow_slope = (M/T) * alpha/(1-alpha)
                # fast_slope = (M/T) * (1-alpha)/alpha
                # first_offset = M * (2*alpha-1)/(2*alpha)
                # second_offset = M * (1-2*alpha)/(1-alpha)
                # first_breakpoint = (1-alpha)*T/2
                # second_breakpoint = (1+alpha)*T/2

                if strobe_in:
                    if transition_counter_1 < transition_counter_limit_1 - 1:
                        transition_counter_1.next = transition_counter_1 + 1
                        slow_accumulator_1.next = (slow_accumulator_1 + slow_slope_1) % ACCUMULATOR_MODULO
                        fast_accumulator_1.next = (fast_accumulator_1 + fast_slope_1) % ACCUMULATOR_MODULO
                    else:
                        current_level_1.next = rd_dataB_laser1
                        prev_level_1.next = current_level_1
                        transition_counter_1.next = 0
                        slow_accumulator_1.next = 0
                        fast_accumulator_1.next = 0
                        if period_counter_1 < period_counter_limit_1 - 1:
                            period_counter_1.next = period_counter_1 + 1
                        else:
                            period_counter_1.next = 0
                        if laser_selected == 0 and mode:  # Laser 1 selected
                            slow_slope_1.next = slow_slope
                            fast_slope_1.next = fast_slope
                            first_offset_1.next = first_offset
                            second_offset_1.next = second_offset
                            first_breakpoint_1.next = first_breakpoint
                            second_breakpoint_1.next = second_breakpoint
                            transition_counter_limit_1.next = transition_counter_limit
                            period_counter_limit_1.next = period_counter_limit
                            lower_window_1.next = lower_window
                            upper_window_1.next = upper_window
                            sequence_id_1.next = sequence_id
                            bank_1.next = bank
                            control_status.next[LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B] = 0
                    #
                    if transition_counter_2 < transition_counter_limit_2 - 1:
                        transition_counter_2.next = transition_counter_2 + 1
                        slow_accumulator_2.next = (slow_accumulator_2 + slow_slope_2) % ACCUMULATOR_MODULO
                        fast_accumulator_2.next = (fast_accumulator_2 + fast_slope_2) % ACCUMULATOR_MODULO
                    else:
                        current_level_2.next = rd_dataB_laser2
                        prev_level_2.next = current_level_2
                        transition_counter_2.next = 0
                        slow_accumulator_2.next = 0
                        fast_accumulator_2.next = 0
                        if period_counter_2 < period_counter_limit_2 - 1:
                            period_counter_2.next = period_counter_2 + 1
                        else:
                            period_counter_2.next = 0
                        if laser_selected == 1 and mode:  # Laser 2 selected
                            slow_slope_2.next = slow_slope
                            fast_slope_2.next = fast_slope
                            first_offset_2.next = first_offset
                            second_offset_2.next = second_offset
                            first_breakpoint_2.next = first_breakpoint
                            second_breakpoint_2.next = second_breakpoint
                            transition_counter_limit_2.next = transition_counter_limit
                            period_counter_limit_2.next = period_counter_limit
                            lower_window_2.next = lower_window
                            upper_window_2.next = upper_window
                            sequence_id_2.next = sequence_id
                            bank_2.next = bank
                            control_status.next[LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B] = 0
                    #
                    if transition_counter_3 < transition_counter_limit_3 - 1:
                        transition_counter_3.next = transition_counter_3 + 1
                        slow_accumulator_3.next = (slow_accumulator_3 + slow_slope_3) % ACCUMULATOR_MODULO
                        fast_accumulator_3.next = (fast_accumulator_3 + fast_slope_3) % ACCUMULATOR_MODULO
                    else:
                        current_level_3.next = rd_dataB_laser3
                        prev_level_3.next = current_level_3
                        transition_counter_3.next = 0
                        slow_accumulator_3.next = 0
                        fast_accumulator_3.next = 0
                        if period_counter_3 < period_counter_limit_3 - 1:
                            period_counter_3.next = period_counter_3 + 1
                        else:
                            period_counter_3.next = 0
                        if laser_selected == 2 and mode:  # Laser 3 selected
                            slow_slope_3.next = slow_slope
                            fast_slope_3.next = fast_slope
                            first_offset_3.next = first_offset
                            second_offset_3.next = second_offset
                            first_breakpoint_3.next = first_breakpoint
                            second_breakpoint_3.next = second_breakpoint
                            transition_counter_limit_3.next = transition_counter_limit
                            period_counter_limit_3.next = period_counter_limit
                            lower_window_3.next = lower_window
                            upper_window_3.next = upper_window
                            sequence_id_3.next = sequence_id
                            bank_3.next = bank
                            control_status.next[LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B] = 0
                    #
                    if transition_counter_4 < transition_counter_limit_4 - 1:
                        transition_counter_4.next = transition_counter_4 + 1
                        slow_accumulator_4.next = (slow_accumulator_4 + slow_slope_4) % ACCUMULATOR_MODULO
                        fast_accumulator_4.next = (fast_accumulator_4 + fast_slope_4) % ACCUMULATOR_MODULO
                    else:
                        current_level_4.next = rd_dataB_laser4
                        prev_level_4.next = current_level_4
                        transition_counter_4.next = 0
                        slow_accumulator_4.next = 0
                        fast_accumulator_4.next = 0
                        if period_counter_4 < period_counter_limit_4 - 1:
                            period_counter_4.next = period_counter_4 + 1
                        else:
                            period_counter_4.next = 0
                        if laser_selected == 3 and mode:  # Laser 4 selected
                            slow_slope_4.next = slow_slope
                            fast_slope_4.next = fast_slope
                            first_offset_4.next = first_offset
                            second_offset_4.next = second_offset
                            first_breakpoint_4.next = first_breakpoint
                            second_breakpoint_4.next = second_breakpoint
                            transition_counter_limit_4.next = transition_counter_limit
                            period_counter_limit_4.next = period_counter_limit
                            lower_window_4.next = lower_window
                            upper_window_4.next = upper_window
                            sequence_id_4.next = sequence_id
                            bank_4.next = bank
                            control_status.next[LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B] = 0

                ## Calculate the laser current outputs
                # We use interpolators to transition between the previous level and the current
                #  level, with the interpolation factor beta being taken from the upper 16 bits
                #  of the template output for the appropriate laser
                #
                # The laser_current_in_window output is used to indicate when the current through the
                #  selected laser lies within the range lower_window and upper_window. This is used
                #  to prevent ring-downs from occuring when the current falls outside the window.
                if output_counter == 0:
                    if strobe_in:
                        output_counter.next = 1
                elif output_counter == 1:
                    output_counter.next = 2
                    interp_y0.next = prev_level_1
                    interp_y1.next = current_level_1
                    interp_beta.next = interp_1[LASER_CURRENT_GEN_ACC_WIDTH:LASER_CURRENT_GEN_ACC_WIDTH-FPGA_REG_WIDTH]
                elif output_counter == 2:
                    output_counter.next = 3
                    laser1_fine_current_out.next = interp_yout
                    if sel_laser_in == 0:
                        laser_current_in_window_out.next = (interp_yout >= lower_window_1) and (interp_yout <= upper_window_1)
                elif output_counter == 3:
                    output_counter.next = 4
                    interp_y0.next = prev_level_2
                    interp_y1.next = current_level_2
                    interp_beta.next = interp_2[LASER_CURRENT_GEN_ACC_WIDTH:LASER_CURRENT_GEN_ACC_WIDTH-FPGA_REG_WIDTH]
                elif output_counter == 4:
                    output_counter.next = 5
                    laser2_fine_current_out.next = interp_yout
                    if sel_laser_in == 1:
                        laser_current_in_window_out.next = (interp_yout >= lower_window_2) and (interp_yout <= upper_window_2)
                elif output_counter == 5:
                    output_counter.next = 6
                    interp_y0.next = prev_level_3
                    interp_y1.next = current_level_3
                    interp_beta.next = interp_3[LASER_CURRENT_GEN_ACC_WIDTH:LASER_CURRENT_GEN_ACC_WIDTH-FPGA_REG_WIDTH]
                elif output_counter == 6:
                    output_counter.next = 7
                    laser3_fine_current_out.next = interp_yout
                    if sel_laser_in == 2:
                        laser_current_in_window_out.next = (interp_yout >= lower_window_3) and (interp_yout <= upper_window_3)
                elif output_counter == 7:
                    output_counter.next = 8
                    interp_y0.next = prev_level_4
                    interp_y1.next = current_level_4
                    interp_beta.next = interp_4[LASER_CURRENT_GEN_ACC_WIDTH:LASER_CURRENT_GEN_ACC_WIDTH-FPGA_REG_WIDTH]
                elif output_counter == 8:
                    output_counter.next = 0
                    laser4_fine_current_out.next = interp_yout
                    if sel_laser_in == 3:
                        laser_current_in_window_out.next = (interp_yout >= lower_window_4) and (interp_yout <= upper_window_4)

    @always_comb
    def comb():
        # This selects the appropriate accumulator and offset depending on the time
        # For 0 <= k < first_breakpoint, the output comes from the slow accumulator
        # For first_breakpoint <= k < second_breakpoint, the output is the sum of the fast
        #  accumulator and the first offset.
        # For second_breakpoint <= k < T, the output is the sum of the slow accumulator and
        #  the second offset.

        if transition_counter_1 < first_breakpoint_1:
            interp_1.next = slow_accumulator_1
        elif transition_counter_1 < second_breakpoint_1:
            interp_1.next = (fast_accumulator_1 + first_offset_1) % ACCUMULATOR_MODULO
        else:
            interp_1.next = (slow_accumulator_1 + second_offset_1) % ACCUMULATOR_MODULO

        if transition_counter_2 < first_breakpoint_2:
            interp_2.next = slow_accumulator_2
        elif transition_counter_2 < second_breakpoint_2:
            interp_2.next = (fast_accumulator_2 + first_offset_2) % ACCUMULATOR_MODULO
        else:
            interp_2.next = (slow_accumulator_2 + second_offset_2) % ACCUMULATOR_MODULO

        if transition_counter_3 < first_breakpoint_3:
            interp_3.next = slow_accumulator_3
        elif transition_counter_3 < second_breakpoint_3:
            interp_3.next = (fast_accumulator_3 + first_offset_3) % ACCUMULATOR_MODULO
        else:
            interp_3.next = (slow_accumulator_3 + second_offset_3) % ACCUMULATOR_MODULO

        if transition_counter_4 < first_breakpoint_4:
            interp_4.next = slow_accumulator_4
        elif transition_counter_4 < second_breakpoint_4:
            interp_4.next = (fast_accumulator_4 + first_offset_4) % ACCUMULATOR_MODULO
        else:
            interp_4.next = (slow_accumulator_4 + second_offset_4) % ACCUMULATOR_MODULO

        # Access from FPGA side
        enB_laser1.next = 1
        wr_enB_laser1.next = 0
        addrB_laser1.next[PERIOD_COUNTER_WIDTH:] = period_counter_1
        addrB_laser1.next[PERIOD_COUNTER_WIDTH] = bank_1
        wr_dataB_laser1.next = 0
        enB_laser2.next = 1
        wr_enB_laser2.next = 0
        addrB_laser2.next[PERIOD_COUNTER_WIDTH:] = period_counter_2
        addrB_laser2.next[PERIOD_COUNTER_WIDTH] = bank_2
        wr_dataB_laser2.next = 0
        enB_laser3.next = 1
        wr_enB_laser3.next = 0
        addrB_laser3.next[PERIOD_COUNTER_WIDTH:] = period_counter_3
        addrB_laser3.next[PERIOD_COUNTER_WIDTH] = bank_3
        wr_dataB_laser3.next = 0
        enB_laser4.next = 1
        wr_enB_laser4.next = 0
        addrB_laser4.next[PERIOD_COUNTER_WIDTH:] = period_counter_4
        addrB_laser4.next[PERIOD_COUNTER_WIDTH] = bank_4
        wr_dataB_laser4.next = 0

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    strobe_in = Signal(LOW)
    sel_laser_in = Signal(intbv(0)[2:])
    laser1_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser_current_in_window_out = Signal(LOW)
    level_counter_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sequence_id_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    map_base = FPGA_LASERCURRENTGENERATOR

    toVHDL(LaserCurrentGenerator, clk=clk, reset=reset,
                                  dsp_addr=dsp_addr,
                                  dsp_data_out=dsp_data_out,
                                  dsp_data_in=dsp_data_in,
                                  dsp_wr=dsp_wr, strobe_in=strobe_in,
                                  sel_laser_in=sel_laser_in,
                                  laser1_fine_current_out=laser1_fine_current_out,
                                  laser2_fine_current_out=laser2_fine_current_out,
                                  laser3_fine_current_out=laser3_fine_current_out,
                                  laser4_fine_current_out=laser4_fine_current_out,
                                  laser_current_in_window_out=laser_current_in_window_out,
                                  level_counter_out=level_counter_out,
                                  sequence_id_out=sequence_id_out,
                                  map_base=map_base)
