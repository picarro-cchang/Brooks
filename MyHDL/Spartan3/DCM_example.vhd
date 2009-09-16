--------------------------------------------------------------------------------
-- Copyright (c) 1995-2008 Xilinx, Inc.  All rights reserved.
--------------------------------------------------------------------------------
--   ____  ____ 
--  /   /\/   / 
-- /___/  \  /    Vendor: Xilinx 
-- \   \   \/     Version : 10.1.03
--  \   \         Application : xaw2vhdl
--  /   /         Filename : DCM_example.vhd
-- /___/   /\     Timestamp : 09/15/2009 18:01:05
-- \   \  /  \ 
--  \___\/\___\ 
--
--Command: xaw2vhdl-intstyle C:/work/CostReducedPlatform/Alpha/MyHDL/Spartan3/DCM_example.xaw -st DCM_example.vhd
--Design Name: DCM_example
--Device: xc3s1000-5ft256
--
-- Module DCM_example
-- Generated by Xilinx Architecture Wizard
-- Written for synthesis tool: XST
-- Period Jitter (unit interval) for block DCM_INST = 0.11 UI
-- Period Jitter (Peak-to-Peak) for block DCM_INST = 0.70 ns

library ieee;
use ieee.std_logic_1164.ALL;
use ieee.numeric_std.ALL;
library UNISIM;
use UNISIM.Vcomponents.ALL;

entity DCM_example is
   port ( CLKIN_IN     : in    std_logic; 
          RST_IN       : in    std_logic; 
          CLKFX_OUT    : out   std_logic; 
          CLKFX180_OUT : out   std_logic; 
          CLK0_OUT     : out   std_logic; 
          CLK180_OUT   : out   std_logic; 
          LOCKED_OUT   : out   std_logic);
end DCM_example;

architecture BEHAVIORAL of DCM_example is
   signal CLKFB_IN     : std_logic;
   signal CLKFX_BUF    : std_logic;
   signal CLKFX180_BUF : std_logic;
   signal CLK0_BUF     : std_logic;
   signal CLK180_BUF   : std_logic;
   signal GND_BIT      : std_logic;
begin
   GND_BIT <= '0';
   CLK0_OUT <= CLKFB_IN;
   CLKFX_BUFG_INST : BUFG
      port map (I=>CLKFX_BUF,
                O=>CLKFX_OUT);
   
   CLKFX180_BUFG_INST : BUFG
      port map (I=>CLKFX180_BUF,
                O=>CLKFX180_OUT);
   
   CLK0_BUFG_INST : BUFG
      port map (I=>CLK0_BUF,
                O=>CLKFB_IN);
   
   CLK180_BUFG_INST : BUFG
      port map (I=>CLK180_BUF,
                O=>CLK180_OUT);
   
   DCM_INST : DCM
   generic map( CLK_FEEDBACK => "1X",
            CLKDV_DIVIDE => 2.0,
            CLKFX_DIVIDE => 1,
            CLKFX_MULTIPLY => 3,
            CLKIN_DIVIDE_BY_2 => FALSE,
            CLKIN_PERIOD => 20.000,
            CLKOUT_PHASE_SHIFT => "NONE",
            DESKEW_ADJUST => "SYSTEM_SYNCHRONOUS",
            DFS_FREQUENCY_MODE => "LOW",
            DLL_FREQUENCY_MODE => "LOW",
            DUTY_CYCLE_CORRECTION => TRUE,
            FACTORY_JF => x"8080",
            PHASE_SHIFT => 0,
            STARTUP_WAIT => FALSE)
      port map (CLKFB=>CLKFB_IN,
                CLKIN=>CLKIN_IN,
                DSSEN=>GND_BIT,
                PSCLK=>GND_BIT,
                PSEN=>GND_BIT,
                PSINCDEC=>GND_BIT,
                RST=>RST_IN,
                CLKDV=>open,
                CLKFX=>CLKFX_BUF,
                CLKFX180=>CLKFX180_BUF,
                CLK0=>CLK0_BUF,
                CLK2X=>open,
                CLK2X180=>open,
                CLK90=>open,
                CLK180=>CLK180_BUF,
                CLK270=>open,
                LOCKED=>LOCKED_OUT,
                PSDONE=>open,
                STATUS=>open);
   
end BEHAVIORAL;


