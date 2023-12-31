#!/usr/bin/python
#
# FILE:
#   RdMan.py
#
# DESCRIPTION:
#   Ringdown manager sequences ringdown cycle

# SEE ALSO:
#
# HISTORY:
#   25-Jun-2009  sze  Initial version.
#   15-Jul-2009  sze  Number of parameters increased to 10 (+2 built-ins)
#   23-Aug-2009  sze  Added RESET_RDMAN bit to control register
#   16-Sep-2009  sze  Added selection between simulated and actual ringdown data
#   10-Jun-2010  sze  Added RINGDOWN_DATA register to test high-speed ADC
#   14-Feb-2011  sze  Added oscilloscope mode for cavity alignment
#   11-Jan-2015  sze  Added precise timing for ringdown and additional laser current
#   01-Oct-2015  sze  Added recording of extended laser current level counter input
#   11-Oct-2015  sze  Added extended laser current sequence id input

from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import (DATA_BANK_ADDR_WIDTH, EMIF_ADDR_WIDTH,
                                    EMIF_DATA_WIDTH, FPGA_RDMAN, FPGA_REG_MASK,
                                    FPGA_REG_WIDTH, META_BANK_ADDR_WIDTH,
                                    PARAM_BANK_ADDR_WIDTH, RDMAN_CONTROL,
                                    RDMAN_CONTROL_ABORT_RD_B,
                                    RDMAN_CONTROL_ABORT_RD_W,
                                    RDMAN_CONTROL_ACQ_DONE_ACK_B,
                                    RDMAN_CONTROL_ACQ_DONE_ACK_W,
                                    RDMAN_CONTROL_BANK0_CLEAR_B,
                                    RDMAN_CONTROL_BANK0_CLEAR_W,
                                    RDMAN_CONTROL_BANK1_CLEAR_B,
                                    RDMAN_CONTROL_BANK1_CLEAR_W,
                                    RDMAN_CONTROL_CONT_B, RDMAN_CONTROL_CONT_W,
                                    RDMAN_CONTROL_RAMP_DITHER_B,
                                    RDMAN_CONTROL_RAMP_DITHER_W,
                                    RDMAN_CONTROL_RD_IRQ_ACK_B,
                                    RDMAN_CONTROL_RD_IRQ_ACK_W,
                                    RDMAN_CONTROL_RESET_RDMAN_B,
                                    RDMAN_CONTROL_RESET_RDMAN_W,
                                    RDMAN_CONTROL_RUN_B, RDMAN_CONTROL_RUN_W,
                                    RDMAN_CONTROL_START_RD_B,
                                    RDMAN_CONTROL_START_RD_W,
                                    RDMAN_DATA_ADDRCNTR, RDMAN_DIVISOR,
                                    RDMAN_EXTRA_DURATION, RDMAN_LOCK_DURATION,
                                    RDMAN_METADATA_ADDR_AT_RINGDOWN,
                                    RDMAN_METADATA_ADDRCNTR, RDMAN_NUM_SAMP,
                                    RDMAN_OFF_DURATION, RDMAN_OPTIONS,
                                    RDMAN_OPTIONS_DITHER_ENABLE_B,
                                    RDMAN_OPTIONS_DITHER_ENABLE_W,
                                    RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B,
                                    RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W,
                                    RDMAN_OPTIONS_LOCK_ENABLE_B,
                                    RDMAN_OPTIONS_LOCK_ENABLE_W,
                                    RDMAN_OPTIONS_SCOPE_MODE_B,
                                    RDMAN_OPTIONS_SCOPE_MODE_W,
                                    RDMAN_OPTIONS_SCOPE_SLOPE_B,
                                    RDMAN_OPTIONS_SCOPE_SLOPE_W,
                                    RDMAN_OPTIONS_SIM_ACTUAL_B,
                                    RDMAN_OPTIONS_SIM_ACTUAL_W,
                                    RDMAN_OPTIONS_UP_SLOPE_ENABLE_B,
                                    RDMAN_OPTIONS_UP_SLOPE_ENABLE_W,
                                    RDMAN_PARAM0, RDMAN_PARAM1, RDMAN_PARAM2,
                                    RDMAN_PARAM3, RDMAN_PARAM4, RDMAN_PARAM5,
                                    RDMAN_PARAM6, RDMAN_PARAM7, RDMAN_PARAM8,
                                    RDMAN_PARAM9, RDMAN_PARAM10, RDMAN_PARAM11,
                                    RDMAN_PARAM12, RDMAN_PARAM13,
                                    RDMAN_PARAM14, RDMAN_PARAM15,
                                    RDMAN_PARAM_ADDRCNTR,
                                    RDMAN_PRECONTROL_DURATION,
                                    RDMAN_RINGDOWN_DATA, RDMAN_STATUS,
                                    RDMAN_STATUS_ABORTED_B,
                                    RDMAN_STATUS_ABORTED_W,
                                    RDMAN_STATUS_ACQ_DONE_B,
                                    RDMAN_STATUS_ACQ_DONE_W,
                                    RDMAN_STATUS_BANK0_IN_USE_B,
                                    RDMAN_STATUS_BANK0_IN_USE_W,
                                    RDMAN_STATUS_BANK1_IN_USE_B,
                                    RDMAN_STATUS_BANK1_IN_USE_W,
                                    RDMAN_STATUS_BANK_B, RDMAN_STATUS_BANK_W,
                                    RDMAN_STATUS_BUSY_B, RDMAN_STATUS_BUSY_W,
                                    RDMAN_STATUS_LAPPED_B,
                                    RDMAN_STATUS_LAPPED_W,
                                    RDMAN_STATUS_LASER_FREQ_LOCKED_B,
                                    RDMAN_STATUS_LASER_FREQ_LOCKED_W,
                                    RDMAN_STATUS_RD_IRQ_B,
                                    RDMAN_STATUS_RD_IRQ_W,
                                    RDMAN_STATUS_SHUTDOWN_B,
                                    RDMAN_STATUS_SHUTDOWN_W,
                                    RDMAN_STATUS_TIMEOUT_B,
                                    RDMAN_STATUS_TIMEOUT_W, RDMAN_THRESHOLD,
                                    RDMAN_TIMEOUT_DURATION,
                                    RDMAN_TUNER_AT_RINGDOWN, RDMEM_DATA_WIDTH,
                                    RDMEM_META_WIDTH, RDMEM_PARAM_WIDTH,
                                    RDMEM_RESERVED_BANK_ADDR_WIDTH)

