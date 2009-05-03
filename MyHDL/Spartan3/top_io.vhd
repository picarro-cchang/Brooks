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
           USB_CONNECTED    : in std_logic;
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
           -- High power board
           PWR_DIN          : out std_logic_vector(7 downto 0);
           PWR_DOUT         : in std_logic_vector(7 downto 0);
           -- Auxiliary board
           AUX_DIN          : out std_logic_vector(3 downto 0);
           AUX_DOUT         : in  std_logic_vector(3 downto 0);
           -- Monitor signal
           MONITOR          : out std_logic;
           -- Laser 1 board
           LSR1_SCK         : out std_logic;
           LSR1_SS_N        : out std_logic;
           LSR1_RD          : out std_logic;
           LSR1_MOSI        : out std_logic;
           LSR1_DISABLE     : out std_logic;
           -- Laser 2 board
           LSR2_SCK         : out std_logic;
           LSR2_SS_N        : out std_logic;
           LSR2_RD          : out std_logic;
           LSR2_MOSI        : out std_logic;
           LSR2_DISABLE     : out std_logic;
           -- Laser 3 board
           LSR3_SCK         : out std_logic;
           LSR3_SS_N        : out std_logic;
           LSR3_RD          : out std_logic;
           LSR3_MOSI        : out std_logic;
           LSR3_DISABLE     : out std_logic;
           -- Laser 4 board
           LSR4_SCK         : out std_logic;
           LSR4_SS_N        : out std_logic;
           LSR4_RD          : out std_logic;
           LSR4_MOSI        : out std_logic;
           LSR4_DISABLE     : out std_logic;
           -- Wavelength monitor board
           WMM_REFL1        : in std_logic;
           WMM_REFL2        : in std_logic;
           WMM_TRAN1        : in std_logic;
           WMM_TRAN2        : in std_logic;
           WMM_BUSY1        : in std_logic;
           WMM_BUSY2        : in std_logic;
           WMM_RD           : out std_logic;
           WMM_CONVST       : out std_logic;
           WMM_CLK          : out std_logic;
           -- SOA board
           SW1              : out std_logic;
           SW2              : out std_logic;
           SW3              : out std_logic;
           SW4              : out std_logic;
           -- Laser TEC PWM lines
           LSR1_0           : out std_logic;
           LSR1_1           : out std_logic;
           LSR2_0           : out std_logic;
           LSR2_1           : out std_logic;
           LSR3_0           : out std_logic;
           LSR3_1           : out std_logic;
           LSR4_0           : out std_logic;
           LSR4_1           : out std_logic;
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
           I2C_SDA1         : in std_logic
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

begin
    top_block_inst : entity work.top_block(behavioral)
    port map (
       clk            => CLK50,
       reset          => '0',       -- Later connect this to a counter
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

       usb_connected  => USB_CONNECTED,
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

       pwr_din        => PWR_DIN_U,
       pwr_dout       => unsigned(PWR_DOUT),

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

       intronix       => INTRONIX_U,
       fpga_led       => FPGA_LED_U,

       i2c_rst0       => I2C_RST0,
       i2c_rst1       => I2C_RST1,

       i2c_scl0       => I2C_SCL0,
       i2c_sda0       => I2C_SDA0,
       i2c_scl1       => I2C_SCL1,
       i2c_sda1       => I2C_SDA1
    );

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
    PWR_DIN             <= std_logic_vector(PWR_DIN_U);
    AUX_DIN             <= std_logic_vector(AUX_DIN_U);
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
end behavioral;
