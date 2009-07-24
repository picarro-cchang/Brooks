from Host.Common import CmdFIFO, SharedTypes
from Host.autogen.interface import *
from numpy import *
from pylab import *
from random import randrange
from time import sleep

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

if __name__ == "__main__":
    serverURI = "http://localhost:%d" % (SharedTypes.RPC_PORT_DRIVER,)
    driver = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="testLaserLocker")
    # Run continuously for awhile to get counter up to maximum
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_CONT_B | 1<<LASERLOCKER_CS_ADC_STROBE_B)
    while driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CYCLE_COUNTER")<50: sleep(0.1)
    
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
        cs = driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS")
        assert i == counter
    print "Cycle counter advances correctly"
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B)
    assert 50 == driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CYCLE_COUNTER")
    print "Cycle counter stops correctly"
    driver.wrFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS",1<<LASERLOCKER_CS_RUN_B | 1<<LASERLOCKER_CS_ADC_STROBE_B)
    assert (1<<LASERLOCKER_CS_CURRENT_OK_B) & driver.rdFPGA("FPGA_LASERLOCKER","LASERLOCKER_CS")
    print "Current OK flag asserted correctly"
    assert driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO1) == div_sim(eta1-eta1_off,ref1-ref1_off)
    assert driver.rdFPGA("FPGA_LASERLOCKER",LASERLOCKER_RATIO2) == div_sim(eta2-eta2_off,ref2-ref2_off)
    print "Ratios calculated correctly"

    