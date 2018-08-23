import numpy as np
from scipy.special import erf
from scipy.optimize import brentq
from CalculateParameters import calc_performance

def make_html(sigmas, ethane_ratios, table):
    result = ["<table>"]
    # Make the heading row
    result.append("<tr>")
    if len(sigmas)>0:
        result.append("<th></th>")
    for ethane_ratio in ethane_ratios:
        result.append('<th style="background-color:#c0c0c0"> %.1f%% </th>' % (100.0*ethane_ratio,))
    result.append("</tr>")
    for i,row in enumerate(table):
        result.append("<tr>")
        if len(sigmas)>0:
            result.append('<th style="background-color:#c0c0c0"> %.2f%% </th>' % (100.0*sigmas[i],))
        for col in row:
            style = ''
            if col >= 0.95:
                style = 'style="background-color:#f0f080"'
            elif col <= 0.05:
                style = 'style="background-color:#c0c0f0"'
            result.append("<td %s> %.1f%% </td>" % (style,100.0*col))
        result.append("</tr>")
    result.append("</table>")
    return "\n".join(result)

if __name__ == "__main__":
    ethane_ratios = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
    output = ["<head>", "<style>", "table {", "    border-collapse: collapse;",
              "}", "table, th, td {", "    border: 1px solid black;", "}", "</style>",
              "</head>", "<body>"]
    a1 = 0.0; b1 = 0.1e-2;
    thresh=0.9; reg=0.05
    # Set maximum permitted value for the probability of incorrectly classifying a mixture
    #  having the minimum value of ethane to methane ratio specified as "not natural gas"
    max_error_prob = 0.1
    output.append("<h1>Common parameter values</h1>")
    output.append("<div>")
    output.append("a1 = %g<br/>" % a1)
    output.append("b1 = %g<br/>" % b1)
    output.append("thresh = %g<br/>" % thresh)
    output.append("reg = %g<br/>" % reg)
    output.append("max_error_prob = %g<br/>" % max_error_prob)
    output.append("</div>")

    N = len(ethane_ratios)
    for i in reversed(range(1,N)):
        high_ethane = ethane_ratios[i]
        print "Calculating tables for maximum ethane to methane ratio of %g%%" % (100.0 * high_ethane, )
        zero_ethane_nng_table = []
        zero_ethane_png_table = []
        zero_ethane_ng_table = []
        min_ethane_nng_table = []
        min_ethane_png_table = []
        min_ethane_ng_table = []
        nng_prior_prob = []
        output.append('<h1>Maximum ethane ratio: %.1f%%</h1>' % (100.0*high_ethane,))
        for j in range(i):
            low_ethane = ethane_ratios[j]
            a2 = low_ethane; b2 = high_ethane;
            # Calculate the prior probability of not natural gas so that the probability of misclassifying
            #  natural gas of the minimum ethane content as not natural gas never exceeds "max_error_prob"
            sigma_list = np.logspace(-4, -1, 50)
            def target_func(p1):
                result0, result1, result2 = calc_performance(sigma_list, [low_ethane], a1, b1, a2, b2, p1, thresh, reg)
                return max(result1)[0] - max_error_prob
            p1 = brentq(target_func, 0.001, 1.0-max_error_prob)
            nng_prior_prob.append(p1)
            #
            display_sigma_list = np.logspace(-3.0,-1.0,13)
            # For each set of parameters, insert pure methane, and a mixture having the minimal ethane content
            result0, result1, result2 = calc_performance(display_sigma_list, [0.0, low_ethane], a1, b1, a2, b2, p1, thresh, reg)
            zero_ethane_png_table.append(result0[:,0])
            zero_ethane_nng_table.append(result1[:,0])
            zero_ethane_ng_table.append(result2[:,0])
            min_ethane_png_table.append(result0[:,1])
            min_ethane_nng_table.append(result1[:,1])
            min_ethane_ng_table.append(result2[:,1])

        output.append('<h2>Prior probabilities of "not natural gas"</h2>')
        output.append(make_html([],ethane_ratios[:i],[nng_prior_prob]))
        output.append('<h2>Ethane-free gas, Probability of classification as "Not Natural Gas"</h2>')
        output.append(make_html(display_sigma_list,ethane_ratios[:i],np.transpose(np.vstack(zero_ethane_nng_table))))
        output.append('<h2>Ethane-free gas, Probability of classification as "Natural Gas"</h2>')
        output.append(make_html(display_sigma_list,ethane_ratios[:i],np.transpose(np.vstack(zero_ethane_ng_table))))
        output.append('<h2>Gas of minimum ethane concentration, Probability of classification as "Not Natural Gas"</h2>')
        output.append(make_html(display_sigma_list,ethane_ratios[:i],np.transpose(np.vstack(min_ethane_nng_table))))
        output.append('<h2>Gas of minimum ethane concentration, Probability of classification as "Natural Gas"</h2>')
        output.append(make_html(display_sigma_list,ethane_ratios[:i],np.transpose(np.vstack(min_ethane_ng_table))))
        output.append('<br/>')

    output.append('</body>')
    with open("new_performance_tables.html","w") as fp:
        fp.write("\n".join(output))
