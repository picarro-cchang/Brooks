#!/usr/bin/python
#
# FILE:
#   SimpleSPI.py
#
# DESCRIPTION:
#   Driver for a simple SPI bus. This version sends data to the slave on demand
#    whenever the processor writes to the MOSI_DATA register in this block. A
#    specified number of SPI clock pulses are sent at a frequency which is derived
#    by dividing the 100MHz system clock. The data read from the slave is placed in
#    the MISO_DATA register.
#
#  The MISO_DATA register is cleared immediately after MOSI_DATA is written, and the
#   value from the shift register is transferred into MISO_DATA only after completion
#   of the serial data transaction
#
# SEE ALSO:
#
# HISTORY:
#   04-Nov-2017  sze  Initial version.
#
#  Copyright (c) 2017 Picarro, Inc. All rights reserved
#
from myhdl import (always, always_comb, always_seq, delay, instance, instances, intbv,
                   modbv, ResetSignal, Signal, Simulation, StopSimulation, toVerilog,
                   traceSignals)
from Host.autogen import interface
from Host.autogen.interface import PL_ADDR_WIDTH, PL_DATA_WIDTH
from Host.autogen.interface import PL_REG_WIDTH, PL_SIMPLESPI

from Host.autogen.interface import SIMPLESPI_SCK_DIVISOR
from Host.autogen.interface import SIMPLESPI_NUM_OF_CLOCK_PULSES
from Host.autogen.interface import SIMPLESPI_MOSI_DATA
from Host.autogen.interface import SIMPLESPI_MISO_DATA


LOW, HIGH = bool(0), bool(1)


