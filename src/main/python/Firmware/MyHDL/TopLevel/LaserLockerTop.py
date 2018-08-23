#!/usr/bin/python
#
# FILE:
#   LaserLockerTop.py
#
# DESCRIPTION:
#   Top level file for synthesizing FPGA with wavelength monitor simulator
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
from MyHDL.Common.DynamicPwm import DynamicPwm
from MyHDL.Common.Inject import Inject
from MyHDL.Common.Kernel import Kernel
from MyHDL.Common.LaserCurrentGenerator import LaserCurrentGenerator
from MyHDL.Common.LaserLocker import LaserLocker
from MyHDL.Common.Ltc2604DacD import Ltc2604DacD
from MyHDL.Common.Pwm1 import Pwm
from MyHDL.Common.RdMan import RdMan
from MyHDL.Common.Rdmemory import Rdmemory
from MyHDL.Common.RdSim import RdSim
from MyHDL.Common.TWGen import TWGen
from MyHDL.Common.WlmAdcReader import WlmAdcReader
from MyHDL.Common.WlmMux import WlmMux
from MyHDL.Common.WlmSim import WlmSim
from MyHDL.Common.Scaler import Scaler

LOW, HIGH = bool(0), bool(1)

def main(clk0,clk180,clk3f,clk3f180,clk_locked,
         reset,intronix,fpga_led,
         dsp_emif_we,dsp_emif_re,dsp_emif_oe,dsp_emif_ardy,
         dsp_emif_ea,dsp_emif_din, dsp_emif_dout,
         dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
         dsp_eclk,
         lsr1_0, lsr1_1, lsr2_0, lsr2_1, lsr3_0, lsr3_1, lsr4_0, lsr4_1,
         lc1, lc2, lc3, lc4,
         lsr1_sck,lsr1_ss,lsr1_rd,lsr1_mosi,lsr1_disable,
         lsr2_sck,lsr2_ss,lsr2_rd,lsr2_mosi,lsr2_disable,
         lsr3_sck,lsr3_ss,lsr3_rd,lsr3_mosi,lsr3_disable,
         lsr4_sck,lsr4_ss,lsr4_rd,lsr4_mosi,lsr4_disable,
         sw1, sw2, sw3, sw4,
         i2c_rst0, i2c_rst1,
         i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
         fp_lcd, fp_led, fp_rs_n,
         rd_adc, rd_adc_clk, rd_adc_oe,
         monitor,
         dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7,
         usb_internal_connected, usb_rear_connected, fpga_program_enable, cyp_reset,
         pzt_valve_dac_ld, pzt_valve_dac_sck, pzt_valve_dac_sdi,
         inlet_valve_pwm, outlet_valve_pwm,
         inlet_valve_comparator, outlet_valve_comparator,
         heater_pwm, hot_box_pwm, hot_box_tec_overload,
         warm_box_pwm, warm_box_tec_overload,
         wmm_refl1, wmm_refl2, wmm_tran1, wmm_tran2,
         wmm_busy1, wmm_busy2,
         wmm_rd, wmm_convst, wmm_clk,
         dout_man, dout, din,
         aux_din, aux_dout):

    NSTAGES = 28
    counter = Signal(intbv(0)[NSTAGES:])

    aux_pzt_dac_sck, aux_pzt_dac_sdi, aux_pzt_dac_ld = [Signal(LOW) for i in range(3)]

    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])

    dsp_data_in_dynamicpwm_inlet  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_dynamicpwm_outlet = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_inject      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_kernel      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_lasercurrentgenerator = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laserlocker = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_heater  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_hotbox  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_engine1 = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_engine2 = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser1  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser2  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser3  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser4  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdman       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdmemory    = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdsim       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_twGen       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_warmbox = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_wlmsim      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_scaler      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_filter_heater = Signal(intbv(0)[EMIF_DATA_WIDTH:])

    dsp_wr, ce2 = [Signal(LOW) for i in range(2)]
    pwm_laser1_out, pwm_laser1_inv_out = [Signal(LOW) for i in range(2)]
    pwm_laser2_out, pwm_laser2_inv_out = [Signal(LOW) for i in range(2)]
    pwm_laser3_out, pwm_laser3_inv_out = [Signal(LOW) for i in range(2)]
    pwm_laser4_out, pwm_laser4_inv_out = [Signal(LOW) for i in range(2)]

    filter_heater_pwm_out = Signal(LOW)
    filter_heater_pwm_inv_out = Signal(LOW)

    status_led = Signal(intbv(0)[2:])
    fan = Signal(intbv(0)[2:])

    heater_pwm_out = Signal(LOW)
    hot_box_pwm_out = Signal(LOW)
    warm_box_pwm_out = Signal(LOW)
    engine1_pwm_out = Signal(LOW)
    engine2_pwm_out = Signal(LOW)

    heater_pwm_inv = Signal(LOW)
    hot_box_pwm_inv = Signal(LOW)
    warm_box_pwm_inv = Signal(LOW)
    engine1_pwm_inv = Signal(LOW)
    engine2_pwm_inv = Signal(LOW)

    wmm_rd_out = Signal(LOW)

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
    clk_10M, clk_5M, clk_2M5, pulse_1M, pulse_100k = [Signal(LOW) for i in range(5)]

    diag_1 = Signal(intbv(0)[8:])
    config = Signal(intbv(0)[16:])
    intronix_clksel = Signal(intbv(0)[5:])
    intronix_1 = Signal(intbv(0)[8:])
    intronix_2 = Signal(intbv(0)[8:])
    intronix_3 = Signal(intbv(0)[8:])
    channel_1 = Signal(intbv(0)[8:])
    channel_2 = Signal(intbv(0)[8:])
    channel_3 = Signal(intbv(0)[8:])
    channel_4 = Signal(intbv(0)[9:])

    tuner_slope = Signal(LOW)
    tuner_in_window = Signal(LOW)

    ratio1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ratio2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    tuner_value = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser_tuning_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser_locking_pid = Signal(intbv(0)[FPGA_REG_WIDTH:])
    lock_error = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pzt = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pzt_scaled = Signal(intbv(0)[FPGA_REG_WIDTH:])

    sel_laser = Signal(intbv(0)[2:])
    sel_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sel_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])

    meta0 = ratio1
    meta1 = ratio2
    meta2 = pzt
    meta3 = laser_tuning_offset
    meta4 = sel_fine_current
    meta5 = lock_error
    meta6 = laser_locking_pid
    meta7 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    rdsim_value = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rd_trig = Signal(LOW)

    wlm_sim_actual = Signal(LOW)

    data_available_actual = Signal(LOW)
    eta1_actual = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_actual = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_actual = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_actual = Signal(intbv(0)[FPGA_REG_WIDTH:])

    data_available_sim = Signal(LOW)
    eta1_sim = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_sim = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_sim = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_sim = Signal(intbv(0)[FPGA_REG_WIDTH:])

    wlm_data_available = Signal(LOW)
    eta1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    z0_in = Signal(intbv(0)[FPGA_REG_WIDTH:])

    sim_loss = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sim_pzt = Signal(intbv(0)[FPGA_REG_WIDTH:])

    laser_freq_ok = Signal(LOW)
    acc_en = Signal(LOW)
    rd_irq = Signal(LOW)
    acq_done_irq = Signal(LOW)
    metadata_strobe = Signal(LOW)
    laser_locked = Signal(LOW)
    i2c_reset = Signal(LOW)

    inlet_valve_dac = Signal(intbv(0)[FPGA_REG_WIDTH:])
    outlet_valve_dac = Signal(intbv(0)[FPGA_REG_WIDTH:])
    chanC_data_in = Signal(intbv(0)[FPGA_REG_WIDTH:])

    overload_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    overload_out = Signal(LOW)

    lsr1_ss_temp = Signal(LOW)
    lsr2_ss_temp = Signal(LOW)
    lsr3_ss_temp = Signal(LOW)
    lsr4_ss_temp = Signal(LOW)
    lsr1_mosi_temp = Signal(LOW)
    lsr2_mosi_temp = Signal(LOW)
    lsr3_mosi_temp = Signal(LOW)
    lsr4_mosi_temp = Signal(LOW)

    laser_extra = Signal(LOW)

    extended_current_mode = Signal(LOW)
    laser1_fine_ext = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser2_fine_ext = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser3_fine_ext = Signal(intbv(0)[FPGA_REG_WIDTH:])
    laser4_fine_ext = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ext_laser_current_in_window = Signal(LOW)
    ext_laser_level_counter = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ext_laser_sequence_id = Signal(intbv(0)[FPGA_REG_WIDTH:])

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

    clkgen = ClkGen(clk=clk0, reset=reset, clk_10M=clk_10M, clk_5M=clk_5M,
                    clk_2M5=clk_2M5, pulse_1M=pulse_1M, pulse_100k=pulse_100k)

    inject = Inject(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                    dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_inject,
                    dsp_wr=dsp_wr, laser_dac_clk_in=clk_5M,
                    strobe_in=metadata_strobe,
                    laser_fine_current_in=laser_fine_current,
                    laser_shutdown_in=rd_trig,
                    soa_shutdown_in=rd_trig,
                    fiber_amp_pwm_in=pwm_laser4_out,
                    laser_extra_in=laser_extra,
                    laser1_fine_ext_in=laser1_fine_ext,
                    laser2_fine_ext_in=laser2_fine_ext,
                    laser3_fine_ext_in=laser3_fine_ext,
                    laser4_fine_ext_in=laser4_fine_ext,
                    laser1_dac_sync_out=lsr1_ss_temp,
                    laser2_dac_sync_out=lsr2_ss_temp,
                    laser3_dac_sync_out=lsr3_ss_temp,
                    laser4_dac_sync_out=lsr4_ss_temp,
                    laser1_dac_din_out=lsr1_mosi_temp,
                    laser2_dac_din_out=lsr2_mosi_temp,
                    laser3_dac_din_out=lsr3_mosi_temp,
                    laser4_dac_din_out=lsr4_mosi_temp,
                    laser1_disable_out=lsr1_disable,
                    laser2_disable_out=lsr2_disable,
                    laser3_disable_out=lsr3_disable,
                    laser4_disable_out=lsr4_disable,
                    laser1_shutdown_out=lsr1_rd,
                    laser2_shutdown_out=lsr2_rd,
                    laser3_shutdown_out=lsr3_rd,
                    laser4_shutdown_out=lsr4_rd,
                    soa_shutdown_out=sw3,
                    sel_laser_out=sel_laser,
                    sel_coarse_current_out=sel_coarse_current,
                    sel_fine_current_out=sel_fine_current,
                    optical_switch1_out=sw1,
                    optical_switch2_out=sw2,
                    optical_switch4_out=sw4,
                    ext_mode_out=extended_current_mode,
                    map_base=FPGA_INJECT)

    kernel = Kernel( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_kernel,
                     dsp_wr=dsp_wr, usb_connected=usb_rear_connected,
                     cyp_reset=cyp_reset, diag_1_out=diag_1,
                     config_out=config,
                     intronix_clksel_out=intronix_clksel,
                     intronix_1_out=intronix_1,
                     intronix_2_out=intronix_2,
                     intronix_3_out=intronix_3,
                     overload_in=overload_in,
                     overload_out=overload_out,
                     i2c_reset_out=i2c_reset,
                     status_led_out=status_led, 
                     fan_out=fan, 
                     dout_man_out=dout_man,
                     dout_out=dout,
                     din_in=din,
                     map_base=FPGA_KERNEL )

    laserCurrentGenerator = LaserCurrentGenerator(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                                                  dsp_data_out=dsp_data_out,
                                                  dsp_data_in=dsp_data_in_lasercurrentgenerator,
                                                  dsp_wr=dsp_wr,
                                                  strobe_in=pulse_100k,
                                                  sel_laser_in=sel_laser,
                                                  laser1_fine_current_out=laser1_fine_ext,
                                                  laser2_fine_current_out=laser2_fine_ext,
                                                  laser3_fine_current_out=laser3_fine_ext,
                                                  laser4_fine_current_out=laser4_fine_ext,
                                                  laser_current_in_window_out=ext_laser_current_in_window,
                                                  level_counter_out=ext_laser_level_counter,
                                                  sequence_id_out=ext_laser_sequence_id,
                                                  map_base=FPGA_LASERCURRENTGENERATOR)

    laserlocker = LaserLocker(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                              dsp_data_out=dsp_data_out,
                              dsp_data_in=dsp_data_in_laserlocker, dsp_wr=dsp_wr,
                              eta1_in=eta1, ref1_in=ref1,
                              eta2_in=eta2, ref2_in=ref2,
                              tuning_offset_in=tuner_value,
                              acc_en_in=acc_en,
                              adc_strobe_in=wlm_data_available,
                              ratio1_out=ratio1,
                              ratio2_out=ratio2,
                              lock_error_out=lock_error,
                              fine_current_out=laser_fine_current,
                              tuning_offset_out=laser_tuning_offset,
                              pid_out=laser_locking_pid,
                              laser_freq_ok_out=laser_freq_ok,
                              current_ok_out=metadata_strobe,
                              sim_actual_out=wlm_sim_actual,
                              map_base=FPGA_LASERLOCKER )

    pwm_laser1 = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_laser1,
              dsp_wr=dsp_wr,
              pwm_out=pwm_laser1_out,
              pwm_inv_out=pwm_laser1_inv_out,
              map_base=FPGA_PWM_LASER1)

    pwm_laser2 = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_laser2,
              dsp_wr=dsp_wr,
              pwm_out=pwm_laser2_out,
              pwm_inv_out=pwm_laser2_inv_out,
              map_base=FPGA_PWM_LASER2)

    pwm_laser3 = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_laser3,
              dsp_wr=dsp_wr,
              pwm_out=pwm_laser3_out,
              pwm_inv_out=pwm_laser3_inv_out,
              map_base=FPGA_PWM_LASER3)

    pwm_laser4 = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
              dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_laser4,
              dsp_wr=dsp_wr,
              pwm_out=pwm_laser4_out,
              pwm_inv_out=pwm_laser4_inv_out,
              map_base=FPGA_PWM_LASER4)

    pwm_warmbox = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                      dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_warmbox,
                      dsp_wr=dsp_wr,
                      pwm_out=warm_box_pwm_out,
                      pwm_inv_out=warm_box_pwm_inv,
                      map_base=FPGA_PWM_WARMBOX)

    pwm_hotbox = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_hotbox,
                     dsp_wr=dsp_wr,
                     pwm_out=hot_box_pwm_out,
                     pwm_inv_out=hot_box_pwm_inv,
                     map_base=FPGA_PWM_HOTBOX)

    pwm_engine1 = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_engine1,
                     dsp_wr=dsp_wr,
                     pwm_out=engine1_pwm_out,
                     pwm_inv_out=engine1_pwm_inv,
                     map_base=FPGA_PWM_ENGINE1)

    pwm_engine2 = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_engine2,
                     dsp_wr=dsp_wr,
                     pwm_out=engine2_pwm_out,
                     pwm_inv_out=engine2_pwm_inv,
                     map_base=FPGA_PWM_ENGINE2)

    pwm_heater = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_heater,
                     dsp_wr=dsp_wr,
                     pwm_out=heater_pwm_out,
                     pwm_inv_out=heater_pwm_inv,
                     map_base=FPGA_PWM_HEATER)

    pwm_filter_heater = Pwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_pwm_filter_heater,
                     dsp_wr=dsp_wr,
                     pwm_out=filter_heater_pwm_out,
                     pwm_inv_out=filter_heater_pwm_inv_out,
                     map_base=FPGA_PWM_FILTER_HEATER)

    rdman = RdMan( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdman,
                   dsp_wr=dsp_wr, pulse_100k_in=pulse_100k,
                   pulse_1M_in=pulse_1M,
                   tuner_value_in=tuner_value, meta0_in=meta0,
                   meta1_in=meta1, meta2_in=meta2,
                   meta3_in=meta3, meta4_in=meta4,
                   meta5_in=meta5, meta6_in=meta6,
                   meta7_in=meta7, rd_sim_in=rdsim_value, rd_data_in=rd_adc,
                   tuner_slope_in=tuner_slope,
                   tuner_window_in=tuner_in_window,
                   laser_freq_ok_in=laser_freq_ok,
                   metadata_strobe_in=metadata_strobe,
                   ext_mode_in=extended_current_mode,
                   sel_fine_current_in=sel_fine_current,
                   ext_laser_current_in_window_in=ext_laser_current_in_window,
                   ext_laser_level_counter_in=ext_laser_level_counter,
                   ext_laser_sequence_id_in=ext_laser_sequence_id,
                   rd_trig_out=rd_trig,
                   laser_extra_out=laser_extra,
                   acc_en_out=acc_en,
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

    rdmemory = Rdmemory(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdmemory,
                dsp_wr=dsp_wr, bank=bank, data_addr=data_addr,
                data=data, wr_data=wr_data, data_we=data_we,
                meta_addr=meta_addr, meta=meta, wr_meta=wr_meta,
                meta_we=meta_we, param_addr=param_addr,
                param=param, wr_param=wr_param, param_we=param_we)

    rdsim = RdSim( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_rdsim,
                   dsp_wr=dsp_wr, rd_trig_in=rd_trig,
                   pzt_value_in=pzt,
                   rd_adc_clk_in=adc_clk,
                   pzt_center_in=sim_pzt, decay_in=sim_loss,
                   rdsim_value_out=rdsim_value, map_base=FPGA_RDSIM )

    twGen = TWGen(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_twGen,
                  dsp_wr=dsp_wr, synth_step_in=pulse_100k,
                  value_out=tuner_value, pzt_out=pzt, slope_out=tuner_slope,
                  in_window_out=tuner_in_window,map_base=FPGA_TWGEN)

    wlmadcreader = WlmAdcReader(clk=clk0, reset=reset, adc_clock_in=clk_2M5,
                                strobe_in=pulse_100k, eta1_in=wmm_refl1,
                                ref1_in=wmm_tran1, eta2_in=wmm_refl2,
                                ref2_in=wmm_tran2, adc_rd_out=wmm_rd_out,
                                adc_convst_out=wmm_convst, data_available_out=data_available_actual,
                                eta1_out=eta1_actual, ref1_out=ref1_actual,
                                eta2_out=eta2_actual, ref2_out=ref2_actual)

    wlmsim = WlmSim( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_wlmsim,
                     dsp_wr=dsp_wr, start_in=pulse_100k,
                     coarse_current_in=sel_coarse_current,
                     fine_current_in=sel_fine_current,
                     eta1_out=eta1_sim, ref1_out=ref1_sim,
                     eta2_out=eta2_sim, ref2_out=ref2_sim,
                     loss_out=sim_loss, pzt_cen_out=sim_pzt,
                     done_out=data_available_sim, map_base=FPGA_WLMSIM )

    wlmmux = WlmMux(sim_actual_in=wlm_sim_actual, eta1_sim_in=eta1_sim,
                    ref1_sim_in=ref1_sim, eta2_sim_in=eta2_sim,
                    ref2_sim_in=ref2_sim, data_available_sim_in=data_available_sim,
                    eta1_actual_in=eta1_actual, ref1_actual_in=ref1_actual,
                    eta2_actual_in=eta2_actual, ref2_actual_in=ref2_actual,
                    data_available_actual_in=data_available_actual,
                    eta1_out=eta1, ref1_out=ref1, eta2_out=eta2, ref2_out=ref2,
                    data_available_out=wlm_data_available)

    #pztValveDac = Ltc2604Dac(clk=clk0, reset=reset, dac_clock_in=clk_10M,
    #                         chanA_data_in=inlet_valve_dac,
    #                         chanB_data_in=outlet_valve_dac,
    #                         chanC_data_in=chanC_data_in,
    #                         chanD_data_in=pzt, strobe_in=pulse_100k,
    #                         dac_sck_out=pzt_valve_dac_sck,
    #                         dac_sdi_out=pzt_valve_dac_sdi, dac_ld_out=pzt_valve_dac_ld)

    pztValveDac = Ltc2604DacD(clk=clk0, reset=reset, dac_clock_in=clk_2M5,
                              chanD_data_in=pzt_scaled, strobe_in=pulse_100k,
                              dac_sck_out=pzt_valve_dac_sck,
                              dac_sdi_out=pzt_valve_dac_sdi, dac_ld_out=pzt_valve_dac_ld)

    auxPztDac = Ltc2604DacD(clk=clk0, reset=reset, dac_clock_in=clk_2M5,
                              chanD_data_in=laser_fine_current, strobe_in=pulse_100k,
                              dac_sck_out=aux_pzt_dac_sck,
                              dac_sdi_out=aux_pzt_dac_sdi, dac_ld_out=aux_pzt_dac_ld)

    dynamicPwmInlet = DynamicPwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                                 dsp_data_out=dsp_data_out,
                                 dsp_data_in=dsp_data_in_dynamicpwm_inlet, dsp_wr=dsp_wr,
                                 comparator_in=inlet_valve_comparator,
                                 update_in=pulse_100k, pwm_out=inlet_valve_pwm,
                                 value_out=inlet_valve_dac, map_base=FPGA_DYNAMICPWM_INLET, MIN_WIDTH=1000,MAX_WIDTH=64535)

    dynamicPwmOutlet = DynamicPwm(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                                  dsp_data_out=dsp_data_out,
                                  dsp_data_in=dsp_data_in_dynamicpwm_outlet, dsp_wr=dsp_wr,
                                  comparator_in=outlet_valve_comparator,
                                  update_in=pulse_100k, pwm_out=outlet_valve_pwm,
                                  value_out=outlet_valve_dac, map_base=FPGA_DYNAMICPWM_OUTLET, MIN_WIDTH=1000,MAX_WIDTH=64535)

    scaler = Scaler(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                    dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_scaler,
                    dsp_wr=dsp_wr, x1_in=pzt, y1_out=pzt_scaled,
                    map_base=FPGA_SCALER)

    @instance
    def  logic():
        while True:
            yield clk0.posedge, reset.posedge
            if reset:
                counter.next = 0
                channel_1.next = 0
                channel_2.next = 0
                channel_3.next = 0
            else:
                counter.next = counter + 1
                tuner_low = tuner_value[8:]
                tuner_high = tuner_value[16:8]
                rd_adc_low = concat(rd_adc[6:0],LOW,LOW)
                rd_adc_high = rd_adc[14:6]
                rd_sim_low = concat(rdsim_value[6:0],LOW,LOW)
                rd_sim_high = rdsim_value[14:6]
                sel_fine_current_low = sel_fine_current[8:]
                sel_fine_current_high = sel_fine_current[16:8]
                lock_error_low = lock_error[8:]
                lock_error_high = lock_error[16:8]
                ratio1_low = ratio1[8:]
                ratio1_high = ratio1[16:8]
                ratio2_low = ratio2[8:]
                ratio2_high = ratio2[16:8]
                pzt_low = pzt[8:]
                pzt_high = pzt[16:8]
                eta1_adc_low = eta1_actual[8:]
                eta1_adc_high = eta1_actual[16:8]
                ref1_adc_low = ref1_actual[8:]
                ref1_adc_high = ref1_actual[16:8]
                eta2_adc_low = eta2_actual[8:]
                eta2_adc_high = eta2_actual[16:8]
                ref2_adc_low = ref2_actual[8:]
                ref2_adc_high = ref2_actual[16:8]
                wlm_adc = concat(wmm_busy2,wmm_busy1,wmm_rd_out,clk_2M5,wmm_tran2,wmm_refl2,wmm_tran1,wmm_refl1)
                system_clocks = concat(data_we,clk_10M,clk_5M,clk_2M5,pulse_1M,pulse_100k,wlm_data_available,metadata_strobe)
                pwm_signals = concat(engine2_pwm_out,engine1_pwm_out,hot_box_pwm_out,warm_box_pwm_out,pwm_laser4_out,pwm_laser3_out,pwm_laser2_out,pwm_laser1_out)
                i2c_signals = concat(heater_pwm_out, LOW, LOW, LOW, i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1)

                # Latch data for the intronix port
                if intronix_1 == 0:
                    channel_1.next = tuner_low
                elif intronix_1 == 1:
                    channel_1.next = tuner_high
                elif intronix_1 == 2:
                    channel_1.next = rd_adc_low
                elif intronix_1 == 3:
                    channel_1.next = rd_adc_high
                elif intronix_1 == 4:
                    channel_1.next = rd_sim_low
                elif intronix_1 == 5:
                    channel_1.next = rd_sim_high
                elif intronix_1 == 6:
                    channel_1.next = sel_fine_current_low
                elif intronix_1 == 7:
                    channel_1.next = sel_fine_current_high
                elif intronix_1 == 8:
                    channel_1.next = lock_error_low
                elif intronix_1 == 9:
                    channel_1.next = lock_error_low
                elif intronix_1 == 10:
                    channel_1.next = ratio1_low
                elif intronix_1 == 11:
                    channel_1.next = ratio1_high
                elif intronix_1 == 12:
                    channel_1.next = ratio2_low
                elif intronix_1 == 13:
                    channel_1.next = ratio2_high
                elif intronix_1 == 14:
                    channel_1.next = pzt_low
                elif intronix_1 == 15:
                    channel_1.next = pzt_high
                elif intronix_1 == 16:
                    channel_1.next = eta1_adc_low
                elif intronix_1 == 17:
                    channel_1.next = eta1_adc_high
                elif intronix_1 == 18:
                    channel_1.next = ref1_adc_low
                elif intronix_1 == 19:
                    channel_1.next = ref1_adc_high
                elif intronix_1 == 20:
                    channel_1.next = eta2_adc_low
                elif intronix_1 == 21:
                    channel_1.next = eta2_adc_high
                elif intronix_1 == 22:
                    channel_1.next = ref2_adc_low
                elif intronix_1 == 23:
                    channel_1.next = ref2_adc_high
                elif intronix_1 == 24:
                    channel_1.next = wlm_adc
                elif intronix_1 == 25:
                    channel_1.next = system_clocks
                elif intronix_1 == 26:
                    channel_1.next = pwm_signals
                else:
                    channel_1.next = i2c_signals

                if intronix_2 == 0:
                    channel_2.next = tuner_low
                elif intronix_2 == 1:
                    channel_2.next = tuner_high
                elif intronix_2 == 2:
                    channel_2.next = rd_adc_low
                elif intronix_2 == 3:
                    channel_2.next = rd_adc_high
                elif intronix_2 == 4:
                    channel_2.next = rd_sim_low
                elif intronix_2 == 5:
                    channel_2.next = rd_sim_high
                elif intronix_2 == 6:
                    channel_2.next = sel_fine_current_low
                elif intronix_2 == 7:
                    channel_2.next = sel_fine_current_high
                elif intronix_2 == 8:
                    channel_2.next = lock_error_low
                elif intronix_2 == 9:
                    channel_2.next = lock_error_low
                elif intronix_2 == 10:
                    channel_2.next = ratio1_low
                elif intronix_2 == 11:
                    channel_2.next = ratio1_high
                elif intronix_2 == 12:
                    channel_2.next = ratio2_low
                elif intronix_2 == 13:
                    channel_2.next = ratio2_high
                elif intronix_2 == 14:
                    channel_2.next = pzt_low
                elif intronix_2 == 15:
                    channel_2.next = pzt_high
                elif intronix_2 == 16:
                    channel_2.next = eta1_adc_low
                elif intronix_2 == 17:
                    channel_2.next = eta1_adc_high
                elif intronix_2 == 18:
                    channel_2.next = ref1_adc_low
                elif intronix_2 == 19:
                    channel_2.next = ref1_adc_high
                elif intronix_2 == 20:
                    channel_2.next = eta2_adc_low
                elif intronix_2 == 21:
                    channel_2.next = eta2_adc_high
                elif intronix_2 == 22:
                    channel_2.next = ref2_adc_low
                elif intronix_2 == 23:
                    channel_2.next = ref2_adc_high
                elif intronix_2 == 24:
                    channel_2.next = wlm_adc
                elif intronix_2 == 25:
                    channel_2.next = system_clocks
                elif intronix_2 == 26:
                    channel_2.next = pwm_signals
                else:
                    channel_2.next = i2c_signals

                if intronix_3 == 0:
                    channel_3.next = tuner_low
                elif intronix_3 == 1:
                    channel_3.next = tuner_high
                elif intronix_3 == 2:
                    channel_3.next = rd_adc_low
                elif intronix_3 == 3:
                    channel_3.next = rd_adc_high
                elif intronix_3 == 4:
                    channel_3.next = rd_sim_low
                elif intronix_3 == 5:
                    channel_3.next = rd_sim_high
                elif intronix_3 == 6:
                    channel_3.next = sel_fine_current_low
                elif intronix_3 == 7:
                    channel_3.next = sel_fine_current_high
                elif intronix_3 == 8:
                    channel_3.next = lock_error_low
                elif intronix_3 == 9:
                    channel_3.next = lock_error_low
                elif intronix_3 == 10:
                    channel_3.next = ratio1_low
                elif intronix_3 == 11:
                    channel_3.next = ratio1_high
                elif intronix_3 == 12:
                    channel_3.next = ratio2_low
                elif intronix_3 == 13:
                    channel_3.next = ratio2_high
                elif intronix_3 == 14:
                    channel_3.next = pzt_low
                elif intronix_3 == 15:
                    channel_3.next = pzt_high
                elif intronix_3 == 16:
                    channel_3.next = eta1_adc_low
                elif intronix_3 == 17:
                    channel_3.next = eta1_adc_high
                elif intronix_3 == 18:
                    channel_3.next = ref1_adc_low
                elif intronix_3 == 19:
                    channel_3.next = ref1_adc_high
                elif intronix_3 == 20:
                    channel_3.next = eta2_adc_low
                elif intronix_3 == 21:
                    channel_3.next = eta2_adc_high
                elif intronix_3 == 22:
                    channel_3.next = ref2_adc_low
                elif intronix_3 == 23:
                    channel_3.next = ref2_adc_high
                elif intronix_3 == 24:
                    channel_3.next = wlm_adc
                elif intronix_3 == 25:
                    channel_3.next = system_clocks
                elif intronix_3 == 26:
                    channel_3.next = pwm_signals
                else:
                    channel_3.next = i2c_signals

                channel_4.next = concat(rd_trig,diag_1[4:],bank,laser_locked,acc_en,tuner_in_window)


    @always_comb
    def  comb():
        dsp_data_in.next = (
                   dsp_data_in_dynamicpwm_inlet |
                   dsp_data_in_dynamicpwm_outlet |
                   dsp_data_in_inject |
                   dsp_data_in_kernel |
                   dsp_data_in_lasercurrentgenerator |
                   dsp_data_in_laserlocker |
                   dsp_data_in_pwm_heater |
                   dsp_data_in_pwm_hotbox |
                   dsp_data_in_pwm_engine1 |
                   dsp_data_in_pwm_engine2 |
                   dsp_data_in_pwm_laser1 |
                   dsp_data_in_pwm_laser2 |
                   dsp_data_in_pwm_laser3 |
                   dsp_data_in_pwm_laser4 |
                   dsp_data_in_rdman |
                   dsp_data_in_rdmemory |
                   dsp_data_in_rdsim |
                   dsp_data_in_twGen |
                   dsp_data_in_pwm_warmbox |
                   dsp_data_in_wlmsim |
                   dsp_data_in_scaler |
                   dsp_data_in_pwm_filter_heater)

        overload_in.next[OVERLOAD_WarmBoxTecBit] = warm_box_tec_overload
        overload_in.next[OVERLOAD_HotBoxTecBit]  = hot_box_tec_overload

        intronix.next[8:] = channel_1
        intronix.next[16:8] = channel_2
        intronix.next[24:16] = channel_3
        intronix.next[33:24] = channel_4

        # Use intronix_clksel to control clocking of Intronix display
        if intronix_clksel == 0:
            intronix.next[33] = clk0
        elif intronix_clksel <= NSTAGES:
            intronix.next[33] = counter[int(intronix_clksel-1)]
        else:
            intronix.next[33] = 0

        monitor.next = rd_trig
        aux_din[3].next = rd_trig

        ce2.next = dsp_emif_ce[2]
        lsr1_0.next = pwm_laser1_out
        lsr1_1.next = pwm_laser1_inv_out
        lsr2_0.next = pwm_laser2_out
        lsr2_1.next = pwm_laser2_inv_out
        lsr3_0.next = pwm_laser3_out
        lsr3_1.next = pwm_laser3_inv_out
        lsr4_0.next = pwm_laser4_out
        lsr4_1.next = pwm_laser4_inv_out

        warm_box_pwm.next = warm_box_pwm_out
        hot_box_pwm.next = hot_box_pwm_out
        heater_pwm.next = heater_pwm_out

        wmm_rd.next = wmm_rd_out

        rd_adc_clk.next = adc_clk
        rd_adc_oe.next = 1
        fpga_led.next = counter[NSTAGES:NSTAGES-4]
        i2c_rst0.next = i2c_reset
        i2c_rst1.next = i2c_reset

        dsp_ext_int4.next = rd_irq
        dsp_ext_int5.next = acq_done_irq
        dsp_ext_int6.next = 0
        dsp_ext_int7.next = 0

        lsr1_sck.next = clk_5M and not diag_1[4]
        lsr2_sck.next = clk_5M and not diag_1[5]
        lsr3_sck.next = clk_5M and not diag_1[6]
        lsr4_sck.next = clk_5M and not diag_1[7]

        lsr1_ss.next = lsr1_ss_temp and not diag_1[4]
        lsr2_ss.next = lsr2_ss_temp and not diag_1[5]
        lsr3_ss.next = lsr3_ss_temp and not diag_1[6]
        lsr4_ss.next = lsr4_ss_temp and not diag_1[7]

        lsr1_mosi.next = lsr1_mosi_temp and not diag_1[4]
        lsr2_mosi.next = lsr2_mosi_temp and not diag_1[5]
        lsr3_mosi.next = lsr3_mosi_temp and not diag_1[6]
        lsr4_mosi.next = lsr4_mosi_temp and not diag_1[7]

        wmm_clk.next = clk_2M5
        chanC_data_in.next  = 0

        if config[KERNEL_CONFIG_AUX_PZT_B]:
            aux_din[0].next = aux_pzt_dac_sdi
            aux_din[1].next = aux_pzt_dac_sck
            aux_din[2].next = aux_pzt_dac_ld

        if config[KERNEL_CONFIG_ENGINE1_TEC_B]:
            aux_din[2].next = engine1_pwm_out

        if config[KERNEL_CONFIG_ENGINE2_TEC_B]:
            aux_din[3].next = engine2_pwm_out

        fp_led.next = 0
        fp_led[0].next = status_led[0]
        fp_led[1].next = status_led[1]
        fp_led[2].next = fan[1]

        fp_lcd.next = 0
        fp_lcd[1].next = filter_heater_pwm_out
        fp_lcd[2].next = fan[0]

        fpga_program_enable.next = 1
        ## Do not reset Cypress
        cyp_reset.next = 0

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
fp_lcd = Signal(intbv(0)[8:])
fp_led = Signal(intbv(0)[4:])
fp_rs_n = Signal(LOW)
rd_adc = Signal(intbv(0)[16:])
rd_adc_clk, rd_adc_oe = [Signal(LOW) for i in range(2)]
dsp_eclk, monitor = [Signal(LOW) for i in range(2)]
lsr1_0, lsr1_1, lsr2_0, lsr2_1 = [Signal(LOW) for i in range(4)]
lsr3_0, lsr3_1, lsr4_0, lsr4_1 = [Signal(LOW) for i in range(4)]
lc1, lc2, lc3, lc4 = [Signal(LOW) for i in range(4)]
lsr1_sck,lsr1_ss,lsr1_rd,lsr1_mosi,lsr1_disable = [Signal(LOW) for i in range(5)]
lsr2_sck,lsr2_ss,lsr2_rd,lsr2_mosi,lsr2_disable = [Signal(LOW) for i in range(5)]
lsr3_sck,lsr3_ss,lsr3_rd,lsr3_mosi,lsr3_disable = [Signal(LOW) for i in range(5)]
lsr4_sck,lsr4_ss,lsr4_rd,lsr4_mosi,lsr4_disable = [Signal(LOW) for i in range(5)]
sw1, sw2, sw3, sw4 = [Signal(LOW) for i in range(4)]
dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7 = [Signal(LOW) for i in range(4)]
usb_internal_connected, usb_rear_connected, cyp_reset = [Signal(LOW) for i in range(3)]
fpga_program_enable = Signal(HIGH)
pzt_valve_dac_ld, pzt_valve_dac_sck, pzt_valve_dac_sdi = [Signal(LOW) for i in range(3)]
inlet_valve_pwm, outlet_valve_pwm = [Signal(LOW) for i in range(2)]
inlet_valve_comparator, outlet_valve_comparator = [Signal(LOW) for i in range(2)]
heater_pwm, hot_box_pwm, hot_box_tec_overload = [Signal(LOW) for i in range(3)]
warm_box_pwm, warm_box_tec_overload = [Signal(LOW) for i in range(2)]
wmm_refl1, wmm_refl2, wmm_tran1, wmm_tran2 = [Signal(LOW) for i in range(4)]
wmm_busy1, wmm_busy2 = [Signal(LOW) for i in range(2)]
wmm_rd, wmm_convst, wmm_clk = [Signal(LOW) for i in range(3)]
dout_man = Signal(LOW)
dout = Signal(intbv(0)[40:])
din  = Signal(intbv(0)[24:])
aux_dout = Signal(intbv(0)[4:])
aux_din  = Signal(intbv(0)[4:])

