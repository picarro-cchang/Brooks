from myhdl import *
from UnsignedMultiplier import UnsignedMultiplier

def linear_interpolator(y0, y1, beta, y_out):
    """
    Linearly interpolates between y0 and y1 depending upon the value of beta

    Inputs:
        y0: Value for output when beta is zero
        y1: Value for output when beta is one
        beta: A binary fraction (between zero and one)
        y_out: Output of interpolator
    """

    mult_a = Signal(intbv(0)[17:])
    mult_b = Signal(intbv(0)[17:])
    mult_p = Signal(intbv(0)[34:])
    multiplier = UnsignedMultiplier(p=mult_p,a=mult_a,b=mult_b)

    @always_comb
    def comb():
        mult_a.next[17:1] = beta
        if y1 >= y0:
            mult_b.next[17:1] = y1 - y0
            y_out.next = y0 + mult_p[34:18]
        else:
            mult_b.next[17:1] = y0 - y1
            y_out.next = y0 - mult_p[34:18]

    return instances()
