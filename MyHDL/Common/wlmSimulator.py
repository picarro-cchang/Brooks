from Host.autogen.interface import FPGA_REG_WIDTH
from MyHDL.Common.Divider import Divider
from math import atan, sqrt, ceil, floor, pi, sqrt

from myhdl import *

LOW, HIGH = bool(0), bool(1)
t_procState = enum("WAITING", "CALCULATING")
t_seqState  = enum("IDLE", "WAIT_PROC", "WAIT_DIV1", "WAIT_DIV2")

VHDL_CODE = \
"""
unsigned_mult18x18 : entity work.UnsignedMult18x18_e(Behavioral) 
    port map (
    A => %(a)s, B => %(b)s, P => %(p)s 
    );
"""
def Multiplier(p,a,b):
    # Multiplies a and b to yield p
    __vhdl__ = VHDL_CODE
    p.driven = "wire"

    @always_comb
    def logic():
        p.next = int(a)*int(b)
    return instances()

def WlmSimulator(clock,reset,start_in,rfac_in,z0_in,eta1_out,ref1_out,eta2_out,ref2_out,done_out):
    """ Simulation of wavelength monitor response using a model for the Fabry-Perot
         interferometer.
         
        rfac_in is a binary number less than unity which is related to the mirror reflectivity R 
           and finesse F by:
            rfac_in = 2*R/(1 + R**2) = F/(2 + F)
    """

    # angle input bit width
    W = len(z0_in)

    # angle input z0_in represents number between 0 and 2*pi
    # scaling factor corresponds to the nr of bits after the point
    M = 2**W
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

    mult_a = Signal(intbv(0)[18:])
    mult_b = Signal(intbv(0)[18:])
    mult_p = Signal(intbv(0)[36:])
    
    multiplier = Multiplier(p=mult_p,a=mult_a,b=mult_b)
    
    # tuple with elementary angles
    angles = tuple([int(round(M2*atan(2**(-i))/pi)) for i in range(N)])

    F = 1.2         # Finesse of etalon
    b = F/(F+2.0)     # Desired transmission is T = b/(1-b*cos(delta))
    num = int((1-b)*M)
    # calculate gain and initial radius to feed into resolver
    An = 1.0
    for i in range(N):
        An *= (sqrt(1.0 + 2**(-2*i)))
    scale = int(M2/An)    
    r0 = int(M2*b/An)
    
    divider = Divider(clk=clock, reset=reset, N_in=div_num, D_in=div_den, Q_out=div_quot,
                      rfd_out=div_rfd, ce_in=div_ce, width=W)
    
    # Sequencer using divider to compute photocurrents
    @instance
    def sequencer():
        state = t_seqState.IDLE
        while True:
            yield clock.posedge, reset.posedge
            div_ce.next = LOW
            div_num.next = M - rfac_in
            mult_a.next[18:2] = scale
            mult_b.next[18:2] = rfac_in - 1
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
                        div_den.next = xu
                        div_ce.next = HIGH
                        state = t_seqState.WAIT_DIV1
                elif state == t_seqState.WAIT_DIV1:
                    if div_rfd and not div_ce:
                        ref1_out.next = div_quot
                        eta1_out.next = M - div_quot
                        div_den.next = yu
                        div_ce.next = HIGH
                        state = t_seqState.WAIT_DIV2
                elif state == t_seqState.WAIT_DIV2:
                    if div_rfd and not div_ce:
                        ref2_out.next = div_quot
                        eta2_out.next = M - div_quot
                        done_out.next = HIGH
                        state = t_seqState.IDLE

    # iterative cordic processor
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
            yield clock.posedge, reset.posedge

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
                        x[:] = mult_p[36:20]
                        y[:] = 0
                        z[:] = z0_in[W-1:].signed()
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
                        if z0_in[W-1]^z0_in[W-2]:
                            xu.next = M2-x
                            yu.next = M2-y
                        else:
                            xu.next = M2+x
                            yu.next = M2+y
                        state = t_procState.WAITING
                        done.next = True
                    else:
                        i += 1

    return instances()