def makeVHDL():
    toVHDL(main,clk0,clk180,clk3f,clk3f180,clk_locked,reset,
                intronix,fpga_led,dsp_emif_we,dsp_emif_re,
                dsp_emif_oe,dsp_emif_ardy,dsp_emif_ea,dsp_emif_din,
                dsp_emif_dout,dsp_emif_ddir, dsp_emif_be, dsp_emif_ce,
                dsp_eclk,
                lsr1_0, lsr1_1, lsr2_0, lsr2_1, lsr3_0, lsr3_1, lsr4_0, lsr4_1,
                lc1, lc2, lc3, lc4,
                lsr1_sck,lsr1_ss,lsr1_rd,lsr1_mosi,lsr1_disable,
                lsr2_sck,lsr2_ss,lsr2_rd,lsr2_mosi,lsr2_disable,
                lsr3_sck,lsr3_ss,lsr3_rd,lsr3_mosi,lsr3_disable,
                lsr4_sck,lsr4_ss,lsr4_rd,lsr4_mosi,lsr4_disable,
                sw1, sw2, sw3, sw4,
                i2c_rst0, i2c_rst1,
                i2c_scl0, i2c_sda0, i2c_scl1, i2c_sda1,
                fp_lcd, fp_led, fp_rs_n,
                rd_adc, rd_adc_clk, rd_adc_oe,
                monitor,
                dsp_ext_int4, dsp_ext_int5, dsp_ext_int6, dsp_ext_int7,
                usb_internal_connected, usb_rear_connected, fpga_program_enable, cyp_reset,
                pzt_valve_dac_ld, pzt_valve_dac_sck, pzt_valve_dac_sdi,
                inlet_valve_pwm, outlet_valve_pwm,
                inlet_valve_comparator, outlet_valve_comparator,
                heater_pwm, hot_box_pwm, hot_box_tec_overload,
                warm_box_pwm, warm_box_tec_overload,
                wmm_refl1, wmm_refl2, wmm_tran1, wmm_tran2,
                wmm_busy1, wmm_busy2,
                wmm_rd, wmm_convst, wmm_clk,
                dout_man, dout, din,
                aux_din, aux_dout)

if __name__ == "__main__":
    makeVHDL()
