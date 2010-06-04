#!/usr/bin/python
#
# FILE:
#   DioMap.py
#
# DESCRIPTION:
#   Mapping between digital IO lines and analyzer signals
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-June-2010  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
LOW, HIGH = bool(0), bool(1)

def dioMap(man,buff_out,buff_in,man_out,man_in,
           pzt_valve_dac_ld,
           pzt_valve_dac_sck,
           inlet_valve_pwm_n,
           outlet_valve_pwm_n,
           pzt_valve_dac_sdi,
           heater_pwm_n,
           hot_box_pwm_n,
           warm_box_pwm_n,
           aux_din,
           monitor,
           wmm_rd,
           wmm_convst,
           wmm_clk,
           sw1,
           sw2,
           sw3,
           sw4,
           lsr1_sck,
           lsr1_rd,
           lsr1_ss_n,
           lsr1_mosi,
           lsr1_disable,
           lsr2_sck,
           lsr2_rd,
           lsr2_ss_n,
           lsr2_mosi,
           lsr2_disable,
           lsr3_sck,
           lsr3_rd,
           lsr3_ss_n,
           lsr3_mosi,
           lsr3_disable,
           lsr4_sck,
           lsr4_rd,
           lsr4_ss_n,
           lsr4_mosi,
           lsr4_disable,
           aux_dout,
           warm_box_tec_overload_n,
           hot_box_tec_overload_n,
           inlet_valve_comparator,
           outlet_valve_comparator,
           wmm_refl1,
           wmm_refl2,
           wmm_tran1,
           wmm_tran2,
           wmm_busy1,
           wmm_busy2):
           
    @always_comb
    def comb():
        if man:
            buff_out.next = man_out
        else:
            buff_out.next = 0
            buff_out[0].next = pzt_valve_dac_ld
            buff_out[1].next = pzt_valve_dac_sck
            buff_out[2].next = inlet_valve_pwm_n
            buff_out[3].next = outlet_valve_pwm_n
            buff_out[4].next = pzt_valve_dac_sdi
            buff_out[5].next = heater_pwm_n
            buff_out[6].next = hot_box_pwm_n
            buff_out[7].next = warm_box_pwm_n
            buff_out[12:8].next = aux_din
            buff_out[12].next = monitor
            buff_out[13].next = wmm_rd
            buff_out[14].next = wmm_convst
            buff_out[15].next = wmm_clk
            buff_out[16].next = sw1
            buff_out[17].next = sw2
            buff_out[18].next = sw3
            buff_out[19].next = sw4
            buff_out[20].next = lsr1_sck
            buff_out[21].next = lsr1_rd
            buff_out[22].next = lsr1_ss_n
            buff_out[23].next = lsr1_mosi
            buff_out[24].next = lsr1_disable
            buff_out[25].next = lsr2_sck
            buff_out[26].next = lsr2_rd
            buff_out[27].next = lsr2_ss_n
            buff_out[28].next = lsr2_mosi
            buff_out[29].next = lsr2_disable
            buff_out[30].next = lsr3_sck
            buff_out[31].next = lsr3_rd
            buff_out[32].next = lsr3_ss_n
            buff_out[33].next = lsr3_mosi
            buff_out[34].next = lsr3_disable
            buff_out[35].next = lsr4_sck
            buff_out[36].next = lsr4_rd
            buff_out[37].next = lsr4_ss_n
            buff_out[38].next = lsr4_mosi
            buff_out[39].next = lsr4_disable
        aux_dout.next = buff_in[4:0]
        warm_box_tec_overload_n.next = buff_in[4]
        hot_box_tec_overload_n.next  = buff_in[5]
        inlet_valve_comparator.next  = buff_in[8]
        outlet_valve_comparator.next = buff_in[9]
        wmm_refl1.next               = buff_in[12]
        wmm_refl2.next               = buff_in[13]
        wmm_tran1.next               = buff_in[14]
        wmm_tran2.next               = buff_in[15]
        wmm_busy1.next               = buff_in[16]
        wmm_busy2.next               = buff_in[17]
        man_in.next   = buff_in
    return instances()

