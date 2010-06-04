----------------------------------------------------------------------------------
-- Company:        Picarro, Inc
-- Engineer:       Sze Tan
--
-- Create Date:    04/29/2009
-- Design Name:
-- Module Name:    top_io - Behavioral
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
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use std.textio.all;
use work.pck_myhdl_06.all;

---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
library UNISIM;
use UNISIM.VComponents.all;

entity top_io is
    port ( CLK50            : in std_logic;
           -- Ringdown ADC signals
           RD_ADC           : in std_logic_vector(15 downto 0);
           RD_ADC_CLK       : out std_logic;
           RD_ADC_OE_N      : out std_logic;
           -- USB connected signal
           USB_INTERNAL_CONNECTED    : in std_logic;
           USB_REAR_CONNECTED        : in std_logic;
           -- FPGA program enable
           FPGA_PROGRAM_ENABLE       : out std_logic;
           -- Cypress reset
           CYP_RESET_N      : out std_logic;
           -- Cypress PortC
           CYP_PC           : in std_logic_vector(7 downto 0);
           -- DSP interrupt inputs
           DSP_EXT_INT4     : out std_logic;
           DSP_EXT_INT5     : out std_logic;
           DSP_EXT_INT6     : out std_logic;
           DSP_EXT_INT7     : out std_logic;
           -- DSP clock outputs
           DSP_CLKOUT2      : in std_logic;
           DSP_CLKOUT3      : in std_logic;
           DSP_ECLKOUT      : in std_logic;
           -- DSP external memory address bus
           DSP_EMIF_EA      : in std_logic_vector(21 downto 2);
           DSP_EMIF_ED      : inout std_logic_vector(31 downto 0);
           -- DSP external memory byte enable
           DSP_EMIF_BE_N    : in std_logic_vector(3 downto 0);
           -- DSP external memory chip enable
           DSP_EMIF_CE_N    : in std_logic_vector(3 downto 0);
           -- DSP external memory control lines
           DSP_EMIF_WE_N    : in std_logic;
           DSP_EMIF_RE_N    : in std_logic;
           DSP_EMIF_OE_N    : in std_logic;
           DSP_EMIF_ARDY    : out std_logic;
           -- DSP timers
           DSP_TINP0        : out std_logic;
           DSP_TINP1        : out std_logic;
           DSP_TOUT0        : in std_logic;
           DSP_TOUT1        : in std_logic;
           -- Front panel
           FP_LCD           : out std_logic_vector(7 downto 0);
           FP_PB            : in std_logic;
           FP_RS_N          : in std_logic;
           FP_LED           : out std_logic_vector(3 downto 0);
           -- Laser TEC PWM lines
           LSR1_0           : out std_logic;
           LSR1_1           : out std_logic;
           LSR2_0           : out std_logic;
           LSR2_1           : out std_logic;
           LSR3_0           : out std_logic;
           LSR3_1           : out std_logic;
           LSR4_0           : out std_logic;
           LSR4_1           : out std_logic;
           -- Laser TEC overcurrent lines
           LC1              : in std_logic;
           LC2              : in std_logic;
           LC3              : in std_logic;
           LC4              : in std_logic;
           -- Mictor connector
           MICTOR           : out std_logic_vector(38 downto 5);
           -- FPGA LEDS
           FPGA_LED         : out std_logic_vector(3 downto 0);
           -- I2C reset
           I2C_RST0_N       : out std_logic;
           I2C_RST1_N       : out std_logic;
           -- DSP I2C signals
           I2C_SCL0         : in std_logic;
           I2C_SDA0         : in std_logic;
           I2C_SCL1         : in std_logic;
           I2C_SDA1         : in std_logic;
           -- Digital IO signals
           BUFF_OUT         : out std_logic_vector(39 downto 0);
           BUFF_IN          : in std_logic_vector(63 downto 40)
    );
end top_io;

