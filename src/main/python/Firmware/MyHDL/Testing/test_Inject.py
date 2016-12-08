#!/usr/bin/python
#
# FILE:
#   test_Inject.py
#
# DESCRIPTION:
#   Test optical injection subsystem
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   1-Jun-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from random import randrange

from MyHDL.Common.ClkGen import ClkGen
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_INJECT

from Host.autogen.interface import INJECT_CONTROL, INJECT_CONTROL2
from Host.autogen.interface import INJECT_LASER1_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER2_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER3_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER4_COARSE_CURRENT
from Host.autogen.interface import INJECT_LASER1_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER2_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER3_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER4_FINE_CURRENT
from Host.autogen.interface import INJECT_LASER1_FINE_CURRENT_RANGE
from Host.autogen.interface import INJECT_LASER2_FINE_CURRENT_RANGE
from Host.autogen.interface import INJECT_LASER3_FINE_CURRENT_RANGE
from Host.autogen.interface import INJECT_LASER4_FINE_CURRENT_RANGE
from Host.autogen.interface import INJECT_LASER1_EXTRA_COARSE_SCALE
from Host.autogen.interface import INJECT_LASER2_EXTRA_COARSE_SCALE
from Host.autogen.interface import INJECT_LASER3_EXTRA_COARSE_SCALE
from Host.autogen.interface import INJECT_LASER4_EXTRA_COARSE_SCALE
from Host.autogen.interface import INJECT_LASER1_EXTRA_FINE_SCALE
from Host.autogen.interface import INJECT_LASER2_EXTRA_FINE_SCALE
from Host.autogen.interface import INJECT_LASER3_EXTRA_FINE_SCALE
from Host.autogen.interface import INJECT_LASER4_EXTRA_FINE_SCALE
from Host.autogen.interface import INJECT_LASER1_EXTRA_OFFSET
from Host.autogen.interface import INJECT_LASER2_EXTRA_OFFSET
from Host.autogen.interface import INJECT_LASER3_EXTRA_OFFSET
from Host.autogen.interface import INJECT_LASER4_EXTRA_OFFSET

from Host.autogen.interface import INJECT_CONTROL_MODE_B, INJECT_CONTROL_MODE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SELECT_B, INJECT_CONTROL_LASER_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_LASER_CURRENT_ENABLE_B, INJECT_CONTROL_LASER_CURRENT_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_LASER_ENABLE_B, INJECT_CONTROL_MANUAL_LASER_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_MANUAL_SOA_ENABLE_B, INJECT_CONTROL_MANUAL_SOA_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_B, INJECT_CONTROL_LASER_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B, INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL_OPTICAL_SWITCH_SELECT_B, INJECT_CONTROL_OPTICAL_SWITCH_SELECT_W
from Host.autogen.interface import INJECT_CONTROL_SOA_PRESENT_B, INJECT_CONTROL_SOA_PRESENT_W
from Host.autogen.interface import INJECT_CONTROL2_FIBER_AMP_PRESENT_B, INJECT_CONTROL2_FIBER_AMP_PRESENT_W
from Host.autogen.interface import INJECT_CONTROL2_EXTINGUISH_DESELECTED_B, INJECT_CONTROL2_EXTINGUISH_DESELECTED_W
from Host.autogen.interface import INJECT_CONTROL2_EXTRA_MODE_B, INJECT_CONTROL2_EXTRA_MODE_W
from Host.autogen.interface import INJECT_CONTROL2_EXTRA_ENABLE_B, INJECT_CONTROL2_EXTRA_ENABLE_W
from Host.autogen.interface import INJECT_CONTROL2_EXTENDED_CURRENT_MODE_B, INJECT_CONTROL2_EXTENDED_CURRENT_MODE_W
from Host.autogen.interface import INJECT_CONTROL2_DISABLE_SOA_WITH_LASER_B, INJECT_CONTROL2_DISABLE_SOA_WITH_LASER_W

