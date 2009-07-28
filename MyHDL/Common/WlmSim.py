#!/usr/bin/python
#
# FILE:
#   WlmSim.py
#
# DESCRIPTION:
#   Simulation of wavelength monitor. This involves calculating the analytic expressions for the
#    reflection and transmission of to quadrature Fabry-Perot etalons. The trigonometric functions 
#    are calculated using the CORDIC algorithm in fixed point format.
#
# SEE ALSO:
#
# HISTORY:
#   21-Jul-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_WLMSIM

from Host.autogen.interface import WLMSIM_OPTIONS, WLMSIM_Z0
from Host.autogen.interface import WLMSIM_RFAC, WLMSIM_ETA1
from Host.autogen.interface import WLMSIM_REF1, WLMSIM_ETA2, WLMSIM_REF2

from Host.autogen.interface import WLMSIM_OPTIONS_INPUT_SEL_B, WLMSIM_OPTIONS_INPUT_SEL_W

from MyHDL.Common.Divider import Divider
from MyHDL.Common.UnsignedMultiplier import UnsignedMultiplier
from math import atan, sqrt, ceil, floor, pi, sqrt

LOW, HIGH = bool(0), bool(1)
t_procState = enum("WAITING", "CALCULATING")
t_seqState  = enum("IDLE", "WAIT_PROC", "WAIT_DIV1", "WAIT_DIV2")


