#!/usr/bin/python
#
# FILE:
#   test_Rdmemory.py
#
# DESCRIPTION:
#   Dual ported memory for storing ringdown information
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   14-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from random import randrange

from MyHDL.Common.Rdmemory import Rdmemory
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH, FPGA_REG_WIDTH
from Host.autogen.interface import DATA_BANK_ADDR_WIDTH, META_BANK_ADDR_WIDTH, PARAM_BANK_ADDR_WIDTH
from Host.autogen.interface import RDMEM_DATA_WIDTH, RDMEM_META_WIDTH, RDMEM_PARAM_WIDTH

LOW, HIGH = bool(0), bool(1)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr, clk, reset, adc_clk = [Signal(LOW) for i in range(4)]
PERIOD = 20

bank = Signal(LOW)
data_addr = Signal(intbv(0)[DATA_BANK_ADDR_WIDTH:])
data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
wr_data = Signal(intbv(0)[RDMEM_DATA_WIDTH:])
data_we = Signal(LOW)
meta_addr = Signal(intbv(0)[META_BANK_ADDR_WIDTH:])
meta = Signal(intbv(0)[RDMEM_META_WIDTH:])
wr_meta = Signal(intbv(0)[RDMEM_META_WIDTH:])
meta_we = Signal(LOW)
param_addr = Signal(intbv(0)[PARAM_BANK_ADDR_WIDTH:])
param = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
wr_param = Signal(intbv(0)[RDMEM_PARAM_WIDTH:])
param_we = Signal(LOW)

def  bench():
    """ Unit test for ringdown memory """
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

    rdmemory = Rdmemory(clk=clk, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                     dsp_wr=dsp_wr, bank=bank,
                     data_addr=data_addr, data=data, wr_data=wr_data, data_we=data_we,
                     meta_addr=meta_addr, meta=meta, wr_meta=wr_meta, meta_we=meta_we,
                     param_addr=param_addr, param=param, wr_param=wr_param, param_we=param_we)

    @instance
    def  stimulus():
        memDict = {}
        result = Signal(intbv(0))
        yield assertReset()
        nWrites = 500
        # Check read-write access to data, meta and param memory
        #  from the DSP
        for iter in range(nWrites):
            dspBank = 0x4000 if randrange(2) else 0
            addr = dspBank + randrange(1<<DATA_BANK_ADDR_WIDTH)
            d = randrange(1<<RDMEM_DATA_WIDTH)
            memDict[addr] = d
            yield wrRingdownMem(addr,d)
            
            dspBank = 0x5000 if randrange(2) else 0x1000
            addr = dspBank + randrange(1<<META_BANK_ADDR_WIDTH)
            d = randrange(1<<RDMEM_META_WIDTH)
            memDict[addr] = d
            yield wrRingdownMem(addr,d)
            
            dspBank = 0x7000 if randrange(2) else 0x3000
            addr = dspBank + randrange(1<<PARAM_BANK_ADDR_WIDTH)
            d = randrange(1<<RDMEM_PARAM_WIDTH)
            memDict[addr] = d
            yield wrRingdownMem(addr,d)
        print "Finished writing to data, metadata and parameter memory via DSP"
        # Read these data back via the DSP interface    
        for a in memDict:
            yield rdRingdownMem(a,result)
            assert result == memDict[a]
        print "Finished reading back data, metadata and parameter memory via DSP"
        
        # Read these back via the FPGA port
        for a in memDict:
            bank.next = 1 if (a & 0x4000) else 0
            if 0 == (a & 0x3000): # This is data memory
                data_addr.next = a & 0xFFF
                yield clk.negedge
                yield clk.negedge
                if data != memDict[a]:
                    print "Bank %d Data Address %x (Dsp Address %x) should contain %x, but we read %x" % (bank,data_addr,a,memDict[a],data)
                    assert False
                yield rdRingdownMem(a+0x2000,result)
                if result & 0xFFFF != memDict[a] & 0xFFFF:
                    print "Bank %d Data Address %x contains %x, but we read %x from DSP address %x" % (bank,data_addr,memDict[a],result,a+0x2000)
                    assert False
                
            elif 0x1000 == (a & 0x3000): # This is metadata memory
                meta_addr.next = a & 0xFFF
                yield clk.negedge
                yield clk.negedge
                if meta != memDict[a]:
                    print "Bank %d Meta Address %x (Dsp Address %x) should contain %x, but we read %x" % (bank,meta_addr,a,memDict[a],data)
                    assert False
                yield rdRingdownMem(a+0x1000,result)
                if (result >> 16) != memDict[a]:
                    print "Bank %d Meta Address %x contains %x, but we read %x from DSP address %x" % (bank,meta_addr,memDict[a],result,a+0x1000)
                    assert False

            elif 0x3000 == (a & 0x3000): # This is parameter memory
                param_addr.next = a & 0x3F
                yield clk.negedge
                yield clk.negedge
                if param != memDict[a]:
                    print "Bank %d Param Address %x (Dsp Address %x) should contain %x, but we read %x" % (bank,param_addr,a,memDict[a],data)
                    assert False
        print "Finished reading back data, metadata and parameter memory via FPGA"
        
        # Perform a number of writes via the FPGA port
        for iter in range(nWrites):
            b = randrange(2)
            dspBank = 0x4000 if b else 0
            a = randrange(1<<DATA_BANK_ADDR_WIDTH)
            addr = dspBank + a
            d = randrange(1<<RDMEM_DATA_WIDTH)
            memDict[addr] = d
            bank.next = b
            data_addr.next = a
            wr_data.next = d
            data_we.next = 1
            yield clk.negedge
            data_we.next = 0
            yield clk.negedge

            b = randrange(2)
            dspBank = 0x5000 if b else 0x1000
            a = randrange(1<<META_BANK_ADDR_WIDTH)
            addr = dspBank + a
            d = randrange(1<<RDMEM_META_WIDTH)
            memDict[addr] = d
            bank.next = b
            meta_addr.next = a
            wr_meta.next = d
            meta_we.next = 1
            yield clk.negedge
            meta_we.next = 0
            yield clk.negedge
            
            b = randrange(2)
            dspBank = 0x7000 if b else 0x3000
            a = randrange(1<<PARAM_BANK_ADDR_WIDTH)
            addr = dspBank + a
            d = randrange(1<<RDMEM_PARAM_WIDTH)
            memDict[addr] = d
            bank.next = b
            param_addr.next = a
            wr_param.next = d
            param_we.next = 1
            yield clk.negedge
            param_we.next = 0
            yield clk.negedge

        print "Finished writing to data, metadata and parameter memory via FPGA"
        # Read these data back via the DSP interface    
        for a in memDict:
            yield rdRingdownMem(a,result)
            assert result == memDict[a]
        print "Finished reading back data, metadata and parameter memory via DSP"
        raise StopSimulation

    return instances()

def test_rdMemory():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_rdMemory()