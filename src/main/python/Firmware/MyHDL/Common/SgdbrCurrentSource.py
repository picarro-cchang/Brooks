#!/usr/bin/python
#
# FILE:
#   SgdbrCurrentSource.py
#
# DESCRIPTION:
#   Programmable logic code for accessing SGDBR current source board which
# allows for the control of five sources (front mirror, back mirror, SOA,
# gain and phase) and for the reading of a thermistor ADC. Communications
# take place through an SPI interface. This block provides two ways of
# accessing these resources, one is through writing a 32-bit number to the
# SGDBRCURRENTSOURCE_MOSI_DATA register, which initiates a transfer via the
# SPI interface. The SGDBRCURRENTSOURCE_CSR_DONE bit in the control status
# register goes high when the transfer is complete. Whenever a transfer takes
# place, the data from the slave (on the data_in line) are also assembled and
# placed in the SGDBRCURRENTSOURCE_MISO_DATA register.
#   The second way of writing to the current source board is referred to as
# making a synchronous update. A sync_strobe_in port is used to feed in a 100kHz
# pulse train with a 20ns wide pulse every 10us. When this is active, the values
# on the sync_current_in (16 bit) and sync_register_in (4 bit) ports are
# transferred via the SPI bus. This is intended for adjusting a current in a
# control loop where the updates need to occur on a precise schedule.
#   Synchronous updates take priority over transfers and a transfer is placed
# in the pending state if it is requested (by writing to the SGDBRCURRENTSOURCE_MOSI_DATA
# register) within a time window in which an update strobe pulse is expected
# to occur. After the synchronous update takes place within the window, the
# pending transfer takes place.
#   Synchronous updates need to be enabled by setting the SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B
# bit in the control status register. They should be disabled when performing
# time-critical SPI transfers, such as programming the Lattice FPGA.
#
# SEE ALSO:
#
# HISTORY:
#   03-Feb-2018  sze  Initial version.
#
#  Copyright (c) 2018 Picarro, Inc. All rights reserved
#
from myhdl import (Signal, always_comb, enum, instance, instances, intbv,
                   modbv, toVHDL)

from Host.autogen import interface
from Host.autogen.interface import (EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH,
                                    FPGA_REG_MASK, FPGA_REG_WIDTH,
                                    FPGA_SGDBRCURRENTSOURCE_A,
                                    SGDBRCURRENTSOURCE_CSR,
                                    SGDBRCURRENTSOURCE_CSR_CPHA_B,
                                    SGDBRCURRENTSOURCE_CSR_CPHA_W,
                                    SGDBRCURRENTSOURCE_CSR_CPOL_B,
                                    SGDBRCURRENTSOURCE_CSR_CPOL_W,
                                    SGDBRCURRENTSOURCE_CSR_DESELECT_B,
                                    SGDBRCURRENTSOURCE_CSR_DESELECT_W,
                                    SGDBRCURRENTSOURCE_CSR_DONE_B,
                                    SGDBRCURRENTSOURCE_CSR_DONE_W,
                                    SGDBRCURRENTSOURCE_CSR_MISO_B,
                                    SGDBRCURRENTSOURCE_CSR_MISO_W,
                                    SGDBRCURRENTSOURCE_CSR_RESET_B,
                                    SGDBRCURRENTSOURCE_CSR_RESET_W,
                                    SGDBRCURRENTSOURCE_CSR_SELECT_B,
                                    SGDBRCURRENTSOURCE_CSR_SELECT_W,
                                    SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B,
                                    SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_W,
                                    SGDBRCURRENTSOURCE_CSR_SUPPRESS_UPDATE_B, 
                                    SGDBRCURRENTSOURCE_CSR_SUPPRESS_UPDATE_W,
                                    SGDBRCURRENTSOURCE_MAX_SYNC_CURRENT,
                                    SGDBRCURRENTSOURCE_MISO_DATA,
                                    SGDBRCURRENTSOURCE_MISO_DELAY,
                                    SGDBRCURRENTSOURCE_MOSI_DATA,
                                    SGDBRCURRENTSOURCE_SYNC_REGISTER,
                                    SGDBRCURRENTSOURCE_SYNC_REGISTER_REG_SELECT_B,
                                    SGDBRCURRENTSOURCE_SYNC_REGISTER_REG_SELECT_W,
                                    SGDBRCURRENTSOURCE_SYNC_REGISTER_SOURCE_B,
                                    SGDBRCURRENTSOURCE_SYNC_REGISTER_SOURCE_W)

LOW, HIGH = bool(0), bool(1)


