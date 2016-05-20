----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date:    16:26:18 06/24/2008 
-- Design Name: 
-- Module Name:    DualPortRamRw_e - Behavioral 
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
--library UNISIM;
--use UNISIM.VComponents.all;

entity DualPortRamRw_e is
    generic (ADDR_WIDTH:natural := 13;
             DATA_WIDTH:natural := 18);
    port ( clockA     : in std_logic;
           enableA    : in std_logic;
           wr_enableA : in std_logic;
           addressA   : in unsigned (ADDR_WIDTH-1 downto 0);
           rd_dataA   : out unsigned (DATA_WIDTH-1 downto 0);
           wr_dataA   : in unsigned (DATA_WIDTH-1 downto 0);
           clockB     : in std_logic;
           enableB    : in std_logic;
           wr_enableB : in std_logic;
           addressB   : in unsigned (ADDR_WIDTH-1 downto 0);
           rd_dataB   : out unsigned (DATA_WIDTH-1 downto 0);
           wr_dataB   : in unsigned (DATA_WIDTH-1 downto 0));
end DualPortRamRw_e;

architecture Behavioral of DualPortRamRw_e is

type ram_type is array (2**ADDR_WIDTH-1 downto 0) of unsigned (DATA_WIDTH-1 downto 0);
shared variable ram: ram_type;

begin
    process (clockA)
    begin
        if (clockA'event and clockA = '1') then
            if (enableA = '1') then
                if (wr_enableA = '1') then
                    ram(to_integer(addressA)) := wr_dataA;
                end if;
                rd_dataA <= ram(to_integer(addressA));
            end if;
        end if;
    end process;

    process (clockB)
    begin
        if (clockB'event and clockB = '1') then
            if (enableB = '1') then
                if (wr_enableB = '1') then
                    ram(to_integer(addressB)) := wr_dataB;
                end if;
                rd_dataB <= ram(to_integer(addressB));
            end if;
        end if;
    end process;
end Behavioral;
