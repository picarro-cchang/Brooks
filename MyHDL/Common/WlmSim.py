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
#   21-Jul-2009  sze  Initial version
#   24-Jul-2009  sze  Made WLM phase depend on laser current inputs
#   27-Jul-2009  sze  Swapped etalon channels so cosine is for etalon/ref 2 and sine is for etalon/ref1
#   28-Jul-2009  sze  Modification to compute ringdown loss as well
#   04-Oct-2009  sze  Added laser temperature register for simulator
#   06-Oct-2009  sze  Added intensity dependence on laser current and photocurrent offsets
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
from myhdl import *
from Host.autogen import interface
from Host.autogen.interface import EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH
from Host.autogen.interface import FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_WLMSIM

from Host.autogen.interface import WLMSIM_OPTIONS, WLMSIM_Z0
from Host.autogen.interface import WLMSIM_RFAC, WLMSIM_WFAC
from Host.autogen.interface import WLMSIM_LASER_TEMP
from Host.autogen.interface import WLMSIM_ETA1_OFFSET
from Host.autogen.interface import WLMSIM_REF1_OFFSET
from Host.autogen.interface import WLMSIM_ETA2_OFFSET
from Host.autogen.interface import WLMSIM_REF2_OFFSET

from Host.autogen.interface import WLMSIM_OPTIONS_INPUT_SEL_B, WLMSIM_OPTIONS_INPUT_SEL_W

from MyHDL.Common.Divider import Divider
from MyHDL.Common.UnsignedMultiplier import UnsignedMultiplier
from math import atan, sqrt, ceil, floor, pi, sqrt

LOW, HIGH = bool(0), bool(1)
t_procState = enum("WAITING", "CALCULATING")
t_seqState  = enum("IDLE", "WAIT_PROC1", "WAIT_PROC2", "WAIT_PROC3", "WAIT_PROC4", "WAIT_DIV1", "WAIT_DIV2", "WAIT_DIV3",
                   "WAIT_SCALE1", "WAIT_SCALE2", "WAIT_SCALE3", "WAIT_SCALE4")