def SgdbrCurrentSource(clk, reset, dsp_addr, dsp_data_out, dsp_data_in,
                       dsp_wr, sck_out, csn_out, data_in,
                       sync_current_in, sync_register_in,
                       sync_strobe_in, data_out, resetn_out, done_out,
                       map_base):
    """
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    sck_out             -- SPI clock out
    csn_out             -- SPI chip select out (active low)
    data_in             -- MISO (data from slave)
    sync_current_in     -- 16-bit current value for synchronous updates
    sync_register_in    -- Specify which SPI register participates in synchronous updates
    sync_strobe_in      -- Single cycle strobe pulse to update current value
    data_out            -- MOSI (data to slave)
    resetn_out          -- reset output (active low) for programming Lattice FPGA
    done_out            -- goes high at end of transaction
    map_base

    Registers:
    SGDBRCURRENTSOURCE_CSR                  -- control/status register
    SGDBRCURRENTSOURCE_MISO_DELAY           -- delay (multiples of 10ns) to introduce when clocking in MISO data
    SGDBRCURRENTSOURCE_MOSI_DATA            -- data to send to slave (write initiates transaction)
    SGDBRCURRENTSOURCE_MISO_DATA            -- data received from slave
    SGDBRCURRENTSOURCE_SYNC_REGISTER        -- select current source for sync updates
    SGDBRCURRENTSOURCE_MAX_SYNC_CURRENT     -- maximum current for sync updates

    Fields in SGDBRCURRENTSOURCE_CSR:
    SGDBRCURRENTSOURCE_CSR_RESET            -- assert reset output
    SGDBRCURRENTSOURCE_CSR_SELECT           -- force assert SPI chip select out
    SGDBRCURRENTSOURCE_CSR_DESELECT         -- force deassert SPI chip select out
    SGDBRCURRENTSOURCE_CSR_CPOL             -- select SPI clock polarity
    SGDBRCURRENTSOURCE_CSR_CPHA             -- select SPI clock phase
    SGDBRCURRENTSOURCE_CSR_DONE             -- SPI transaction complete
    SGDBRCURRENTSOURCE_CSR_MISO             -- level of MISO input
    SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE      -- enable synchronous updates

    The following timing diagram shows mosi data being clocked out with num_of_clock_pulses
    set to 8 (http://wavedrom.com/editor.html)

    {signal: [
    {name: 'clk', wave: 'p......................'},
    {name: 'spi_active', wave:'01.................0...'},
    {name: 'sck_active', wave:'0.1...............0....'},
    {name: 'sck_phase', wave:'0.101010101010101010...'},
    {name: 'clock_counter', wave:'2..2.2.2.2.2.2.2.2.2...', data:['0','1','2','3','4','5','6','7','8','0']},
    {name: 'data_clk', wave:'0..1010101010101010....'},
    {name: 'csn', wave:'1.0................1...'},
    {name: 'mosi_data', wave:'x2..................x..', data:['42']},
    {name: 'data_out', wave:'0....1.0.......1.0.....'},

    ]}
    """
    t_EnumType = enum("NORMAL", "PENDING", "SYNC_UPDATE")
    sgdbrcurrentsource_csr_addr = map_base + SGDBRCURRENTSOURCE_CSR
    sgdbrcurrentsource_miso_delay_addr = map_base + SGDBRCURRENTSOURCE_MISO_DELAY
    sgdbrcurrentsource_mosi_data_addr = map_base + SGDBRCURRENTSOURCE_MOSI_DATA
    sgdbrcurrentsource_miso_data_addr = map_base + SGDBRCURRENTSOURCE_MISO_DATA
    sgdbrcurrentsource_sync_register_addr = map_base + SGDBRCURRENTSOURCE_SYNC_REGISTER
    sgdbrcurrentsource_max_sync_current_addr = map_base + \
        SGDBRCURRENTSOURCE_MAX_SYNC_CURRENT
    csr = Signal(intbv(0)[FPGA_REG_WIDTH:])
    miso_delay = Signal(intbv(0)[4:])
    mosi_data = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    miso_data = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    sync_register = Signal(intbv(0)[5:])
    max_sync_current = Signal(intbv(0)[FPGA_REG_WIDTH:])

    sck_divisor = 1     # 25 MHz SPI clock
    num_of_clock_pulses = 32

    sync_counter = Signal(modbv(0)[10:])
    clock_counter = Signal(modbv(0)[6:])
    sck_divider = Signal(modbv(0)[6:])
    sck_active = Signal(LOW)
    sck_phase = Signal(LOW)
    data_clk = Signal(LOW)
    spi_active = Signal(LOW)
    transfer_pending = Signal(LOW)
    csn = Signal(HIGH)
    miso_buff_a = Signal(modbv(0)[EMIF_DATA_WIDTH:])
    miso_buff_b = Signal(modbv(0)[EMIF_DATA_WIDTH:])
    mosi_buff = Signal(modbv(0)[EMIF_DATA_WIDTH:])

    max_delay = 16
    delay_sr_a = Signal(modbv(0)[max_delay // 2:])
    delay_sr_b = Signal(modbv(0)[max_delay // 2:])
    miso_shift = Signal(LOW)

    extra_active = Signal(LOW)
    extra_counter = Signal(intbv(0, min=0, max=max_delay // 2))
    edge_strobe = Signal(LOW)
    sync_strobe_prev = Signal(LOW)

    min_sync_counter_for_transfer = 100
    max_sync_counter_for_transfer = 400
    ok_to_transfer = Signal(LOW)
    access_type = Signal(t_EnumType.NORMAL)

    @always_comb
    def comb():
        sck_out.next = (csr[SGDBRCURRENTSOURCE_CSR_CPOL_B] != data_clk)
        csn_out.next = (csn and not csr[SGDBRCURRENTSOURCE_CSR_SELECT_B]) or csr[
            SGDBRCURRENTSOURCE_CSR_DESELECT_B]
        resetn_out.next = not csr[SGDBRCURRENTSOURCE_CSR_RESET_B]
        miso_shift.next = (spi_active and sck_divider == 0 and
                           ((clock_counter < num_of_clock_pulses and sck_phase and not csr[SGDBRCURRENTSOURCE_CSR_CPHA_B]) or
                            (clock_counter > 0 and not sck_phase and csr[SGDBRCURRENTSOURCE_CSR_CPHA_B])))
        ok_to_transfer.next = (
            sync_counter >= min_sync_counter_for_transfer and sync_counter <= max_sync_counter_for_transfer)

    @instance
    def half_steps():
        while True:
            yield clk.negedge, reset.posedge
            if reset:
                delay_sr_b.next = 0
                miso_buff_a.next = 0
            else:
                delay_sr_b.next[0] = miso_shift
                delay_sr_b.next[:1] = delay_sr_a[max_delay // 2 - 1:0]
                if delay_sr_a[miso_delay[:1]]:
                    miso_buff_a.next[:1] = miso_buff_a[len(miso_buff_a) - 1:0]
                    miso_buff_a.next[0] = data_in

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                csr.next = 0
                miso_delay.next = 0
                mosi_data.next = 0
                miso_data.next = 0
                sync_register.next = 0
                max_sync_current.next = 0
                clock_counter.next = 0
                sck_divider.next = 0
                sck_active.next = LOW
                sck_phase.next = LOW
                data_clk.next = LOW
                spi_active.next = LOW
                csn.next = HIGH
                miso_buff_b.next = 0
                done_out.next = LOW
                delay_sr_a.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH - 1] == FPGA_REG_MASK:
                    if False:
                        pass
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == sgdbrcurrentsource_csr_addr:  # rw
                        if dsp_wr:
                            csr.next = dsp_data_out
                        dsp_data_in.next = csr
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == sgdbrcurrentsource_miso_delay_addr:  # rw
                        if dsp_wr:
                            miso_delay.next = dsp_data_out
                        dsp_data_in.next = miso_delay
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == sgdbrcurrentsource_mosi_data_addr:  # rw
                        if dsp_wr:
                            mosi_data.next = dsp_data_out
                            csr.next[SGDBRCURRENTSOURCE_CSR_DONE_B] = LOW
                            done_out.next = LOW
                            if csr[SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B] and not ok_to_transfer:
                                access_type.next = t_EnumType.PENDING
                                transfer_pending.next = HIGH
                            elif not spi_active:
                                access_type.next = t_EnumType.NORMAL
                                mosi_buff.next = dsp_data_out
                                spi_active.next = HIGH
                                sck_phase.next = LOW
                                extra_active.next = LOW
                                miso_data.next = 0
                                sck_divider.next = 0
                        dsp_data_in.next = mosi_data
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == sgdbrcurrentsource_miso_data_addr:  # rw
                        if dsp_wr:
                            miso_data.next = dsp_data_out
                        dsp_data_in.next = miso_data
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == sgdbrcurrentsource_sync_register_addr:  # rw
                        if dsp_wr:
                            sync_register.next = dsp_data_out
                        dsp_data_in.next = sync_register
                    elif dsp_addr[EMIF_ADDR_WIDTH - 1:] == sgdbrcurrentsource_max_sync_current_addr:  # rw
                        if dsp_wr:
                            max_sync_current.next = dsp_data_out
                        dsp_data_in.next = max_sync_current
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0

                sync_strobe_prev.next = sync_strobe_in
                edge_strobe.next = sync_strobe_in and not sync_strobe_prev

                if edge_strobe:
                    sync_counter.next = 0
                else:
                    sync_counter.next = sync_counter + 1

                if transfer_pending and ok_to_transfer and not spi_active:
                    access_type.next = t_EnumType.PENDING
                    transfer_pending.next = LOW
                    csr.next[SGDBRCURRENTSOURCE_CSR_DONE_B] = LOW
                    done_out.next = LOW
                    mosi_buff.next = mosi_data
                    spi_active.next = HIGH
                    sck_phase.next = LOW
                    extra_active.next = LOW
                    # miso_data.next = 0
                    sck_divider.next = 0

                if edge_strobe and csr[SGDBRCURRENTSOURCE_CSR_SYNC_UPDATE_B] and not spi_active:
                    access_type.next = t_EnumType.SYNC_UPDATE
                    mosi_buff.next = 0
                    if sync_current_in < max_sync_current:
                        mosi_buff.next[16:] = sync_current_in
                    else:
                        mosi_buff.next[16:] = max_sync_current
                    if sync_register[SGDBRCURRENTSOURCE_SYNC_REGISTER_SOURCE_B]:
                        b = SGDBRCURRENTSOURCE_SYNC_REGISTER_REG_SELECT_B
                        w = SGDBRCURRENTSOURCE_SYNC_REGISTER_REG_SELECT_W
                        mosi_buff.next[27:24] = sync_register[b + w:b]
                    else:
                        mosi_buff.next[27:24] = sync_register_in
                    spi_active.next = HIGH
                    sck_phase.next = LOW
                    extra_active.next = LOW
                    sck_divider.next = 0

                delay_sr_a.next = delay_sr_b
                if delay_sr_b[miso_delay[:1]]:
                    miso_buff_b.next[:1] = miso_buff_b[len(miso_buff_b) - 1:0]
                    miso_buff_b.next[0] = data_in

                csr.next[SGDBRCURRENTSOURCE_CSR_MISO_B] = data_in
                if spi_active:
                    # Update the counters and dividers
                    if sck_divider + 1 < sck_divisor:
                        sck_divider.next = sck_divider + 1
                    else:
                        sck_divider.next = 0
                        sck_phase.next = not sck_phase
                        if sck_phase:
                            if clock_counter < num_of_clock_pulses:
                                clock_counter.next = clock_counter + 1
                            else:
                                clock_counter.next = 0
                                spi_active.next = LOW
                                if access_type != t_EnumType.SYNC_UPDATE:
                                    extra_active.next = HIGH
                                    extra_counter.next = 0

                    # Generate the SPI signals based on sck_divider,
                    # sck_phase and clock_counter
                    if sck_divider == 0:
                        data_clk.next = sck_phase and sck_active
                        if clock_counter < num_of_clock_pulses:
                            if sck_phase == csr[SGDBRCURRENTSOURCE_CSR_CPHA_B]:
                                data_out.next = mosi_buff[
                                    num_of_clock_pulses - clock_counter - 1]

                        if clock_counter == 0:
                            if not sck_phase:
                                csn.next = LOW
                                sck_active.next = HIGH
                        elif clock_counter == num_of_clock_pulses:
                            if not sck_phase:
                                sck_active.next = LOW
                            else:
                                csn.next = HIGH

                if extra_active:
                    if extra_counter == miso_delay[:1]:
                        extra_active.next = LOW
                        extra_counter.next = 0
                        if not transfer_pending:
                            csr.next[SGDBRCURRENTSOURCE_CSR_DONE_B] = HIGH
                            done_out.next = HIGH
                        if miso_delay[0]:
                            miso_data.next = miso_buff_a[num_of_clock_pulses:]
                        else:
                            miso_data.next = miso_buff_b[num_of_clock_pulses:]
                    else:
                        extra_counter.next = extra_counter + 1

    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    sck_out = Signal(LOW)
    csn_out = Signal(LOW)
    data_in = Signal(LOW)
    sync_current_in = Signal(intbv(0)[16:])
    sync_register_in = Signal(intbv(0)[4:])
    sync_strobe_in = Signal(LOW)
    data_out = Signal(LOW)
    resetn_out = Signal(LOW)
    done_out = Signal(LOW)
    map_base = FPGA_SGDBRCURRENTSOURCE_A

    toVHDL(SgdbrCurrentSource, clk=clk, reset=reset, dsp_addr=dsp_addr,
           dsp_data_out=dsp_data_out,
           dsp_data_in=dsp_data_in, dsp_wr=dsp_wr,
           sck_out=sck_out, csn_out=csn_out,
           data_in=data_in,
           sync_current_in=sync_current_in,
           sync_register_in=sync_register_in,
           sync_strobe_in=sync_strobe_in,
           data_out=data_out, resetn_out=resetn_out,
           done_out=done_out, map_base=map_base)
