----------------------------------------------------------------------------------
-- Company:        Picarro, Inc
-- Engineer:       Sze Tan
--
-- Create Date:    04/29/2009
-- Design Name:
-- Module Name:    top_io_map - Behavioral
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
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity top_io_map is
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
           -- Buffered inputs/outputs
           BUFF_OUT         : out std_logic_vector(39 downto 0);
           BUFF_IN          : in std_logic_vector(63 downto 40);
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
           I2C_SDA1         : in std_logic
    );
end top_io_map;

architecture behavioral of top_io_map is

begin
    top_io_inst : entity work.top_io(behavioral)
    port map (
           CLK50            => CLK50,
           RD_ADC           => RD_ADC,
           RD_ADC_CLK       => RD_ADC_CLK,
           RD_ADC_OE_N      => RD_ADC_OE_N,
           USB_INTERNAL_CONNECTED => USB_INTERNAL_CONNECTED,
           USB_REAR_CONNECTED     => USB_REAR_CONNECTED,
           FPGA_PROGRAM_ENABLE    => FPGA_PROGRAM_ENABLE,
           CYP_RESET_N      => CYP_RESET_N,
           CYP_PC           => CYP_PC,
           DSP_EXT_INT4     => DSP_EXT_INT4,
           DSP_EXT_INT5     => DSP_EXT_INT5,
           DSP_EXT_INT6     => DSP_EXT_INT6,
           DSP_EXT_INT7     => DSP_EXT_INT7,
           DSP_CLKOUT2      => DSP_CLKOUT2,
           DSP_CLKOUT3      => DSP_CLKOUT3,
           DSP_ECLKOUT      => DSP_ECLKOUT,
           DSP_EMIF_EA      => DSP_EMIF_EA,
           DSP_EMIF_ED      => DSP_EMIF_ED,
           DSP_EMIF_BE_N    => DSP_EMIF_BE_N,
           DSP_EMIF_CE_N    => DSP_EMIF_CE_N,
           DSP_EMIF_WE_N    => DSP_EMIF_WE_N,
           DSP_EMIF_RE_N    => DSP_EMIF_RE_N,
           DSP_EMIF_OE_N    => DSP_EMIF_OE_N,
           DSP_EMIF_ARDY    => DSP_EMIF_ARDY,
           DSP_TINP0        => DSP_TINP0,
           DSP_TINP1        => DSP_TINP1,
           DSP_TOUT0        => DSP_TOUT0,
           DSP_TOUT1        => DSP_TOUT1,
           FP_LCD           => FP_LCD,
           FP_PB            => FP_PB,
           FP_RS_N          => FP_RS_N,
           FP_LED           => FP_LED,

           PZT_VALVE_DAC_LD      => BUFF_OUT(0),
           PZT_VALVE_DAC_SCK     => BUFF_OUT(1),
           INLET_VALVE_PWM_N     => BUFF_OUT(2),
           OUTLET_VALVE_PWM_N    => BUFF_OUT(3),
           PZT_VALVE_DAC_SDI     => BUFF_OUT(4),
           HEATER_PWM_N          => BUFF_OUT(5),
           HOT_BOX_PWM_N         => BUFF_OUT(6),
           WARM_BOX_PWM_N        => BUFF_OUT(7),
           
           WARM_BOX_TEC_OVERLOAD_N  => BUFF_IN(44),
           HOT_BOX_TEC_OVERLOAD_N   => BUFF_IN(45),
           INLET_VALVE_COMPARATOR   => BUFF_IN(48),
           OUTLET_VALVE_COMPARATOR  => BUFF_IN(49),

           AUX_DIN(3 downto 0)  => BUFF_OUT(11 downto 8),
           AUX_DOUT(3 downto 0) => BUFF_IN(43 downto 40),
           MONITOR          => BUFF_OUT(12),
           LSR1_SCK         => BUFF_OUT(20),
           LSR1_SS_N        => BUFF_OUT(22),
           LSR1_RD          => BUFF_OUT(21),
           LSR1_MOSI        => BUFF_OUT(23),
           LSR1_DISABLE     => BUFF_OUT(24),
           LSR2_SCK         => BUFF_OUT(25),
           LSR2_SS_N        => BUFF_OUT(27),
           LSR2_RD          => BUFF_OUT(26),
           LSR2_MOSI        => BUFF_OUT(28),
           LSR2_DISABLE     => BUFF_OUT(29),
           LSR3_SCK         => BUFF_OUT(30),
           LSR3_SS_N        => BUFF_OUT(32),
           LSR3_RD          => BUFF_OUT(31),
           LSR3_MOSI        => BUFF_OUT(33),
           LSR3_DISABLE     => BUFF_OUT(34),
           LSR4_SCK         => BUFF_OUT(35),
           LSR4_SS_N        => BUFF_OUT(37),
           LSR4_RD          => BUFF_OUT(36),
           LSR4_MOSI        => BUFF_OUT(38),
           LSR4_DISABLE     => BUFF_OUT(39),
           WMM_REFL1        => BUFF_IN(52),
           WMM_REFL2        => BUFF_IN(53),
           WMM_TRAN1        => BUFF_IN(54),
           WMM_TRAN2        => BUFF_IN(55),
           WMM_BUSY1        => BUFF_IN(56),
           WMM_BUSY2        => BUFF_IN(57),
           WMM_RD           => BUFF_OUT(13),
           WMM_CONVST       => BUFF_OUT(14),
           WMM_CLK          => BUFF_OUT(15),
           SW1              => BUFF_OUT(16),
           SW2              => BUFF_OUT(18),
           SW3              => BUFF_OUT(17),
           SW4              => BUFF_OUT(19),
           LSR1_0           => LSR1_0,
           LSR1_1           => LSR1_1,
           LSR2_0           => LSR2_0,
           LSR2_1           => LSR2_1,
           LSR3_0           => LSR3_0,
           LSR3_1           => LSR3_1,
           LSR4_0           => LSR4_0,
           LSR4_1           => LSR4_1,
           LC1              => LC1,
           LC2              => LC2,
           LC3              => LC3,
           LC4              => LC4,           
           MICTOR           => MICTOR,
           FPGA_LED         => FPGA_LED,
           I2C_RST0_N       => I2C_RST0_N,
           I2C_RST1_N       => I2C_RST1_N,
           I2C_SCL0         => I2C_SCL0,
           I2C_SDA0         => I2C_SDA0,
           I2C_SCL1         => I2C_SCL1,
           I2C_SDA1         => I2C_SDA1
    );

end behavioral;
