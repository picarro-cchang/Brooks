#!/usr/bin/python
#
# FILE:
#   PwmTop.py
#
# DESCRIPTION:
#   Top level file for synthesizing laser PWM blocks
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   9-May-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen.interface import *
from MyHDL.Common.Pwm1 import Pwm
from MyHDL.Common.dsp_interface import Dsp_interface
from MyHDL.Common.Rdcompare import Rdcompare

LOW, HIGH = bool(0), bool(1)

def main(clk0,clk180,clk3f,clk3f180,clk_locked,
         reset,intronix,fpga_led,
         dsp_emif_we,dsp_emif_re,dsp_emif_oe,dsp_emif_ardy,
         dsp_emif_ea,dsp_emif_din, dsp_emif_dout,
         dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
         dsp_eclk,
         lsr1_0, lsr1_1, lsr2_0, lsr2_1, lsr3_0, lsr3_1, lsr4_0, lsr4_1,
         i2c_rst0, i2c_rst1,
         i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
         rd_adc, rd_adc_clk, rd_adc_oe,
         monitor):

    NSTAGES = 28
    counter = Signal(intbv(0)[NSTAGES:])

    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser1_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser2_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser3_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser4_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdcompare  = Signal(intbv(0)[EMIF_DATA_WIDTH:])

    dsp_wr, ce2 = [Signal(LOW) for i in range(2)]
    laser1_pwm_out, laser1_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser2_pwm_out, laser2_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser3_pwm_out, laser3_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser4_pwm_out, laser4_pwm_inv_out = [Signal(LOW) for i in range(2)]
    compare_result = Signal(LOW)

    dsp_interface = Dsp_interface(clk=clk0, reset=reset, addr=dsp_emif_ea,
                                  to_dsp=dsp_emif_din, re=dsp_emif_re,
                                  we=dsp_emif_we, oe=dsp_emif_oe,
                                  ce=ce2,
                                  from_dsp=dsp_emif_dout,
                                  rdy=dsp_emif_ardy,
                                  dsp_oe=dsp_emif_ddir,
                                  dsp_addr=dsp_addr,
                                  dsp_data_out=dsp_data_out,
                                  dsp_data_in=dsp_data_in,
                                  dsp_wr=dsp_wr)

    laser1_pwm = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_laser1_pwm,
              dsp_wr=dsp_wr,
              pwm_out=laser1_pwm_out,
              pwm_inv_out=laser1_pwm_inv_out,
              map_base=FPGA_LASER1_PWM)

    laser2_pwm = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_laser2_pwm,
              dsp_wr=dsp_wr,
              pwm_out=laser2_pwm_out,
              pwm_inv_out=laser2_pwm_inv_out,
              map_base=FPGA_LASER2_PWM)

    laser3_pwm = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_laser3_pwm,
              dsp_wr=dsp_wr,
              pwm_out=laser3_pwm_out,
              pwm_inv_out=laser3_pwm_inv_out,
              map_base=FPGA_LASER3_PWM)

    laser4_pwm = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_laser4_pwm,
              dsp_wr=dsp_wr,
              pwm_out=laser4_pwm_out,
              pwm_inv_out=laser4_pwm_inv_out,
              map_base=FPGA_LASER4_PWM)

    rdcompare = Rdcompare(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdcompare,
                dsp_wr=dsp_wr,
                value=rd_adc,result=compare_result,
                map_base=FPGA_RDCOMPARE)

    @instance
    def  logic():
        while True:
            yield clk0.posedge, reset.posedge
            if reset:
                counter.next = 0
            else:
                counter.next = counter + 1

    @always_comb
    def  comb():
        dsp_data_in.next = dsp_data_in_laser1_pwm | \
                           dsp_data_in_laser2_pwm | \
                           dsp_data_in_laser3_pwm | \
                           dsp_data_in_laser4_pwm | \
                           dsp_data_in_rdcompare

        ce2.next = dsp_emif_ce[2]
        intronix.next[16]  = laser1_pwm_out
        intronix.next[17]  = laser1_pwm_inv_out
        lsr1_0.next = laser1_pwm_out
        lsr1_1.next = laser1_pwm_inv_out
        intronix.next[18]  = laser2_pwm_out
        intronix.next[19]  = laser2_pwm_inv_out
        lsr2_0.next = laser2_pwm_out
        lsr2_1.next = laser2_pwm_inv_out
        intronix.next[20]  = laser3_pwm_out
        intronix.next[21]  = laser3_pwm_inv_out
        lsr3_0.next = laser3_pwm_out
        lsr3_1.next = laser3_pwm_inv_out
        intronix.next[22]  = laser4_pwm_out
        intronix.next[23]  = laser4_pwm_inv_out
        lsr4_0.next = laser4_pwm_out
        lsr4_1.next = laser4_pwm_inv_out
        intronix.next[24] = dsp_emif_we
        intronix.next[25] = dsp_emif_oe
        intronix.next[26] = dsp_emif_re
        intronix.next[27] = dsp_emif_ce[2]
        intronix.next[32] = compare_result
        monitor.next = compare_result

        intronix.next[16:] = rd_adc
        rd_adc_clk.next = counter[0]
        rd_adc_oe.next = 1
        fpga_led.next = counter[NSTAGES:NSTAGES-4]
        i2c_rst0.next = reset
        i2c_rst1.next = reset
        intronix.next[28] = i2c_scl0
        intronix.next[29] = i2c_sda0
        intronix.next[30] = i2c_scl1
        intronix.next[31] = i2c_sda1
        intronix.next[33] = clk0

    return instances()

# Clock generator
clk0, clk180, clk3f, clk3f180, clk_locked = \
    [Signal(LOW) for i in range(5)]
# Reset
reset = Signal(LOW)
# Mictor connector to Intronix probe
intronix = Signal(intbv(0)[34:])
# FPGA LEDS
fpga_led = Signal(intbv(0)[4:])
# DSP EMIF signals
dsp_emif_we, dsp_emif_re, dsp_emif_oe, dsp_emif_ddir, dsp_emif_ardy =  \
    [Signal(LOW) for i in range(5)]
dsp_emif_ea = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
dsp_emif_din = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_emif_dout = Signal(intbv(0)[EMIF_DATA_WIDTH:])
dsp_emif_be = Signal(intbv(0)[4:])
dsp_emif_ce = Signal(intbv(0)[4:])
i2c_rst0, i2c_rst1 = [Signal(LOW) for i in range(2)]
i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1 = [Signal(LOW) for i in range(4)]
rd_adc = Signal(intbv(0)[16:])
rd_adc_clk, rd_adc_oe = [Signal(LOW) for i in range(2)]
dsp_eclk, monitor = [Signal(LOW) for i in range(2)]
lsr1_0, lsr1_1, lsr2_0, lsr2_1 = [Signal(LOW) for i in range(4)]
lsr3_0, lsr3_1, lsr4_0, lsr4_1 = [Signal(LOW) for i in range(4)]

def makeVHDL():
    toVHDL(main,clk0,clk180,clk3f,clk3f180,clk_locked,reset,
                intronix,fpga_led,dsp_emif_we,dsp_emif_re,
                dsp_emif_oe,dsp_emif_ardy,dsp_emif_ea,dsp_emif_din,
                dsp_emif_dout,dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
                dsp_eclk,
                lsr1_0, lsr1_1, lsr2_0, lsr2_1, lsr3_0, lsr3_1, lsr4_0, lsr4_1,
                i2c_rst0, i2c_rst1,
                i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
                rd_adc, rd_adc_clk, rd_adc_oe,
                monitor)

if __name__ == "__main__":
    makeVHDL()