SeqState = enum("IDLE", "START_INJECT", "WAIT_FOR_PRECONTROL",
                "WAIT_FOR_LOCK", "WAIT_FOR_GATING_CONDITIONS",
                "CHECK_BELOW_THRESHOLD", "WAIT_FOR_THRESHOLD",
                "IN_RINGDOWN", "CHECK_PARAMS_DONE", "ACQ_DONE",
                "AWAIT_SWEEP_1", "AWAIT_SWEEP_2", "WAIT_RD_DONE_1", "WAIT_RD_DONE_2")
MetadataAcqState = enum("IDLE", "AWAIT_STROBE", "ACQUIRING", "DONE")
ParamState = enum("IDLE", "STORING", "DONE")

LOW, HIGH = bool(0), bool(1)


def RdMan(clk, reset, dsp_addr, dsp_data_out, dsp_data_in, dsp_wr,
          pulse_100k_in, pulse_1M_in, tuner_value_in, meta0_in, meta1_in,
          meta2_in, meta3_in, meta4_in, meta5_in, meta6_in, meta7_in,
          rd_sim_in, rd_data_in, tuner_slope_in, tuner_window_in,
          laser_freq_ok_in, metadata_strobe_in, ext_mode_in,
          sel_fine_current_in, ext_laser_current_in_window_in,
          ext_laser_level_counter_in, ext_laser_sequence_id_in,
          rd_trig_out, laser_extra_out, acc_en_out, rd_irq_out,
          acq_done_irq_out, rd_adc_clk_out, bank_out, laser_locked_out,
          data_addr_out, wr_data_out, data_we_out, meta_addr_out,
          wr_meta_out, meta_we_out, param_addr_out, wr_param_out,
          param_we_out, map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    pulse_100k_in       -- 100kHz pulse
    pulse_1M_in         -- 1MHz pulse for timing
    tuner_value_in      -- data from tuner, to be sampled at time of ringdown
    meta0_in            -- WLM ratio 1 (from LaserLocker)
    meta1_in            -- WLM ratio 2 (from LaserLocker)
    meta2_in            -- PZT DAC value
    meta3_in            -- Laser locker tuning offset
    meta4_in            -- Fine laser current from laser locker
    meta5_in            -- Lock error from laser locker
    meta6_in            -- PID output from laser locker
    meta7_in
    rd_sim_in           -- Ringdown data input from simulator
    rd_data_in          -- Ringdown data input from ADC
    tuner_slope_in      -- Tuner slope (1 on up slope, 0 on down slope)
    tuner_window_in     -- Indicates when tuner waveform is within window
    laser_freq_ok_in    -- Indicates when laser frequency is within window set in laser locker
    metadata_strobe_in  -- Indicates when metadata should be stored
    ext_mode_in         -- Indicates if extended laser current control is used
    sel_fine_current_in -- Fine current of selected laser
    ext_laser_current_in_window_in -- Indicates if extended laser current for each laser is within its window
    ext_laser_level_counter_in -- Level counter from extended laser current generator
    ext_laser_sequence_id_in -- Sequence id from extended laser current generator
    rd_trig_out         -- Indicates optical injection should stop
    laser_extra_out     -- Indicates when extra laser current should be applied
    acc_en_out          -- Signals the laser locker to accumulate error signal for control
    rd_irq_out          -- Signals that a ringdown has been initiated, or that a timeout/abort has occured
    acq_done_irq_out    -- Signals that ringdown data have been placed in FPGA memory
    rd_adc_clk_out      -- 25MHz clock to high-speed ADC
    bank_out            -- Bank select for Rdmemory block
    laser_locked_out    -- Indicates laser frequency is locked
    data_addr_out       -- Data address for Rdmemory block
    wr_data_out         -- Ringdown data to write
    data_we_out         -- Enable write of ringdown data
    meta_addr_out       -- Metadata address for Rdmemory block
    wr_meta_out         -- Ringdown metadata to write
    meta_we_out         -- Enable write of ringdown metadata
    param_addr_out      -- Parameter address for Rdmemory block
    wr_param_out        -- Ringdown parameters to write
    param_we_out        -- Enable write of ringdown parameters
    map_base            -- Base address of FPGA block

    Registers:
    RDMAN_CONTROL
    RDMAN_STATUS
    RDMAN_OPTIONS
    RDMAN_PARAM0        -- Injection settings
    RDMAN_PARAM1        -- Temperature of active laser (millidegrees C)
    RDMAN_PARAM2        -- Coarse laser current of active laser
    RDMAN_PARAM3        -- Etalon temperature (millidegrees C)
    RDMAN_PARAM4        -- Cavity pressure (50 x pressure in Torr)
    RDMAN_PARAM5        -- Ambient pressure (50 x pressure in Torr)
    RDMAN_PARAM6        -- Scheme index (which scheme) and row (within a scheme)
    RDMAN_PARAM7        -- Subscheme ID (passthrough)
    RDMAN_PARAM8        -- Ringdown threshold
    RDMAN_PARAM9        -- Spare
    RDMAN_PARAM10       -- Spare
    RDMAN_PARAM11       -- Spare
    RDMAN_PARAM12       -- Spare
    RDMAN_PARAM13       -- Spare
    RDMAN_PARAM14       -- Spare
    RDMAN_PARAM15       -- Spare
    RDMAN_DATA_ADDRCNTR     -- Address counter for ringdown data memory
    RDMAN_METADATA_ADDRCNTR -- Address counter for ringdown metadata memory
    RDMAN_PARAM_ADDRCNTR    -- Address counter for ringdown parameter memory
    RDMAN_DIVISOR       -- Ringdown ADC divisor for data storage
    RDMAN_NUM_SAMP      -- Number of ringdown samples to collect
    RDMAN_THRESHOLD     -- Ringdown threshold
    RDMAN_LOCK_DURATION -- Microseconds to wait with frequency in window before declaring laser frequency locked
    RDMAN_PRECONTROL_DURATION -- Microseconds to keep laser current at nominal value before enabling locking
    RDMAN_OFF_DURATION -- Microseconds to stop optical injection for ringdown to take place
    RDMAN_EXTRA_DURATION -- Microseconds to apply extra laser current after ringdown
    RDMAN_TIMEOUT_DURATION -- Microseconds (32 bit) to wait before giving up on a ringdown
    RDMAN_TUNER_AT_RINGDOWN -- Tuner value at time of ringdown
    RDMAN_METADATA_ADDR_AT_RINGDOWN -- Metadata address at time of ringdown
    RDMAN_RINGDOWN_DATA -- Ringdown data (read-only) from ADC or simulator

    Fields in RDMAN_CONTROL:
    RDMAN_CONTROL_RUN
    RDMAN_CONTROL_CONT
    RDMAN_CONTROL_START_RD  -- Initiates ringdown cycle after DSP has written parameters
    RDMAN_CONTROL_ABORT_RD  -- Programmatically aborts a ringdown cycle
    RDMAN_CONTROL_RESET_RDMAN -- Resets ringdown manager to a sane state
    RDMAN_CONTROL_BANK0_CLEAR -- Indicates that memory bank 0 is available for use
    RDMAN_CONTROL_BANK1_CLEAR -- Indicates that memory bank 1 is available for use
    RDMAN_CONTROL_RD_IRQ_ACK  -- Used to acknowledge ringdown interrupt
    RDMAN_CONTROL_ACQ_DONE_ACK -- Used to acknowledge data collected interrupt
    RDMAN_CONTROL_RAMP_DITHER -- Indicates ramp mode (0) or dither mode (1). Set by DSP.

    Fields in RDMAN_STATUS:
    RDMAN_STATUS_SHUTDOWN   -- Indicates optical injection has been cut off
    RDMAN_STATUS_RD_IRQ     -- Indicates that a ringdown interrupt has been issued
    RDMAN_STATUS_ACQ_DONE   -- Indicates that a acquisition done interrupt has been issued
    RDMAN_STATUS_BANK       -- Indicates current bank for data acquisition
    RDMAN_STATUS_BANK0_IN_USE   -- Indicates memory bank 0 is in use
    RDMAN_STATUS_BANK1_IN_USE   -- Indicates memory bank 1 is in use
    RDMAN_STATUS_LAPPED     -- Indicates metadata has wrapped around
    RDMAN_STATUS_LASER_FREQ_LOCKED -- High while laser frequency is locked
    RDMAN_STATUS_TIMEOUT    -- Indicates that a timeout has occured with no ringdown
    RDMAN_STATUS_ABORTED    -- Indicates that an abort command has been sent
    RDMAN_STATUS_BUSY

    Fields in RDMAN_OPTIONS:
    RDMAN_OPTIONS_LOCK_ENABLE -- Enables laser frequency locking
    RDMAN_OPTIONS_UP_SLOPE_ENABLE -- Enables ringdowns on positive slope of tuner waveform
    RDMAN_OPTIONS_DOWN_SLOPE_ENABLE -- Enables ringdowns on negative slope of tuner waveform
    RDMAN_OPTIONS_DITHER_ENABLE -- Allows transition to dither mode. Used by DSP.
    RDMAN_OPTIONS_SIM_ACTUAL -- Selects simulated (0) or actual (1) data
    RDMAN_OPTIONS_SCOPE_MODE -- Selects normal ringdown mode (0) or oscilloscope mode (1)
    RDMAN_OPTIONS_SCOPE_SLOPE -- Selects falling (0) or rising (1) slope of tuner to trigger oscilloscope
    """
    rdman_control_addr = map_base + RDMAN_CONTROL
    rdman_status_addr = map_base + RDMAN_STATUS
    rdman_options_addr = map_base + RDMAN_OPTIONS
    rdman_param0_addr = map_base + RDMAN_PARAM0
    rdman_param1_addr = map_base + RDMAN_PARAM1
    rdman_param2_addr = map_base + RDMAN_PARAM2
    rdman_param3_addr = map_base + RDMAN_PARAM3
    rdman_param4_addr = map_base + RDMAN_PARAM4
    rdman_param5_addr = map_base + RDMAN_PARAM5
    rdman_param6_addr = map_base + RDMAN_PARAM6
    rdman_param7_addr = map_base + RDMAN_PARAM7
    rdman_param8_addr = map_base + RDMAN_PARAM8
    rdman_param9_addr = map_base + RDMAN_PARAM9
    rdman_param10_addr = map_base + RDMAN_PARAM10
    rdman_param11_addr = map_base + RDMAN_PARAM11
    rdman_param12_addr = map_base + RDMAN_PARAM12
    rdman_param13_addr = map_base + RDMAN_PARAM13
    rdman_param14_addr = map_base + RDMAN_PARAM14
    rdman_param15_addr = map_base + RDMAN_PARAM15
    rdman_data_addrcntr_addr = map_base + RDMAN_DATA_ADDRCNTR
    rdman_metadata_addrcntr_addr = map_base + RDMAN_METADATA_ADDRCNTR
    rdman_param_addrcntr_addr = map_base + RDMAN_PARAM_ADDRCNTR
    rdman_divisor_addr = map_base + RDMAN_DIVISOR
    rdman_num_samp_addr = map_base + RDMAN_NUM_SAMP
    rdman_threshold_addr = map_base + RDMAN_THRESHOLD
    rdman_lock_duration_addr = map_base + RDMAN_LOCK_DURATION
    rdman_precontrol_duration_addr = map_base + RDMAN_PRECONTROL_DURATION
    rdman_off_duration_addr = map_base + RDMAN_OFF_DURATION
    rdman_extra_duration_addr = map_base + RDMAN_EXTRA_DURATION
    rdman_timeout_duration_addr = map_base + RDMAN_TIMEOUT_DURATION
    rdman_tuner_at_ringdown_addr = map_base + RDMAN_TUNER_AT_RINGDOWN
    rdman_metadata_addr_at_ringdown_addr = map_base + RDMAN_METADATA_ADDR_AT_RINGDOWN
    rdman_ringdown_data_addr = map_base + RDMAN_RINGDOWN_DATA
    control = Signal(intbv(0)[FPGA_REG_WIDTH:])
    status = Signal(intbv(0)[FPGA_REG_WIDTH:])
    options = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param0 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param1 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param2 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param3 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param4 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param5 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param6 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param7 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param8 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param9 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param10 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param11 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param12 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param13 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param14 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param15 = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    data_addrcntr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    metadata_addrcntr = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
    param_addrcntr = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH:])
    divisor = Signal(intbv(0)[16:])
    num_samp = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    threshold = Signal(intbv(0)[FPGA_REG_WIDTH:])
    lock_duration = Signal(intbv(0)[FPGA_REG_WIDTH:])
    precontrol_duration = Signal(intbv(0)[FPGA_REG_WIDTH:])
    off_duration = Signal(intbv(0)[FPGA_REG_WIDTH:])
    extra_duration = Signal(intbv(0)[FPGA_REG_WIDTH:])
    timeout_duration = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    tuner_at_ringdown = Signal(intbv(0)[FPGA_REG_WIDTH:])
    metadata_addr_at_ringdown = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ringdown_data = Signal(intbv(0)[18:])

    META_SIZE = (1 << META_BANK_ADDR_WIDTH) / 8

    abort = Signal(LOW)
    acq_done_irq = Signal(LOW)
    bank = Signal(LOW)
    expiry_time = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    freq_gating_conditions = Signal(LOW)
    init_flag = Signal(LOW)
    lapped = Signal(LOW)
    metadata_acq = Signal(LOW)
    metadataAcqState = Signal(MetadataAcqState.IDLE)
    param_acq = Signal(LOW)
    paramState = Signal(ParamState.IDLE)
    rd_adc_clk = Signal(LOW)
    rd_divider = Signal(intbv(0)[16:])
    rd_irq = Signal(LOW)
    rd_trig = Signal(LOW)
    laser_extra = Signal(LOW)
    seqState = Signal(SeqState.IDLE)
    timeout = Signal(LOW)
    tuner_gating_conditions = Signal(LOW)
    us_since_start = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    us_timer_enable = Signal(LOW)
    rd_data = Signal(intbv(0)[FPGA_REG_WIDTH:])
    div50_counter = Signal(intbv(val=0, min=0, max=50))
    us_after_ringdown = Signal(intbv(0)[FPGA_REG_WIDTH + 1:])
    sel_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sel_fine_current_prev = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sel_fine_current_slope = Signal(LOW)
    ext_laser_level_counter = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ext_laser_sequence_id = Signal(intbv(0)[FPGA_REG_WIDTH:])

    @always_comb
    def comb1():
        if options[RDMAN_OPTIONS_SIM_ACTUAL_B]:
            rd_data.next = rd_data_in
        else:
            rd_data.next = rd_sim_in

    @always_comb
    def comb2():
        bank_out.next = bank
        rd_irq_out.next = rd_irq
        acq_done_irq_out.next = acq_done_irq
        rd_trig_out.next = rd_trig
        laser_extra_out.next = laser_extra
        rd_adc_clk_out.next = rd_adc_clk

        # In extended laser current control mode, the slope is inferred from the fine laser current waveform of the selected
        # laser. In normal mode, the slope is obtained from the tuner waveform
        # generator
        if ext_mode_in:
            tuner_gating_conditions.next = (ext_laser_current_in_window_in and
                                            ((sel_fine_current_slope and options[RDMAN_OPTIONS_UP_SLOPE_ENABLE_B]) or
                                             (not sel_fine_current_slope and options[RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B])))
        else:
            tuner_gating_conditions.next = tuner_window_in and ((tuner_slope_in and options[RDMAN_OPTIONS_UP_SLOPE_ENABLE_B]) or
                                                                (not tuner_slope_in and options[RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B]))
        freq_gating_conditions.next = laser_freq_ok_in or not options[
            RDMAN_OPTIONS_LOCK_ENABLE_B]
        wr_data_out.next = rd_data

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                control.next = 0
                status.next = 0
                options.next = 0
                param0.next = 0
                param1.next = 0
                param2.next = 0
                param3.next = 0
                param4.next = 0
                param5.next = 0
                param6.next = 0
                param7.next = 0
                param8.next = 0
                param9.next = 0
                param10.next = 0
                param11.next = 0
                param12.next = 0
                param13.next = 0
                param14.next = 0
                param15.next = 0
                data_addrcntr.next = 0
                metadata_addrcntr.next = 0
                param_addrcntr.next = 0
                divisor.next = 0
                num_samp.next = 0
                threshold.next = 0
                lock_duration.next = 0
                precontrol_duration.next = 0
                off_duration.next = 0
                extra_duration.next = 0
                timeout_duration.next = 0
                tuner_at_ringdown.next = 0
                metadata_addr_at_ringdown.next = 0
                ringdown_data.next = 0

                abort.next = LOW
                acq_done_irq.next = 0
                bank.next = LOW
                expiry_time.next = 0
                init_flag.next = HIGH
                lapped.next = LOW
                metadataAcqState.next = MetadataAcqState.IDLE
                metadata_acq.next = LOW
                paramState.next = ParamState.IDLE
                param_acq.next = LOW
                rd_adc_clk.next = 0
                rd_divider.next = 0
                rd_irq.next = 0
                rd_trig.next = LOW
                seqState.next = SeqState.IDLE
                timeout.next = LOW
                us_since_start.next = 0
                us_timer_enable.next = LOW
                acc_en_out.next = 0
                laser_locked_out.next = 0
                div50_counter.next = 0
                us_after_ringdown.next = 0
                sel_fine_current.next = 0
                sel_fine_current_prev.next = 0
                sel_fine_current_slope.next = LOW
                ext_laser_level_counter.next = 0
                ext_laser_sequence_id.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH - 1] == FPGA_REG_MASK:
                    if False:
                        pass
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_control_addr:  # rw
                        if dsp_wr:
                            control.next = dsp_data_out
                        dsp_data_in.next = control
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_status_addr:  # r
                        dsp_data_in.next = status
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_options_addr:  # rw
                        if dsp_wr:
                            options.next = dsp_data_out
                        dsp_data_in.next = options
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param0_addr:  # rw
                        if dsp_wr:
                            param0.next = dsp_data_out
                        dsp_data_in.next = param0
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param1_addr:  # rw
                        if dsp_wr:
                            param1.next = dsp_data_out
                        dsp_data_in.next = param1
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param2_addr:  # rw
                        if dsp_wr:
                            param2.next = dsp_data_out
                        dsp_data_in.next = param2
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param3_addr:  # rw
                        if dsp_wr:
                            param3.next = dsp_data_out
                        dsp_data_in.next = param3
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param4_addr:  # rw
                        if dsp_wr:
                            param4.next = dsp_data_out
                        dsp_data_in.next = param4
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param5_addr:  # rw
                        if dsp_wr:
                            param5.next = dsp_data_out
                        dsp_data_in.next = param5
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param6_addr:  # rw
                        if dsp_wr:
                            param6.next = dsp_data_out
                        dsp_data_in.next = param6
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param7_addr:  # rw
                        if dsp_wr:
                            param7.next = dsp_data_out
                        dsp_data_in.next = param7
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param8_addr:  # rw
                        if dsp_wr:
                            param8.next = dsp_data_out
                        dsp_data_in.next = param8
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param9_addr:  # rw
                        if dsp_wr:
                            param9.next = dsp_data_out
                        dsp_data_in.next = param9
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param10_addr:  # rw
                        if dsp_wr:
                            param10.next = dsp_data_out
                        dsp_data_in.next = param10
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param11_addr:  # rw
                        if dsp_wr:
                            param11.next = dsp_data_out
                        dsp_data_in.next = param11
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param12_addr:  # rw
                        if dsp_wr:
                            param12.next = dsp_data_out
                        dsp_data_in.next = param12
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param13_addr:  # rw
                        if dsp_wr:
                            param13.next = dsp_data_out
                        dsp_data_in.next = param13
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param14_addr:  # rw
                        if dsp_wr:
                            param14.next = dsp_data_out
                        dsp_data_in.next = param14
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param15_addr:  # rw
                        if dsp_wr:
                            param15.next = dsp_data_out
                        dsp_data_in.next = param15
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_data_addrcntr_addr:  # r
                        dsp_data_in.next = data_addrcntr
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_metadata_addrcntr_addr:  # r
                        dsp_data_in.next = metadata_addrcntr
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_param_addrcntr_addr:  # r
                        dsp_data_in.next = param_addrcntr
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_divisor_addr:  # rw
                        if dsp_wr:
                            divisor.next = dsp_data_out
                        dsp_data_in.next = divisor
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_num_samp_addr:  # rw
                        if dsp_wr:
                            num_samp.next = dsp_data_out
                        dsp_data_in.next = num_samp
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_threshold_addr:  # rw
                        if dsp_wr:
                            threshold.next = dsp_data_out
                        dsp_data_in.next = threshold
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_lock_duration_addr:  # rw
                        if dsp_wr:
                            lock_duration.next = dsp_data_out
                        dsp_data_in.next = lock_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_precontrol_duration_addr:  # rw
                        if dsp_wr:
                            precontrol_duration.next = dsp_data_out
                        dsp_data_in.next = precontrol_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_off_duration_addr:  # rw
                        if dsp_wr:
                            off_duration.next = dsp_data_out
                        dsp_data_in.next = off_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_extra_duration_addr:  # rw
                        if dsp_wr:
                            extra_duration.next = dsp_data_out
                        dsp_data_in.next = extra_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_timeout_duration_addr:  # rw
                        if dsp_wr:
                            timeout_duration.next = dsp_data_out
                        dsp_data_in.next = timeout_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_tuner_at_ringdown_addr:  # r
                        dsp_data_in.next = tuner_at_ringdown
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_metadata_addr_at_ringdown_addr:  # r
                        dsp_data_in.next = metadata_addr_at_ringdown
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == rdman_ringdown_data_addr:  # r
                        dsp_data_in.next = ringdown_data
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                if control[RDMAN_CONTROL_RUN_B]:
                    # Reset the run bit if continuous mode is not selected
                    if not control[RDMAN_CONTROL_CONT_B]:
                        control.next[RDMAN_CONTROL_RUN_B] = 0

                    data_we_out.next = LOW
                    rd_adc_clk.next = not rd_adc_clk
                    if rd_adc_clk:
                        ringdown_data.next = rd_data
                    sel_fine_current.next = sel_fine_current_in
                    ext_laser_level_counter.next = ext_laser_level_counter_in
                    ext_laser_sequence_id.next = ext_laser_sequence_id_in

                    # Ignore requests to start if the state machine is busy
                    if status[RDMAN_STATUS_BUSY_B]:
                        control.next[RDMAN_CONTROL_START_RD_B] = 0

                    if seqState == SeqState.IDLE:
                        status.next[RDMAN_STATUS_BUSY_B] = 0
                        us_since_start.next = 0
                        metadata_acq.next = LOW
                        param_acq.next = LOW
                        us_timer_enable.next = LOW
                        acc_en_out.next = LOW
                        laser_locked_out.next = 0
                        if options[RDMAN_OPTIONS_SCOPE_MODE_B]:
                            status.next[RDMAN_STATUS_BUSY_B] = 1
                            seqState.next = SeqState.AWAIT_SWEEP_1
                        elif control[RDMAN_CONTROL_START_RD_B]:
                            status.next[RDMAN_STATUS_BUSY_B] = 1
                            seqState.next = SeqState.START_INJECT

                    elif seqState == SeqState.AWAIT_SWEEP_1:
                        abort.next = 0
                        timeout.next = 0
                        us_timer_enable.next = HIGH  # Start microsecond counter
                        if bool(tuner_slope_in) != bool(options[RDMAN_OPTIONS_SCOPE_SLOPE_B]):
                            seqState.next = SeqState.AWAIT_SWEEP_2

                    elif seqState == SeqState.AWAIT_SWEEP_2:
                        if bool(tuner_slope_in) == bool(options[RDMAN_OPTIONS_SCOPE_SLOPE_B]):
                            data_addrcntr.next = 0
                            rd_divider.next = 0
                            seqState.next = SeqState.IN_RINGDOWN

                    elif seqState == SeqState.START_INJECT:
                        abort.next = 0
                        timeout.next = 0
                        metadata_acq.next = HIGH    # Start acquiring metadata
                        lapped.next = LOW           # Reset lapped flag
                        us_timer_enable.next = HIGH  # Start microsecond counter
                        acc_en_out.next = LOW
                        expiry_time.next = precontrol_duration
                        seqState.next = SeqState.WAIT_FOR_PRECONTROL

                    elif seqState == SeqState.WAIT_FOR_PRECONTROL:
                        if us_since_start >= expiry_time:
                            if options[RDMAN_OPTIONS_LOCK_ENABLE_B]:
                                acc_en_out.next = HIGH
                                expiry_time.next = us_since_start + lock_duration
                                seqState.next = SeqState.WAIT_FOR_LOCK
                            else:
                                seqState.next = SeqState.WAIT_FOR_GATING_CONDITIONS

                    elif seqState == SeqState.WAIT_FOR_LOCK:
                        acc_en_out.next = HIGH
                        if laser_freq_ok_in:
                            if us_since_start >= expiry_time:
                                laser_locked_out.next = 1
                                seqState.next = SeqState.WAIT_FOR_GATING_CONDITIONS
                        else:
                            expiry_time.next = us_since_start + lock_duration

                    elif seqState == SeqState.WAIT_FOR_GATING_CONDITIONS:
                        # The gating conditions are:
                        #  Laser wavelength in range (if LOCK_ENABLE is selected)
                        #  Tuner is within window
                        #  Tuner slope is correct
                        if not freq_gating_conditions:
                            laser_locked_out.next = 0
                            seqState.next = SeqState.WAIT_FOR_LOCK
                        elif tuner_gating_conditions:
                            seqState.next = SeqState.CHECK_BELOW_THRESHOLD

                    elif seqState == SeqState.CHECK_BELOW_THRESHOLD:
                        if rd_data < threshold:
                            seqState.next = SeqState.WAIT_FOR_THRESHOLD
                        else:
                            seqState.next = SeqState.WAIT_FOR_GATING_CONDITIONS

                    elif seqState == SeqState.WAIT_FOR_THRESHOLD:
                        if not freq_gating_conditions:
                            laser_locked_out.next = 0
                            seqState.next = SeqState.WAIT_FOR_LOCK
                        elif not tuner_gating_conditions:
                            seqState.next = SeqState.WAIT_FOR_GATING_CONDITIONS
                        elif rd_data >= threshold:
                            seqState.next = SeqState.IN_RINGDOWN
                            rd_trig.next = HIGH          # Turn off the injection to start ringdown
                            metadata_acq.next = LOW      # Stop metadata collection
                            data_addrcntr.next = 0
                            rd_divider.next = 0
                            # Latch the metadata address counter and tuner value at ringdown
                            #  Note that the MSB of the metadata address is used to indicate a
                            #  lapped condition
                            metadata_addr_at_ringdown.next = metadata_addrcntr
                            metadata_addr_at_ringdown.next[
                                FPGA_REG_WIDTH - 1] = lapped
                            if ext_mode_in:
                                tuner_at_ringdown.next = sel_fine_current_in
                            else:
                                tuner_at_ringdown.next = tuner_value_in
                            us_timer_enable.next = LOW  # No more timeouts
                            rd_irq.next = 1
                            # The init_flag is used to allow num_samp = 0 represent 4096
                            #  data points
                            init_flag.next = HIGH

                    elif seqState == SeqState.IN_RINGDOWN:
                        param_acq.next = HIGH        # Start parameter storage
                        if rd_adc_clk:
                            # Continue until num_samp samples have been
                            # collected
                            if data_addrcntr == num_samp and not init_flag:
                                seqState.next = SeqState.CHECK_PARAMS_DONE
                                if bank:
                                    status.next[
                                        RDMAN_STATUS_BANK1_IN_USE_B] = 1
                                else:
                                    status.next[
                                        RDMAN_STATUS_BANK0_IN_USE_B] = 1
                            elif rd_divider == divisor:
                                rd_divider.next = 0
                                data_addrcntr.next = (
                                    data_addrcntr + 1) % data_addrcntr.max
                                init_flag.next = LOW
                                data_we_out.next = HIGH
                            else:
                                rd_divider.next = (
                                    rd_divider + 1) % divisor.max

                    elif seqState == SeqState.CHECK_PARAMS_DONE:
                        if paramState == ParamState.DONE:
                            seqState.next = SeqState.ACQ_DONE
                            metadataAcqState.next = MetadataAcqState.IDLE
                            paramState.next = ParamState.IDLE

                    elif seqState == SeqState.ACQ_DONE:
                        bank.next = not bank
                        acq_done_irq.next = 1  # Raise acq_done_irq
                        seqState.next = SeqState.WAIT_RD_DONE_1

                    elif seqState == SeqState.WAIT_RD_DONE_1:
                        seqState.next = SeqState.WAIT_RD_DONE_2

                    elif seqState == SeqState.WAIT_RD_DONE_2:
                        if div50_counter == 0 and us_after_ringdown == 0:
                            seqState.next = SeqState.IDLE

                    else:
                        seqState.next = SeqState.IDLE

                    # Parameter storage state machine - writes parameter
                    #  data together with tuner value and metadata address
                    #  at ringdown into parameter memory at the current bank
                    if paramState == ParamState.IDLE:
                        param_we_out.next = LOW
                        if param_acq:
                            param_addrcntr.next = 0
                            paramState.next = ParamState.STORING
                    elif paramState == ParamState.STORING:
                        # Store parameters on the next nineteen clock cycles
                        param_we_out.next = HIGH
                        param_addrcntr.next = param_addrcntr + 1
                        if param_addrcntr[5:] == 0:
                            wr_param_out.next = param0
                        elif param_addrcntr[5:] == 1:
                            wr_param_out.next = param1
                        elif param_addrcntr[5:] == 2:
                            wr_param_out.next = param2
                        elif param_addrcntr[5:] == 3:
                            wr_param_out.next = param3
                        elif param_addrcntr[5:] == 4:
                            wr_param_out.next = param4
                        elif param_addrcntr[5:] == 5:
                            wr_param_out.next = param5
                        elif param_addrcntr[5:] == 6:
                            wr_param_out.next = param6
                        elif param_addrcntr[5:] == 7:
                            wr_param_out.next = param7
                        elif param_addrcntr[5:] == 8:
                            wr_param_out.next = param8
                        elif param_addrcntr[5:] == 9:
                            wr_param_out.next = param9
                        # elif param_addrcntr[5:] == 10:
                        #     wr_param_out.next = param10
                        # elif param_addrcntr[5:] == 11:
                        #     wr_param_out.next = param11
                        # elif param_addrcntr[5:] == 12:
                        #     wr_param_out.next = param12
                        # elif param_addrcntr[5:] == 13:
                        #     wr_param_out.next = param13
                        # elif param_addrcntr[5:] == 14:
                        #     wr_param_out.next = param14
                        # elif param_addrcntr[5:] == 15:
                        #     wr_param_out.next = param15
                        # elif param_addrcntr[5:] == 16:
                        #     wr_param_out.next = tuner_at_ringdown
                        # elif param_addrcntr[5:] == 17:
                        #     wr_param_out.next = metadata_addr_at_ringdown
                        # elif param_addrcntr[5:] == 18:
                        #     wr_param_out.next = ext_laser_level_counter
                        elif param_addrcntr[5:] == 10:
                            wr_param_out.next = tuner_at_ringdown
                        elif param_addrcntr[5:] == 11:
                            wr_param_out.next = metadata_addr_at_ringdown
                        elif param_addrcntr[5:] == 12:
                            wr_param_out.next = ext_laser_level_counter
                        elif param_addrcntr[5:] == 13:
                            wr_param_out.next = ext_laser_sequence_id
                        elif param_addrcntr[5:] == 14:
                            wr_param_out.next = param10
                        elif param_addrcntr[5:] == 15:
                            wr_param_out.next = param11
                        elif param_addrcntr[5:] == 16:
                            wr_param_out.next = param12
                        elif param_addrcntr[5:] == 17:
                            wr_param_out.next = param13
                        elif param_addrcntr[5:] == 18:
                            wr_param_out.next = param14
                        else:
                            wr_param_out.next = param15
                            paramState.next = ParamState.DONE
                    elif paramState == ParamState.DONE:
                        param_acq.next = LOW
                        param_we_out.next = LOW
                    else:
                        paramState.next = ParamState.IDLE

                    # Metadata storage state machine - collects metadata
                    #  when metadata_strobe_in goes high into a modified circular
                    #  buffer
                    if metadataAcqState == MetadataAcqState.IDLE:
                        meta_we_out.next = LOW
                        metadata_addrcntr.next = 0  # Reset address counters
                        metadataAcqState.next = MetadataAcqState.AWAIT_STROBE
                    elif metadataAcqState == MetadataAcqState.AWAIT_STROBE:
                        if metadata_acq and metadata_strobe_in:
                            metadataAcqState.next = MetadataAcqState.ACQUIRING
                            # Compute the slope of the fine current of the selected laser for the
                            #  purposes of extended laser current control
                            sel_fine_current_slope.next = (
                                sel_fine_current >= sel_fine_current_prev)
                            sel_fine_current_prev.next = sel_fine_current
                    elif metadataAcqState == MetadataAcqState.ACQUIRING:
                        # Stop acquisition promptly if metadata_acq goes False
                        #  (i.e., a ringdown is initiated)
                        if not metadata_acq:
                            metadataAcqState.next = MetadataAcqState.DONE
                        else:
                            # Store metadata on the next eight clock cycles
                            meta_we_out.next = HIGH
                            if metadata_addrcntr < 8 * META_SIZE - 1:
                                metadata_addrcntr.next = metadata_addrcntr + 1
                            else:
                                metadata_addrcntr.next = 4 * META_SIZE
                                lapped.next = HIGH
                            if metadata_addrcntr[3:] == 0:
                                wr_meta_out.next = meta0_in
                            elif metadata_addrcntr[3:] == 1:
                                wr_meta_out.next = meta1_in
                            elif metadata_addrcntr[3:] == 2:
                                wr_meta_out.next = meta2_in
                            elif metadata_addrcntr[3:] == 3:
                                wr_meta_out.next = meta3_in
                            elif metadata_addrcntr[3:] == 4:
                                wr_meta_out.next = meta4_in
                            elif metadata_addrcntr[3:] == 5:
                                wr_meta_out.next = meta5_in
                            elif metadata_addrcntr[3:] == 6:
                                wr_meta_out.next = meta6_in
                            else:
                                wr_meta_out.next = meta7_in
                                metadataAcqState.next = MetadataAcqState.DONE
                    elif metadataAcqState == MetadataAcqState.DONE:
                        meta_we_out.next = LOW
                        if not metadata_strobe_in:
                            metadataAcqState.next = MetadataAcqState.AWAIT_STROBE
                    else:
                        metadataAcqState.next = MetadataAcqState.IDLE

                    # Timeout detection
                    if us_timer_enable and pulse_1M_in:
                        us_since_start.next = us_since_start.next + 1
                        if us_since_start >= timeout_duration:
                            timeout.next = 1
                            metadata_acq.next = LOW
                            param_acq.next = LOW
                            us_timer_enable.next = LOW
                            metadataAcqState.next = MetadataAcqState.IDLE
                            paramState.next = ParamState.IDLE
                            # Signal an abnormal ringdown interrupt
                            rd_trig.next = HIGH     # Turn off the injection
                            rd_irq.next = 1
                            seqState.next = SeqState.WAIT_RD_DONE_1

                    # Abort detection
                    if control[RDMAN_CONTROL_ABORT_RD_B]:
                        control.next[RDMAN_CONTROL_ABORT_RD_B] = 0
                        rd_trig.next = HIGH     # Turn off the injection
                        abort.next = 1
                        rd_irq.next = 1
                        acq_done_irq.next = LOW
                        metadata_acq.next = LOW
                        param_acq.next = LOW
                        us_timer_enable.next = LOW
                        seqState.next = SeqState.WAIT_RD_DONE_1
                        metadataAcqState.next = MetadataAcqState.IDLE
                        paramState.next = ParamState.IDLE

                    # Reset manager to a known state
                    if control[RDMAN_CONTROL_RESET_RDMAN_B]:
                        control.next[RDMAN_CONTROL_RESET_RDMAN_B] = 0
                        rd_trig.next = HIGH     # Turn off the injection
                        abort.next = 0
                        rd_irq.next = LOW
                        acq_done_irq.next = LOW
                        metadata_acq.next = LOW
                        param_acq.next = LOW
                        us_timer_enable.next = LOW
                        seqState.next = SeqState.WAIT_RD_DONE_1
                        metadataAcqState.next = MetadataAcqState.IDLE
                        paramState.next = ParamState.IDLE

                    # Ringdown IRQ acknowledgement
                    if control[RDMAN_CONTROL_RD_IRQ_ACK_B]:
                        control.next[RDMAN_CONTROL_RD_IRQ_ACK_B] = 0
                        rd_irq.next = LOW

                    # Acquisition done IRQ acknowledgement
                    if control[RDMAN_CONTROL_ACQ_DONE_ACK_B]:
                        control.next[RDMAN_CONTROL_ACQ_DONE_ACK_B] = 0
                        acq_done_irq.next = LOW

                    # Mark bank0 available
                    if control[RDMAN_CONTROL_BANK0_CLEAR_B]:
                        control.next[RDMAN_CONTROL_BANK0_CLEAR_B] = 0
                        status.next[RDMAN_STATUS_BANK0_IN_USE_B] = 0

                    # Mark bank1 available
                    if control[RDMAN_CONTROL_BANK1_CLEAR_B]:
                        control.next[RDMAN_CONTROL_BANK1_CLEAR_B] = 0
                        status.next[RDMAN_STATUS_BANK1_IN_USE_B] = 0

                    data_addr_out.next = data_addrcntr
                    meta_addr_out.next = metadata_addrcntr
                    param_addr_out.next = param_addrcntr

                # Advance ringdown counter
                if div50_counter == 0 and us_after_ringdown == 0:
                    if rd_trig:
                        div50_counter.next = div50_counter + 1
                else:
                    if div50_counter == div50_counter.max - 1:
                        div50_counter.next = 0
                        us_after_ringdown.next = us_after_ringdown + 1
                    else:
                        div50_counter.next = div50_counter + 1
                if us_after_ringdown >= off_duration:
                    rd_trig.next = LOW  # Restart injection
                    laser_extra.next = HIGH
                if us_after_ringdown >= off_duration + extra_duration:
                    laser_extra.next = LOW
                    div50_counter.next = 0
                    us_after_ringdown.next = 0

                status.next[RDMAN_STATUS_ACQ_DONE_B] = acq_done_irq
                status.next[RDMAN_STATUS_BANK_B] = bank
                status.next[RDMAN_STATUS_LAPPED_B] = lapped
                status.next[RDMAN_STATUS_RD_IRQ_B] = rd_irq
                status.next[RDMAN_STATUS_SHUTDOWN_B] = rd_trig
                status.next[RDMAN_STATUS_ABORTED_B] = abort
                status.next[RDMAN_STATUS_TIMEOUT_B] = timeout
    return instances()


if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    pulse_100k_in = Signal(LOW)
    pulse_1M_in = Signal(LOW)
    tuner_value_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta0_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta1_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta2_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta3_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta4_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta5_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta6_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta7_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rd_sim_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rd_data_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuner_slope_in = Signal(LOW)
    tuner_window_in = Signal(LOW)
    laser_freq_ok_in = Signal(LOW)
    metadata_strobe_in = Signal(LOW)
    ext_mode_in = Signal(LOW)
    sel_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ext_laser_current_in_window_in = Signal(LOW)
    ext_laser_level_counter_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ext_laser_sequence_id_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rd_trig_out = Signal(LOW)
    laser_extra_out = Signal(LOW)
    acc_en_out = Signal(LOW)
    rd_irq_out = Signal(LOW)
    acq_done_irq_out = Signal(LOW)
    rd_adc_clk_out = Signal(LOW)
    bank_out = Signal(LOW)
    laser_locked_out = Signal(LOW)
    data_addr_out = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    wr_data_out = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
    data_we_out = Signal(LOW)
    meta_addr_out = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
    wr_meta_out = Signal(intbv(0)[RDMEM_META_WIDTH:])
    meta_we_out = Signal(LOW)
    param_addr_out = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH:])
    wr_param_out = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
    param_we_out = Signal(LOW)
    map_base = FPGA_RDMAN

    toVHDL(RdMan, clk=clk, reset=reset, dsp_addr=dsp_addr,
           dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
           dsp_wr=dsp_wr, pulse_100k_in=pulse_100k_in,
           pulse_1M_in=pulse_1M_in,
           tuner_value_in=tuner_value_in, meta0_in=meta0_in,
           meta1_in=meta1_in, meta2_in=meta2_in,
           meta3_in=meta3_in, meta4_in=meta4_in,
           meta5_in=meta5_in, meta6_in=meta6_in,
           meta7_in=meta7_in, rd_sim_in=rd_sim_in,
           rd_data_in=rd_data_in, tuner_slope_in=tuner_slope_in,
           tuner_window_in=tuner_window_in,
           laser_freq_ok_in=laser_freq_ok_in,
           metadata_strobe_in=metadata_strobe_in,
           ext_mode_in=ext_mode_in,
           sel_fine_current_in=sel_fine_current_in,
           ext_laser_current_in_window_in=ext_laser_current_in_window_in,
           ext_laser_level_counter_in=ext_laser_level_counter_in,
           ext_laser_sequence_id_in=ext_laser_sequence_id_in,
           rd_trig_out=rd_trig_out,
           laser_extra_out=laser_extra_out,
           acc_en_out=acc_en_out, rd_irq_out=rd_irq_out,
           acq_done_irq_out=acq_done_irq_out,
           rd_adc_clk_out=rd_adc_clk_out, bank_out=bank_out,
           laser_locked_out=laser_locked_out,
           data_addr_out=data_addr_out, wr_data_out=wr_data_out,
           data_we_out=data_we_out, meta_addr_out=meta_addr_out,
           wr_meta_out=wr_meta_out, meta_we_out=meta_we_out,
           param_addr_out=param_addr_out,
           wr_param_out=wr_param_out, param_we_out=param_we_out,
           map_base=map_base)
