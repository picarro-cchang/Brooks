-- File: dioMap.vhd
-- Generated by MyHDL 0.9.0
-- Date: Tue Jun  2 14:27:23 2020


library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use std.textio.all;

use work.pck_myhdl_090.all;

entity dioMap is
    port (
        man: in std_logic;
        buff_out: out unsigned(39 downto 0);
        buff_in: in unsigned(23 downto 0);
        man_out: in unsigned(39 downto 0);
        man_in: out unsigned(23 downto 0);
        pzt_valve_dac_ld: in std_logic;
        pzt_valve_dac_sck: in std_logic;
        inlet_valve_pwm_n: in std_logic;
        outlet_valve_pwm_n: in std_logic;
        pzt_valve_dac_sdi: in std_logic;
        heater_pwm_n: in std_logic;
        hot_box_pwm_n: in std_logic;
        warm_box_pwm_n: in std_logic;
        aux_din: in unsigned(3 downto 0);
        monitor: in std_logic;
        wmm_rd: in std_logic;
        wmm_convst: in std_logic;
        wmm_clk: in std_logic;
        sw1: in std_logic;
        sw2: in std_logic;
        sw3: in std_logic;
        sw4: in std_logic;
        lsr1_sck: in std_logic;
        lsr1_rd: in std_logic;
        lsr1_ss_n: in std_logic;
        lsr1_mosi: in std_logic;
        lsr1_miso: out std_logic;
        lsr1_disable: in std_logic;
        lsr2_sck: in std_logic;
        lsr2_rd: in std_logic;
        lsr2_ss_n: in std_logic;
        lsr2_mosi: in std_logic;
        lsr2_miso: out std_logic;
        lsr2_disable: in std_logic;
        lsr3_sck: in std_logic;
        lsr3_rd: in std_logic;
        lsr3_ss_n: in std_logic;
        lsr3_mosi: in std_logic;
        lsr3_miso: out std_logic;
        lsr3_disable: in std_logic;
        lsr4_sck: in std_logic;
        lsr4_rd: in std_logic;
        lsr4_ss_n: in std_logic;
        lsr4_mosi: in std_logic;
        lsr4_miso: out std_logic;
        lsr4_disable: in std_logic;
        aux_dout: out unsigned(3 downto 0);
        warm_box_tec_overload_n: out std_logic;
        hot_box_tec_overload_n: out std_logic;
        inlet_valve_comparator: out std_logic;
        outlet_valve_comparator: out std_logic;
        wmm_refl1: out std_logic;
        wmm_refl2: out std_logic;
        wmm_tran1: out std_logic;
        wmm_tran2: out std_logic;
        wmm_busy1: out std_logic;
        wmm_busy2: out std_logic
    );
end entity dioMap;


architecture MyHDL of dioMap is






begin





DIOMAP_COMB: process (buff_in, lsr3_ss_n, lsr1_sck, pzt_valve_dac_sdi, lsr4_disable, aux_din, lsr1_mosi, lsr3_disable, heater_pwm_n, lsr4_ss_n, lsr1_disable, wmm_clk, monitor, warm_box_pwm_n, lsr4_mosi, lsr3_sck, pzt_valve_dac_ld, inlet_valve_pwm_n, wmm_rd, lsr2_ss_n, lsr1_ss_n, outlet_valve_pwm_n, lsr4_rd, hot_box_pwm_n, lsr2_disable, lsr3_mosi, lsr1_rd, pzt_valve_dac_sck, man, wmm_convst, lsr2_mosi, lsr4_sck, lsr3_rd, man_out, lsr2_rd, sw1, sw3, sw2, sw4, lsr2_sck) is
begin
    if bool(man) then
        buff_out <= man_out;
    else
        buff_out <= to_unsigned(0, 40);
        buff_out(0) <= pzt_valve_dac_ld;
        buff_out(1) <= pzt_valve_dac_sck;
        buff_out(2) <= inlet_valve_pwm_n;
        buff_out(3) <= outlet_valve_pwm_n;
        buff_out(4) <= pzt_valve_dac_sdi;
        buff_out(5) <= heater_pwm_n;
        buff_out(6) <= hot_box_pwm_n;
        buff_out(7) <= warm_box_pwm_n;
        buff_out(12-1 downto 8) <= aux_din;
        buff_out(12) <= monitor;
        buff_out(13) <= wmm_rd;
        buff_out(14) <= wmm_convst;
        buff_out(15) <= wmm_clk;
        buff_out(16) <= sw1;
        buff_out(17) <= sw3;
        buff_out(18) <= sw2;
        buff_out(19) <= sw4;
        buff_out(20) <= lsr1_sck;
        buff_out(21) <= lsr1_rd;
        buff_out(22) <= lsr1_ss_n;
        buff_out(23) <= lsr1_mosi;
        buff_out(24) <= lsr1_disable;
        buff_out(25) <= lsr2_sck;
        buff_out(26) <= lsr2_rd;
        buff_out(27) <= lsr2_ss_n;
        buff_out(28) <= lsr2_mosi;
        buff_out(29) <= lsr2_disable;
        buff_out(30) <= lsr3_sck;
        buff_out(31) <= lsr3_rd;
        buff_out(32) <= lsr3_ss_n;
        buff_out(33) <= lsr3_mosi;
        buff_out(34) <= lsr3_disable;
        buff_out(35) <= lsr4_sck;
        buff_out(36) <= lsr4_rd;
        buff_out(37) <= lsr4_ss_n;
        buff_out(38) <= lsr4_mosi;
        buff_out(39) <= lsr4_disable;
    end if;
    aux_dout <= buff_in(4-1 downto 0);
    warm_box_tec_overload_n <= buff_in(4);
    hot_box_tec_overload_n <= buff_in(5);
    inlet_valve_comparator <= buff_in(8);
    outlet_valve_comparator <= buff_in(9);
    wmm_refl1 <= buff_in(12);
    wmm_refl2 <= buff_in(13);
    wmm_tran1 <= buff_in(14);
    wmm_tran2 <= buff_in(15);
    wmm_busy1 <= buff_in(16);
    wmm_busy2 <= buff_in(17);
    lsr1_miso <= buff_in(20);
    lsr2_miso <= buff_in(21);
    lsr3_miso <= buff_in(22);
    lsr4_miso <= buff_in(23);
    man_in <= buff_in;
end process DIOMAP_COMB;

end architecture MyHDL;