architecture behavioral of top_io is
    signal DSP_EMIF_DIN  : unsigned(31 downto 0);
    signal DSP_EMIF_DOUT : std_logic_vector(31 downto 0);
    signal DSP_EMIF_WE : std_logic;
    signal DSP_EMIF_RE : std_logic;
    signal DSP_EMIF_OE : std_logic;
    signal DSP_EMIF_DDIR : std_logic;
    signal DSP_EMIF_DDIR_N : std_logic;
    signal RD_ADC_OE : std_logic;
    signal CYP_RESET : std_logic;
    signal DSP_EMIF_BE : std_logic_vector(3 downto 0);
    signal DSP_EMIF_CE : std_logic_vector(3 downto 0);
    signal FP_LCD_U    : unsigned(7 downto 0);
    signal FP_LED_U    : unsigned(3 downto 0);
    signal PWR_DIN_U   : unsigned(7 downto 0);
    signal AUX_DIN_U   : unsigned(3 downto 0);
    signal LSR1_SS     : std_logic;
    signal LSR2_SS     : std_logic;
    signal LSR3_SS     : std_logic;
    signal LSR4_SS     : std_logic;
    signal INTRONIX_U  : unsigned(33 downto 0);
    signal FPGA_LED_U  : unsigned(3 downto 0);
    signal I2C_RST0    : std_logic;
    signal I2C_RST1    : std_logic;
    signal INLET_VALVE_PWM     : std_logic;
    signal OUTLET_VALVE_PWM    : std_logic;
    signal HEATER_PWM          : std_logic;
    signal HOT_BOX_PWM         : std_logic;
    signal WARM_BOX_PWM        : std_logic;
    signal HOT_BOX_TEC_OVERLOAD    : std_logic;
    signal WARM_BOX_TEC_OVERLOAD   : std_logic;

    signal reset_counter: unsigned(15 downto 0);
    signal reset       : std_logic;

    signal DOUT_MAN : std_logic;
    signal DOUT     : unsigned(39 downto 0);
    signal DIN      : unsigned(23 downto 0);

    signal PZT_VALVE_DAC_LD: std_logic;
    signal PZT_VALVE_DAC_SCK: std_logic;
    signal INLET_VALVE_PWM_N: std_logic;
    signal OUTLET_VALVE_PWM_N: std_logic;
    signal PZT_VALVE_DAC_SDI: std_logic;
    signal HEATER_PWM_N: std_logic;
    signal HOT_BOX_PWM_N: std_logic;
    signal WARM_BOX_PWM_N: std_logic;
    signal AUX_DIN: unsigned(3 downto 0);
    signal MONITOR: std_logic;
    signal WMM_RD:  std_logic;
    signal WMM_CONVST: std_logic;
    signal WMM_CLK: std_logic;
    signal SW1: std_logic;
    signal SW2: std_logic;
    signal SW3: std_logic;
    signal SW4: std_logic;
    signal LSR1_SCK: std_logic;
    signal LSR1_RD: std_logic;
    signal LSR1_SS_N: std_logic;
    signal LSR1_MOSI: std_logic;
    signal LSR1_DISABLE: std_logic;
    signal LSR2_SCK: std_logic;
    signal LSR2_RD: std_logic;
    signal LSR2_SS_N: std_logic;
    signal LSR2_MOSI: std_logic;
    signal LSR2_DISABLE: std_logic;
    signal LSR3_SCK: std_logic;
    signal LSR3_RD: std_logic;
    signal LSR3_SS_N: std_logic;
    signal LSR3_MOSI: std_logic;
    signal LSR3_DISABLE: std_logic;
    signal LSR4_SCK: std_logic;
    signal LSR4_RD: std_logic;
    signal LSR4_SS_N: std_logic;
    signal LSR4_MOSI: std_logic;
    signal LSR4_DISABLE: std_logic;
    signal AUX_DOUT: unsigned(3 downto 0);
    signal WARM_BOX_TEC_OVERLOAD_N: std_logic;
    signal HOT_BOX_TEC_OVERLOAD_N: std_logic;
    signal INLET_VALVE_COMPARATOR: std_logic;
    signal OUTLET_VALVE_COMPARATOR: std_logic;
    signal WMM_REFL1: std_logic;
    signal WMM_REFL2: std_logic;
    signal WMM_TRAN1: std_logic;
    signal WMM_TRAN2: std_logic;
    signal WMM_BUSY1: std_logic;
    signal WMM_BUSY2: std_logic;
    
    signal BUFF_OUT_U: unsigned(39 downto 0);
    signal BUFF_IN_U: unsigned(23 downto 0);
    