from MyHDL.Common.Inject import Inject

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
laser_dac_clk_in = Signal(LOW)
strobe_in = Signal(LOW)
laser_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser_shutdown_in = Signal(LOW)
soa_shutdown_in = Signal(LOW)
fiber_amp_pwm_in = Signal(LOW)
laser_extra_in = Signal(LOW)
laser1_fine_ext_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser2_fine_ext_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser3_fine_ext_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser4_fine_ext_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser1_dac_sync_out = Signal(LOW)
laser2_dac_sync_out = Signal(LOW)
laser3_dac_sync_out = Signal(LOW)
laser4_dac_sync_out = Signal(LOW)
laser1_dac_din_out = Signal(LOW)
laser2_dac_din_out = Signal(LOW)
laser3_dac_din_out = Signal(LOW)
laser4_dac_din_out = Signal(LOW)
laser1_disable_out = Signal(LOW)
laser2_disable_out = Signal(LOW)
laser3_disable_out = Signal(LOW)
laser4_disable_out = Signal(LOW)
laser1_shutdown_out = Signal(LOW)
laser2_shutdown_out = Signal(LOW)
laser3_shutdown_out = Signal(LOW)
laser4_shutdown_out = Signal(LOW)
soa_shutdown_out = Signal(LOW)
sel_laser_out = Signal(intbv(0)[2:])
sel_coarse_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
sel_fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
optical_switch1_out = Signal(LOW)
optical_switch2_out = Signal(LOW)
optical_switch4_out = Signal(LOW)
ext_mode_out = Signal(LOW)

data1 = Signal(intbv(0)[24:])
data2 = Signal(intbv(0)[24:])
data3 = Signal(intbv(0)[24:])
data4 = Signal(intbv(0)[24:])
acq_done = Signal(LOW)
clk_10M = Signal(LOW)
clk_2M5 = Signal(LOW)
pulse_1M = Signal(LOW)

map_base = FPGA_INJECT
mod = (1<<FPGA_REG_WIDTH)

def add_sim(x,y):
    return (x+y) % mod

def sub_sim(x,y):
    return (x-y) % mod

