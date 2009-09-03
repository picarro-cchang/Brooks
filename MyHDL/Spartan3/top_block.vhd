----------------------------------------------------------------------------------
-- Company:        Picarro, Inc
-- Engineer:       Sze Tan
--
-- Create Date:    04/29/2009
-- Design Name:
-- Module Name:    top_block - Behavioral
-- Project Name:
-- Target Devices:
-- Tool versions:
-- Description:
--
-- Dependencies:
--
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
--
----------------------------------------------------------------------------------
library ieee;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use std.textio.all;
use work.pck_myhdl_06.all;

---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
library UNISIM;
use UNISIM.VComponents.all;

entity top_block is
    port (
           clk              : in std_logic;
           reset            : in std_logic;

           rd_adc           : in unsigned(15 downto 0);
           rd_adc_clk       : out std_logic;
           rd_adc_oe        : out std_logic;

           dsp_emif_we      : in std_logic;
           dsp_emif_re      : in std_logic;
           dsp_emif_oe      : in std_logic;
           dsp_emif_ardy    : out std_logic;

           dsp_emif_ea      : in unsigned(19 downto 0);
           dsp_emif_din     : out unsigned(31 downto 0);
           dsp_emif_dout    : in  unsigned(31 downto 0);
           dsp_emif_ddir    : out  std_logic;

           dsp_emif_be      : in unsigned(3 downto 0);
           dsp_emif_ce      : in unsigned(3 downto 0);

           usb_connected    : in std_logic;
           cyp_reset        : out std_logic;
           cyp_pc           : in unsigned(7 downto 0);
           dsp_ext_int4     : out std_logic;
           dsp_ext_int5     : out std_logic;
           dsp_ext_int6     : out std_logic;
           dsp_ext_int7     : out std_logic;

           dsp_clkout2      : in std_logic;
           dsp_clkout3      : in std_logic;
           dsp_eclkout      : in std_logic;

           dsp_tinp0        : out std_logic;
           dsp_tinp1        : out std_logic;
           dsp_tout0        : in std_logic;
           dsp_tout1        : in std_logic;

           fp_lcd           : out unsigned(7 downto 0);
           fp_pb            : in std_logic;
           fp_rs_n          : in std_logic;
           fp_led           : out unsigned(3 downto 0);

           aux_din          : out unsigned(3 downto 0);
           aux_dout         : in unsigned(3 downto 0);

           monitor          : out std_logic;

           lsr1_sck         : out std_logic;
           lsr1_ss          : out std_logic;
           lsr1_rd          : out std_logic;
           lsr1_mosi        : out std_logic;
           lsr1_disable     : out std_logic;

           lsr2_sck         : out std_logic;
           lsr2_ss          : out std_logic;
           lsr2_rd          : out std_logic;
           lsr2_mosi        : out std_logic;
           lsr2_disable     : out std_logic;

           lsr3_sck         : out std_logic;
           lsr3_ss          : out std_logic;
           lsr3_rd          : out std_logic;
           lsr3_mosi        : out std_logic;
           lsr3_disable     : out std_logic;

           lsr4_sck         : out std_logic;
           lsr4_ss          : out std_logic;
           lsr4_rd          : out std_logic;
           lsr4_mosi        : out std_logic;
           lsr4_disable     : out std_logic;

           wmm_refl1        : in std_logic;
           wmm_refl2        : in std_logic;
           wmm_tran1        : in std_logic;
           wmm_tran2        : in std_logic;
           wmm_busy1        : in std_logic;
           wmm_busy2        : in std_logic;
           wmm_rd           : out std_logic;
           wmm_convst       : out std_logic;
           wmm_clk          : out std_logic;

           sw1              : out std_logic;
           sw2              : out std_logic;
           sw3              : out std_logic;
           sw4              : out std_logic;

           lsr1_0           : out std_logic;
           lsr1_1           : out std_logic;
           lsr2_0           : out std_logic;
           lsr2_1           : out std_logic;
           lsr3_0           : out std_logic;
           lsr3_1           : out std_logic;
           lsr4_0           : out std_logic;
           lsr4_1           : out std_logic;

           intronix         : out unsigned(33 downto 0);
           fpga_led         : out unsigned(3 downto 0);

           i2c_rst0         : out std_logic;
           i2c_rst1         : out std_logic;

           i2c_scl0         : in std_logic;
           i2c_sda0         : in std_logic;
           i2c_scl1         : in std_logic;
           i2c_sda1         : in std_logic;
           
           pzt_valve_dac_ld   : out std_logic;
           pzt_valve_dac_sck  : out std_logic;
           pzt_valve_dac_sdi  : out std_logic;

           inlet_valve_pwm    : out std_logic;
           outlet_valve_pwm   : out std_logic;
           inlet_valve_comparator  : in std_logic;
           outlet_valve_comparator : in std_logic;
       
           heater_pwm         : out std_logic;
           hot_box_pwm        : out std_logic;
           hot_box_tec_overload    : in std_logic;
           warm_box_pwm       : out std_logic;
           warm_box_tec_overload   : in std_logic
    );
