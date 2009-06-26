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
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH, META_BANK_ADDR_WIDTH, PARAM_BANK_ADDR_WIDTH
from Host.autogen.interface import RDMEM_DATA_WIDTH, RDMEM_META_WIDTH, RDMEM_PARAM_WIDTH, RDMEM_RESERVED_BANK_ADDR_WIDTH
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_RDMAN

from Host.autogen.interface import RDMAN_CONTROL, RDMAN_STATUS
from Host.autogen.interface import RDMAN_PARAM0, RDMAN_PARAM1
from Host.autogen.interface import RDMAN_PARAM2, RDMAN_PARAM3
from Host.autogen.interface import RDMAN_PARAM4, RDMAN_PARAM5
from Host.autogen.interface import RDMAN_PARAM6, RDMAN_PARAM7
from Host.autogen.interface import RDMAN_DATA_ADDRCNTR
from Host.autogen.interface import RDMAN_METADATA_ADDRCNTR
from Host.autogen.interface import RDMAN_PARAM_ADDRCNTR, RDMAN_DIVISOR
from Host.autogen.interface import RDMAN_NUM_SAMP, RDMAN_THRESHOLD
from Host.autogen.interface import RDMAN_LOCK_DURATION
from Host.autogen.interface import RDMAN_PRECONTROL_DURATION
from Host.autogen.interface import RDMAN_TIMEOUT_DURATION
from Host.autogen.interface import RDMAN_TUNER_AT_RINGDOWN
from Host.autogen.interface import RDMAN_METADATA_ADDR_AT_RINGDOWN

from Host.autogen.interface import RDMAN_CONTROL_RUN_B, RDMAN_CONTROL_RUN_W
from Host.autogen.interface import RDMAN_CONTROL_CONT_B, RDMAN_CONTROL_CONT_W
from Host.autogen.interface import RDMAN_CONTROL_START_RD_B, RDMAN_CONTROL_START_RD_W
from Host.autogen.interface import RDMAN_CONTROL_ABORT_RD_B, RDMAN_CONTROL_ABORT_RD_W
from Host.autogen.interface import RDMAN_CONTROL_LOCK_ENABLE_B, RDMAN_CONTROL_LOCK_ENABLE_W
from Host.autogen.interface import RDMAN_CONTROL_UP_SLOPE_ENABLE_B, RDMAN_CONTROL_UP_SLOPE_ENABLE_W
from Host.autogen.interface import RDMAN_CONTROL_DOWN_SLOPE_ENABLE_B, RDMAN_CONTROL_DOWN_SLOPE_ENABLE_W
from Host.autogen.interface import RDMAN_CONTROL_BANK0_CLEAR_B, RDMAN_CONTROL_BANK0_CLEAR_W
from Host.autogen.interface import RDMAN_CONTROL_BANK1_CLEAR_B, RDMAN_CONTROL_BANK1_CLEAR_W
from Host.autogen.interface import RDMAN_CONTROL_RD_IRQ_ACK_B, RDMAN_CONTROL_RD_IRQ_ACK_W
from Host.autogen.interface import RDMAN_CONTROL_ACQ_DONE_ACK_B, RDMAN_CONTROL_ACQ_DONE_ACK_W
from Host.autogen.interface import RDMAN_STATUS_SHUTDOWN_B, RDMAN_STATUS_SHUTDOWN_W
from Host.autogen.interface import RDMAN_STATUS_RD_IRQ_B, RDMAN_STATUS_RD_IRQ_W
from Host.autogen.interface import RDMAN_STATUS_ACQ_DONE_B, RDMAN_STATUS_ACQ_DONE_W
from Host.autogen.interface import RDMAN_STATUS_BANK_B, RDMAN_STATUS_BANK_W
from Host.autogen.interface import RDMAN_STATUS_BANK0_IN_USE_B, RDMAN_STATUS_BANK0_IN_USE_W
from Host.autogen.interface import RDMAN_STATUS_BANK1_IN_USE_B, RDMAN_STATUS_BANK1_IN_USE_W
from Host.autogen.interface import RDMAN_STATUS_LAPPED_B, RDMAN_STATUS_LAPPED_W
from Host.autogen.interface import RDMAN_STATUS_LASER_FREQ_LOCKED_B, RDMAN_STATUS_LASER_FREQ_LOCKED_W
from Host.autogen.interface import RDMAN_STATUS_TIMEOUT_B, RDMAN_STATUS_TIMEOUT_W
from Host.autogen.interface import RDMAN_STATUS_ABORTED_B, RDMAN_STATUS_ABORTED_W

