#
#
# EWMA - Exponential Weighted Moving Average
#
# From http://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm
#
# Single Exponential Smoothing general formula for t >= 3
#
# S(t) = a*y(t-1) + (1 - a)*S(t-1)
#
# with a = alpha, y = input raw signal, S = output smoothed signal
#
# Bootstrapping the series
# t=0
# S(0) = y(0)
#
# t=1
# S(1) = y(0)
#
# t=2
# S(2) = y(1)
#
# t=3
# S(3) = a*y(2) + (1-a)*S(2)
#
#class SingleExponentialSmoother(object):

 #   def __init__(self):
 #       self.__bootstrapcounter = 0
 #       self.__alpha = 0.5
 #       self.__previousS = 0
 #       self.__previousY = 0

    # Smooth the current input data. The alpha_factor allows dynamic
    # adjustment of the smoothing time constant.
    #
    # Allowed values of 0.0 < alpha_factor <= 2.0
    # alpha_factor = 2.0 smoothing is disabled
    # alpha_factor < 1.0 more smoothing and slower rise/fall response.
    #
    # Inputs:
    # y - (double) Unfiltered datum
    # alpha_factor - (double) scale the alpha smoothing factor
    #
    # Outputs:
    # (double) The smooth datum
    #
from scipy import stats
from numpy import mean, sum, sqrt

N_max=8
r_0=1.2
Max_len=2**(N_max+1)+4

def smooth(y, alpha_factor,__bootstrapcounter,__previousS,__previousY):
    current_s = 0
    __alpha = 0.5
    #print y, __bootstrapcounter, __previousS, __previousY
    # t = 0
    if __bootstrapcounter == 0:
        __previousY = y
        current_s = y
        __previousS = current_s

    # t = 1, t = 2
    elif __bootstrapcounter == 1 or __bootstrapcounter == 2:
        current_s = __previousY
        __previousS = current_s
        __previousY = y

    # t >= 3, general case
    elif __bootstrapcounter > 2:
        f = alpha_factor
        current_s = __alpha*f*__previousY + (1-__alpha*f)*__previousS
        __previousY = y
        __previousS = current_s
        
    __bootstrapcounter += 1
    #print y, __bootstrapcounter, __previousS, __previousY
    return current_s, __bootstrapcounter, __previousS, __previousY

def variableExpAverage(buffer, y, t, length, bootstrapcounter,previousS,previousY):
    buffer.append((y,t))
    
    while t-buffer[0][1] > length:
        buffer.pop(0)

    alpha_factor = 1.0

    if(len(buffer) >= length):
        y_array = [y1[0] for y1 in buffer]
        x_array = range(len(y_array))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_array, y_array)
        if abs(slope) < 1.0:
            if alpha_factor > 1.0:
                alpha_factor = 1.0
            if alpha_factor < 0.01:
                alpha_factor = 0.01
        else:
            alpha_factor = 1.0
    #print "input.....",y, bootstrapcounter,previousS,previousY        
    sm,b,pS,pY = smooth(y,alpha_factor,bootstrapcounter,previousS,previousY)
    #print "output...", sm,b,pS,pY
    return sm,b,pS,pY
    
def calc_tau(buffer,sigma):
    """calculates the differences in the 2^m data blocks"""
    D=[0.8,0.7,0.6,0.5,0.4,0.35,0.35,0.35] #ensures that the instrument responds quickly as the filter 'winds up'
    Conc = [y1[0] for y1 in buffer]
    for i in range(N_max):
        if len(Conc) > 2**(i+1):
            s1 = -2**i
            s2 = -2**(i+1)
            D1 = Conc[s1:]        #last block
            D2 = Conc[s2:s1]      #first block
            D2.reverse()           
            # calculate the sawtooth version of the difference
            P1 = [D1[k]*(k+0.5) for k in range(len(D1))]
            P2 = [D2[j]*(j+0.5) for j in range(len(D2))]
            N1 = [(k+0.5) for k in range(len(D1))]
            N2 = [(j+0.5) for j in range(len(D2))]
            #self.D[i] = abs(np.mean(D1) - np.mean(D2))
            D[i] = abs(sum(P1)/sum(N1) - sum(P2)/sum(N2))
    
# run calc_differences() first
# then calc_tau 

    tau_max = 9000
    rho=[8,7,6,5,4,3.5,3.5,3.5]  #rho is the number of sigma noise detection; rho is set higher for smaller m values so that fast noise doesn't cause the signal to jump
    rates = []
    
    for i in range(N_max):
        r = D[i] / sigma * sqrt((i+1)) / rho[i]  #r equals 'xi' from wiki description
        f = r**4 / (1.0 + r**4)                                    # regularizes to zero for r << 1
        # The 0.75 power in the next expression is from a previous version, but this is the version I validated.  I suspect we should just make the power 1.0
        rates.append(self.r_0 * f * abs(r)**0.75/ 2**i)      
         
    rates.append(self.r_0 / 2**N_max*rho[-1])  #adds the final term without regularization
    #adds the sum of the rates from each block, and then adds that sum in quadrature with the maximum tau
    return sqrt(sum(rates)**2 + (1.0 / tau_max)**2)