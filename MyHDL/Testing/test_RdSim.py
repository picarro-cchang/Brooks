#!/usr/bin/python
#
# FILE:
#   test_RdSim.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   28-Jun-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import RDSIM_EXTRA
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_RDSIM

from Host.autogen.interface import RDSIM_TUNER_CENTER
from Host.autogen.interface import RDSIM_TUNER_WINDOW_HALF_WIDTH
from Host.autogen.interface import RDSIM_FILLING_RATE, RDSIM_DECAY
from Host.autogen.interface import RDSIM_ACCUMULATOR

from MyHDL.Common.RdSim import RdSim

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
rd_trig_in = Signal(LOW)
tuner_value_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
rd_adc_clk_in = Signal(LOW)
rdsim_value_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
map_base = FPGA_RDSIM

def bench():
    PERIOD = 20  # 50MHz clock
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk
        if not clk:
            rd_adc_clk_in.next = not rd_adc_clk_in
            
    def writeFPGA(regNum,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 1
        dsp_data_out.next = data
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
    rdsim = RdSim( clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, rd_trig_in=rd_trig_in,
                   tuner_value_in=tuner_value_in,
                   rd_adc_clk_in=rd_adc_clk_in,
                   rdsim_value_out=rdsim_value_out, map_base=map_base )
    @instance
    def stimulus():
        yield assertReset()
        # Write parameters
        yield writeFPGA(FPGA_RDSIM+RDSIM_TUNER_CENTER,0xC000)
        yield writeFPGA(FPGA_RDSIM+RDSIM_TUNER_WINDOW_HALF_WIDTH,1100)
        yield writeFPGA(FPGA_RDSIM+RDSIM_FILLING_RATE,1000)
        yield writeFPGA(FPGA_RDSIM+RDSIM_DECAY,0x0575)
        yield delay(1000000)
        raise StopSimulation
        
    @instance
    def tuner():
        minVal = 0x1000
        maxVal = 0xF000
        incr = 1100
        tuner = 0xE000
        while True:
            if tuner >= maxVal:
                tuner = maxVal
                incr = -abs(incr)
            elif tuner <= minVal:
                tuner = minVal
                incr = abs(incr)
            tuner_value_in.next = tuner
            tuner += incr
            yield delay(10000)  # Updated every 10us
        
    return instances()

def test_RdSim():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_RdSim()