SeqState = enum("IDLE","START_INJECT","WAIT_FOR_PRECONTROL",
                "WAIT_FOR_LOCK","WAIT_FOR_GATING_CONDITIONS")
MetadataAcqState = enum("IDLE","AWAIT_STROBE","ACQUIRING","DONE")

LOW, HIGH = bool(0), bool(1)
def RdMan(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,
          pulse_100k_in,pulse_1M_in,tuner_value_in,meta0_in,meta1_in,
          meta2_in,meta3_in,meta4_in,meta5_in,meta6_in,meta7_in,
          rd_data_in,tuner_slope_in,tuner_window_in,laser_freq_ok_in,
          metadata_strobe_in,rd_trig_out,acc_en_out,rd_irq_out,
          acq_done_irq_out,rd_adc_clk_out,bank_out,data_addr_out,
          wr_data_out,data_we_out,meta_addr_out,wr_meta_out,meta_we_out,
          param_addr_out,wr_param_out,param_we_out,map_base):
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
    meta6_in
    meta7_in
    rd_data_in          -- Ringdown data input from ADC
    tuner_slope_in      -- Tuner slope (1 on up slope, 0 on down slope)
    tuner_window_in     -- Indicates when tuner waveform is within window
    laser_freq_ok_in    -- Indicates when laser frequency is within window set in laser locker
    metadata_strobe_in  -- Indicates when metadata should be stored
    rd_trig_out         -- Indicates optical injection should stop
    acc_en_out          -- Signals the laser locker to accumulate error signal for control
    rd_irq_out          -- Signals that a ringdown has been initiated, or that a timeout/abort has occured
    acq_done_irq_out    -- Signals that ringdown data have been placed in FPGA memory
    rd_adc_clk_out      -- 25MHz clock to high-speed ADC
    bank_out            -- Bank select for Rdmemory block
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
    RDMAN_PARAM0        -- Injection settings
    RDMAN_PARAM1        -- Temperature of active laser (millidegrees C)
    RDMAN_PARAM2        -- Coarse laser current of active laser
    RDMAN_PARAM3        -- Etalon temperature (millidegrees C)
    RDMAN_PARAM4        -- Cavity pressure (50 x pressure in Torr)
    RDMAN_PARAM5        -- Scheme row (within a scheme)
    RDMAN_PARAM6        -- Scheme index (which scheme)
    RDMAN_PARAM7        -- Ringdown threshold
    RDMAN_DATA_ADDRCNTR     -- Address counter for ringdown data memory
    RDMAN_METADATA_ADDRCNTR -- Address counter for ringdown metadata memory
    RDMAN_PARAM_ADDRCNTR    -- Address counter for ringdown parameter memory
    RDMAN_DIVISOR       -- Ringdown ADC divisor for data storage
    RDMAN_NUM_SAMP      -- Number of ringdown samples to collect
    RDMAN_THRESHOLD     -- Ringdown threshold
    RDMAN_LOCK_DURATION -- Microseconds to wait with frequency in window before declaring laser frequency locked
    RDMAN_PRECONTROL_DURATION -- Microseconds to keep laser frequency at nominal value before enabling locking
    RDMAN_TIMEOUT_DURATION -- Microseconds (32 bit) to wait before giving up on a ringdown
    RDMAN_TUNER_AT_RINGDOWN -- Tuner value at time of ringdown
    RDMAN_METADATA_ADDR_AT_RINGDOWN -- Metadata address at time of ringdown

    Fields in RDMAN_CONTROL:
    RDMAN_CONTROL_RUN
    RDMAN_CONTROL_CONT
    RDMAN_CONTROL_START_RD  -- Initiates ringdown cycle after DSP has written parameters
    RDMAN_CONTROL_ABORT_RD  -- Programmatically aborts a ringdown cycle
    RDMAN_CONTROL_LOCK_ENABLE -- Enables laser frequency locking
    RDMAN_CONTROL_UP_SLOPE_ENABLE -- Enables ringdowns on positive slope of tuner waveform
    RDMAN_CONTROL_DOWN_SLOPE_ENABLE -- Enables ringdowns on negative slope of tuner waveform
    RDMAN_CONTROL_BANK0_CLEAR -- Indicates that memory bank 0 is available for use
    RDMAN_CONTROL_BANK1_CLEAR -- Indicates that memory bank 1 is available for use
    RDMAN_CONTROL_RD_IRQ_ACK  -- Used to acknowledge ringdown interrupt
    RDMAN_CONTROL_ACQ_DONE_ACK -- Used to acknowledge data collected interrupt

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
    """
    rdman_control_addr = map_base + RDMAN_CONTROL
    rdman_status_addr = map_base + RDMAN_STATUS
    rdman_param0_addr = map_base + RDMAN_PARAM0
    rdman_param1_addr = map_base + RDMAN_PARAM1
    rdman_param2_addr = map_base + RDMAN_PARAM2
    rdman_param3_addr = map_base + RDMAN_PARAM3
    rdman_param4_addr = map_base + RDMAN_PARAM4
    rdman_param5_addr = map_base + RDMAN_PARAM5
    rdman_param6_addr = map_base + RDMAN_PARAM6
    rdman_param7_addr = map_base + RDMAN_PARAM7
    rdman_data_addrcntr_addr = map_base + RDMAN_DATA_ADDRCNTR
    rdman_metadata_addrcntr_addr = map_base + RDMAN_METADATA_ADDRCNTR
    rdman_param_addrcntr_addr = map_base + RDMAN_PARAM_ADDRCNTR
    rdman_divisor_addr = map_base + RDMAN_DIVISOR
    rdman_num_samp_addr = map_base + RDMAN_NUM_SAMP
    rdman_threshold_addr = map_base + RDMAN_THRESHOLD
    rdman_lock_duration_addr = map_base + RDMAN_LOCK_DURATION
    rdman_precontrol_duration_addr = map_base + RDMAN_PRECONTROL_DURATION
    rdman_timeout_duration_addr = map_base + RDMAN_TIMEOUT_DURATION
    rdman_tuner_at_ringdown_addr = map_base + RDMAN_TUNER_AT_RINGDOWN
    rdman_metadata_addr_at_ringdown_addr = map_base + RDMAN_METADATA_ADDR_AT_RINGDOWN
    control = Signal(intbv(0)[FPGA_REG_WIDTH:])
    status = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param0 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param5 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param6 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    param7 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    data_addrcntr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
    metadata_addrcntr = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
    param_addrcntr = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH:])
    divisor = Signal(intbv(0)[FPGA_REG_WIDTH:])
    num_samp = Signal(intbv(0)[FPGA_REG_WIDTH:])
    threshold = Signal(intbv(0)[FPGA_REG_WIDTH:])
    lock_duration = Signal(intbv(0)[FPGA_REG_WIDTH:])
    precontrol_duration = Signal(intbv(0)[FPGA_REG_WIDTH:])
    timeout_duration = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    tuner_at_ringdown = Signal(intbv(0)[FPGA_REG_WIDTH:])
    metadata_addr_at_ringdown = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
    
    META_SIZE  = (1<<META_BANK_ADDR_WIDTH)/8

    abort = Signal(LOW)
    acq_done_irq = Signal(LOW)
    bank = Signal(LOW)
    expiry_time = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    lapped = Signal(LOW)
    metadataAcqState = Signal(MetadataAcqState.IDLE)
    metadata_acq = Signal(LOW)
    rd_irq = Signal(LOW)
    rd_trig = Signal(LOW)
    seqState = Signal(SeqState.IDLE)
    timeout = Signal(LOW)
    us_since_start = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    us_timer_enable = Signal(LOW)
    
    @always_comb
    def comb():
        bank_out.next = bank
        rd_irq_out.next = rd_irq
        acq_done_irq_out.next = acq_done_irq
        rd_trig_out.next = rd_trig
        
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                control.next = 0
                status.next = 0
                param0.next = 0
                param1.next = 0
                param2.next = 0
                param3.next = 0
                param4.next = 0
                param5.next = 0
                param6.next = 0
                param7.next = 0
                data_addrcntr.next = 0
                metadata_addrcntr.next = 0
                param_addrcntr.next = 0
                divisor.next = 0
                num_samp.next = 0
                threshold.next = 0
                lock_duration.next = 0
                precontrol_duration.next = 0
                timeout_duration.next = 0
                tuner_at_ringdown.next = 0
                metadata_addr_at_ringdown.next = 0
                
                abort.next = LOW
                acq_done_irq.next = 0
                bank.next = LOW
                expiry_time.next = 0
                lapped.next = LOW
                metadataAcqState.next = MetadataAcqState.IDLE
                metadata_acq.next = LOW
                rd_irq.next = 0
                rd_trig.next = HIGH
                seqState.next = SeqState.IDLE
                timeout.next = LOW
                us_since_start.next = 0
                us_timer_enable.next = LOW
                acc_en_out.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_control_addr: # rw
                        if dsp_wr: control.next = dsp_data_out
                        dsp_data_in.next = control
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_status_addr: # r
                        dsp_data_in.next = status
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param0_addr: # rw
                        if dsp_wr: param0.next = dsp_data_out
                        dsp_data_in.next = param0
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param1_addr: # rw
                        if dsp_wr: param1.next = dsp_data_out
                        dsp_data_in.next = param1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param2_addr: # rw
                        if dsp_wr: param2.next = dsp_data_out
                        dsp_data_in.next = param2
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param3_addr: # rw
                        if dsp_wr: param3.next = dsp_data_out
                        dsp_data_in.next = param3
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param4_addr: # rw
                        if dsp_wr: param4.next = dsp_data_out
                        dsp_data_in.next = param4
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param5_addr: # rw
                        if dsp_wr: param5.next = dsp_data_out
                        dsp_data_in.next = param5
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param6_addr: # rw
                        if dsp_wr: param6.next = dsp_data_out
                        dsp_data_in.next = param6
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param7_addr: # rw
                        if dsp_wr: param7.next = dsp_data_out
                        dsp_data_in.next = param7
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_data_addrcntr_addr: # r
                        dsp_data_in.next = data_addrcntr
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_metadata_addrcntr_addr: # r
                        dsp_data_in.next = metadata_addrcntr
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_param_addrcntr_addr: # r
                        dsp_data_in.next = param_addrcntr
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_divisor_addr: # rw
                        if dsp_wr: divisor.next = dsp_data_out
                        dsp_data_in.next = divisor
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_num_samp_addr: # rw
                        if dsp_wr: num_samp.next = dsp_data_out
                        dsp_data_in.next = num_samp
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_threshold_addr: # rw
                        if dsp_wr: threshold.next = dsp_data_out
                        dsp_data_in.next = threshold
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_lock_duration_addr: # rw
                        if dsp_wr: lock_duration.next = dsp_data_out
                        dsp_data_in.next = lock_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_precontrol_duration_addr: # rw
                        if dsp_wr: precontrol_duration.next = dsp_data_out
                        dsp_data_in.next = precontrol_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_timeout_duration_addr: # rw
                        if dsp_wr: timeout_duration.next = dsp_data_out
                        dsp_data_in.next = timeout_duration
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_tuner_at_ringdown_addr: # r
                        dsp_data_in.next = tuner_at_ringdown
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == rdman_metadata_addr_at_ringdown_addr: # r
                        dsp_data_in.next = metadata_addr_at_ringdown
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                    
                if control[RDMAN_CONTROL_RUN_B]:
                    # Reset the run bit if continuous mode is not selected
                    if not control[RDMAN_CONTROL_CONT_B]:
                        control.next[RDMAN_CONTROL_RUN_B] = 0
                    
                    if seqState == SeqState.IDLE:
                        us_since_start.next = 0                        
                        metadata_acq.next = LOW   
                        us_timer_enable.next = LOW
                        acc_en_out.next = LOW
                        if control[RDMAN_CONTROL_START_RD_B]:
                            seqState.next = SeqState.START_INJECT
                            
                    elif seqState == SeqState.START_INJECT:
                        abort.next = 0
                        timeout.next = 0
                        rd_trig.next = LOW          # Turn on the injection
                        metadata_acq.next = HIGH    # Start acquiring metadata
                        us_timer_enable.next = HIGH # Start microsecond counter
                        acc_en_out.next = LOW
                        expiry_time.next = precontrol_duration
                        control.next[RDMAN_CONTROL_START_RD_B] = 0
                        seqState.next = SeqState.WAIT_FOR_PRECONTROL
                        
                    elif seqState == SeqState.WAIT_FOR_PRECONTROL:
                        if us_since_start >= expiry_time:
                            if control[RDMAN_CONTROL_LOCK_ENABLE_B]:
                                acc_en_out.next = HIGH
                                seqState.next = SeqState.WAIT_FOR_LOCK
                            else:
                                seqState.next = SeqState.WAIT_FOR_GATING_CONDITIONS
                        
                    elif seqState == SeqState.WAIT_FOR_LOCK:
                        acc_en_out.next = HIGH
                        if laser_freq_ok_in:
                            if us_since_start >= expiry_time:
                                seqState.next = SeqState.WAIT_FOR_GATING_CONDITIONS                            
                        else:
                            expiry_time.next = us_since_start + lock_duration
                        
                        
                    # Metadata storage state machine - collects metadata
                    #  when metadata_strobe_in goes high into a modified circular
                    #  buffer
                    if metadataAcqState == MetadataAcqState.IDLE:
                        metadata_addrcntr.next = 0  # Reset address counters
                        param_addrcntr.next = 0
                        if metadata_acq:    # Start acquisition
                            metadataAcqState.next = MetadataAcqState.AWAIT_STROBE
                    elif metadataAcqState == MetadataAcqState.AWAIT_STROBE:
                        if metadata_strobe_in:
                            metadataAcqState.next = MetadataAcqState.ACQUIRING
                    elif metadataAcqState == MetadataAcqState.ACQUIRING:
                        # Store metadata on the next eight clock cycles
                        meta_we_out.next = HIGH
                        if metadata_addrcntr < 8*META_SIZE-1:
                            metadata_addrcntr.next = metadata_addrcntr + 1
                        else:
                            metadata_addrcntr.next = 4*META_SIZE
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

                    # Timeout detection
                    if us_timer_enable and pulse_1M_in:
                        us_since_start.next = us_since_start.next + 1
                        if us_since_start >= timeout_duration:
                            rd_trig.next = HIGH     # Turn off the injection
                            timeout.next = 1
                            rd_irq.next  = 1
                            metadata_acq.next = LOW   
                            us_timer_enable.next = LOW
                            seqState.next = SeqState.IDLE
                            metadataAcqState.next = MetadataAcqState.IDLE
                            
                    # Abort detection
                    if control[RDMAN_CONTROL_ABORT_RD_B]:
                        control.next[RDMAN_CONTROL_ABORT_RD_B] = 0
                        rd_trig.next = HIGH     # Turn off the injection
                        abort.next = 1
                        rd_irq.next  = 1
                        metadata_acq.next = LOW   
                        us_timer_enable.next = LOW
                        seqState.next = SeqState.IDLE
                        metadataAcqState.next = MetadataAcqState.IDLE
                        
                    # Ringdown IRQ acknowledgement
                    if control[RDMAN_CONTROL_RD_IRQ_ACK_B]:
                        control.next[RDMAN_CONTROL_RD_IRQ_ACK_B] = 0
                        rd_irq.next = LOW
                    
                    # Acquisition done IRQ acknowledgement
                    if control[RDMAN_CONTROL_ACQ_DONE_ACK_B]:
                        control.next[RDMAN_CONTROL_ACQ_DONE_ACK_B] = 0
                        acq_done_irq.next = LOW
                            
                    data_addr_out.next = data_addrcntr
                    meta_addr_out.next = metadata_addrcntr
                    param_addr_out.next = param_addrcntr

                            
                status.next[RDMAN_STATUS_ACQ_DONE_B] = acq_done_irq
                status.next[RDMAN_STATUS_BANK_B] = bank
                status.next[RDMAN_STATUS_LAPPED_B] = lapped
                status.next[RDMAN_STATUS_RD_IRQ_B] = rd_irq
                status.next[RDMAN_STATUS_SHUTDOWN_B] = rd_trig
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
    rd_data_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuner_slope_in = Signal(LOW)
    tuner_window_in = Signal(LOW)
    laser_freq_ok_in = Signal(LOW)
    metadata_strobe_in = Signal(LOW)
    rd_trig_out = Signal(LOW)
    acc_en_out = Signal(LOW)
    rd_irq_out = Signal(LOW)
    acq_done_irq_out = Signal(LOW)
    rd_adc_clk_out = Signal(LOW)
    bank_out = Signal(LOW)
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
                  meta7_in=meta7_in, rd_data_in=rd_data_in,
                  tuner_slope_in=tuner_slope_in,
                  tuner_window_in=tuner_window_in,
                  laser_freq_ok_in=laser_freq_ok_in,
                  metadata_strobe_in=metadata_strobe_in,
                  rd_trig_out=rd_trig_out, acc_en_out=acc_en_out,
                  rd_irq_out=rd_irq_out,
                  acq_done_irq_out=acq_done_irq_out,
                  rd_adc_clk_out=rd_adc_clk_out, bank_out=bank_out,
                  data_addr_out=data_addr_out, wr_data_out=wr_data_out,
                  data_we_out=data_we_out, meta_addr_out=meta_addr_out,
                  wr_meta_out=wr_meta_out, meta_we_out=meta_we_out,
                  param_addr_out=param_addr_out,
                  wr_param_out=wr_param_out, param_we_out=param_we_out,
                  map_base=map_base)
