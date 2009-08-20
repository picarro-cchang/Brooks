#!/usr/bin/python
#
# FILE:
#   test_RdMan.py
#
# DESCRIPTION:
#
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
from Host.autogen.interface import RDMAN_OPTIONS, RDMAN_PARAM0
from Host.autogen.interface import RDMAN_PARAM1, RDMAN_PARAM2
from Host.autogen.interface import RDMAN_PARAM3, RDMAN_PARAM4
from Host.autogen.interface import RDMAN_PARAM5, RDMAN_PARAM6
from Host.autogen.interface import RDMAN_PARAM7, RDMAN_PARAM8
from Host.autogen.interface import RDMAN_PARAM9, RDMAN_DATA_ADDRCNTR
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
from Host.autogen.interface import RDMAN_CONTROL_BANK0_CLEAR_B, RDMAN_CONTROL_BANK0_CLEAR_W
from Host.autogen.interface import RDMAN_CONTROL_BANK1_CLEAR_B, RDMAN_CONTROL_BANK1_CLEAR_W
from Host.autogen.interface import RDMAN_CONTROL_RD_IRQ_ACK_B, RDMAN_CONTROL_RD_IRQ_ACK_W
from Host.autogen.interface import RDMAN_CONTROL_ACQ_DONE_ACK_B, RDMAN_CONTROL_ACQ_DONE_ACK_W
from Host.autogen.interface import RDMAN_CONTROL_RAMP_DITHER_B, RDMAN_CONTROL_RAMP_DITHER_W
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
from Host.autogen.interface import RDMAN_STATUS_BUSY_B, RDMAN_STATUS_BUSY_W
from Host.autogen.interface import RDMAN_OPTIONS_LOCK_ENABLE_B, RDMAN_OPTIONS_LOCK_ENABLE_W
from Host.autogen.interface import RDMAN_OPTIONS_UP_SLOPE_ENABLE_B, RDMAN_OPTIONS_UP_SLOPE_ENABLE_W
from Host.autogen.interface import RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B, RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_W
from Host.autogen.interface import RDMAN_OPTIONS_DITHER_ENABLE_B, RDMAN_OPTIONS_DITHER_ENABLE_W

from MyHDL.Common.RdMan import *
from MyHDL.Common.Rdmemory import Rdmemory
from MyHDL.Common.ClkGen import ClkGen

LOW, HIGH = bool(0), bool(1)
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

data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
meta = Signal(intbv(0)[RDMEM_META_WIDTH:])
param = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
clk_5M = Signal(LOW)
clk_2M5 = Signal(LOW)
# N.B. It is important to OR together the dsp_data_in buses
#  from all blocks connected to the DSP
dsp_data_in_rdmemory = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in_rdman = Signal(intbv(0)[EMIF_DATA_WIDTH:])

