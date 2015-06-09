#!/usr/bin/python
#
# FILE:
#   test_LaserLocker.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   02-Jul-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from random import randrange

from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import WLM_ADC_WIDTH
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_LASERLOCKER

from Host.autogen.interface import LASERLOCKER_CS, LASERLOCKER_OPTIONS
from Host.autogen.interface import LASERLOCKER_ETA1, LASERLOCKER_REF1
from Host.autogen.interface import LASERLOCKER_ETA2, LASERLOCKER_REF2
from Host.autogen.interface import LASERLOCKER_ETA1_DARK
from Host.autogen.interface import LASERLOCKER_REF1_DARK
from Host.autogen.interface import LASERLOCKER_ETA2_DARK
from Host.autogen.interface import LASERLOCKER_REF2_DARK
from Host.autogen.interface import LASERLOCKER_ETA1_OFFSET
from Host.autogen.interface import LASERLOCKER_REF1_OFFSET
from Host.autogen.interface import LASERLOCKER_ETA2_OFFSET
from Host.autogen.interface import LASERLOCKER_REF2_OFFSET
from Host.autogen.interface import LASERLOCKER_RATIO1
from Host.autogen.interface import LASERLOCKER_RATIO2
from Host.autogen.interface import LASERLOCKER_RATIO1_CENTER
from Host.autogen.interface import LASERLOCKER_RATIO1_MULTIPLIER
from Host.autogen.interface import LASERLOCKER_RATIO2_CENTER
from Host.autogen.interface import LASERLOCKER_RATIO2_MULTIPLIER
from Host.autogen.interface import LASERLOCKER_TUNING_OFFSET
from Host.autogen.interface import LASERLOCKER_LOCK_ERROR
from Host.autogen.interface import LASERLOCKER_WM_LOCK_WINDOW
from Host.autogen.interface import LASERLOCKER_WM_INT_GAIN
from Host.autogen.interface import LASERLOCKER_WM_PROP_GAIN
from Host.autogen.interface import LASERLOCKER_WM_DERIV_GAIN
from Host.autogen.interface import LASERLOCKER_FINE_CURRENT
from Host.autogen.interface import LASERLOCKER_CYCLE_COUNTER

from Host.autogen.interface import LASERLOCKER_CS_RUN_B, LASERLOCKER_CS_RUN_W
from Host.autogen.interface import LASERLOCKER_CS_CONT_B, LASERLOCKER_CS_CONT_W
from Host.autogen.interface import LASERLOCKER_CS_PRBS_B, LASERLOCKER_CS_PRBS_W
from Host.autogen.interface import LASERLOCKER_CS_ACC_EN_B, LASERLOCKER_CS_ACC_EN_W
from Host.autogen.interface import LASERLOCKER_CS_SAMPLE_DARK_B, LASERLOCKER_CS_SAMPLE_DARK_W
from Host.autogen.interface import LASERLOCKER_CS_ADC_STROBE_B, LASERLOCKER_CS_ADC_STROBE_W
from Host.autogen.interface import LASERLOCKER_CS_TUNING_OFFSET_SEL_B, LASERLOCKER_CS_TUNING_OFFSET_SEL_W
from Host.autogen.interface import LASERLOCKER_CS_LASER_FREQ_OK_B, LASERLOCKER_CS_LASER_FREQ_OK_W
from Host.autogen.interface import LASERLOCKER_CS_CURRENT_OK_B, LASERLOCKER_CS_CURRENT_OK_W
from Host.autogen.interface import LASERLOCKER_OPTIONS_SIM_ACTUAL_B, LASERLOCKER_OPTIONS_SIM_ACTUAL_W
from Host.autogen.interface import LASERLOCKER_OPTIONS_DIRECT_TUNE_B, LASERLOCKER_OPTIONS_DIRECT_TUNE_W

