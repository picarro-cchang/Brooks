#!/usr/bin/python
#
# FILE:
#   WlmAdcReader.py
#
# DESCRIPTION:
#   Reads wavelength monitor simultaneous-sampling serial output ADCs 
#
# SEE ALSO:
#
# HISTORY:
#   28-Aug-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK

LOW, HIGH = bool(0), bool(1)
t_State = enum("IDLE","WAIT_1","WAIT_0")

def WlmAdcReader(clk,reset,adc_clock_in,strobe_in,eta1_in,ref1_in,
                 eta2_in,ref2_in,adc_rd_out,adc_convst_out,
                 data_available_out,eta1_out,ref1_out,eta2_out,ref2_out):
    """
    Parameters:
    clk                -- 50 MHz clock
    reset              -- Reset
    adc_clock_out      -- Clock for ADC (2.5 MHz)
    strobe_in          -- Pulse to initiate conversion (100kHz)
    eta1_in            -- Serial data from etalon 1 channel
    ref1_in            -- Serial data from reference 1 channel
    eta2_in            -- Serial data from etalon 2 channel
    ref2_in            -- Serial data from reference 2 channel
    adc_rd_out         -- RD output for ADC
    adc_convst_out     -- Conversion start output for ADC
    data_available_out -- Indicates data are available (100 kHz)
    eta1_out           -- Parallel data for etalon 1
    ref1_out           -- Parallel data for reference 1
    eta2_out           -- Parallel data for etalon 2
    ref2_out           -- Parallel data for reference 2
    """
    
    ADC_CYCLE = 21
    ADC_START_CYCLE = 4
    ADC_DATA_WIDTH = 16
    ADC_LAST_CYCLE = ADC_START_CYCLE + ADC_DATA_WIDTH - 1
    
    state = Signal(t_State.IDLE)
    counter = Signal(intbv(0)[5:])
    eta1 = Signal(intbv(0)[16:])
    ref1 = Signal(intbv(0)[16:])
    eta2 = Signal(intbv(0)[16:])
    ref2 = Signal(intbv(0)[16:])
    
    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                counter.next = ADC_CYCLE
                eta1_out.next = 0
                ref1_out.next = 0
                eta2_out.next = 0
                ref2_out.next = 0
                state.next = t_State.IDLE
            else:
                data_available_out.next = 0
                # State machine is synchronized to adc clock
                if state == t_State.IDLE:
                    counter.next = ADC_CYCLE
                    eta1.next = 0
                    ref1.next = 0
                    eta2.next = 0
                    ref2.next = 0
                    if strobe_in:
                        counter.next = 0
                        state.next = t_State.WAIT_1
                elif state == t_State.WAIT_0:
                    if not adc_clock_in:
                        # Get here on falling edge of ADC clock
                        # Sample serial inputs here
                        if counter>=ADC_START_CYCLE and counter<=ADC_LAST_CYCLE:
                            eta1.next[ADC_LAST_CYCLE-int(counter)] = eta1_in
                            ref1.next[ADC_LAST_CYCLE-int(counter)] = ref1_in
                            eta2.next[ADC_LAST_CYCLE-int(counter)] = eta2_in
                            ref2.next[ADC_LAST_CYCLE-int(counter)] = ref2_in
                        if counter == ADC_CYCLE-1:
                            data_available_out.next = 1
                        state.next = t_State.WAIT_1
                elif state == t_State.WAIT_1:
                    if adc_clock_in:
                        # Get here on rising edge of ADC clock
                        if counter == ADC_CYCLE-2:
                            eta1_out.next = eta1
                            ref1_out.next = ref1
                            eta2_out.next = eta2
                            ref2_out.next = ref2
                        if counter < ADC_CYCLE:
                            counter.next = counter + 1
                            state.next = t_State.WAIT_0
                        else:
                            state.next = t_State.IDLE
                else:
                    state.next = t_State.IDLE

                adc_rd_out.next = (counter == 1)
                adc_convst_out.next = (counter == 1)
                
    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    adc_clock_in = Signal(LOW)
    strobe_in = Signal(LOW)
    eta1_in = Signal(LOW)
    ref1_in = Signal(LOW)
    eta2_in = Signal(LOW)
    ref2_in = Signal(LOW)
    adc_rd_out = Signal(LOW)
    adc_convst_out = Signal(LOW)
    data_available_out = Signal(LOW)
    eta1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])

    toVHDL(WlmAdcReader, clk=clk, reset=reset,
                         adc_clock_in=adc_clock_in, strobe_in=strobe_in,
                         eta1_in=eta1_in, ref1_in=ref1_in,
                         eta2_in=eta2_in, ref2_in=ref2_in,
                         adc_rd_out=adc_rd_out,
                         adc_convst_out=adc_convst_out,
                         data_available_out=data_available_out,
                         eta1_out=eta1_out, ref1_out=ref1_out,
                         eta2_out=eta2_out, ref2_out=ref2_out)