def div_sim(x,y):
    x = x % mod
    y = y % mod
    return x*(mod//2)//y

def signed_mul_sim(x,y):
    x = x % mod
    if x>mod//2: x -= mod
    y = y % mod
    if y>mod//2: y -= mod
    p = (x * y) % (mod**2/2)
    return p // (mod//2)

def unsigned_mul_sim(x,y):
    x = x % mod
    y = y % mod
    p = (x * y) % (mod**2)
    return p // mod

def unsigned_mul_sim2(x,y):
    x = x % mod
    y = y % mod
    p = (x * y) % (mod**2)
    return p // (mod // 2)

def bench():
    PERIOD = 20  # 50MHz clock
    MS = 1000000
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

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
    inject = Inject( clk=clk, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                     dsp_wr=dsp_wr, laser_dac_clk_in=laser_dac_clk_in,
                     strobe_in=strobe_in,
                     laser_fine_current_in=laser_fine_current_in,
                     laser_shutdown_in=laser_shutdown_in,
                     soa_shutdown_in=soa_shutdown_in,
                     fiber_amp_pwm_in=fiber_amp_pwm_in,
                     laser_extra_in=laser_extra_in,
                     laser1_fine_ext_in=laser1_fine_ext_in,
                     laser2_fine_ext_in=laser2_fine_ext_in,
                     laser3_fine_ext_in=laser3_fine_ext_in,
                     laser4_fine_ext_in=laser4_fine_ext_in,
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
                     sel_laser_out=sel_laser_out,
                     sel_coarse_current_out=sel_coarse_current_out,
                     sel_fine_current_out=sel_fine_current_out,
                     optical_switch1_out=optical_switch1_out,
                     optical_switch2_out=optical_switch2_out,
                     optical_switch4_out=optical_switch4_out,
                     ext_mode_out=ext_mode_out, map_base=map_base )

    clkGen = ClkGen(clk=clk, reset=reset, clk_10M=clk_10M, clk_5M=laser_dac_clk_in,
                    clk_2M5=clk_2M5, pulse_1M=pulse_1M, pulse_100k=strobe_in)

    @instance
    def  acquire():
        while True:
            yield laser1_dac_sync_out.posedge
            acq_done.next = 0
            data1.next = 0
            data2.next = 0
            data3.next = 0
            data4.next = 0
            for i in range(24):
                yield laser_dac_clk_in.negedge
                data1.next[23-i] = laser1_dac_din_out
                data2.next[23-i] = laser2_dac_din_out
                data3.next[23-i] = laser3_dac_din_out
                data4.next[23-i] = laser4_dac_din_out
            acq_done.next = 1

    @instance
    def  stimulus():
        yield assertReset()
        assert laser1_disable_out == 1
        assert laser2_disable_out == 1
        assert laser3_disable_out == 1
        assert laser4_disable_out == 1
        assert laser1_shutdown_out == 1
        assert laser2_shutdown_out == 1
        assert laser3_shutdown_out == 1
        assert laser4_shutdown_out == 1
        assert soa_shutdown_out == 1
        # Test manual mode for laser and SOA switching
        for trials in range(200):
            laser_current_enable = randrange(1<<4)
            manual_laser_enable = randrange(1<<4)
            manual_soa_enable = randrange(1<<1)
            soa_present = randrange(1<<1)
            control = (laser_current_enable << INJECT_CONTROL_LASER_CURRENT_ENABLE_B) | \
                      (manual_laser_enable  << INJECT_CONTROL_MANUAL_LASER_ENABLE_B) | \
                      (manual_soa_enable << INJECT_CONTROL_MANUAL_SOA_ENABLE_B) | \
                      (soa_present << INJECT_CONTROL_SOA_PRESENT_B)
            yield writeFPGA(FPGA_INJECT+INJECT_CONTROL,control)
            assert laser1_disable_out == (not (laser_current_enable & 1))
            assert laser2_disable_out == (not ((laser_current_enable>>1) & 1))
            assert laser3_disable_out == (not ((laser_current_enable>>2) & 1))
            assert laser4_disable_out == (not ((laser_current_enable>>3) & 1))
            assert laser1_shutdown_out == (not (manual_laser_enable & 1))
            assert laser2_shutdown_out == (not ((manual_laser_enable>>1) & 1))
            assert laser3_shutdown_out == (not ((manual_laser_enable>>2) & 1))
            assert laser4_shutdown_out == (not ((manual_laser_enable>>3) & 1))
            assert soa_shutdown_out == (not soa_present) or (not((manual_soa_enable) & 1))
        # Check laser selection
        for trials in range(100):
            mode = randrange(2)
            laser_sel = randrange(4)
            manual_soa_enable = randrange(1<<1)
            ssin = randrange(2)
            soa_shutdown_in.next = ssin
            soa_shutdown_enable = randrange(2)
            soa_present = randrange(2)
            extended_mode = randrange(2)

            control = (laser_sel << INJECT_CONTROL_LASER_SELECT_B) | \
                      (mode << INJECT_CONTROL_MODE_B) | \
                      (manual_soa_enable << INJECT_CONTROL_MANUAL_SOA_ENABLE_B) |\
                      (soa_shutdown_enable << INJECT_CONTROL_SOA_SHUTDOWN_ENABLE_B) |\
                      (soa_present << INJECT_CONTROL_SOA_PRESENT_B)
            yield writeFPGA(FPGA_INJECT+INJECT_CONTROL,control)

            control2 = (extended_mode << INJECT_CONTROL2_EXTENDED_CURRENT_MODE_B)
            yield writeFPGA(FPGA_INJECT+INJECT_CONTROL2,control2)

            laser1_coarse = randrange(1<<16)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_COARSE_CURRENT,laser1_coarse)
            laser2_coarse = randrange(1<<16)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_COARSE_CURRENT,laser2_coarse)
            laser3_coarse = randrange(1<<16)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_COARSE_CURRENT,laser3_coarse)
            laser4_coarse = randrange(1<<16)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_COARSE_CURRENT,laser4_coarse)
            laser1_fine = randrange((1<<16)-1)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_FINE_CURRENT,laser1_fine)
            laser2_fine = randrange((1<<16)-1)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_FINE_CURRENT,laser2_fine)
            laser3_fine = randrange((1<<16)-1)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_FINE_CURRENT,laser3_fine)
            laser4_fine = randrange((1<<16)-1)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_FINE_CURRENT,laser4_fine)
            laser_sel_fine = randrange((1<<16)-1)
            laser_fine_current_in.next = laser_sel_fine
            # Set up extended laser current control values
            laser1_fine_ext = randrange((1<<16)-1)
            laser1_fine_ext_in.next = laser1_fine_ext
            laser2_fine_ext = randrange((1<<16)-1)
            laser2_fine_ext_in.next = laser2_fine_ext
            laser3_fine_ext = randrange((1<<16)-1)
            laser3_fine_ext_in.next = laser3_fine_ext
            laser4_fine_ext = randrange((1<<16)-1)
            laser4_fine_ext_in.next = laser4_fine_ext
            #
            laser1_fine_current_range = randrange(1<<15)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_FINE_CURRENT_RANGE,laser1_fine_current_range)
            laser2_fine_current_range = randrange(1<<15)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_FINE_CURRENT_RANGE,laser2_fine_current_range)
            laser3_fine_current_range = randrange(1<<15)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_FINE_CURRENT_RANGE,laser3_fine_current_range)
            laser4_fine_current_range = randrange(1<<15)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_FINE_CURRENT_RANGE,laser4_fine_current_range)

            yield delay(10*PERIOD)
            assert sel_laser_out == laser_sel
            if laser_sel == 0:
                assert sel_coarse_current_out == laser1_coarse
                if mode:
                    if extended_mode:
                        assert sel_fine_current_out == laser1_fine_ext
                    else:
                        assert sel_fine_current_out == min(max(laser_fine_current_in,32768-laser1_fine_current_range),32768+laser1_fine_current_range)
                else:
                    assert sel_fine_current_out == laser1_fine
            if laser_sel == 1:
                assert sel_coarse_current_out == laser2_coarse
                if mode:
                    if extended_mode:
                        assert sel_fine_current_out == laser2_fine_ext
                    else:
                        assert sel_fine_current_out == min(max(laser_fine_current_in,32768-laser2_fine_current_range),32768+laser2_fine_current_range)
                else:
                    assert sel_fine_current_out == laser2_fine
            if laser_sel == 2:
                assert sel_coarse_current_out == laser3_coarse
                if mode:
                    if extended_mode:
                        assert sel_fine_current_out == laser3_fine_ext
                    else:
                        assert sel_fine_current_out == min(max(laser_fine_current_in,32768-laser3_fine_current_range),32768+laser3_fine_current_range)
                else:
                    assert sel_fine_current_out == laser3_fine
            if laser_sel == 3:
                assert sel_coarse_current_out == laser4_coarse
                if mode:
                    if extended_mode:
                        assert sel_fine_current_out == laser4_fine_ext
                    else:
                        assert sel_fine_current_out == min(max(laser_fine_current_in,32768-laser4_fine_current_range),32768+laser4_fine_current_range)
                else:
                    assert sel_fine_current_out == laser4_fine
            if not soa_present:
                assert soa_shutdown_out
            else:
                if mode == 0:
                    assert soa_shutdown_out == (not manual_soa_enable)
                else:
                    assert soa_shutdown_out == (ssin and soa_shutdown_enable)

        # Check writing to serial DACs
        yield writeFPGA(FPGA_INJECT+INJECT_CONTROL,0)
        for trials in range(5):
            laser1_coarse = randrange(1<<16)
            laser2_coarse = randrange(1<<16)
            laser3_coarse = randrange(1<<16)
            laser4_coarse = randrange(1<<16)
            laser1_fine = randrange(1<<16)
            laser2_fine = randrange(1<<16)
            laser3_fine = randrange(1<<16)
            laser4_fine = randrange(1<<16)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_COARSE_CURRENT,laser1_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_COARSE_CURRENT,laser2_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_COARSE_CURRENT,laser3_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_COARSE_CURRENT,laser4_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_FINE_CURRENT,laser1_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_FINE_CURRENT,laser2_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_FINE_CURRENT,laser3_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_FINE_CURRENT,laser4_fine)
            yield strobe_in.posedge
            yield delay(10*PERIOD)
            yield acq_done.posedge
            assert (data1 & 0xFFFF) == laser1_coarse
            assert (data2 & 0xFFFF) == laser2_coarse
            assert (data3 & 0xFFFF) == laser3_coarse
            assert (data4 & 0xFFFF) == laser4_coarse
            yield acq_done.posedge
            assert (data1 & 0xFFFF) == laser1_fine
            assert (data2 & 0xFFFF) == laser2_fine
            assert (data3 & 0xFFFF) == laser3_fine
            assert (data4 & 0xFFFF) == laser4_fine
        yield delay(10*PERIOD)

        # Write to serial DACs with scaling
        yield writeFPGA(FPGA_INJECT+INJECT_CONTROL, 0)
        yield writeFPGA(FPGA_INJECT+INJECT_CONTROL2,
                        (1<<INJECT_CONTROL2_EXTRA_ENABLE_B)|
                        (1<<INJECT_CONTROL2_EXTRA_MODE_B))
        laser1_extra_coarse_scale = randrange(1<<16)
        laser1_extra_fine_scale = randrange(1<<16)
        laser1_extra_offset = randrange(1<<16)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER1_EXTRA_COARSE_SCALE, laser1_extra_coarse_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER1_EXTRA_FINE_SCALE, laser1_extra_fine_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER1_EXTRA_OFFSET, laser1_extra_offset)
        laser2_extra_coarse_scale = randrange(1<<16)
        laser2_extra_fine_scale = randrange(1<<16)
        laser2_extra_offset = randrange(1<<16)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER2_EXTRA_COARSE_SCALE, laser2_extra_coarse_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER2_EXTRA_FINE_SCALE, laser2_extra_fine_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER2_EXTRA_OFFSET, laser2_extra_offset)
        laser3_extra_coarse_scale = randrange(1<<16)
        laser3_extra_fine_scale = randrange(1<<16)
        laser3_extra_offset = randrange(1<<16)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER3_EXTRA_COARSE_SCALE, laser3_extra_coarse_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER3_EXTRA_FINE_SCALE, laser3_extra_fine_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER3_EXTRA_OFFSET, laser3_extra_offset)
        laser4_extra_coarse_scale = randrange(1<<16)
        laser4_extra_fine_scale = randrange(1<<16)
        laser4_extra_offset = randrange(1<<16)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER4_EXTRA_COARSE_SCALE, laser4_extra_coarse_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER4_EXTRA_FINE_SCALE, laser4_extra_fine_scale)
        yield writeFPGA(FPGA_INJECT+INJECT_LASER4_EXTRA_OFFSET, laser4_extra_offset)

        for trials in range(5):
            laser1_coarse = randrange(1<<16)
            laser2_coarse = randrange(1<<16)
            laser3_coarse = randrange(1<<16)
            laser4_coarse = randrange(1<<16)
            laser1_fine = randrange(1<<16)
            laser2_fine = randrange(1<<16)
            laser3_fine = randrange(1<<16)
            laser4_fine = randrange(1<<16)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_COARSE_CURRENT,laser1_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_COARSE_CURRENT,laser2_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_COARSE_CURRENT,laser3_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_COARSE_CURRENT,laser4_coarse)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER1_FINE_CURRENT,laser1_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER2_FINE_CURRENT,laser2_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER3_FINE_CURRENT,laser3_fine)
            yield writeFPGA(FPGA_INJECT+INJECT_LASER4_FINE_CURRENT,laser4_fine)
            yield strobe_in.posedge
            yield delay(10*PERIOD)
            yield acq_done.posedge
            laser1_coarse_scaled = add_sim(add_sim(unsigned_mul_sim2(laser1_coarse, laser1_extra_coarse_scale),
                                   unsigned_mul_sim(laser1_fine, laser1_extra_fine_scale)), laser1_extra_offset)
            laser2_coarse_scaled = add_sim(add_sim(unsigned_mul_sim2(laser2_coarse, laser2_extra_coarse_scale),
                                   unsigned_mul_sim(laser2_fine, laser2_extra_fine_scale)), laser2_extra_offset)
            laser3_coarse_scaled = add_sim(add_sim(unsigned_mul_sim2(laser3_coarse, laser3_extra_coarse_scale),
                                   unsigned_mul_sim(laser3_fine, laser3_extra_fine_scale)), laser3_extra_offset)
            laser4_coarse_scaled = add_sim(add_sim(unsigned_mul_sim2(laser4_coarse, laser4_extra_coarse_scale),
                                   unsigned_mul_sim(laser4_fine, laser4_extra_fine_scale)), laser4_extra_offset)
            assert (data1 & 0xFFFF) == laser1_coarse_scaled
            assert (data2 & 0xFFFF) == laser2_coarse_scaled
            assert (data3 & 0xFFFF) == laser3_coarse_scaled
            assert (data4 & 0xFFFF) == laser4_coarse_scaled
            yield acq_done.posedge
            assert (data1 & 0xFFFF) == laser1_fine
            assert (data2 & 0xFFFF) == laser2_fine
            assert (data3 & 0xFFFF) == laser3_fine
            assert (data4 & 0xFFFF) == laser4_fine
        yield delay(10*PERIOD)

        raise StopSimulation
    return instances()

def test_Inject():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_Inject()
