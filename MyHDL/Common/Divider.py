#!/usr/bin/python
#
# FILE:
#   Divider.py
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   02-Jul-2008  sze  Initial version.
#
#  Copyright (c) 2008 Picarro, Inc. All rights reserved
#
from myhdl import *

LOW, HIGH = bool(0), bool(1)

def Divider(clk,reset,N_in,D_in,Q_out,rfd_out,ce_in,width):
    """ divider divides N by D to give Q.

    N_in  -- numerator (dividend)
    D_in  -- denominator (divisor). D must be strictly greater than N/2.
    Q_out -- quotient. Binary point in the quotient appears after the MSB of Q,
            so that the largest quotient is binary 1.111111...
    rfd_out -- ready for data. When high, and ce_in is asserted, data are latched on
            the rising edge of the clock.
    ce_in -- clock enable. If low, rfd stays high at end of division and a new
            division is not started.
    reset -- asynchronous reset
    width -- size of N_in, D_in and Q_out.
    """
    Nreg  = Signal(intbv(0)[width+1:])
    Dreg  = Signal(intbv(0)[width:])
    Qreg  = Signal(intbv(0)[width:])
    rfd   = Signal(LOW)
    done  = Signal(LOW)
    i_width = len(intbv(min=0,max=width))
    i     = Signal(intbv(0)[i_width:])

    @instance
    def logic():
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                rfd.next = HIGH
                rfd_out.next = HIGH
                Nreg.next = 0
                Dreg.next = 0
                Qreg.next = 0
                Q_out.next = 0
                done.next = LOW
                i.next = width-1
            else:
                if done:
                    Q_out.next = Qreg
                    rfd.next = HIGH
                    rfd_out.next = HIGH
                    done.next = LOW
                elif rfd and ce_in:
                    Nreg.next = N_in
                    Dreg.next = D_in
                    rfd.next = LOW
                    rfd_out.next = LOW
                    i.next = width-1
                    done.next = LOW
                elif not rfd:
                    if Nreg>=Dreg:
                        Qreg.next[int(i)] = 1
                        Nreg.next = (Nreg-Dreg) << 1
                    else:
                        Qreg.next[int(i)] = 0
                        Nreg.next = Nreg << 1
                    if i == 0:
                        done.next = HIGH
                        i.next = width-1
                    else:
                        i.next = i-1
    return logic
