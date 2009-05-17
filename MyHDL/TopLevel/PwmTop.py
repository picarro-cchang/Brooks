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
from MyHDL.Common.Rdmemory  import Rdmemory
from MyHDL.Common.RdDataAddrGen import RdDataAddrGen

LOW, HIGH = bool(0), bool(1)

t_State = enum("IDLE","RESETTING","COLLECTING","DONE")

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
         monitor,
         dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7):

    NSTAGES = 28
    counter = Signal(intbv(0)[NSTAGES:])

    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser1_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser2_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser3_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser4_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdcompare   = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdmemory    = Signal(intbv(0)[EMIF_DATA_WIDTH:])

    dsp_wr, ce2 = [Signal(LOW) for i in range(2)]
    laser1_pwm_out, laser1_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser2_pwm_out, laser2_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser3_pwm_out, laser3_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser4_pwm_out, laser4_pwm_inv_out = [Signal(LOW) for i in range(2)]
    compare_result = Signal(LOW)

    # The divisor signal is actually a 16 bit word from the DSP. We use
    #  the low order 5 bits for the ringdown memory address divisor
    #  and the high-order 8 bits for controlling a state machine
    divisor = Signal(intbv(0)[FPGA_REG_WIDTH:])
    arm = Signal(LOW)
    addr_div = Signal(intbv(0)[5:])
    addr_reset,enable,data_we,adc_clk = [Signal(LOW) for i in range(4)]

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

    state = Signal(t_State.IDLE)
    rdmem_max_data_addr = (1<<DATA_BANK_ADDR_WIDTH)-1

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
                dsp_wr=dsp_wr, divisor=divisor,
                value=rd_adc,result=compare_result,
                map_base=FPGA_RDCOMPARE)

    rdmemory = Rdmemory(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdmemory,
                dsp_wr=dsp_wr, bank=bank, data_addr=data_addr,
                data=data, wr_data=wr_data, data_we=data_we,
                meta_addr=meta_addr, meta=meta, wr_meta=wr_meta,
                meta_we=meta_we, param_addr=param_addr,
                param=param, wr_param=wr_param, param_we=param_we)

    rdDataAddrGen = RdDataAddrGen(clk=clk0,addr_reset=addr_reset,
                enable=enable,addr_div=addr_div,
                data_addr=data_addr,data_we=data_we,
                adc_clk=adc_clk)

    @instance
    def  logic():
        while True:
            yield clk0.posedge, reset.posedge
            if reset:
                counter.next = 0
            else:
                counter.next = counter + 1
                # Simple state machine to acquire a buffer of data
                #  into rindown data memory
                if state == t_State.IDLE:
                    enable.next = 0
                    addr_reset.next = 0
                    if arm:
                        state.next = t_State.RESETTING
                elif state == t_State.RESETTING:
                    enable.next = 0
                    addr_reset.next = 1
                    state.next = t_State.COLLECTING
                elif state == t_State.COLLECTING:
                    enable.next = 1
                    addr_reset.next = 0
                    if (data_addr == rdmem_max_data_addr) and data_we:
                        state.next = t_State.DONE
                elif state == t_State.DONE:
                    enable.next = 0
                    addr_reset.next = 0
                    if not arm:
                        state.next = t_State.IDLE

    @always_comb
    def  comb():
        dsp_data_in.next = dsp_data_in_laser1_pwm | \
                           dsp_data_in_laser2_pwm | \
                           dsp_data_in_laser3_pwm | \
                           dsp_data_in_laser4_pwm | \
                           dsp_data_in_rdcompare  | \
                           dsp_data_in_rdmemory

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
        rd_adc_clk.next = adc_clk
        rd_adc_oe.next = 1
        fpga_led.next = counter[NSTAGES:NSTAGES-4]
        i2c_rst0.next = reset
        i2c_rst1.next = reset
        intronix.next[28] = i2c_scl0
        intronix.next[29] = i2c_sda0
        intronix.next[30] = i2c_scl1
        intronix.next[31] = i2c_sda1
        intronix.next[33] = clk0

        bank.next = 0
        meta_addr.next = 0
        wr_meta.next = 0
        meta_we.next = 0
        param_addr.next = 0
        wr_param.next = 0
        param_we.next = 0

        wr_data.next = rd_adc
        addr_div.next = divisor[5:]
        arm.next = divisor[8]

        dsp_ext_int4.next = counter[NSTAGES-4]
        dsp_ext_int5.next = 0
        dsp_ext_int6.next = 0
        dsp_ext_int7.next = 0

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
dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7 = [Signal(LOW) for i in range(4)]

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
                monitor,
                dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7)

if __name__ == "__main__":
    makeVHDL()