def WlmSim(clk,reset,dsp_addr,dsp_data_out,dsp_data_in,dsp_wr,start_in,
           coarse_current_in,fine_current_in,eta1_out,ref1_out,eta2_out,
           ref2_out,loss_out,pzt_cen_out,done_out,map_base):
    """
    When OPTIONS_INPUT_SEL==1, simulate the output of the wavelength monitor when the specified coarse 
    and fine currents are applied to the laser and the laser temperature is specified. The WLM "phase" 
    is related to the currents and laser temp (in milli-C) by:

        phase = (2*pi/65536) * (5*coarse current + fine current + 18*laser_temp)
        
    The phase is stored in the variable z0 multiplied by 65536 to convert it to an integer. The phase may
    be read back from the WLMSIM_Z0 register. If OPTIONS_INPUT_SEL==0, the WLMSIM_Z0 register is used to
    specify the phase. In the latter case, the coarse and fine current inputs and the contents of the
    WLMSIM_LASER_TEMP register are ignored.
    
    The CORDIC algorithm (in the function process) takes the phase and computes its cosine in x and its
    sine in y. These are used to find xu = 1-rho*cos(phase) and yu=1-rho*sin(phase). The quantity rho is
    related to the reflectivity of the etalon. The register rfac contains 65536*rho.
    
    Etalon1 = rho*(1-sin(phase)) / (1-rho*sin(phase)) * Intensity + Etalon1_offset
    Reference1 = (1-rho) / (1-rho*sin(phase)) * Intensity + Reference1_offset
    
    Etalon2 = rho*(1-cos(phase)) / (1-rho*cos(phase)) * Intensity + Etalon2_offset
    Reference2 = (1-rho) / (1-rho*cos(phase)) * Intensity + Reference2_offset
    
    The offset values are taken from the registers and the intensity is a linear function of the
     total laser current
     
    Intensity = ((5/8)*(coarse current) + (1/8)*(fine current)) / 65536
    
    This block also calculates a loss using
    Loss = (1-w) / (1-w*cos(4*phase))
    where 65536*w is placed in the register wfac.
    
    The value of pzt_cen_out is set to -16*(5*coarse current + fine current + 18*laser_temp), where the negative sign is 
    necessary for compatibility with existing hardware. This is computed by shifting the angle for the loss computation by
    a further two bits.
    
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
    loss_out            -- loss at this frequency for ringdown simulator
    pzt_cen_out         -- pzt value at which ringdown occurs
    done_out            -- goes high once photocurrents are valid
    map_base

    Registers:
    WLMSIM_OPTIONS      -- options
    WLMSIM_Z0           -- angle input
    WLMSIM_RFAC         -- factor related to mirror reflectivity = 2*R/(1+R**2)
    WLMSIM_WFAC         -- factor specifying width of spectral feature
    WLMSIM_LASER_TEMP   -- simulator laser temperature in millidegrees Celsius
    WLMSIM_ETA1_OFFSET  -- etalon 1 (reflected) photocurrent offset
    WLMSIM_REF1_OFFSET  -- reference 1 (transmitted) photocurrent offset
    WLMSIM_ETA2_OFFSET  -- etalon 2 (reflected) photocurrent offset
    WLMSIM_REF2_OFFSET  -- reference 2 (transmitted) photocurrent offset

    Fields in WLMSIM_OPTIONS:
    WLMSIM_OPTIONS_INPUT_SEL -- selects angle input from register (0) or input port (1)
    """
    wlmsim_options_addr = map_base + WLMSIM_OPTIONS
    wlmsim_z0_addr = map_base + WLMSIM_Z0
    wlmsim_rfac_addr = map_base + WLMSIM_RFAC
    wlmsim_wfac_addr = map_base + WLMSIM_WFAC
    wlmsim_laser_temp_addr = map_base + WLMSIM_LASER_TEMP
    wlmsim_eta1_offset_addr = map_base + WLMSIM_ETA1_OFFSET
    wlmsim_ref1_offset_addr = map_base + WLMSIM_REF1_OFFSET
    wlmsim_eta2_offset_addr = map_base + WLMSIM_ETA2_OFFSET
    wlmsim_ref2_offset_addr = map_base + WLMSIM_REF2_OFFSET
    options = Signal(intbv(0)[1:])
    z0 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    rfac = Signal(intbv(0x8000)[FPGA_REG_WIDTH:])
    wfac = Signal(intbv(0xF800)[FPGA_REG_WIDTH:])
    laser_temp = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta1_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2_offset = Signal(intbv(0)[FPGA_REG_WIDTH:])

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
    start_cordic = Signal(LOW)
    zval = Signal(intbv(0)[FPGA_REG_WIDTH:])
    
    eta1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref1 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    eta2 = Signal(intbv(0)[FPGA_REG_WIDTH:])
    ref2 = Signal(intbv(0)[FPGA_REG_WIDTH:])

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
    scale = int(M2/An)    # This is the CORDIC factor which gives unit amplitude sine and cosine
    
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
                wfac.next = 0xF800
                laser_temp.next = 0
                eta1_offset.next = 0
                ref1_offset.next = 0
                eta2_offset.next = 0
                ref2_offset.next = 0
                zval.next = 0
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
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_wfac_addr: # rw
                        if dsp_wr: wfac.next = dsp_data_out
                        dsp_data_in.next = wfac
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_laser_temp_addr: # rw
                        if dsp_wr: laser_temp.next = dsp_data_out
                        dsp_data_in.next = laser_temp
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_eta1_offset_addr: # rw
                        if dsp_wr: eta1_offset.next = dsp_data_out
                        dsp_data_in.next = eta1_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_ref1_offset_addr: # rw
                        if dsp_wr: ref1_offset.next = dsp_data_out
                        dsp_data_in.next = ref1_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_eta2_offset_addr: # rw
                        if dsp_wr: eta2_offset.next = dsp_data_out
                        dsp_data_in.next = eta2_offset
                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == wlmsim_ref2_offset_addr: # rw
                        if dsp_wr: ref2_offset.next = dsp_data_out
                        dsp_data_in.next = ref2_offset
                    else:
                        dsp_data_in.next = 0
                else:
                    dsp_data_in.next = 0
                    
                div_ce.next = LOW
                if options[WLMSIM_OPTIONS_INPUT_SEL_B]:
                    z0.next = ((laser_temp << 4) + (laser_temp << 1) + (coarse_current_in << 2) + coarse_current_in + (fine_current_in)) % M
                # z0 now contains the angle, where 0 to 2*pi is represented by 0 to 65536
                    
                if reset:
                    state = t_seqState.IDLE
                    done_out.next = HIGH
                else:
                    if state == t_seqState.IDLE:
                        mult_a.next[17:1] = scale
                        div_num.next = M - rfac
                        mult_b.next[17:1] = rfac - 1
                        if start_in:
                            zval.next = z0
                            start_cordic.next = HIGH
                            state = t_seqState.WAIT_PROC1
                            done_out.next = LOW
                    elif state == t_seqState.WAIT_PROC1:
                        start_cordic.next = LOW
                        state = t_seqState.WAIT_PROC2
                    elif state == t_seqState.WAIT_PROC2: # Wait for first CORDIC computation of sin & cos for WLM                        
                        if done:
                            div_den.next = yu
                            div_ce.next = HIGH
                            state = t_seqState.WAIT_DIV1
                    elif state == t_seqState.WAIT_DIV1:  # Division for ref1 computation
                        if div_rfd and not div_ce:
                            ref1.next = div_quot
                            eta1.next = M - div_quot     # eta1 and ref1 sum to unity
                            div_den.next = xu
                            div_ce.next = HIGH
                            state = t_seqState.WAIT_DIV2
                    elif state == t_seqState.WAIT_DIV2:  # Division for ref2 computation
                        if div_rfd and not div_ce:
                            ref2.next = div_quot
                            eta2.next = M - div_quot     # eta2 and ref2 sum to unity
                            div_num.next = M - wfac
                            mult_b.next[17:1] = wfac - 1
                            zval.next = (zval << 2) % M
                            start_cordic.next = HIGH
                            state = t_seqState.WAIT_PROC3
                    elif state == t_seqState.WAIT_PROC3:
                        start_cordic.next = LOW
                        state = t_seqState.WAIT_PROC4
                    elif state == t_seqState.WAIT_PROC4: # Wait for second CORDIC computation of sin & cos for loss
                        if done:
                            div_den.next = xu
                            div_ce.next = HIGH
                            # Set up an "intensity" factor depending on the laser current to scale the photodiode outputs
                            mult_a.next[17:1] = ((coarse_current_in >> 1) + (coarse_current_in >> 3) + (fine_current_in >> 3)) % M
                            state = t_seqState.WAIT_DIV3
                    elif state == t_seqState.WAIT_DIV3:  # Division for loss computation
                        if div_rfd and not div_ce:
                            loss_out.next = div_quot
                            mult_b.next[17:1] = eta1
                            state = t_seqState.WAIT_SCALE1
                    elif state == t_seqState.WAIT_SCALE1:
                        eta1_out.next = mult_p[34:18] + eta1_offset
                        mult_b.next[17:1] = ref1
                        state = t_seqState.WAIT_SCALE2
                    elif state == t_seqState.WAIT_SCALE2:
                        ref1_out.next = mult_p[34:18] + ref1_offset
                        mult_b.next[17:1] = eta2
                        state = t_seqState.WAIT_SCALE3
                    elif state == t_seqState.WAIT_SCALE3:
                        eta2_out.next = mult_p[34:18] + eta2_offset
                        mult_b.next[17:1] = ref2
                        state = t_seqState.WAIT_SCALE4
                    elif state == t_seqState.WAIT_SCALE4:
                        ref2_out.next = mult_p[34:18] + ref2_offset
                        pzt_cen_out.next = (M - (zval << 2)) % M
                        done_out.next = HIGH
                        state = t_seqState.IDLE
                            
    # Iterative CORDIC processor for calculating 1-rho*cos(phi) and 1-rho*sin(phi) in xu and yu.
    #  The amplitude of the trigonometric term is multiplied by the CORDIC normalization term
    #  and is initially placed in mult_p
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
                    if start_cordic:
                        x[:] = mult_p[34:18]
                        y[:] = 0
                        z[:] = zval[W-1:].signed()
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
                        if zval[W-1] != zval[W-2]:
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
    loss_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    pzt_cen_out = Signal(intbv(0)[FPGA_REG_WIDTH:])
    done_out = Signal(LOW)
    map_base = FPGA_WLMSIM

    toVHDL(WlmSim, clk=clk, reset=reset, dsp_addr=dsp_addr,
                   dsp_data_out=dsp_data_out, dsp_data_in=dsp_data_in,
                   dsp_wr=dsp_wr, start_in=start_in,
                   coarse_current_in=coarse_current_in,
                   fine_current_in=fine_current_in, eta1_out=eta1_out,
                   ref1_out=ref1_out, eta2_out=eta2_out,
                   ref2_out=ref2_out, loss_out=loss_out,
                   pzt_cen_out=pzt_cen_out, done_out=done_out,
                   map_base=map_base)