end top_block;

architecture behavioral of top_block is
    component dcm_example -- DCM for generating quadrature phase clocks
    port(
        clkin_in : in std_logic;
        rst_in : in std_logic;
        clkfx_out : out std_logic;
        clkfx180_out : out std_logic;
        clk0_out : out std_logic;
        clk180_out : out std_logic;
        locked_out : out std_logic
        );
    end component;
    signal clk0, clk180, clk3f, clk3f180, clk_locked : std_logic;

begin
    dcm_inst : dcm_example port map (
        clkin_in => clk,
        rst_in => reset,
        clk0_out => clk0,
        clk180_out => clk180,
        clkfx_out => clk3f,
        clkfx180_out => clk3f180,
        locked_out => clk_locked
    );

    main_inst : entity work.main(MyHDL) port map(
        clk0 => clk0,
        clk180 => clk180,
        clk3f => clk3f,
        clk3f180 => clk3f180,
        clk_locked => clk_locked,
        reset => reset,
        intronix => intronix,
        fpga_led => fpga_led,
        dsp_emif_we => dsp_emif_we,
        dsp_emif_re => dsp_emif_re,
        dsp_emif_oe => dsp_emif_oe,
        dsp_emif_ardy => dsp_emif_ardy,
        dsp_emif_ea => dsp_emif_ea,
        dsp_emif_din => dsp_emif_din,
        dsp_emif_dout => dsp_emif_dout,
        dsp_emif_ddir => dsp_emif_ddir,
        dsp_emif_be => dsp_emif_be,
        dsp_emif_ce => dsp_emif_ce,
        dsp_eclk => dsp_eclkout,
        lsr1_0 => lsr1_0,
        lsr1_1 => lsr1_1,
        lsr2_0 => lsr2_0,
        lsr2_1 => lsr2_1,
        lsr3_0 => lsr3_0,
        lsr3_1 => lsr3_1,
        lsr4_0 => lsr4_0,
        lsr4_1 => lsr4_1,
        lsr1_sck => lsr1_sck,
        lsr1_ss  => lsr1_ss,
        lsr1_rd  => lsr1_rd,
        lsr1_mosi => lsr1_mosi,
        lsr1_disable => lsr1_disable,
        lsr2_sck => lsr2_sck,
        lsr2_ss  => lsr2_ss,
        lsr2_rd  => lsr2_rd,
        lsr2_mosi => lsr2_mosi,
        lsr2_disable => lsr2_disable,
        lsr3_sck => lsr3_sck,
        lsr3_ss  => lsr3_ss,
        lsr3_rd  => lsr3_rd,
        lsr3_mosi => lsr3_mosi,
        lsr3_disable => lsr3_disable,
        lsr4_sck => lsr4_sck,
        lsr4_ss  => lsr4_ss,
        lsr4_rd  => lsr4_rd,
        lsr4_mosi => lsr4_mosi,
        lsr4_disable => lsr4_disable,
        sw1 => sw1,
        sw2 => sw2,
        sw3 => sw3,
        sw4 => sw4,
        i2c_rst0 => i2c_rst0,
        i2c_rst1 => i2c_rst1,
        i2c_scl0 => i2c_scl0,
        i2c_sda0 => i2c_sda0,
        i2c_scl1 => i2c_scl1,
        i2c_sda1 => i2c_sda1,
        rd_adc => rd_adc,
        rd_adc_clk => rd_adc_clk,
        rd_adc_oe => rd_adc_oe,
        monitor => monitor,
        dsp_ext_int4 => dsp_ext_int4,
        dsp_ext_int5 => dsp_ext_int5,
        dsp_ext_int6 => dsp_ext_int6,
        dsp_ext_int7 => dsp_ext_int7,
        usb_connected => usb_connected,
        cyp_reset => cyp_reset,
        
        pzt_valve_dac_ld        => pzt_valve_dac_ld,
        pzt_valve_dac_sck       => pzt_valve_dac_sck,
        pzt_valve_dac_sdi       => pzt_valve_dac_sdi,

        inlet_valve_pwm         => inlet_valve_pwm,
        outlet_valve_pwm        => outlet_valve_pwm,
        inlet_valve_comparator  => inlet_valve_comparator,
        outlet_valve_comparator => outlet_valve_comparator,
       
        heater_pwm              => heater_pwm,
        hot_box_pwm             => hot_box_pwm,
        hot_box_tec_overload    => hot_box_tec_overload,
        warm_box_pwm            => warm_box_pwm,
        warm_box_tec_overload   => warm_box_tec_overload,
       
        wmm_refl1               => wmm_refl1,
        wmm_refl2               => wmm_refl2,
        wmm_tran1               => wmm_tran1,
        wmm_tran2               => wmm_tran2,
        wmm_busy1               => wmm_busy1,
        wmm_busy2               => wmm_busy2,
        wmm_rd                  => wmm_rd,
        wmm_convst              => wmm_convst,
        wmm_clk                 => wmm_clk
    );
end behavioral;