def SimpleSPI(clk, resetn, waddr, wdata, wstrobe, wen, raddr, rdata,
              sck_out, csn_out, data_in, data_out, map_base):
    """
    Parameters:
    <Write descriptions of ports as comments>
    Parameters:
    clk                 -- Clock input
    resetn              -- Reset input (active low)
    waddr               -- processor write address
    wdata               -- write data (from processor)
    wstrobe             -- write strobe
    wen                 -- write enable
    raddr               -- processor read address
    rdata               -- read data (to processor)
    sck_out             -- SPI clock output
    csn_out             -- SPI CS output (active low)
    data_in             -- SPI data from slave
    data_out            -- SPI data to slave
    map_base

    Registers:
    <Write descriptions of registers as comments>
    SIMPLESPI_SCK_DIVISOR           -- Divisor from 50MHz frequency used to derive SPI clock
    SIMPLESPI_NUM_OF_CLOCK_PULSES   -- Number of SPI clock pulses to generate
    SIMPLESPI_MOSI_DATA             -- Data to be written to slave. Writing to this register starts the transfer
    SIMPLESPI_MISO_DATA             -- Data read from the slave
    """

    # Addresses of registers in block (in units of 4 bytes)
    simplespi_sck_divisor_addr = map_base + SIMPLESPI_SCK_DIVISOR
    simplespi_num_of_clock_pulses_addr = map_base + SIMPLESPI_NUM_OF_CLOCK_PULSES
    simplespi_mosi_data_addr = map_base + SIMPLESPI_MOSI_DATA
    simplespi_miso_data_addr = map_base + SIMPLESPI_MISO_DATA
    # Signals representing registers
    sck_divisor = Signal(modbv(0)[16:])
    num_of_clock_pulses = Signal(modbv(0)[6:])
    mosi_data = Signal(modbv(0)[PL_REG_WIDTH:])
    miso_data = Signal(modbv(0)[PL_REG_WIDTH:])

    clock_counter = Signal(modbv(0)[len(num_of_clock_pulses):])
    sck_divider = Signal(modbv(0)[len(sck_divisor):])
    sck_active = Signal(LOW)
    data_clk = Signal(LOW)
    transfer_active = Signal(LOW)
    csn = Signal(HIGH)
    miso_buff = Signal(modbv(0)[PL_REG_WIDTH:])

    @always_comb
    def comb():
        # Read access of registers
        rdata.next = 0
        if raddr == simplespi_sck_divisor_addr:
            rdata.next = sck_divisor
        elif raddr == simplespi_num_of_clock_pulses_addr:
            rdata.next = num_of_clock_pulses
        elif raddr == simplespi_mosi_data_addr:
            rdata.next = mosi_data
        elif raddr == simplespi_miso_data_addr:
            rdata.next = miso_data
        sck_out.next = data_clk
        csn_out.next = csn

    @always_seq(clk.posedge, reset=resetn)
    def logic():
        # Write access of registers
        if wen:
            if waddr == simplespi_sck_divisor_addr:
                for byte_index in range((PL_REG_WIDTH + 7) // 8):
                    if wstrobe[byte_index]:
                        for bit_index in range(8):
                            bit = 8 * byte_index + bit_index
                            if bit < len(sck_divisor):
                                sck_divisor.next[bit] = wdata[bit]
            elif waddr == simplespi_num_of_clock_pulses_addr:
                for byte_index in range((PL_REG_WIDTH + 7) // 8):
                    if wstrobe[byte_index]:
                        for bit_index in range(8):
                            bit = 8 * byte_index + bit_index
                            if bit < len(num_of_clock_pulses):
                                num_of_clock_pulses.next[bit] = wdata[bit]
            elif waddr == simplespi_mosi_data_addr:
                for byte_index in range((PL_REG_WIDTH + 7) // 8):
                    if wstrobe[byte_index]:
                        for bit_index in range(8):
                            bit = 8 * byte_index + bit_index
                            if bit < len(mosi_data):
                                mosi_data.next[bit] = wdata[bit]
                if not transfer_active:
                    transfer_active.next = HIGH
                    miso_data.next = 0
                    miso_buff.next = 0
            elif waddr == simplespi_miso_data_addr:
                for byte_index in range((PL_REG_WIDTH + 7) // 8):
                    if wstrobe[byte_index]:
                        for bit_index in range(8):
                            bit = 8 * byte_index + bit_index
                            if bit < len(miso_data):
                                miso_data.next[bit] = wdata[bit]

        if transfer_active:
            sck_active.next = HIGH
            csn.next = LOW
            if sck_divider + 1 < sck_divisor:
                sck_divider.next = sck_divider + 1
            else:
                sck_divider.next = 0
                latch_data = sck_active and not data_clk
                if latch_data:
                    miso_buff.next[:1] = miso_buff[len(miso_buff) - 1:0]
                    miso_buff.next[0] = data_in
                data_clk.next = latch_data
                if data_clk:
                    if clock_counter + 1 < num_of_clock_pulses:
                        clock_counter.next = clock_counter + 1
                    else:
                        miso_data.next = miso_buff
                        clock_counter.next = 0
                        sck_active.next = LOW
                        transfer_active.next = LOW
                        csn.next = HIGH

        if sck_active and clock_counter < num_of_clock_pulses:
            data_out.next = mosi_data[num_of_clock_pulses - clock_counter - 1]
        else:
            data_out.next = LOW

    return instances()

if __name__ == "__main__":
    # Define signals for block ports
    clk = Signal(LOW)
    resetn = ResetSignal(0, active=0, async=True)
    waddr = Signal(modbv(0)[PL_ADDR_WIDTH:])
    wdata = Signal(modbv(0)[PL_DATA_WIDTH:])
    wstrobe = Signal(modbv(0)[4:])
    wen = Signal(LOW)
    raddr = Signal(modbv(0)[PL_ADDR_WIDTH:])
    rdata = Signal(modbv(0)[PL_DATA_WIDTH:])
    sck_out = Signal(LOW)
    csn_out = Signal(LOW)
    data_in = Signal(LOW)
    data_out = Signal(LOW)
    map_base = PL_SIMPLESPI

    toVerilog(SimpleSPI, clk=clk, resetn=resetn, waddr=waddr,
              wdata=wdata, wstrobe=wstrobe, wen=wen,
              raddr=raddr, rdata=rdata, sck_out=sck_out,
              csn_out=csn_out, data_in=data_in,
              data_out=data_out, map_base=map_base)
