#!/usr/bin/python
#
# FILE:
#   test_DynamicPwm.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   16-Sep-2009  sze  Initial version
#   29-Sep-2009  sze  Add dither waveform generation
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_DYNAMICPWM_INLET, FPGA_DYNAMICPWM_OUTLET

from Host.autogen.interface import DYNAMICPWM_CS, DYNAMICPWM_DELTA
from Host.autogen.interface import DYNAMICPWM_HIGH, DYNAMICPWM_LOW
from Host.autogen.interface import DYNAMICPWM_SLOPE

from Host.autogen.interface import DYNAMICPWM_CS_RUN_B, DYNAMICPWM_CS_RUN_W
from Host.autogen.interface import DYNAMICPWM_CS_CONT_B, DYNAMICPWM_CS_CONT_W
from Host.autogen.interface import DYNAMICPWM_CS_PWM_ENABLE_B, DYNAMICPWM_CS_PWM_ENABLE_W
from Host.autogen.interface import DYNAMICPWM_CS_USE_COMPARATOR_B, DYNAMICPWM_CS_USE_COMPARATOR_W
from Host.autogen.interface import DYNAMICPWM_CS_PWM_OUT_B, DYNAMICPWM_CS_PWM_OUT_W

from MyHDL.Common.DynamicPwm import DynamicPwm
from MyHDL.Common.ClkGen import ClkGen

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
comparator_in = Signal(LOW)
update_in = Signal(LOW)
pwm_out = Signal(LOW)
value_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
map_base = FPGA_DYNAMICPWM_INLET

clk_10M = Signal(LOW)
clk_5M = Signal(LOW)
clk_2M5 = Signal(LOW)
strobe_1M = Signal(LOW)

def bench():
    PERIOD = 20  # 50MHz clock
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    def writeFPGA(regNum,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 1
        dsp_data_out.next = data & 0xFFFFFFFF
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readFPGA(regNum,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def wrRingdownMem(wordAddr,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def rdRingdownMem(wordAddr,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def assertReset():
        yield clk.negedge
        yield clk.posedge
        reset.next = 1
        dsp_wr.next = 0
        yield clk.posedge
        reset.next = 0
        yield clk.negedge

    # N.B. If there are several blocks configured, ensure that dsp_data_in is 
    #  derived as the OR of the data buses from the individual blocks.
    dynamicpwm = DynamicPwm( clk=clk, reset=reset, dsp_addr=dsp_addr,
                             dsp_data_out=dsp_data_out,
                             dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                             comparator_in=comparator_in,
                             update_in=update_in, pwm_out=pwm_out,
                             value_out=value_out, map_base=map_base,MIN_WIDTH=500,MAX_WIDTH=65000 )

    clkGen = ClkGen(clk=clk, reset=reset, clk_10M=clk_10M, clk_5M=clk_5M,
                    clk_2M5=clk_2M5, pulse_1M=strobe_1M, pulse_100k=update_in)
    
    @instance
    def stimulus():
        locals = dynamicpwm[1].gen.gi_frame.f_locals
        yield assertReset()
        startWidth = int(locals['pulse_width'])
        MAX_WIDTH = int(locals['MAX_WIDTH'])
        MIN_WIDTH = int(locals['MIN_WIDTH'])
        # Test a positive value of delta
        delta = 0x800
        yield writeFPGA(FPGA_DYNAMICPWM_INLET+DYNAMICPWM_DELTA,delta)
        high = 0x1000
        low = 0x800
        slope = 0xC000
        yield writeFPGA(FPGA_DYNAMICPWM_INLET+DYNAMICPWM_HIGH,high)
        yield writeFPGA(FPGA_DYNAMICPWM_INLET+DYNAMICPWM_LOW,low)
        yield writeFPGA(FPGA_DYNAMICPWM_INLET+DYNAMICPWM_SLOPE,slope)
        
        control = (1 << DYNAMICPWM_CS_RUN_B) | \
                  (1 << DYNAMICPWM_CS_CONT_B) | \
                  (1 << DYNAMICPWM_CS_USE_COMPARATOR_B)
        yield writeFPGA(FPGA_DYNAMICPWM_INLET+DYNAMICPWM_CS,control)
        comparator_in.next = 1
        while True:
            yield negedge(update_in)
            if startWidth+delta != locals['pulse_width']: break
            startWidth += delta
        assert locals['pulse_width'] == MAX_WIDTH
        startWidth = MAX_WIDTH
        comparator_in.next = 0
        while True:
            yield negedge(update_in)
            if startWidth-delta != locals['pulse_width']: break
            startWidth -= delta
        assert locals['pulse_width'] == MIN_WIDTH
        # Test a negative value of delta
        delta = -0x800
        startWidth = MIN_WIDTH
        yield writeFPGA(FPGA_DYNAMICPWM_INLET+DYNAMICPWM_DELTA,delta)
        comparator_in.next = 0
        while True:
            yield negedge(update_in)
            if startWidth-delta != locals['pulse_width']: break
            startWidth -= delta
        assert locals['pulse_width'] == MAX_WIDTH
        startWidth = MAX_WIDTH
        comparator_in.next = 1
        while True:
            yield negedge(update_in)
            if startWidth+delta != locals['pulse_width']: break
            startWidth += delta
        assert locals['pulse_width'] == MIN_WIDTH
        
        
        yield delay(1000*PERIOD)
        raise StopSimulation
    return instances()

def test_DynamicPwm():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_DynamicPwm()
