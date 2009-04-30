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
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

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
           DSP_EMIF_BE      : in std_logic_vector(3 downto 0);
           -- DSP external memory chip enable
           DSP_EMIF_CE      : in std_logic_vector(3 downto 0);
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

begin
end behavioral;
