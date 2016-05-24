import numpy as np
from scipy.special import erf
from scipy.optimize import brentq

# Calculates parameters for ethane disposition block

def func(x, a, b, sigma):
    """ Calculate probability of measuring x in a measurement with uncertainty sigma when the actual ratio is
    uniformly distributed between a and b.
    """
    return (erf((x - a)/(np.sqrt(2)*sigma)) - erf((x-b)/(np.sqrt(2)*sigma)))/(2*(b-a))

def cum_norm(a, b, sigma):
    """ Calculate the probability that a Gaussian distributed random variable of zero mean and standard deviation
    sigma lies between a and b
    """
    return 0.5*(erf(b/(np.sqrt(2)*sigma)) - erf(a/(np.sqrt(2)*sigma)))

def find_positive_intervals(target_func, test_values):
    # Find the set of intervals in which the target_func is positive
    #
    # Returns list of lower_bounds and upper_bounds of the intervals
    # The target_func is evaluated on the collection of test_values
    #  to initially locate the positions of the zero crossings using
    #  Bolzano's theorem
    compare = target_func(test_values)
    # crossings1 are transitions from outside to inside the set
    # crossings2 are transitions from inside to outside the set
    crossings1 = np.flatnonzero((compare[:-1]<0) & (compare[1:]>0))
    crossings2 = np.flatnonzero((compare[:-1]>0) & (compare[1:]<0))
    # Convert indices to actual values
    lower_limits = [brentq(target_func, test_values[c1], test_values[c1+1]) for c1 in crossings1]
    upper_limits = [brentq(target_func, test_values[c2], test_values[c2+1]) for c2 in crossings2]
    assert len(lower_limits) == len(upper_limits), "Unexpected number of crossings, check test_values"
    # Sort limits into order and include type of limit
    limits = [(limit,1) for limit in lower_limits] + [(limit,2) for limit in upper_limits]
    limits.sort()
    # Prepend and append infinite limits if needed in order to start with a lower limit
    #  and end with an upper limit
    if limits and  limits[0][1] == 2:
        limits.insert(0, (-np.inf,1))
    if limits and  limits[-1][1] == 1:
        limits.append((np.inf,2))
    # Check that the limits interleave correctly
    intervals = []
    for low, high in zip(limits[::2], limits[1::2]):
        # Check that the limit types interleave correctly
        assert low[1] == 1 and high[1] == 2, "Unexpected limit type found"
        intervals.append((low[0], high[0]))
    return intervals

def calc_performance(sigma_list, ratio_list, a1, b1, a2, b2, p1, thresh, reg=1.0e-6):
    # Given a classification system based on the parameters
    # a1, b1: Range of ethane to methane ratios for classification as not natural gas,
    # a2, b2: Range of ethane to methane ratios for classification as natural gas,
    # p1: The prior probability of not natural gas,
    # T: The threshold posterior probability below which possible natural gas is reported,
    # reg: A regularization factor used to eliminate definite classification when the
    #       likelihoods of both hypotheses are small.
    #
    # Given a list of measurement uncertainties sigma_list and a list of ethane to methane
    #  ratios ratio_list, calculate the probability of classification as
    # possible natural gas: these are placed in result0
    # not natural gas: these are placed in result1
    # natural gas: these are placed in result2
    p2 = (1 - p1)
    result0 = []
    result1 = []
    result2 = []
    for sigma in sigma_list:
        test_ratios = np.linspace(a1-10*sigma, b2+10*sigma, 1000)
        def postprob1(ratio):
            y1 = func(ratio, a1, b1, sigma)
            y2 = func(ratio, a2, b2, sigma)
            return p1*y1/(p1*y1 + p2*y2 + reg)
        def postprob2(ratio):
            y1 = func(ratio, a1, b1, sigma)
            y2 = func(ratio, a2, b2, sigma)
            return p2*y2/(p1*y1 + p2*y2 + reg)
        # We want to find the set in which the target_func is positive, since these
        #  are the values of the ratio which get classified as the hypothesis with
        #  confidence exceeding thresh
        target_func = lambda r: postprob1(r) - thresh
        intervals = find_positive_intervals(target_func, test_ratios)
        prob1 = [sum(cum_norm(low-r,high-r,sigma) for low,high in intervals) for r in ratio_list]
        target_func = lambda r: postprob2(r) - thresh
        intervals = find_positive_intervals(target_func, test_ratios)
        prob2 = [sum(cum_norm(low-r,high-r,sigma) for low,high in intervals) for r in ratio_list]
        target_func = lambda r: (1.0 - postprob1(r) - postprob2(r)) - thresh
        intervals = find_positive_intervals(target_func, test_ratios)
        result1.append(np.asarray(prob1))
        result2.append(np.asarray(prob2))
    result1 = np.asarray(result1)
    result2 = np.asarray(result2)
    result0 = 1.0 - result1 - result2

    return result0, result1, result2

def get_float_def(prompt, default):
    reply = raw_input(prompt % default)
    return float(reply) if len(reply) > 0 else default

if __name__ == "__main__":
    print "Please enter following quantities as ratios and probabilities, NOT as percentages"
    a1 = get_float_def("Minimum ratio for not natural gas (a1 [%g]): ", 0.0)
    b1 = get_float_def("Maximum ratio for not natural gas (b1 [%g]): ", 0.001)
    a2 = get_float_def("Minimum ratio for natural gas (a2 [%g]): ", 0.02)
    b2 = get_float_def("Maximum ratio for natural gas (b2 [%g]): ", 0.1)
    thresh = get_float_def("Threshold confidence for definite verdict (thresh [%g]): ", 0.9)
    reg = get_float_def("Regularization constant (reg [%g]): ", 0.05)
    max_error_prob = get_float_def("Maximum allowed incorrect chassification probability for mixture with minimum ethane ratio (max_error_prob [%g]): ", 0.1)
    # Calculate the prior probability of not natural gas so that the probability of misclassifying
    #  natural gas of the minimum ethane content as not natural gas never exceeds "max_error_prob"
    sigma_list = np.logspace(-4, -1, 50)
    def target_func(p1):
        result0, result1, result2 = calc_performance(sigma_list, [a2], a1, b1, a2, b2, p1, thresh, reg)
        return max(result1)[0] - max_error_prob
    p1 = brentq(target_func, 0.001, 1.0-max_error_prob)
    print "Prior probability of not natural gas (p1): %.4f" % p1