from MyHDL.Common.LaserLocker import LaserLocker

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
eta1_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
ref1_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
eta2_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
ref2_in = Signal(intbv(0)[WLM_ADC_WIDTH:])
tuning_offset_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
acc_en_in = Signal(LOW)
adc_strobe_in = Signal(LOW)
ratio1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
ratio2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
lock_error_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
fine_current_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
tuning_offset_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
pid_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
laser_freq_ok_out = Signal(LOW)
current_ok_out = Signal(LOW)
sim_actual_out = Signal(LOW)
map_base = FPGA_LASERLOCKER

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
    laserlocker = LaserLocker( clk=clk, reset=reset, dsp_addr=dsp_addr,
                               dsp_data_out=dsp_data_out,
                               dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
                               eta1_in=eta1_in, ref1_in=ref1_in,
                               eta2_in=eta2_in, ref2_in=ref2_in,
                               tuning_offset_in=tuning_offset_in,
                               acc_en_in=acc_en_in,
                               adc_strobe_in=adc_strobe_in,
                               ratio1_out=ratio1_out,
                               ratio2_out=ratio2_out,
                               lock_error_out=lock_error_out,
                               fine_current_out=fine_current_out,
                               tuning_offset_out=tuning_offset_out,
                               pid_out=pid_out,
                               laser_freq_ok_out=laser_freq_ok_out,
                               current_ok_out=current_ok_out,
                               sim_actual_out=sim_actual_out,
                               map_base=map_base )
    @instance
    def stimulus():
        result = Signal(intbv(0))
        yield assertReset()
        # Check single step mode
        yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_CS,1<<LASERLOCKER_CS_RUN_B)
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_CS,result)
        assert result & (1<<LASERLOCKER_CS_RUN_B) == 0
        # Test that we can read inputs in continuous mode
        eta1_in.next = randrange(mod)
        ref1_in.next = randrange(mod)
        eta2_in.next = randrange(mod)
        ref2_in.next = randrange(mod)
        tuning_offset_in.next = randrange(mod)
        yield clk.posedge
        yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_CS,
                        1<<LASERLOCKER_CS_RUN_B | \
                        1<<LASERLOCKER_CS_CONT_B | \
                        1<<LASERLOCKER_CS_TUNING_OFFSET_SEL_B)
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_ETA1,result)
        assert result == eta1_in
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_REF1,result)
        assert result == ref1_in
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_ETA2,result)
        assert result == eta2_in
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_REF2,result)
        assert result == ref2_in
        print "Reading inputs in continuous mode OK"
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_TUNING_OFFSET,result)
        assert result == tuning_offset_in
        print "Reading tuning offset input OK"
        # Test transfer of dark readings
        yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_CS,
                        1<<LASERLOCKER_CS_RUN_B | \
                        1<<LASERLOCKER_CS_CONT_B | \
                        1<<LASERLOCKER_CS_SAMPLE_DARK_B | \
                        1<<LASERLOCKER_CS_TUNING_OFFSET_SEL_B)        
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_ETA1_DARK,result)
        assert result == eta1_in
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_REF1_DARK,result)
        assert result == ref1_in
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_ETA2_DARK,result)
        assert result == eta2_in
        yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_REF2_DARK,result)
        assert result == ref2_in
        print "Transfer of dark currents OK"
        yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_CS,
                        1<<LASERLOCKER_CS_RUN_B | \
                        1<<LASERLOCKER_CS_CONT_B | \
                        1<<LASERLOCKER_CS_TUNING_OFFSET_SEL_B)
        prev_lock_error = 0
        prev_lock_error_deriv = 0
        deriv = 0
        deriv2 = 0

        for sets in range(5):
            yield clk.posedge
            acc_en_in.next = LOW
            yield clk.posedge
            fine_current = 0x8000
            wm_lock_window = randrange(32768)
            yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_WM_LOCK_WINDOW,wm_lock_window)
            wm_int_gain = randrange(-5000,5000) % mod
            yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_WM_INT_GAIN,wm_int_gain)
            wm_prop_gain = randrange(-5000,5000) % mod
            yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_WM_PROP_GAIN,wm_prop_gain)
            wm_deriv_gain = randrange(-5000,5000) % mod
            yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_WM_DERIV_GAIN,wm_deriv_gain)

            # Generate some mock data
            eta1_offset = randrange(1000)
            ref1_offset = randrange(1000)
            eta2_offset = randrange(1000)
            ref2_offset = randrange(1000)

            ratio1_cen = randrange(20000,44000)
            ratio2_cen = randrange(20000,44000)

            ratio1_multiplier = randrange(65536)
            ratio2_multiplier = randrange(65536)

            for steps in range(5):
                ref1 = 20000 + randrange(40000)
                ref2 = 20000 + randrange(45000)
                eta1 = eta1_offset + randrange(min(2*(ref1-ref1_offset),60000))
                eta2 = eta2_offset + randrange(min(2*(ref2-ref2_offset),60000))

                tuning_offset = randrange(30000,34000)

                ratio1 = div_sim(sub_sim(eta1,eta1_offset),sub_sim(ref1,ref1_offset))
                ratio2 = div_sim(sub_sim(eta2,eta2_offset),sub_sim(ref2,ref2_offset))

                print "Ratio1 = %04x, Ratio2 = %04x" % (ratio1,ratio2)
                ratio1c = sub_sim(ratio1,ratio1_cen)
                ratio2c = sub_sim(ratio2,ratio2_cen)
                print "Ratio1_cen = %04x, Ratio2_cen = %04x" % (ratio1_cen,ratio2_cen)
                print "CenteredRatio1 = %04x, CenteredRatio2 = %04x" % (ratio1c,ratio2c)
                print "Ratio1_multiplier = %04x, Ratio2_multiplier = %04x" % (ratio1_multiplier,ratio2_multiplier)
                prod1 = signed_mul_sim(ratio1_multiplier,ratio1c)
                prod2 = signed_mul_sim(ratio2_multiplier,ratio2c)
                print "Product1 = %04x, Product2 = %04x" % (prod1,prod2)
                print "Tuning offset = %04x" % (tuning_offset,)
                lock_error = add_sim(add_sim((tuning_offset - 32768) >> 3,prod1),prod2)
                print "LockError = %04x" % (lock_error,)
                locked = abs(intbv(lock_error)[16:].signed()) <= wm_lock_window
                deriv = lock_error - prev_lock_error
                deriv2 = deriv - prev_lock_error_deriv
                prev_lock_error = lock_error
                prev_lock_error_deriv = deriv

                int_prod = signed_mul_sim(lock_error,wm_int_gain)
                prop_prod = signed_mul_sim(deriv,wm_prop_gain)
                deriv_prod = signed_mul_sim(deriv2,wm_deriv_gain)

                fine_current = add_sim(fine_current,int_prod)
                fine_current = add_sim(fine_current,prop_prod)
                fine_current = add_sim(fine_current,deriv_prod)

                print "IntegralProduct = %04x" % (int_prod,)
                print "ProportionalProduct = %04x" % (prop_prod,)
                print "DerivProduct = %04x" % (deriv_prod,)
                print "FineCurrent = %04x" % (fine_current,)

                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_ETA1_OFFSET,eta1_offset)
                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_REF1_OFFSET,ref1_offset)
                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_ETA2_OFFSET,eta2_offset)
                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_REF2_OFFSET,ref2_offset)
                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO1_CENTER,ratio1_cen)
                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO2_CENTER,ratio2_cen)
                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO1_MULTIPLIER,ratio1_multiplier)
                yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO2_MULTIPLIER,ratio2_multiplier)

                yield clk.negedge
                tuning_offset_in.next = tuning_offset
                yield clk.negedge

                yield clk.negedge
                eta1_in.next = eta1
                ref1_in.next = ref1
                eta2_in.next = eta2
                ref2_in.next = ref2
                yield clk.negedge
                adc_strobe_in.next = HIGH
                yield clk.negedge
                acc_en_in.next = HIGH
                yield current_ok_out.posedge

                yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO1,result)
                assert ratio1 == result
                assert ratio1 == ratio1_out
                yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_RATIO2,result)
                assert ratio2 == result
                assert ratio2 == ratio2_out

                yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_FINE_CURRENT,result)
                assert fine_current == result
                assert fine_current_out == result

                yield readFPGA(FPGA_LASERLOCKER + LASERLOCKER_LOCK_ERROR,result)
                assert lock_error == result
                assert lock_error == lock_error_out

                assert locked == laser_freq_ok_out
                clk.negedge
                adc_strobe_in.next = LOW

        yield writeFPGA(FPGA_LASERLOCKER + LASERLOCKER_CS,
                        1<<LASERLOCKER_CS_RUN_B | \
                        1<<LASERLOCKER_CS_CONT_B | \
                        1<<LASERLOCKER_CS_PRBS_B)

        for k in range(256):
            yield clk.posedge
            adc_strobe_in.next = HIGH
            yield clk.posedge
            adc_strobe_in.next = LOW
            yield current_ok_out.posedge
            print "0x%4x" % fine_current_out

        yield delay(200*PERIOD)
        raise StopSimulation
    return instances()

def test_LaserLocker():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_LaserLocker()