def WlmSim(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,start_in,
           coarse_current_in,fine_current_in,eta1_out,ref1_out,eta2_out,
           ref2_out,done_out,map_base):
    """
    Simulate the output of the wavelength monitor when the specified coarse and fine currents are
    applied to the laser. The  WLM angle coordinate is related to the currents by:

        angle = (2*pi/65536) * (5*coarse current + fine current/2)
    
    Parameters:
    clk                 -- Clock input
    reset               -- Reset input
    dsp_addr            -- address from dsp_interface block
    dsp_data_out        -- write data from dsp_interface block
    dsp_data_in         -- read data to dsp_interface_block
    dsp_wr              -- single-cycle write command from dsp_interface block
    start_in            -- raise to start calculation
    coarse_current_in   -- coarse laser current
    fine_current_in     -- fine laser current
    eta1_out            -- etalon 1 (reflected) photocurrent
    ref1_out            -- reference 1 (transmitted) photocurrent
    eta2_out            -- etalon 2 (reflected) photocurrent
    ref2_out            -- reference 2 (transmitted) photocurrent
    done_out            -- goes high once photocurrents are valid
    map_base

    Registers:
    WLMSIM_OPTIONS      -- options
    WLMSIM_Z0           -- angle input
    WLMSIM_RFAC         -- factor related to mirror reflectivity = 2*R/(1+R**2)
    WLMSIM_ETA1         -- etalon 1 (reflected) photocurrent
    WLMSIM_REF1         -- reference 1 (transmitted) photocurrent
    WLMSIM_ETA2         -- etalon 2 (reflected) photocurrent
    WLMSIM_REF2         -- reference 2 (transmitted) photocurrent

    Fields in WLMSIM_OPTIONS:
    WLMSIM_OPTIONS_INPUT_SEL -- selects angle input from register (0) or input port (1)
    """
    wlmsim_options_addr = map_base + WLMSIM_OPTIONS
    wlmsim_z0_addr = map_base + WLMSIM_Z0
    wlmsim_rfac_addr = map_base + WLMSIM_RFAC
    wlmsim_eta1_addr = map_base + WLMSIM_ETA1
    wlmsim_ref1_addr = map_base + WLMSIM_REF1
    wlmsim_eta2_addr = map_base + WLMSIM_ETA2
    wlmsim_ref2_addr = map_base + WLMSIM_REF2
    options = Signal(intbv(0)[1:])
    z0 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rfac = Signal(intbv(0x8000)[FPGA_REG_WIDTH:])
    eta1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2 = Signal(intbv(0)[FPGA_REG_WIDTH:])

    # angle input bit width
    W = FPGA_REG_WIDTH

    # angle input z0_in represents number between 0 and 2*pi
    # scaling factor corresponds to the nr of bits after the point
    M = 2**W
    Mmask = M-1
    M2 = M//2
    M4 = M//4
    
    # nr of iterations equals nr of significant input bits
    N = W-2

    xu = Signal(intbv(0,min=0,max=M))
    yu = Signal(intbv(0,min=0,max=M))
    div_num = Signal(intbv(0,min=0,max=M))
    div_den = Signal(intbv(0,min=0,max=M))
    div_quot = Signal(intbv(0,min=0,max=M))
    div_rfd = Signal(LOW)
    div_ce = Signal(LOW)
    done = Signal(LOW)

    mult_a = Signal(intbv(0)[17:])
    mult_b = Signal(intbv(0)[17:])
    mult_p = Signal(intbv(0)[34:])
    
    multiplier = UnsignedMultiplier(p=mult_p,a=mult_a,b=mult_b)
    
    # tuple with elementary angles
    angles = tuple([int(round(M2*atan(2**(-i))/pi)) for i in range(N)])

    # calculate gain and initial radius to feed into resolver
    An = 1.0
    for i in range(N):
        An *= (sqrt(1.0 + 2**(-2*i)))
    scale = int(M2/An)    
    
    divider = Divider(clk=clk, reset=reset, N_in=div_num, D_in=div_den, Q_out=div_quot,
                      rfd_out=div_rfd, ce_in=div_ce, width=W)
    
    @instance
    def logic():
        state = t_seqState.IDLE
        while True:
            yield clk.posedge, reset.posedge
            if reset:
                options.next = 0
                z0.next = 0
                rfac.next = 0x8000
                eta1.next = 0
                ref1.next = 0
                eta2.next = 0
                ref2.next = 0
            else:
                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:
                    if False: pass
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_options_addr: # rw
                        if dsp_wr: options.next = dsp_data_out
                        dsp_data_in.next = options
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_z0_addr: # rw
                        if dsp_wr: z0.next = dsp_data_out
                        dsp_data_in.next = z0
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_rfac_addr: # rw
                        if dsp_wr: rfac.next = dsp_data_out
                        dsp_data_in.next = rfac
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_eta1_addr: # r
                        dsp_data_in.next = eta1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_ref1_addr: # r
                        dsp_data_in.next = ref1
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_eta2_addr: # r
                        dsp_data_in.next = eta2
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_ref2_addr: # r
                        dsp_data_in.next = ref2
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                if options[WLMSIM_OPTIONS_INPUT_SEL_B]:
                    z0.next = ((coarse_current_in << 2) + coarse_current_in + (fine_current_in >> 1)) % M
                    
                div_ce.next = LOW
                div_num.next = M - rfac
                mult_a.next[17:1] = scale
                mult_b.next[17:1] = rfac - 1
                if reset:
                    state = t_seqState.IDLE
                    done_out.next = HIGH
                else:
                    if state == t_seqState.IDLE:
                        if start_in:
                            state = t_seqState.WAIT_PROC
                            done_out.next = LOW
                    elif state == t_seqState.WAIT_PROC:
                        if done:
                            div_den.next = yu
                            div_ce.next = HIGH
                            state = t_seqState.WAIT_DIV1
                    elif state == t_seqState.WAIT_DIV1:
                        if div_rfd and not div_ce:
                            ref1.next = div_quot
                            eta1.next = M - div_quot
                            div_den.next = xu
                            div_ce.next = HIGH
                            state = t_seqState.WAIT_DIV2
                    elif state == t_seqState.WAIT_DIV2:
                        if div_rfd and not div_ce:
                            ref2.next = div_quot
                            eta2.next = M - div_quot
                            done_out.next = HIGH
                            state = t_seqState.IDLE
                            eta1_out.next = eta1
                            ref1_out.next = ref1
                            eta2_out.next = eta2
                            ref2_out.next = ref2

    # iterative CORDIC processor
    @instance
    def processor():
        x = intbv(0, min=-M2, max=M2)
        y = intbv(0, min=-M2, max=M2)
        z = intbv(0, min=-M4, max=M4)
        dx = intbv(0, min=-M2, max=M2)
        dy = intbv(0, min=-M2, max=M2)
        dz = intbv(0, min=-M4, max=M4)
        i = intbv(0, min=0, max=N)
        state = t_procState.WAITING

        while True:
            yield clk.posedge, reset.posedge

            if reset:
                state = t_procState.WAITING
                xu.next = 0
                yu.next = 0
                done.next = False
                x[:] = 0
                y[:] = 0
                z[:] = 0
                i[:] = 0

            else:
                if state == t_procState.WAITING:
                    if start_in:
                        x[:] = mult_p[34:18]
                        y[:] = 0
                        z[:] = z0[W-1:].signed()
                        i[:] = 0
                        done.next = False
                        state = t_procState.CALCULATING

                elif state == t_procState.CALCULATING:
                    dx[:] = y >> i
                    dy[:] = x >> i
                    dz[:] = angles[int(i)]
                    if (z >= 0):
                        x -= dx
                        y += dy
                        z -= dz
                    else:
                        x += dx
                        y -= dy
                        z += dz
                    if i == N-1:
                        if z0[W-1] != z0[W-2]:
                            xu.next = M2 + x
                            yu.next = M2 + y
                        else:
                            xu.next = M2 - x
                            yu.next = M2 - y
                        state = t_procState.WAITING
                        done.next = True
                    else:
                        i += 1
                    
    return instances()

if __name__ == "__main__":
    clk = Signal(LOW)
    reset = Signal(LOW)
    dsp_addr = Signal(intbv(0)[EMIF_ADDR_WIDTH:])
    dsp_data_out = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_data_in = Signal(intbv(0)[EMIF_DATA_WIDTH:])
    dsp_wr = Signal(LOW)
    start_in = Signal(LOW)
    coarse_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    fine_current_in = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    done_out = Signal(LOW)
    map_base = FPGA_WLMSIM

    toVHDL(WlmSim, clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, start_in=start_in,
                   coarse_current_in=coarse_current_in,
                   fine_current_in=fine_current_in, eta1_out=eta1_out,
                   ref1_out=ref1_out, eta2_out=eta2_out,
                   ref2_out=ref2_out, done_out=done_out,
                   map_base=map_base)
