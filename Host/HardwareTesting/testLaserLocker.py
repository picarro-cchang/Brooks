from Host.Common import CmdFIFO, SharedTypes
from Host.autogen.interface import *
from myhdl import *
from random import randrange
from time import sleep
import sys

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


def test_laserLocker():
    serverURI = "http://localhost:%d" % (SharedTypes.RPC_PORT_DRIVER,)
    driver = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="testLaserLocker")
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B)
    cs = driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS")
    assert 0 == cs & (1<<LASERLOCKER_CS_RUN_B) 
    print "Single step test passed"
    eta1_dark, ref1_dark, eta2_dark, ref2_dark = [randrange(100,200) for i in range(4)]
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA1",eta1_dark)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF1",ref1_dark)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA2",eta2_dark)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF2",ref2_dark)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_SAMPLE_DARK_B)
    assert driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA1_DARK") == eta1_dark
    assert driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF1_DARK") == ref1_dark
    assert driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA2_DARK") == eta2_dark
    assert driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF2_DARK") == ref2_dark
    print "Dark current transfer passed"
    eta1_off, ref1_off, eta2_off, ref2_off = [randrange(100,200) for i in range(4)]
    ref1, ref2 = [randrange(30000,65536-200) for i in range(2)]
    eta1 = randrange(0,min(2*ref1,65536-200))
    eta2 = randrange(0,min(2*ref2,65536-200))
    eta1 += eta1_off
    ref1 += ref1_off
    eta2 += eta2_off
    ref2 += ref2_off
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA1_OFFSET",eta1_off)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF1_OFFSET",ref1_off)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA2_OFFSET",eta2_off)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF2_OFFSET",ref2_off)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA1",eta1)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF1",ref1)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_ETA2",eta2)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_REF2",ref2)
    for i in range(51):
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B)
        counter = driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CYCLE_COUNTER")
        assert i == counter
    print "Cycle counter advances correctly"
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B)
    assert 50 == driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CYCLE_COUNTER")
    print "Cycle counter stops correctly"
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B)
    assert (1<<LASERLOCKER_CS_CURRENT_OK_B) & driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS")
    print "Current OK flag asserted correctly"
    assert driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO1) == div_sim(eta1-eta1_off,ref1-ref1_off)
    assert driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO2) == div_sim(eta2-eta2_off,ref2-ref2_off)
    print "Ratios calculated correctly"

    # Reset the internal memories by forcing zero error output
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO1_MULTIPLIER",0)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_RATIO2_MULTIPLIER",0)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_TUNING_OFFSET",32768)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_DERIV_GAIN",16384)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_INT_GAIN",16384)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_PROP_GAIN",16384)
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_LOCK_WINDOW",1)
    # Run to get counter up to maximum
    for loops in range(3):
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B)
        while driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CYCLE_COUNTER")<50:
            driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B)
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B)
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B)

    # Enable accumulator and check that it remains at 32768
    for loops in range(4):
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        while driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CYCLE_COUNTER")<50:
            driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        assert (1<<LASERLOCKER_CS_CURRENT_OK_B) & driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS")
        assert (1<<LASERLOCKER_CS_LASER_FREQ_OK_B) & driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS")
        assert 32768 == driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_FINE_CURRENT")
    print "Internal memories reset correctly"

    prev_lock_error = 0
    prev_lock_error_deriv = 0
    deriv = 0
    deriv2 = 0
    fine_current = 0x8000

    print "Trying random test vectors:"
    for iter in range(100):
        # Generate some test vectors
        wm_lock_window = randrange(32768)
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_WM_LOCK_WINDOW",wm_lock_window)
        
        wm_int_gain = randrange(-5000,5000) % mod
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_WM_INT_GAIN,wm_int_gain)
        wm_prop_gain = randrange(-5000,5000) % mod
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_WM_PROP_GAIN,wm_prop_gain)
        wm_deriv_gain = randrange(-5000,5000) % mod
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_WM_DERIV_GAIN,wm_deriv_gain)
        
        ref1, ref2 = [randrange(30000,65536-200) for i in range(2)]
        eta1 = randrange(0,min(2*ref1,65536-200))
        eta2 = randrange(0,min(2*ref2,65536-200))
        eta1 += eta1_off
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_ETA1,eta1)
        ref1 += ref1_off
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_REF1,ref1)
        eta2 += eta2_off
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_ETA2,eta2)
        ref2 += ref2_off
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_REF2,ref2)
    
        ratio1_cen = randrange(20000,44000)
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO1_CENTER,ratio1_cen)
        ratio2_cen = randrange(20000,44000)
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO2_CENTER,ratio2_cen)
        ratio1_multiplier = randrange(65536)
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO1_MULTIPLIER,ratio1_multiplier)
        ratio2_multiplier = randrange(65536)
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO2_MULTIPLIER,ratio2_multiplier)
        tuning_offset = randrange(30000,34000)
        driver.wrFPGA("FPGA_LASERLOCKER",LASERLOCKER_TUNING_OFFSET,tuning_offset)
    
        # Calculate expected values of all locker variables
        ratio1 = div_sim(sub_sim(eta1,eta1_off),sub_sim(ref1,ref1_off))
        ratio2 = div_sim(sub_sim(eta2,eta2_off),sub_sim(ref2,ref2_off))
        #print "Ratio1 = %04x, Ratio2 = %04x" % (ratio1,ratio2)
        ratio1c = sub_sim(ratio1,ratio1_cen)
        ratio2c = sub_sim(ratio2,ratio2_cen)
        #print "Ratio1_cen = %04x, Ratio2_cen = %04x" % (ratio1_cen,ratio2_cen)
        #print "CenteredRatio1 = %04x, CenteredRatio2 = %04x" % (ratio1c,ratio2c)
        #print "Ratio1_multiplier = %04x, Ratio2_multiplier = %04x" % (ratio1_multiplier,ratio2_multiplier)
        prod1 = signed_mul_sim(ratio1_multiplier,ratio1c)
        prod2 = signed_mul_sim(ratio2_multiplier,ratio2c)
        #print "Product1 = %04x, Product2 = %04x" % (prod1,prod2)
        #print "Tuning offset = %04x" % (tuning_offset,)
        lock_error = add_sim(add_sim(tuning_offset-32768,prod1),prod2)
        #print "LockError = %04x" % (lock_error,)
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
    
        #print "IntegralProduct = %04x" % (int_prod,)
        #print "ProportionalProduct = %04x" % (prop_prod,)
        #print "DerivProduct = %04x" % (deriv_prod,)
        #print "FineCurrent = %04x" % (fine_current,)
    
        # Carry out algorithm in FPGA
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        while driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CYCLE_COUNTER")<50:
            driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ACC_EN_B)
        fpga_ratio1 = driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO1)
        assert ratio1 == fpga_ratio1
        fpga_ratio2 = driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO2)
        assert ratio2 == fpga_ratio2
        fpga_lock_error = driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_LOCK_ERROR)
        assert lock_error == fpga_lock_error
        fpga_fine_current = driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_FINE_CURRENT)
        assert fine_current == fpga_fine_current
        cs = driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_CS)
        assert locked == (0 != (cs & 1<<LASERLOCKER_CS_LASER_FREQ_OK_B))
        sys.stdout.write(".")
    print
    
if __name__ == "__main__":
    test_laserLocker()
    