begin
    dioMap_inst : entity work.dioMap(MyHDL) port map(
        man                     => DOUT_MAN,
        buff_out                => BUFF_OUT_U,
        buff_in                 => BUFF_IN_U,
        man_out                 => DOUT,
        man_in                  => DIN,

        pzt_valve_dac_ld        => PZT_VALVE_DAC_LD,
        pzt_valve_dac_sck       => PZT_VALVE_DAC_SCK,
        inlet_valve_pwm_n       => INLET_VALVE_PWM_N,
        outlet_valve_pwm_n      => OUTLET_VALVE_PWM_N,
        pzt_valve_dac_sdi       => PZT_VALVE_DAC_SDI,
        heater_pwm_n            => HEATER_PWM_N,
        hot_box_pwm_n           => HOT_BOX_PWM_N,
        warm_box_pwm_n          => WARM_BOX_PWM_N,
        aux_din                 => AUX_DIN,
        monitor                 => MONITOR,
        wmm_rd                  => WMM_RD,
        wmm_convst              => WMM_CONVST,
        wmm_clk                 => WMM_CLK,
        sw1                     => SW1,
        sw2                     => SW2,
        sw3                     => SW3,
        sw4                     => SW4,
        lsr1_sck                => LSR1_SCK,
        lsr1_rd                 => LSR1_RD,
        lsr1_ss_n               => LSR1_SS_N,
        lsr1_mosi               => LSR1_MOSI,
        lsr1_disable            => LSR1_DISABLE,
        lsr2_sck                => LSR2_SCK,
        lsr2_rd                 => LSR2_RD,
        lsr2_ss_n               => LSR2_SS_N,
        lsr2_mosi               => LSR2_MOSI,
        lsr2_disable            => LSR2_DISABLE,
        lsr3_sck                => LSR3_SCK,
        lsr3_rd                 => LSR3_RD,
        lsr3_ss_n               => LSR3_SS_N,
        lsr3_mosi               => LSR3_MOSI,
        lsr3_disable            => LSR3_DISABLE,
        lsr4_sck                => LSR4_SCK,
        lsr4_rd                 => LSR4_RD,
        lsr4_ss_n               => LSR4_SS_N,
        lsr4_mosi               => LSR4_MOSI,
        lsr4_disable            => LSR4_DISABLE,
        aux_dout                => AUX_DOUT,
        warm_box_tec_overload_n => WARM_BOX_TEC_OVERLOAD_N,
        hot_box_tec_overload_n  => HOT_BOX_TEC_OVERLOAD_N,
        inlet_valve_comparator  => INLET_VALVE_COMPARATOR,
        outlet_valve_comparator => OUTLET_VALVE_COMPARATOR,
        wmm_refl1               => WMM_REFL1,
        wmm_refl2               => WMM_REFL2,
        wmm_tran1               => WMM_TRAN1,
        wmm_tran2               => WMM_TRAN2,
        wmm_busy1               => WMM_BUSY1,
        wmm_busy2               => WMM_BUSY2
    );

    top_block_inst : entity work.top_block(behavioral)
    port map (
       clk            => CLK50,
       reset          => reset,       -- Later connect this to a counter
       rd_adc         => unsigned(RD_ADC),
       rd_adc_clk     => RD_ADC_CLK,
       rd_adc_oe      => RD_ADC_OE,

       dsp_emif_we    => DSP_EMIF_WE,
       dsp_emif_re    => DSP_EMIF_RE,
       dsp_emif_oe    => DSP_EMIF_OE,
       dsp_emif_ardy  => DSP_EMIF_ARDY,

       dsp_emif_ea    => unsigned(DSP_EMIF_EA),
       dsp_emif_din   => DSP_EMIF_DIN,
       dsp_emif_dout  => unsigned(DSP_EMIF_DOUT),
       dsp_emif_ddir  => DSP_EMIF_DDIR,

       dsp_emif_be    => unsigned(DSP_EMIF_BE),
       dsp_emif_ce    => unsigned(DSP_EMIF_CE),

       usb_internal_connected  => USB_INTERNAL_CONNECTED,
       usb_rear_connected  => USB_REAR_CONNECTED,
       fpga_program_enable  => FPGA_PROGRAM_ENABLE,

       cyp_reset      => CYP_RESET,

       cyp_pc         => unsigned(CYP_PC),
       dsp_ext_int4   => DSP_EXT_INT4,
       dsp_ext_int5   => DSP_EXT_INT5,
       dsp_ext_int6   => DSP_EXT_INT6,
       dsp_ext_int7   => DSP_EXT_INT7,

       dsp_clkout2    => DSP_CLKOUT2,
       dsp_clkout3    => DSP_CLKOUT3,
       dsp_eclkout    => DSP_ECLKOUT,

       dsp_tinp0      => DSP_TINP0,
       dsp_tinp1      => DSP_TINP1,
       dsp_tout0      => DSP_TOUT0,
       dsp_tout1      => DSP_TOUT1,

       fp_lcd         => FP_LCD_U,
       fp_pb          => FP_PB,
       fp_rs_n        => FP_RS_N,
       fp_led         => FP_LED_U,

       aux_din        => AUX_DIN_U,
       aux_dout       => unsigned(AUX_DOUT),

       monitor        => MONITOR,

       lsr1_sck       => LSR1_SCK,
       lsr1_ss        => LSR1_SS,
       lsr1_rd        => LSR1_RD,
       lsr1_mosi      => LSR1_MOSI,
       lsr1_disable   => LSR1_DISABLE,

       lsr2_sck       => LSR2_SCK,
       lsr2_ss        => LSR2_SS,
       lsr2_rd        => LSR2_RD,
       lsr2_mosi      => LSR2_MOSI,
       lsr2_disable   => LSR2_DISABLE,

       lsr3_sck       => LSR3_SCK,
       lsr3_ss        => LSR3_SS,
       lsr3_rd        => LSR3_RD,
       lsr3_mosi      => LSR3_MOSI,
       lsr3_disable   => LSR3_DISABLE,

       lsr4_sck       => LSR4_SCK,
       lsr4_ss        => LSR4_SS,
       lsr4_rd        => LSR4_RD,
       lsr4_mosi      => LSR4_MOSI,
       lsr4_disable   => LSR4_DISABLE,

       wmm_refl1      => WMM_REFL1,
       wmm_refl2      => WMM_REFL2,
       wmm_tran1      => WMM_TRAN1,
       wmm_tran2      => WMM_TRAN2,
       wmm_busy1      => WMM_BUSY1,
       wmm_busy2      => WMM_BUSY2,
       wmm_rd         => WMM_RD,
       wmm_convst     => WMM_CONVST,
       wmm_clk        => WMM_CLK,

       sw1            => SW1,
       sw2            => SW2,
       sw3            => SW3,
       sw4            => SW4,

       lsr1_0         => LSR1_0,
       lsr1_1         => LSR1_1,
       lsr2_0         => LSR2_0,
       lsr2_1         => LSR2_1,
       lsr3_0         => LSR3_0,
       lsr3_1         => LSR3_1,
       lsr4_0         => LSR4_0,
       lsr4_1         => LSR4_1,

       lc1            => lc1,
       lc2            => lc2,
       lc3            => lc3,
       lc4            => lc4,

       intronix       => INTRONIX_U,
       fpga_led       => FPGA_LED_U,

       i2c_rst0       => I2C_RST0,
       i2c_rst1       => I2C_RST1,

       i2c_scl0       => I2C_SCL0,
       i2c_sda0       => I2C_SDA0,
       i2c_scl1       => I2C_SCL1,
       i2c_sda1       => I2C_SDA1,

       pzt_valve_dac_ld        => PZT_VALVE_DAC_LD,
       pzt_valve_dac_sck       => PZT_VALVE_DAC_SCK,
       pzt_valve_dac_sdi       => PZT_VALVE_DAC_SDI,

       inlet_valve_pwm         => INLET_VALVE_PWM,
       outlet_valve_pwm        => OUTLET_VALVE_PWM,
       inlet_valve_comparator  => INLET_VALVE_COMPARATOR,
       outlet_valve_comparator => OUTLET_VALVE_COMPARATOR,

       heater_pwm              => HEATER_PWM,
       hot_box_pwm             => HOT_BOX_PWM,
       hot_box_tec_overload    => HOT_BOX_TEC_OVERLOAD,
       warm_box_pwm            => WARM_BOX_PWM,
       warm_box_tec_overload   => WARM_BOX_TEC_OVERLOAD,

       dout_man                => DOUT_MAN,
       dout                    => DOUT,
       din                     => DIN
       );

    -- digital I/O lines
    
    BUFF_OUT            <= std_logic_vector(BUFF_OUT_U);
    BUFF_IN_U           <= unsigned(BUFF_IN);
    
    -- change logic polarity to fit hardware

    DSP_EMIF_WE         <= not DSP_EMIF_WE_N;
    DSP_EMIF_RE         <= not DSP_EMIF_RE_N;
    DSP_EMIF_OE         <= not DSP_EMIF_OE_N;
    RD_ADC_OE_N         <= not RD_ADC_OE;
    CYP_RESET_N         <= not CYP_RESET;
    DSP_EMIF_BE         <= not DSP_EMIF_BE_N;
    DSP_EMIF_CE         <= not DSP_EMIF_CE_N;
    FP_LCD              <= std_logic_vector(FP_LCD_U);
    FP_LED              <= std_logic_vector(FP_LED_U);
    AUX_DIN             <= AUX_DIN_U;
    LSR1_SS_N           <= not LSR1_SS;
    LSR2_SS_N           <= not LSR2_SS;
    LSR3_SS_N           <= not LSR3_SS;
    LSR4_SS_N           <= not LSR4_SS;
    -- permute MICTOR connections for Intronix channel numbers
    MICTOR(5)           <= std_logic(INTRONIX_U(33));
    MICTOR(6)           <= std_logic(INTRONIX_U(32));
    MICTOR(7)           <= std_logic(INTRONIX_U(31));
    MICTOR(8)           <= std_logic(INTRONIX_U(15));
    MICTOR(9)           <= std_logic(INTRONIX_U(30));
    MICTOR(10)          <= std_logic(INTRONIX_U(14));
    MICTOR(11)          <= std_logic(INTRONIX_U(29));
    MICTOR(12)          <= std_logic(INTRONIX_U(13));
    MICTOR(13)          <= std_logic(INTRONIX_U(28));
    MICTOR(14)          <= std_logic(INTRONIX_U(12));
    MICTOR(15)          <= std_logic(INTRONIX_U(27));
    MICTOR(16)          <= std_logic(INTRONIX_U(11));
    MICTOR(17)          <= std_logic(INTRONIX_U(26));
    MICTOR(18)          <= std_logic(INTRONIX_U(10));
    MICTOR(19)          <= std_logic(INTRONIX_U(25));
    MICTOR(20)          <= std_logic(INTRONIX_U(9));
    MICTOR(21)          <= std_logic(INTRONIX_U(24));
    MICTOR(22)          <= std_logic(INTRONIX_U(8));
    MICTOR(23)          <= std_logic(INTRONIX_U(23));
    MICTOR(24)          <= std_logic(INTRONIX_U(7));
    MICTOR(25)          <= std_logic(INTRONIX_U(22));
    MICTOR(26)          <= std_logic(INTRONIX_U(6));
    MICTOR(27)          <= std_logic(INTRONIX_U(21));
    MICTOR(28)          <= std_logic(INTRONIX_U(5));
    MICTOR(29)          <= std_logic(INTRONIX_U(20));
    MICTOR(30)          <= std_logic(INTRONIX_U(4));
    MICTOR(31)          <= std_logic(INTRONIX_U(19));
    MICTOR(32)          <= std_logic(INTRONIX_U(3));
    MICTOR(33)          <= std_logic(INTRONIX_U(18));
    MICTOR(34)          <= std_logic(INTRONIX_U(2));
    MICTOR(35)          <= std_logic(INTRONIX_U(17));
    MICTOR(36)          <= std_logic(INTRONIX_U(1));
    MICTOR(37)          <= std_logic(INTRONIX_U(16));
    MICTOR(38)          <= std_logic(INTRONIX_U(0));
    FPGA_LED            <= std_logic_vector(FPGA_LED_U);
    I2C_RST0_N          <= not I2C_RST0;
    I2C_RST1_N          <= not I2C_RST1;
    DSP_EMIF_DDIR_N     <= not DSP_EMIF_DDIR;

    -- Signals on high power board

    INLET_VALVE_PWM_N   <= not INLET_VALVE_PWM;
    OUTLET_VALVE_PWM_N  <= not OUTLET_VALVE_PWM;
    HEATER_PWM_N        <= not HEATER_PWM;
    HOT_BOX_PWM_N       <= not HOT_BOX_PWM;
    WARM_BOX_PWM_N      <= not WARM_BOX_PWM;
    HOT_BOX_TEC_OVERLOAD    <= not HOT_BOX_TEC_OVERLOAD_N;
    WARM_BOX_TEC_OVERLOAD   <= not WARM_BOX_TEC_OVERLOAD_N;

    -- instantiate the top level bidirectional io buffers

    DSP_EMIF_DBUFF:
        for i in 0 to 31 generate
        begin
            DSP_EMIF_DBUFF_INST : IOBUF
            generic map (
                drive => 12,
                iostandard => "default",
                slew => "fast")
                port map (
                    o  => DSP_EMIF_DOUT(i),    -- buffer output
                    io => DSP_EMIF_ED(i),      -- buffer inout port (connect directly to top-level port)
                    i  => DSP_EMIF_DIN(i),     -- buffer input
                    t  => DSP_EMIF_DDIR_N      -- 3-state enable input
                );
        end generate;

    -- reset is asserted for 65536 clock cycles at start

    RESET_LOGIC: process (CLK50) is
    begin
        if rising_edge(CLK50) then
            if not(reset_counter = "1111111111111111") then
                reset_counter <= (reset_counter + 1);
            end if;
        end if;
    end process RESET_LOGIC;

    reset <= '0' when reset_counter = "1111111111111111" else '1';

end behavioral;