result = Signal(intbv(0))
filling = False
meta_sample = 0
def bench():
    PERIOD = 20  # 50MHz clock
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    @always_comb
    def comb():
        dsp_data_in.next = dsp_data_in_rdman | dsp_data_in_rdmemory

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
    rdman = RdMan( clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdman,
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
                   laser_locked_out=laser_locked_out,
                   data_addr_out=data_addr_out, wr_data_out=wr_data_out,
                   data_we_out=data_we_out, meta_addr_out=meta_addr_out,
                   wr_meta_out=wr_meta_out, meta_we_out=meta_we_out,
                   param_addr_out=param_addr_out,
                   wr_param_out=wr_param_out, param_we_out=param_we_out,
                   map_base=map_base )

    rdmemory = Rdmemory( clk=clk, reset=reset, dsp_addr=dsp_addr,
                         dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdmemory,
                         dsp_wr=dsp_wr, bank=bank_out,
                         data_addr=data_addr_out, data=data, wr_data=wr_data_out, data_we=data_we_out,
                         meta_addr=meta_addr_out, meta=meta, wr_meta=wr_meta_out, meta_we=meta_we_out,
                         param_addr=param_addr_out, param=param, wr_param=wr_param_out, param_we=param_we_out )

    clkGen = ClkGen( clk=clk, reset=reset, clk_5M=clk_5M, clk_2M5=clk_2M5,
                     pulse_1M=pulse_1M_in, pulse_100k=pulse_100k_in)

    @instance
    def stimulus():
        global filling
        paramVals = [
            (FPGA_RDMAN+RDMAN_PARAM0,0xFFFFFFFF),(FPGA_RDMAN+RDMAN_PARAM1,0xEEEEEEEE),
            (FPGA_RDMAN+RDMAN_PARAM2,0xDDDDDDDD),(FPGA_RDMAN+RDMAN_PARAM3,0xCCCCCCCC),
            (FPGA_RDMAN+RDMAN_PARAM4,0xBBBBBBBB),(FPGA_RDMAN+RDMAN_PARAM5,0xAAAAAAAA),
            (FPGA_RDMAN+RDMAN_PARAM6,0x99999999),(FPGA_RDMAN+RDMAN_PARAM7,0x88888888),
            (FPGA_RDMAN+RDMAN_PARAM8,0x77777777),(FPGA_RDMAN+RDMAN_PARAM9,0x66666666)]
        yield assertReset()
        # Write to the parameter area
        for a,v in paramVals:
            yield writeFPGA(a,v)
        # Check by reading back
        for a,v in paramVals:
            yield readFPGA(a,result)
            assert result == v
        print "Passed readback of parameter registers"
        # Check injection is off
        assert rd_trig_out == 1
        yield readFPGA(FPGA_RDMAN+RDMAN_STATUS,result)
        assert result[RDMAN_STATUS_SHUTDOWN_B] == 1
        print "Passed check that injection is off"
        # Write timeout duration in microseconds and check that
        #  a 32 bit number can be stored
        yield writeFPGA(FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,0xAAAA5555)
        yield readFPGA(FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,result)
        assert result == 0xAAAA5555
        print "Verified that timeout is 32 bits long"
        yield writeFPGA(FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,50)
        # Write a precontrol duration of 30us
        yield writeFPGA(FPGA_RDMAN+RDMAN_PRECONTROL_DURATION,30)
        # Write a lock duration of 40us
        yield writeFPGA(FPGA_RDMAN+RDMAN_LOCK_DURATION,40)
        # Write a ringdown threshold of 20000
        yield writeFPGA(FPGA_RDMAN+RDMAN_THRESHOLD,20000)
        # Write a ringdown rate divisor of 2
        yield writeFPGA(FPGA_RDMAN+RDMAN_DIVISOR,1)
        # Write number of samples
        yield writeFPGA(FPGA_RDMAN+RDMAN_NUM_SAMP,2048)

        for iter in range(2):
            yield readFPGA(FPGA_RDMAN+RDMAN_CONTROL,result)
            # Assert the CONT START_RD bit in the control register
            control = result | (1 << RDMAN_CONTROL_RUN_B) | \
                              (1 << RDMAN_CONTROL_CONT_B) | \
                              (1 << RDMAN_CONTROL_START_RD_B)
            yield writeFPGA(FPGA_RDMAN+RDMAN_CONTROL,control)

            startTime = now()
            yield negedge(clk)
            # Check injection is now on
            assert rd_trig_out == 0
            yield readFPGA(FPGA_RDMAN+RDMAN_STATUS,result)
            assert result[RDMAN_STATUS_SHUTDOWN_B] == 0
            print "Passed check that injection has been turned on"
            # Check that the START_RD control bit has been reset
            yield readFPGA(FPGA_RDMAN+RDMAN_CONTROL,result)
            assert result[RDMAN_CONTROL_START_RD_B] == 0
            print "Passed check that START_RD has been deasserted"
            assert bank_out == 0
            assert result[RDMAN_STATUS_BANK_B] == 0
            print "Passed check that injection is on after start_rd is asserted"

            # Check that the timeout works correctly
            yield posedge(rd_irq_out)
            duration = now()-startTime
            yield readFPGA(FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,result)
            assert abs(duration-1000*int(result)) < 2000
            print "Correct timeout duration"
            yield negedge(clk)
            yield readFPGA(FPGA_RDMAN+RDMAN_STATUS,result)
            assert result[RDMAN_STATUS_RD_IRQ_B] == 1
            assert result[RDMAN_STATUS_TIMEOUT_B] == 1
            # Check that we can clear the interrupt flag
            yield readFPGA(FPGA_RDMAN+RDMAN_CONTROL,result)
            yield writeFPGA(FPGA_RDMAN+RDMAN_CONTROL,result | (1<<RDMAN_CONTROL_RD_IRQ_ACK_B))
            yield readFPGA(FPGA_RDMAN+RDMAN_STATUS,result)
            assert result[RDMAN_STATUS_RD_IRQ_B] == 0
            assert result[RDMAN_STATUS_TIMEOUT_B] == 1

        yield writeFPGA(FPGA_RDMAN+RDMAN_TIMEOUT_DURATION,1000)
        yield readFPGA(FPGA_RDMAN+RDMAN_CONTROL,result)
        options = (1 << RDMAN_OPTIONS_LOCK_ENABLE_B) | \
                  (1 << RDMAN_OPTIONS_UP_SLOPE_ENABLE_B)
        yield writeFPGA(FPGA_RDMAN+RDMAN_OPTIONS,options)
        # Assert the CONT START_RD bit in the control register
        control = result | (1 << RDMAN_CONTROL_RUN_B) | \
                           (1 << RDMAN_CONTROL_CONT_B) | \
                           (1 << RDMAN_CONTROL_START_RD_B)
        yield writeFPGA(FPGA_RDMAN+RDMAN_CONTROL,control)
        startTime = now()
        # Wait for end of pre-control duration
        yield posedge(acc_en_out)
        duration = now()-startTime
        yield readFPGA(FPGA_RDMAN+RDMAN_PRECONTROL_DURATION,result)
        assert abs(duration-1000*int(result)) < 2000
        print "Correct precontrol duration"
        # We now enter the mode for laser locking
        yield readFPGA(FPGA_RDMAN+RDMAN_LOCK_DURATION,result)
        laser_freq_ok_in.next = HIGH
        yield delay(int(0.5*1000*int(result)))
        laser_freq_ok_in.next = LOW
        yield delay(2*PERIOD)
        laser_freq_ok_in.next = HIGH
        startTime = now()
        yield posedge(laser_locked_out)
        duration = now()-startTime
        yield readFPGA(FPGA_RDMAN+RDMAN_LOCK_DURATION,result)
        assert abs(duration-1000*int(result)) < 2000
        print "Correct laser locked duration"
        # We now wait for the gating conditions to be satisfied
        tuner_slope_in.next = HIGH
        yield delay(100)
        tuner_window_in.next = HIGH
        filling = True
        yield posedge(rd_trig_out)
        filling = False

        # We should now be acquiring metadata each time the metadata strobe occurs
        while True:
            yield negedge(metadata_strobe_in)
            start = int(meta_addr_out)  # Get start of metadata block
            yield negedge(meta_we_out)
            # There should be metadata stored in ringdown memory
            for addr in range(start,start+8):
                yield rdRingdownMem((0x5000 if bank_out else 0x1000)+addr,result)
                assert (addr & 7) == (result & 7)

    @instance
    def rdSim():
        while True:
            yield negedge(rd_adc_clk_out)
            if filling:
                rd_data_in.next = rd_data_in + 100
            else:
                rd_data_in.next = int(0.9995*rd_data_in)


    @instance
    def stopSimulation():
        yield delay(20000*PERIOD)
        raise StopSimulation

    METADATA_PERIOD = 2000  # 500kHz clock
    @instance
    def metadataStrobeGen():
        global meta_sample
        while True:
            yield delay(METADATA_PERIOD-PERIOD)
            meta0_in.next = (meta_sample<<8) | 0x00
            meta1_in.next = (meta_sample<<8) | 0x01
            meta2_in.next = (meta_sample<<8) | 0x02
            meta3_in.next = (meta_sample<<8) | 0x03
            meta4_in.next = (meta_sample<<8) | 0x04
            meta5_in.next = (meta_sample<<8) | 0x05
            meta6_in.next = (meta_sample<<8) | 0x06
            meta7_in.next = (meta_sample<<8) | 0x07
            meta_sample = (meta_sample + 1) % 256
            yield posedge(clk)
            metadata_strobe_in.next = HIGH
            yield posedge(clk)
            metadata_strobe_in.next = LOW


    return instances()

def test_RdMan():
    s = Simulation(traceSignals(bench))
    # s = Simulation(bench())
    s.run(quiet=1)

if __name__ == "__main__":
    test_RdMan()