man = Signal(LOW)
buff_out = Signal(intbv(0)[40:])
buff_in  = Signal(intbv(0)[24:])
man_out  = Signal(intbv(0)[40:])
man_in   = Signal(intbv(0)[24:])
pzt_valve_dac_ld   = Signal(LOW)
pzt_valve_dac_sck  = Signal(LOW)
inlet_valve_pwm_n  = Signal(LOW)
outlet_valve_pwm_n = Signal(LOW)
pzt_valve_dac_sdi = Signal(LOW)
heater_pwm_n      = Signal(LOW)
hot_box_pwm_n     = Signal(LOW)
warm_box_pwm_n    = Signal(LOW)
aux_din           = Signal(intbv(0)[4:])
monitor           = Signal(LOW)
wmm_rd            = Signal(LOW)
wmm_convst        = Signal(LOW)
wmm_clk           = Signal(LOW)
sw1               = Signal(LOW)
sw2               = Signal(LOW)
sw3               = Signal(LOW)
sw4               = Signal(LOW)
lsr1_sck          = Signal(LOW)
lsr1_rd           = Signal(LOW)
lsr1_ss_n         = Signal(LOW)
lsr1_mosi         = Signal(LOW)
lsr1_disable      = Signal(LOW)
lsr2_sck          = Signal(LOW)
lsr2_rd           = Signal(LOW)
lsr2_ss_n         = Signal(LOW)
lsr2_mosi         = Signal(LOW)
lsr2_disable      = Signal(LOW)
lsr3_sck          = Signal(LOW)
lsr3_rd           = Signal(LOW)
lsr3_ss_n         = Signal(LOW)
lsr3_mosi         = Signal(LOW)
lsr3_disable      = Signal(LOW)
lsr4_sck          = Signal(LOW)
lsr4_rd           = Signal(LOW)
lsr4_ss_n         = Signal(LOW)
lsr4_mosi         = Signal(LOW)
lsr4_disable      = Signal(LOW)
aux_dout          = Signal(intbv(0)[4:])
warm_box_tec_overload_n = Signal(LOW)
hot_box_tec_overload_n  = Signal(LOW)
inlet_valve_comparator  = Signal(LOW)
outlet_valve_comparator = Signal(LOW)
wmm_refl1         = Signal(LOW)
wmm_refl2         = Signal(LOW)
wmm_tran1         = Signal(LOW)
wmm_tran2         = Signal(LOW)
wmm_busy1         = Signal(LOW)
wmm_busy2         = Signal(LOW)

def makeVHDL():
    toVHDL(dioMap,man,buff_out,buff_in,man_out,man_in,
                  pzt_valve_dac_ld,
                  pzt_valve_dac_sck,
                  inlet_valve_pwm_n,
                  outlet_valve_pwm_n,
                  pzt_valve_dac_sdi,
                  heater_pwm_n,
                  hot_box_pwm_n,
                  warm_box_pwm_n,
                  aux_din,
                  monitor,
                  wmm_rd,
                  wmm_convst,
                  wmm_clk,
                  sw1,
                  sw2,
                  sw3,
                  sw4,
                  lsr1_sck,
                  lsr1_rd,
                  lsr1_ss_n,
                  lsr1_mosi,
                  lsr1_disable,
                  lsr2_sck,
                  lsr2_rd,
                  lsr2_ss_n,
                  lsr2_mosi,
                  lsr2_disable,
                  lsr3_sck,
                  lsr3_rd,
                  lsr3_ss_n,
                  lsr3_mosi,
                  lsr3_disable,
                  lsr4_sck,
                  lsr4_rd,
                  lsr4_ss_n,
                  lsr4_mosi,
                  lsr4_disable,
                  aux_dout,
                  warm_box_tec_overload_n,
                  hot_box_tec_overload_n,
                  inlet_valve_comparator,
                  outlet_valve_comparator,
                  wmm_refl1,
                  wmm_refl2,
                  wmm_tran1,
                  wmm_tran2,
                  wmm_busy1,
                  wmm_busy2)

if __name__ == "__main__":
    makeVHDL()
