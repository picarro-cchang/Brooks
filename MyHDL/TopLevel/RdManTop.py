#!/usr/bin/python
#
# FILE:
#   RdSimTop.py
#
# DESCRIPTION:
#   Top level file for synthesizing FPGA with ringdown manager
#  and simulator
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
from MyHDL.Common.ClkGen import ClkGen
from MyHDL.Common.dsp_interface import Dsp_interface
from MyHDL.Common.Kernel import Kernel
from MyHDL.Common.Inject import Inject
from MyHDL.Common.Pwm1 import Pwm
from MyHDL.Common.Rdcompare import Rdcompare
from MyHDL.Common.Rdmemory  import Rdmemory
from MyHDL.Common.TWGen import TWGen
from MyHDL.Common.RdSim import RdSim
from MyHDL.Common.RdMan import RdMan

LOW, HIGH = bool(0), bool(1)

def main(clk0,clk180,clk3f,clk3f180,clk_locked,
         reset,intronix,fpga_led,
         dsp_emif_we,dsp_emif_re,dsp_emif_oe,dsp_emif_ardy,
         dsp_emif_ea,dsp_emif_din, dsp_emif_dout,
         dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
         dsp_eclk,
         lsr1_0, lsr1_1, lsr2_0, lsr2_1, lsr3_0, lsr3_1, lsr4_0, lsr4_1,
         lsr1_sck,lsr1_ss,lsr1_rd,lsr1_mosi,lsr1_disable,
         lsr2_sck,lsr2_ss,lsr2_rd,lsr2_mosi,lsr2_disable,
         lsr3_sck,lsr3_ss,lsr3_rd,lsr3_mosi,lsr3_disable,
         lsr4_sck,lsr4_ss,lsr4_rd,lsr4_mosi,lsr4_disable,
         sw1, sw2, sw3, sw4,
         i2c_rst0, i2c_rst1,
         i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
         rd_adc, rd_adc_clk, rd_adc_oe,
         monitor,
         dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7,
         usb_connected, cyp_reset):

    NSTAGES = 28
    counter = Signal(intbv(0)[NSTAGES:])

    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser1_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser2_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser3_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laser4_pwm  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdmemory    = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_kernel      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_inject      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_twGen       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdsim       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdman       = Signal(intbv(0)[EMIF_DATA_WIDTH:])

    dsp_wr, ce2 = [Signal(LOW) for i in range(2)]
    laser1_pwm_out, laser1_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser2_pwm_out, laser2_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser3_pwm_out, laser3_pwm_inv_out = [Signal(LOW) for i in range(2)]
    laser4_pwm_out, laser4_pwm_inv_out = [Signal(LOW) for i in range(2)]

    data_we,adc_clk = [Signal(LOW) for i in range(2)]

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
    clk_5M, clk_2M5, pulse_1M, pulse_100k = [Signal(LOW) for i in range(4)]

    gpreg_1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuner_value = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuner_slope = Signal(LOW)
    tuner_in_window = Signal(LOW)

    laser_fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser_shutdown_in = Signal(LOW)
    soa_shutdown_in = Signal(LOW)

    rdsim_value = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rd_trig = Signal(LOW)

    meta0 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta3 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta4 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta5 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta6 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta7 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    laser_freq_ok = Signal(LOW)
    acc_en = Signal(LOW)
    rd_irq = Signal(LOW)
    acq_done_irq = Signal(LOW)
    metadata_strobe = Signal(LOW)
    laser_locked = Signal(LOW)

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

    rdmemory = Rdmemory(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdmemory,
                dsp_wr=dsp_wr, bank=bank, data_addr=data_addr,
                data=data, wr_data=wr_data, data_we=data_we,
                meta_addr=meta_addr, meta=meta, wr_meta=wr_meta,
                meta_we=meta_we, param_addr=param_addr,
                param=param, wr_param=wr_param, param_we=param_we)

    kernel = Kernel(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out,
                  dsp_data_in=dsp_data_in_kernel,
                  dsp_wr=dsp_wr,
                  usb_connected=usb_connected,
                  cyp_reset=cyp_reset,
                  gpreg_1_out=gpreg_1,
                  map_base=FPGA_KERNEL)

    clkgen = ClkGen(clk=clk0, reset=reset, clk_5M=clk_5M,
                    clk_2M5=clk_2M5, pulse_1M=pulse_1M, pulse_100k=pulse_100k)

    twGen = TWGen(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_twGen,
                  dsp_wr=dsp_wr, synth_step_in=pulse_100k,
                  value_out=tuner_value, slope_out=tuner_slope,
                  in_window_out=tuner_in_window,map_base=FPGA_TWGEN)

    inject = Inject(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                    dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_inject,
                    dsp_wr=dsp_wr, laser_dac_clk_in=clk_5M,
                    strobe_in=pulse_100k,
                    laser_fine_current_in=laser_fine_current_in,
                    laser_shutdown_in=laser_shutdown_in,
                    soa_shutdown_in=soa_shutdown_in,
                    laser1_dac_sync_out=lsr1_ss,
                    laser2_dac_sync_out=lsr2_ss,
                    laser3_dac_sync_out=lsr3_ss,
                    laser4_dac_sync_out=lsr4_ss,
                    laser1_dac_din_out=lsr1_mosi,
                    laser2_dac_din_out=lsr2_mosi,
                    laser3_dac_din_out=lsr3_mosi,
                    laser4_dac_din_out=lsr4_mosi,
                    laser1_disable_out=lsr1_disable,
                    laser2_disable_out=lsr2_disable,
                    laser3_disable_out=lsr3_disable,
                    laser4_disable_out=lsr4_disable,
                    laser1_shutdown_out=lsr1_rd,
                    laser2_shutdown_out=lsr2_rd,
                    laser3_shutdown_out=lsr3_rd,
                    laser4_shutdown_out=lsr4_rd,
                    soa_shutdown_out=sw3,
                    map_base=FPGA_INJECT)

    rdsim = RdSim( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdsim,
                   dsp_wr=dsp_wr, rd_trig_in=rd_trig,
                   tuner_value_in=tuner_value,
                   rd_adc_clk_in=adc_clk,
                   rdsim_value_out=rdsim_value, map_base=FPGA_RDSIM )

    rdman = RdMan( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdman,
                   dsp_wr=dsp_wr, pulse_100k_in=pulse_100k,
                   pulse_1M_in=pulse_1M,
                   tuner_value_in=tuner_value, meta0_in=meta0,
                   meta1_in=meta1, meta2_in=meta2,
                   meta3_in=meta3, meta4_in=meta4,
                   meta5_in=meta5, meta6_in=meta6,
                   meta7_in=meta7, rd_data_in=rdsim_value,
                   tuner_slope_in=tuner_slope,
                   tuner_window_in=tuner_in_window,
                   laser_freq_ok_in=laser_freq_ok,
                   metadata_strobe_in=metadata_strobe,
                   rd_trig_out=rd_trig, acc_en_out=acc_en,
                   rd_irq_out=rd_irq,
                   acq_done_irq_out=acq_done_irq,
                   rd_adc_clk_out=adc_clk, bank_out=bank,
                   laser_locked_out=laser_locked,
                   data_addr_out=data_addr, wr_data_out=wr_data,
                   data_we_out=data_we, meta_addr_out=meta_addr,
                   wr_meta_out=wr_meta, meta_we_out=meta_we,
                   param_addr_out=param_addr,
                   wr_param_out=wr_param, param_we_out=param_we,
                   map_base=FPGA_RDMAN )

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
                           dsp_data_in_rdman      | \
                           dsp_data_in_rdmemory   | \
                           dsp_data_in_kernel     | \
                           dsp_data_in_inject     | \
                           dsp_data_in_twGen      | \
                           dsp_data_in_rdsim

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
        intronix.next[24] = adc_clk
        intronix.next[25] = acc_en
        intronix.next[26] = laser_locked
        intronix.next[27] = bank
        intronix.next[32] = rd_trig
        monitor.next = rd_trig

        rd_adc_clk.next = adc_clk
        rd_adc_oe.next = 1
        fpga_led.next = counter[NSTAGES:NSTAGES-4]
        i2c_rst0.next = reset
        i2c_rst1.next = reset
        intronix.next[28] = i2c_scl0
        intronix.next[29] = i2c_sda0
        intronix.next[30] = i2c_scl1
        intronix.next[31] = i2c_sda1

        # Use gpreg_1 to control the Intronix display
        if gpreg_1[5:] == 0:
            intronix.next[33] = clk0
        elif gpreg_1[5:] <= NSTAGES:
            intronix.next[33] = counter[int(gpreg_1[5:]-1)]
        else:
            intronix.next[33] = 0

        if gpreg_1[6]:
            intronix.next[8:] = tuner_value[16:8]
        else:
            intronix.next[8:] = rd_adc[14:6]

        intronix.next[16:8] = rdsim_value[14:6]

        dsp_ext_int4.next = counter[NSTAGES-4]
        dsp_ext_int5.next = 0
        dsp_ext_int6.next = 0
        dsp_ext_int7.next = 0

        lsr1_sck.next = clk_5M
        lsr2_sck.next = clk_5M
        lsr3_sck.next = clk_5M
        lsr4_sck.next = clk_5M

        sw1.next = 0
        sw2.next = 0
        sw4.next = 0
        laser_freq_ok.next = HIGH
        metadata_strobe.next = pulse_100k

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
lsr1_sck,lsr1_ss,lsr1_rd,lsr1_mosi,lsr1_disable = [Signal(LOW) for i in range(5)]
lsr2_sck,lsr2_ss,lsr2_rd,lsr2_mosi,lsr2_disable = [Signal(LOW) for i in range(5)]
lsr3_sck,lsr3_ss,lsr3_rd,lsr3_mosi,lsr3_disable = [Signal(LOW) for i in range(5)]
lsr4_sck,lsr4_ss,lsr4_rd,lsr4_mosi,lsr4_disable = [Signal(LOW) for i in range(5)]
sw1, sw2, sw3, sw4 = [Signal(LOW) for i in range(4)]
dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7 = [Signal(LOW) for i in range(4)]
usb_connected, cyp_reset = [Signal(LOW) for i in range(2)]

def makeVHDL():
    toVHDL(main,clk0,clk180,clk3f,clk3f180,clk_locked,reset,
                intronix,fpga_led,dsp_emif_we,dsp_emif_re,
                dsp_emif_oe,dsp_emif_ardy,dsp_emif_ea,dsp_emif_din,
                dsp_emif_dout,dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
                dsp_eclk,
                lsr1_0, lsr1_1, lsr2_0, lsr2_1, lsr3_0, lsr3_1, lsr4_0, lsr4_1,
                lsr1_sck,lsr1_ss,lsr1_rd,lsr1_mosi,lsr1_disable,
                lsr2_sck,lsr2_ss,lsr2_rd,lsr2_mosi,lsr2_disable,
                lsr3_sck,lsr3_ss,lsr3_rd,lsr3_mosi,lsr3_disable,
                lsr4_sck,lsr4_ss,lsr4_rd,lsr4_mosi,lsr4_disable,
                sw1, sw2, sw3, sw4,
                i2c_rst0, i2c_rst1,
                i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
                rd_adc, rd_adc_clk, rd_adc_oe,
                monitor,
                dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7,
                usb_connected, cyp_reset)

if __name__ == "__main__":
    makeVHDL()
