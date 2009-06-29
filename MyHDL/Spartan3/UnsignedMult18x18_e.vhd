----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date:    15:26:18 22/01/2009 
-- Design Name: 
-- Module Name:    UnsignedMult18x18_e - Behavioral 
-- Project Name: 
-- Target Devices: 
-- Tool versions: 
-- Description:    Unsigned multiplier 18bit x 18bit => 36 bit product
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

library UNISIM;
use UNISIM.VComponents.all;

entity UnsignedMult18x18_e is
    port ( p          : out unsigned(35 downto 0);
           a          : in  unsigned(17 downto 0);
           b          : in  unsigned(17 downto 0));
end UnsignedMult18x18_e;

architecture Behavioral of UnsignedMult18x18_e is

signal p_v : std_logic_vector(35 downto 0);
signal a_v : std_logic_vector(17 downto 0);
signal b_v : std_logic_vector(17 downto 0);
begin
    MULT18X18_inst : MULT18X18
    port map (
        P => p_v,    -- 36-bit multiplier output
        A => a_v,    -- 18-bit multiplier input
        B => b_v     -- 18-bit multiplier input
    );
    p <= unsigned(p_v);
    a_v <= std_logic_vector(a);
    b_v <= std_logic_vector(b);
    
end Behavioral;
