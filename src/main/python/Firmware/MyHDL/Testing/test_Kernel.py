#!/usr/bin/python
#
# FILE:
#   test_Kernel.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   27-Jul-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import FPGA_MAGIC_CODE
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_KERNEL

from Host.autogen.interface import KERNEL_MAGIC_CODE, KERNEL_CONTROL
from Host.autogen.interface import KERNEL_DIAG_1, KERNEL_CONFIG
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL
from Host.autogen.interface import KERNEL_INTRONIX_1, KERNEL_INTRONIX_2
from Host.autogen.interface import KERNEL_INTRONIX_3, KERNEL_OVERLOAD
from Host.autogen.interface import KERNEL_DOUT_HI, KERNEL_DOUT_LO
from Host.autogen.interface import KERNEL_DIN, KERNEL_STATUS_LED
from Host.autogen.interface import KERNEL_FAN
from Host.autogen.interface import KERNEL_FAN, KERNEL_SEL_DETECTOR_MODE

from Host.autogen.interface import KERNEL_CONTROL_CYPRESS_RESET_B, KERNEL_CONTROL_CYPRESS_RESET_W
from Host.autogen.interface import KERNEL_CONTROL_OVERLOAD_RESET_B, KERNEL_CONTROL_OVERLOAD_RESET_W
from Host.autogen.interface import KERNEL_CONTROL_I2C_RESET_B, KERNEL_CONTROL_I2C_RESET_W
from Host.autogen.interface import KERNEL_CONTROL_DOUT_MAN_B, KERNEL_CONTROL_DOUT_MAN_W
from Host.autogen.interface import KERNEL_INTRONIX_CLKSEL_DIVISOR_B, KERNEL_INTRONIX_CLKSEL_DIVISOR_W
from Host.autogen.interface import KERNEL_INTRONIX_1_CHANNEL_B, KERNEL_INTRONIX_1_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_2_CHANNEL_B, KERNEL_INTRONIX_2_CHANNEL_W
from Host.autogen.interface import KERNEL_INTRONIX_3_CHANNEL_B, KERNEL_INTRONIX_3_CHANNEL_W
from Host.autogen.interface import KERNEL_STATUS_LED_RED_B, KERNEL_STATUS_LED_RED_W
from Host.autogen.interface import KERNEL_STATUS_LED_GREEN_B, KERNEL_STATUS_LED_GREEN_W
from Host.autogen.interface import KERNEL_FAN_FAN1_B, KERNEL_FAN_FAN1_W
from Host.autogen.interface import KERNEL_FAN_FAN2_B, KERNEL_FAN_FAN2_W
from Host.autogen.interface import KERNEL_SEL_DETECTOR_MODE_MODE_B, KERNEL_SEL_DETECTOR_MODE_MODE_W

from MyHDL.Common.Kernel import Kernel

LOW, HIGH = bool(0), bool(1)
clk = Signal(LOW)
reset = Signal(LOW)
dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_wr = Signal(LOW)
sel_laser_in = Signal(intbv(0)[2:])
usb_connected = Signal(LOW)
cyp_reset = Signal(LOW)
sel_detector_out = Signal(LOW)
diag_1_out = Signal(intbv(0)[8:])
config_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
intronix_clksel_out = Signal(intbv(0)[5:])
intronix_1_out = Signal(intbv(0)[8:])
intronix_2_out = Signal(intbv(0)[8:])
intronix_3_out = Signal(intbv(0)[8:])
overload_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
overload_out = Signal(LOW)
i2c_reset_out = Signal(LOW)
status_led_out = Signal(intbv(0)[2:])
fan_out = Signal(intbv(0)[2:])
dout_man_out = Signal(LOW)
dout_out = Signal(intbv(0)[40:])
din_in = Signal(intbv(0)[24:])
map_base = FPGA_KERNEL
result = Signal(intbv(0))

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
    kernel = Kernel( clk=clk, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                     dsp_wr=dsp_wr, sel_laser_in=sel_laser_in,
                     usb_connected=usb_connected, cyp_reset=cyp_reset,
                     sel_detector_out=sel_detector_out,
                     diag_1_out=diag_1_out, config_out=config_out,
                     intronix_clksel_out=intronix_clksel_out,
                     intronix_1_out=intronix_1_out,
                     intronix_2_out=intronix_2_out,
                     intronix_3_out=intronix_3_out,
                     overload_in=overload_in, overload_out=overload_out,
                     i2c_reset_out=i2c_reset_out,
                     status_led_out=status_led_out, fan_out=fan_out,
                     dout_man_out=dout_man_out, dout_out=dout_out,
                     din_in=din_in, map_base=map_base )
    @instance
    def stimulus():
        yield delay(10*PERIOD)
        yield assertReset()
        overload_in.next = 0x42
        assert i2c_reset_out
        yield readFPGA(FPGA_KERNEL+KERNEL_OVERLOAD,result)
        assert int(result) == 0x42
        yield writeFPGA(FPGA_KERNEL+KERNEL_CONTROL,1<<KERNEL_CONTROL_OVERLOAD_RESET_B)
        yield readFPGA(FPGA_KERNEL+KERNEL_OVERLOAD,result)
        assert int(result) == 0x42
        overload_in.next = 0x7
        yield readFPGA(FPGA_KERNEL+KERNEL_OVERLOAD,result)
        assert int(result) == 0x47
        yield writeFPGA(FPGA_KERNEL+KERNEL_CONTROL,1<<KERNEL_CONTROL_OVERLOAD_RESET_B)
        yield readFPGA(FPGA_KERNEL+KERNEL_OVERLOAD,result)
        assert int(result) == 0x7
        overload_in.next = 0x0
        yield writeFPGA(FPGA_KERNEL+KERNEL_CONTROL,1<<KERNEL_CONTROL_OVERLOAD_RESET_B)
        yield readFPGA(FPGA_KERNEL+KERNEL_OVERLOAD,result)
        assert int(result) == 0x0
        assert not i2c_reset_out
        yield writeFPGA(FPGA_KERNEL+KERNEL_CONTROL,1<<KERNEL_CONTROL_I2C_RESET_B)
        assert i2c_reset_out        
        yield writeFPGA(FPGA_KERNEL+KERNEL_CONTROL,0)
        assert not i2c_reset_out
        yield writeFPGA(FPGA_KERNEL+KERNEL_CONTROL,1<<KERNEL_CONTROL_DOUT_MAN_B)
        yield writeFPGA(FPGA_KERNEL+KERNEL_DOUT_HI,0xFE)
        yield writeFPGA(FPGA_KERNEL+KERNEL_DOUT_LO,0xDCBA9876)
        # Test detector selection
        yield writeFPGA(FPGA_KERNEL+KERNEL_SEL_DETECTOR_MODE, 0x7)
        for i in range(4):
            sel_laser_in.next = i
            yield clk.posedge
            yield delay(20*PERIOD)

        yield delay(20*PERIOD)
        raise StopSimulation
    return instances()

def test_Kernel():
    s = Simulation(traceSignals(bench))
    s.run(quiet=1)

if __name__ == "__main__":
    test_Kernel()
