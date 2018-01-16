
"""
Created on Thu Jul 07 08:33:28 2016

@author: chris
"""

#from numpy import mean, sum, sqrt, polyfit
import sys
import os
from math import fabs, pow
import numpy as np
from Host.Common.CustomConfigObj import CustomConfigObj

#if sys.platform == 'win32':
#    Paras=CustomConfigObj("C:\Picarro\G2000\AppConfig\Config\DataManager\DynamicFilter_AMADS.ini")
#else:
#    try:
#        Paras=CustomConfigObj(os.path.expanduser('~') +"/git/host/Config/AMADS/AppConfig/Config/DataManager/DynamicFilter_AMADS.ini")
#    except Exception as e:
#        print("Exception:",e)
#        raise 
		
Paras=CustomConfigObj("../../AppConfig/Config/DataManager/DynamicFilter.ini")

N_max=Paras.getint("Dynamic filter","N_max") # ini
r_0=Paras.getfloat("Dynamic filter","r_0") #ini
minNoise = [0.002, 0.05, 0.01,0.1]
minNoise[0] = Paras.getfloat("Dynamic filter","MinNoiseHF")
minNoise[1] = Paras.getfloat("Dynamic filter","MinNoiseNH3")
minNoise[2] = Paras.getfloat("Dynamic filter","MinNoiseHCl")
minNoise[3] = Paras.getfloat("Dynamic filter","MinNoiseH2S")

# Operating parameters for the negative number filter.
# See http://confluence.picarro.int/x/_gY4
#
nnfParams = {}
nnfParams["alpha"] = Paras.getfloat("Negative Number Filter", "alpha")
nnfParams["b_HF"] = Paras.getfloat("Negative Number Filter", "b_HF")
nnfParams["b_HCl"] = Paras.getfloat("Negative Number Filter", "b_HCl")
nnfParams["b_NH3"] = Paras.getfloat("Negative Number Filter", "b_NH3")
nnfParams["b_H2S"] = Paras.getfloat("Negative Number Filter", "b_H2S")
Max_len=2**(N_max+1)+4



# EWMA - Exponential Weighted Moving Average
#
# From http://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm
#
# Single Exponential Smoothing general formula for t >= 3
#
# S(t) = a*y(t-1) + (1 - a)*S(t-1)
#
# with a = alpha, y = input raw signal, S = output smoothed signal

def continuous_ave(previousS, raw, N):
    alpha=np.exp(-1.0/N)
    if N != 0:
        currentS = previousS*alpha + raw * (1.0 - alpha)
    else:
        currentS = previousS
    return currentS
    
def calc_tau(buffer,sigma):
    """calculates the differences in the 2^m data blocks"""
    
    rho=[3.5 for n in range(N_max)]  #rho is the number of sigma noise detection; rho is set higher for smaller m values so that fast noise doesn't cause the signal to jump
    
    rho[0] = 8                                 #rho is set higher for smaller m values so that fast noise doesn't cause the signal to jump
    rho[1] = 7
    rho[2] = 6
    rho[3] = 5
    rho[4] = 4
    
    D = [sigma*rho[k]*2 for k in range(N_max)]  #ensures that the instrument responds quickly as the filter 'winds up'
    
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
            D[i] = abs(np.sum(P1)/sum(N1) - np.sum(P2)/np.sum(N2))
    
# run calc_differences() first
# then calc_tau 

    tau_max = 9000
    
    rates = []
    
    for i in range(N_max):
        r = D[i] / sigma * np.sqrt((i+1)) / rho[i]  #r equals 'xi' from wiki description
        f = r**4 / (1.0 + r**4)                                    # regularizes to zero for r << 1
        # The 0.75 power in the next expression is from a previous version, but this is the version I validated.  I suspect we should just make the power 1.0
        rates.append(r_0 * f * abs(r)/ 2**i)      
         
    rates.append(r_0 / 2**N_max*rho[-1])  #adds the final term without regularization
    #adds the sum of the rates from each block, and then adds that sum in quadrature with the maximum tau
    return np.sqrt(np.sum(rates)**2 + (1.0 / tau_max)**2)
    
    
def variableExpAverage(bufferZZ,buffer,y, t, length, MinNoiseID, previousS,previousNoise):
    MinNoise = minNoise[MinNoiseID]

    if MinNoise < 0.002: MinNoise = 0.002
    if MinNoise > 0.5:  MinNoise = 0.5
    #print MinNoise
    
    buffer.append((y,t))
    
    while t-buffer[0][1] > length:
        buffer.pop(0)
    
    k=len(buffer)
    #calculate sigma    
    if(k > 3):
        conc = [y1[0] for y1 in buffer] 
        T=     [t1[1] for t1 in buffer]
        conc=np.array(conc)
        T=np.array(T)
        
        X = T[-3:] - T[-1]
        
        Y = conc[-3:] - conc[-1]
        
        a1, a0 = np.polyfit(X,Y, 1)
        z = Y - a1*X - a0
        #print z
    else:
        z=0    
    zz = np.sqrt(np.sum(z**2))
    
    bufferZZ.append(zz)
   
    while len(bufferZZ)>512:
        bufferZZ.pop(0)
        
    # print len(bufferZZ)
    current_noise_est=np.median(bufferZZ)
    
    #current_noise_est = continuous_ave(previousNoise, zz, min(k, 500))
 
    sigma = max(MinNoise, current_noise_est)*1.5*np.sqrt(2) #0.01 should be species specific (HF 0.002, HCl 0.01, NH3 0.05) put in an ini file
    
    kk=calc_tau(buffer,sigma)
     
    tau = 1.0 /kk
    
    #if k % 250 == 0 and True:
    #print k
    #print "%.3f  %.2f  %.3f, %.3f" % (sigma, tau,current_noise_est, zz)
    
    current_ave = continuous_ave(previousS, y, tau)
               
    return current_ave, current_noise_est, tau

#
# a = alpha = 2.0
# b = 0.05 for HCl & NH3
#     0.025 for HF
#
def negative_number_filter(moleculeName, x):
    a = nnfParams["alpha"]
    b = 0.05
    
    if moleculeName is "HF":
        b = nnfParams["b_HF"]
    elif moleculeName is "HCl":
        b = nnfParams["b_HCl"]
    elif moleculeName is "NH3":
        b = nnfParams["b_NH3"]
    elif moleculeName is "H2S":
        b = nnfParams["b_H2S"]	
    else:
        print("Molecule name:", moleculeName, " in DynamicNoiseFilter.py is an invalid key.")
    tmp = pow((pow(fabs(x), a) + pow((2*b), a) ), (1/a))
    y = 0.5*tmp + x/2

    return y
