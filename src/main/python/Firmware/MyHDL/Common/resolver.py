from math import atan, sqrt, ceil, floor, pi

from myhdl import *

t_State = enum("WAITING", "CALCULATING")

def Resolver(x0, y0, done, r0, z0, start, clock, reset):

    """ Polar to rectangular computer.

    This module computes rectangular coordinates of a point specified
    in polar coordinates. The floating point numbers are represented as 
    integers by scaling them up with a factor corresponding to the number 
    of bits after the point.

    Ports:
    -----
    x0: x coordinate of point
    y0: y coordinate of point
    done: output flag indicated completion of the computation
    r0: distance from origin, scaled by gain term
    z0: input angle expressed as an unsigned in the range 0 through (M-1)
        where M represents an angle of 2*pi
    start: input that starts the computation on a posedge
    clock: clock input
    reset: reset input
    """
    # angle input bit width
    W = len(z0)

    # angle input z0 represents number between 0 and 2*pi
    # scaling factor corresponds to the nr of bits after the point
    M = 2 ** (W-1)
    zMin = -M//2
    zMax = M//2 - 1

    # nr of iterations equals nr of significant input bits
    N = W-2

    # calculate gain
    #An = 1.0
    #for i in range(N):
    #    An *= (sqrt(1.0 + 2**(-2*i)))
    #print "Gain = %f" % (An,)
        
    # tuple with elementary angles
    angles = tuple([int(round(M*atan(2**(-i))/pi)) for i in range(N)])

    # iterative cordic processor
    @instance
    def processor():

        x = intbv(0, min=y0.min, max=y0.max)
        y = intbv(0, min=y0.min, max=y0.max)
        z = intbv(0, min=zMin, max=zMax)
        dx = intbv(0, min=y0.min, max=y0.max)
        dy = intbv(0, min=y0.min, max=y0.max)
        dz = intbv(0, min=zMin, max=zMax)
        i = intbv(0, min=0, max=N)
        state = t_State.WAITING

        while True:
            yield clock.posedge, reset.posedge

            if reset:
                state = t_State.WAITING
                x0.next = 1
                y0.next = 0
                done.next = False
                x[:] = 0
                y[:] = 0
                z[:] = 0
                i[:] = 0

            else:
                if state == t_State.WAITING:
                    if start:
                        x[:] = r0
                        y[:] = 0
                        z[:] = z0[W-1:].signed()
                        i[:] = 0
                        done.next = False
                        state = t_State.CALCULATING

                elif state == t_State.CALCULATING:
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
                        if z0[W-1]^z0[W-2]:
                            x0.next = -x
                            y0.next = -y
                        else:
                            x0.next = x
                            y0.next = y
                        state = t_State.WAITING
                        done.next = True
                    else:
                        i += 1

    return processor
