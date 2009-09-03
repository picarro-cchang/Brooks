#!/usr/bin/python
#
# FILE:
#   WlmSimTop.py
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
from MyHDL.Common.Inject import Inject
from MyHDL.Common.Kernel import Kernel
from MyHDL.Common.LaserLocker import LaserLocker
from MyHDL.Common.Ltc2604Dac import Ltc2604Dac
from MyHDL.Common.Pwm1 import Pwm
from MyHDL.Common.RdMan import RdMan
from MyHDL.Common.Rdmemory import Rdmemory
from MyHDL.Common.RdSim import RdSim
from MyHDL.Common.TWGen import TWGen
from MyHDL.Common.WlmSim import WlmSim

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
         usb_connected, cyp_reset,
         pzt_valve_dac_ld, pzt_valve_dac_sck, pzt_valve_dac_sdi,
         inlet_valve_pwm, outlet_valve_pwm,
         inlet_valve_comparator, outlet_valve_comparator,
         heater_pwm, hot_box_pwm, hot_box_tec_overload,
         warm_box_pwm, warm_box_tec_overload,
         wmm_refl1, wmm_refl2, wmm_tran1, wmm_tran2,
         wmm_busy1, wmm_busy2,
         wmm_rd, wmm_convst, wmm_clk
        ):

    NSTAGES = 28
    counter = Signal(intbv(0)[NSTAGES:])

    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_inject      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_kernel      = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_laserlocker = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser1  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser2  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser3  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_pwm_laser4  = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdman       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdmemory    = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_rdsim       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_twGen       = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in_wlmsim      = Signal(intbv(0)[EMIF_DATA_WIDTH:])

    dsp_wr, ce2 = [Signal(LOW) for i in range(2)]
    pwm_laser1_out, pwm_laser1_inv_out = [Signal(LOW) for i in range(2)]
    pwm_laser2_out, pwm_laser2_inv_out = [Signal(LOW) for i in range(2)]
    pwm_laser3_out, pwm_laser3_inv_out = [Signal(LOW) for i in range(2)]
    pwm_laser4_out, pwm_laser4_inv_out = [Signal(LOW) for i in range(2)]

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
    lock_error = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pzt = Signal(intbv(0)[FPGA_REG_WIDTH:])    

    meta0 = ratio1
    meta1 = ratio2
    meta2 = pzt
    meta3 = laser_tuning_offset
    meta4 = laser_fine_current
    meta5 = lock_error
    meta6 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    meta7 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    
    laser_shutdown_in = Signal(LOW)
    soa_shutdown_in = Signal(LOW)
    sel_laser = Signal(intbv(0)[2:])
    sel_coarse_current = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sel_fine_current = Signal(intbv(0)[FPGA_REG_WIDTH:])

    rdsim_value = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rd_trig = Signal(LOW)

    eta1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    wlmsimDone = Signal(LOW)
    z0_in = Signal(intbv(0)[FPGA_REG_WIDTH:])

    sim_loss = Signal(intbv(0)[FPGA_REG_WIDTH:])
    sim_pzt = Signal(intbv(0)[FPGA_REG_WIDTH:])
    
    sample_dark_in = Signal(LOW)
    pzt_dac = Signal(intbv(0)[FPGA_REG_WIDTH:])

    laser_freq_ok = Signal(LOW)
    acc_en = Signal(LOW)
    rd_irq = Signal(LOW)
    acq_done_irq = Signal(LOW)
    metadata_strobe = Signal(LOW)
    laser_locked = Signal(LOW)
    
    chanA_data_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    chanB_data_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    chanD_data_in = Signal(intbv(0)[FPGA_REG_WIDTH:])

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
                    sel_laser_out=sel_laser,
                    sel_coarse_current_out=sel_coarse_current,
                    sel_fine_current_out=sel_fine_current,
                    map_base=FPGA_INJECT)

    kernel = Kernel( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_kernel,
                     dsp_wr=dsp_wr, usb_connected=usb_connected,
                     cyp_reset=cyp_reset, diag_1_out=diag_1,
                     intronix_clksel_out=intronix_clksel,
                     intronix_1_out=intronix_1,
                     intronix_2_out=intronix_2,
                     intronix_3_out=intronix_3, map_base=FPGA_KERNEL )
    
    laserlocker = LaserLocker( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                               dsp_data_out=dsp_data_out,
                               dsp_data_in=dsp_data_in_laserlocker, dsp_wr=dsp_wr,
                               eta1_in=eta1, ref1_in=ref1,
                               eta2_in=eta2, ref2_in=ref2,
                               tuning_offset_in=tuner_value,
                               acc_en_in=acc_en,
                               sample_dark_in=sample_dark_in,
                               adc_strobe_in=wlmsimDone,
                               ratio1_out=ratio1,
                               ratio2_out=ratio2,
                               lock_error_out=lock_error,
                               fine_current_out=laser_fine_current,
                               tuning_offset_out=laser_tuning_offset,
                               laser_freq_ok_out=laser_freq_ok,
                               current_ok_out=metadata_strobe,
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
                   tuner_value_in=tuner_value,
                   rd_adc_clk_in=adc_clk,
                   pzt_center_in=sim_pzt, decay_in=sim_loss,
                   rdsim_value_out=rdsim_value, map_base=FPGA_RDSIM )

    twGen = TWGen(clk=clk0, reset=reset, dsp_addr=dsp_addr,
                  dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_twGen,
                  dsp_wr=dsp_wr, synth_step_in=pulse_100k,
                  value_out=tuner_value, pzt_out=pzt, slope_out=tuner_slope,
                  in_window_out=tuner_in_window,map_base=FPGA_TWGEN)
    
    wlmsim = WlmSim( clk=clk0, reset=reset, dsp_addr=dsp_addr,
                     dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in_wlmsim,
                     dsp_wr=dsp_wr, start_in=pulse_100k,
                     coarse_current_in=sel_coarse_current,
                     fine_current_in=sel_fine_current,
                     eta1_out=eta1, ref1_out=ref1,
                     eta2_out=eta2, ref2_out=ref2,
                     loss_out=sim_loss, pzt_cen_out=sim_pzt,
                     done_out=wlmsimDone, map_base=FPGA_WLMSIM )

    pztValveDac = Ltc2604Dac(clk=clk0, reset=reset, dac_clock_in=clk_10M,
                             chanA_data_in=chanA_data_in,
                             chanB_data_in=chanB_data_in,
                             chanC_data_in=pzt,
                             chanD_data_in=chanD_data_in, strobe_in=pulse_100k,
                             dac_sdi_out=pzt_valve_dac_sdi, dac_ld_out=pzt_valve_dac_ld)

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

                # Latch data for the intronix port
                if intronix_1 == 0:
                    channel_1.next = tuner_value[8:]
                elif intronix_1 == 1:
                    channel_1.next = tuner_value[16:8]
                elif intronix_1 == 2:
                    channel_1.next = concat(rd_adc[6:0],LOW,LOW)
                elif intronix_1 == 3:
                    channel_1.next = rd_adc[14:6]
                elif intronix_1 == 4:
                    channel_1.next = concat(rdsim_value[6:0],LOW,LOW)
                elif intronix_1 == 5:
                    channel_1.next = rdsim_value[14:6]
                elif intronix_1 == 6:
                    channel_1.next = laser_fine_current[8:]
                elif intronix_1 == 7:
                    channel_1.next = laser_fine_current[16:8]
                elif intronix_1 == 8:
                    channel_1.next = lock_error[8:]
                elif intronix_1 == 9:
                    channel_1.next = lock_error[16:8]
                elif intronix_1 == 10:
                    channel_1.next = ratio1[8:]
                elif intronix_1 == 11:
                    channel_1.next = ratio1[16:8]
                elif intronix_1 == 12:
                    channel_1.next = ratio2[8:]
                else:
                    channel_1.next = ratio2[16:8]
                    
                if intronix_2 == 0:
                    channel_2.next = tuner_value[8:]
                elif intronix_2 == 1:
                    channel_2.next = tuner_value[16:8]
                elif intronix_2 == 2:
                    channel_2.next = concat(rd_adc[6:0],LOW,LOW)
                elif intronix_2 == 3:
                    channel_2.next = rd_adc[14:6]
                elif intronix_2 == 4:
                    channel_2.next = concat(rdsim_value[6:0],LOW,LOW)
                elif intronix_2 == 5:
                    channel_2.next = rdsim_value[14:6]
                elif intronix_2 == 6:
                    channel_2.next = laser_fine_current[8:]
                elif intronix_2 == 7:
                    channel_2.next = laser_fine_current[16:8]
                elif intronix_2 == 8:
                    channel_2.next = lock_error[8:]
                elif intronix_2 == 9:
                    channel_2.next = lock_error[16:8]
                elif intronix_2 == 10:
                    channel_2.next = ratio1[8:]
                elif intronix_2 == 11:
                    channel_2.next = ratio1[16:8]
                elif intronix_2 == 12:
                    channel_2.next = ratio2[8:]
                else:
                    channel_2.next = ratio2[16:8]
                    
                if intronix_3 == 0:
                    channel_3.next = tuner_value[8:]
                elif intronix_3 == 1:
                    channel_3.next = tuner_value[16:8]
                elif intronix_3 == 2:
                    channel_3.next = concat(rd_adc[6:0],LOW,LOW)
                elif intronix_3 == 3:
                    channel_3.next = rd_adc[14:6]
                elif intronix_3 == 4:
                    channel_3.next = concat(rdsim_value[6:0],LOW,LOW)
                elif intronix_3 == 5:
                    channel_3.next = rdsim_value[14:6]
                elif intronix_3 == 6:
                    channel_3.next = laser_fine_current[8:]
                elif intronix_3 == 7:
                    channel_3.next = laser_fine_current[16:8]
                elif intronix_3 == 8:
                    channel_3.next = lock_error[8:]
                elif intronix_3 == 9:
                    channel_3.next = lock_error[16:8]
                elif intronix_3 == 10:
                    channel_3.next = ratio1[8:]
                elif intronix_3 == 11:
                    channel_3.next = ratio1[16:8]
                elif intronix_3 == 12:
                    channel_3.next = ratio2[8:]
                else:
                    channel_3.next = ratio2[16:8]
        
                channel_4.next = concat(rd_trig,diag_1[4:],bank,laser_locked,acc_en,tuner_in_window)
        

    @always_comb
    def  comb():
        dsp_data_in.next = \
                           dsp_data_in_inject      | \
                           dsp_data_in_kernel      | \
                           dsp_data_in_laserlocker | \
                           dsp_data_in_pwm_laser1  | \
                           dsp_data_in_pwm_laser2  | \
                           dsp_data_in_pwm_laser3  | \
                           dsp_data_in_pwm_laser4  | \
                           dsp_data_in_rdman       | \
                           dsp_data_in_rdmemory    | \
                           dsp_data_in_rdsim       | \
                           dsp_data_in_twGen       | \
                           dsp_data_in_wlmsim

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
        
        ce2.next = dsp_emif_ce[2]
        lsr1_0.next = pwm_laser1_out
        lsr1_1.next = pwm_laser1_inv_out
        lsr2_0.next = pwm_laser2_out
        lsr2_1.next = pwm_laser2_inv_out
        lsr3_0.next = pwm_laser3_out
        lsr3_1.next = pwm_laser3_inv_out
        lsr4_0.next = pwm_laser4_out
        lsr4_1.next = pwm_laser4_inv_out
        

        rd_adc_clk.next = adc_clk
        rd_adc_oe.next = 1
        fpga_led.next = counter[NSTAGES:NSTAGES-4]
        i2c_rst0.next = reset
        i2c_rst1.next = reset
        
        dsp_ext_int4.next = rd_irq
        dsp_ext_int5.next = acq_done_irq
        dsp_ext_int6.next = 0
        dsp_ext_int7.next = 0

        lsr1_sck.next = clk_5M
        lsr2_sck.next = clk_5M
        lsr3_sck.next = clk_5M
        lsr4_sck.next = clk_5M

        pzt_valve_dac_sck.next = clk_10M

        sw1.next = 0
        sw2.next = 0
        sw4.next = 0

        inlet_valve_pwm.next = 0
        outlet_valve_pwm.next = 0
        heater_pwm.next = 0
        hot_box_pwm.next = 0
        warm_box_pwm.next = 0

        wmm_rd.next = 0
        wmm_convst.next = 0
        wmm_clk.next = 0
        
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
pzt_valve_dac_ld, pzt_valve_dac_sck, pzt_valve_dac_sdi = [Signal(LOW) for i in range(3)]
inlet_valve_pwm, outlet_valve_pwm = [Signal(LOW) for i in range(2)]
inlet_valve_comparator, outlet_valve_comparator = [Signal(LOW) for i in range(2)]
heater_pwm, hot_box_pwm, hot_box_tec_overload = [Signal(LOW) for i in range(3)]
warm_box_pwm, warm_box_tec_overload = [Signal(LOW) for i in range(2)]
wmm_refl1, wmm_refl2, wmm_tran1, wmm_tran2 = [Signal(LOW) for i in range(4)]
wmm_busy1, wmm_busy2 = [Signal(LOW) for i in range(2)]
wmm_rd, wmm_convst, wmm_clk = [Signal(LOW) for i in range(3)]

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
                usb_connected, cyp_reset,
                pzt_valve_dac_ld, pzt_valve_dac_sck, pzt_valve_dac_sdi,
                inlet_valve_pwm, outlet_valve_pwm,
                inlet_valve_comparator, outlet_valve_comparator,
                heater_pwm, hot_box_pwm, hot_box_tec_overload,
                warm_box_pwm, warm_box_tec_overload,
                wmm_refl1, wmm_refl2, wmm_tran1, wmm_tran2,
                wmm_busy1, wmm_busy2,
                wmm_rd, wmm_convst, wmm_clk
                )

if __name__ == "__main__":
    makeVHDL()
