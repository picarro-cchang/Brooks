from numpy import *
from tables import *
from scipy.signal import *
from Host.autogen.interface import *
import pylab

class Ltid(object):
    # Discrete time invariant linear system
    def __init__(self,Phi,Gamma,C,D):
        self.Phi = mat(Phi)
        self.Gamma = mat(Gamma)
        self.C = mat(C)
        self.D = mat(D)
        k,l = self.Phi.shape
        if k!=l: raise ValueError("Phi matrix must be square")
        self.n = k  # Dimensionality of state space
        k,l = self.D.shape
        if k!=l: raise ValueError("D matrix must be square")
        self.m = k  # Dimensionality of input/output space
        if (self.n,self.m) != self.Gamma.shape: raise ValueError("Gamma matrix has wrong shape")
        if (self.m,self.n) != self.C.shape: raise ValueError("C matrix has wrong shape")
    
    def simulate(self,u,x0=None):
        # Feed in u to the system, starting with initial condition x0
        u = mat(u)
        m,N = u.shape
        y = mat(zeros((m,N)))
        if x0 is None:
            x0 = mat(zeros((self.n,),dtype=float)).T
        x = mat(x0).copy()
        for k in range(N):
            y[:,k] = self.C*x + self.D*u[:,k]
            x = self.Phi*x + self.Gamma*u[:,k]
        return y
    
    def cascade(self,sys2):
        # Return a system which is the cascade of the current system and sys2
        Phi = r_[c_[self.Phi,zeros((self.n,sys2.n))],c_[sys2.Gamma*self.C,sys2.Phi]]
        Gamma = r_[self.Gamma,sys2.Gamma*self.D]
        C = c_[sys2.D*self.C,sys2.C]
        D = sys2.D*self.D
        return Ltid(Phi,Gamma,C,D)
        
    def feedback(self,sys2=None):    
        # Return a system which results from feeding back the output via sys2 and 
        #  subtracting it from the input
        if sys2 != None:
            f = (eye(self.m,self.m)+self.D*sys2.D).I
            c = r_[-self.Gamma*sys2.D,sys2.Gamma]
            r = c_[self.C,-self.D*sys2.C]
            
            Phi = r_[c_[self.Phi,-self.Gamma*sys2.C],c_[zeros((sys2.n,self.n)),sys2.Phi]]+c*f*r
            Gamma = r_[self.Gamma,zeros((sys2.n,self.m))]+c*f*self.D
            C = f*r
            D = f*self.D
            return Ltid(Phi,Gamma,C,D)
        else:
            f = (eye(self.m,self.m)+self.D).I
            Phi = self.Phi-self.Gamma*f*self.C
            Gamma = self.Gamma*f
            C = f*self.C
            D = f*self.D
            return Ltid(Phi,Gamma,C,D)
        
        
    def freqz(self,wArray):
        def _freqz(w):
            # Return the frequency response at exp(i*w)
            H = self.D + self.C*(exp(1j*w)*eye(self.n)-self.Phi).I*self.Gamma
            return H[0,0]
        return array([_freqz(w) for w in wArray])
        
    def toNumDen(self):
        # Estimate the numerator and denominator polynomials for the
        #  discrete time-invariant system
        N = 2*self.n + 1
        L = 4*self.n + 1
        wArray = 2*pi*linspace(0.5/L,(L-0.5)/L,L)
        T = mat(self.freqz(wArray)).T
        M = mat(zeros((L,N),dtype=complex))
        M[:,0] = 1
        zc = mat(exp(-1j*wArray)).T
        for k in range(self.n):
            M[:,k+1] = M[:,k].A * zc.A
        M[:,self.n+1] = -T.A * zc.A
        for k in range(1,self.n):
            M[:,self.n+k+1] = M[:,self.n+k].A * zc.A
        c,res,rank,sv = linalg.lstsq(M,T)
        num = real(c[:self.n+1,0])
        den = concatenate(([1.0],real(c[self.n+1:,0])))
        return num, den
    
    @staticmethod
    def fromNumDen(num,den):
        # Create state space description from numerator and denominator
        #  polynomial arrays
        L = max(len(num),len(den))
        a = zeros(L)
        a[:len(den)] = den[:]
        b = zeros(L)
        b[:len(num)] = num[:]
        a = mat(a)
        b = mat(b)
        b = b/a[0,0]
        a = a/a[0,0]
        Phi = c_[-a[:,1:].T,eye(L-1,L-2)]
        Gamma = b[:,1:].T-b[0,0]*a[:,1:].T
        C = zeros(L-1)
        C[0] = 1
        D = b[0,0]
        return Ltid(Phi,Gamma,C,D)
        
def find_ARMA(u,y,b_lags,a_lags,ntrend=1):
    # Find the coefficients a_k, b_l for k in a_lags and l in b_lags
    #  to fit the ARMA model
    #
    # y[n] = Sum b[l]*u[n-l] - Sum a[k]*y[n-k]
    #
    # in the least-squares sense. Notice that a_0 is assumed to be 1.
    #
    if any(a_lags<=0) or any(b_lags<0):
        raise ValueError("Lags cannot be negative")
    nmax = max(max(a_lags),max(b_lags))
    rhs = y[nmax:]
    M = zeros((len(rhs),len(a_lags)+len(b_lags)+ntrend),dtype=float)
    for i,k in enumerate(b_lags):
        M[:,i] = u[nmax-k:-k]
    for i,k in enumerate(a_lags):
        M[:,len(b_lags)+i] = y[nmax-k:-k]
    for i in range(ntrend):
        M[:,len(b_lags)+len(a_lags)+i] = cos(i*arccos(linspace(-1,1,len(rhs))))
        
    c,res,rank,sv = linalg.lstsq(M,rhs)
    num = zeros(max(b_lags)+1,dtype=float)
    num[b_lags] = c[:len(b_lags)]
    den = zeros(max(a_lags)+1,dtype=float)
    den[a_lags] = -c[len(b_lags):len(b_lags)+len(a_lags)]
    den[0] = 1.0
    return num,den,res,rank,sv,dot(M,c)
    
if __name__ == "__main__":
    fname = "../Host/Driver/Sensor_PRBS1.h5"
    h5f = openFile(fname,"r")
    table = h5f.root.sensors
    y = table.readWhere("(streamNum == %d)" % STREAM_Laser1Temp)
    x = table.readWhere("(streamNum == %d)" % STREAM_Laser1Tec)
    h5f.close()
    # Obtain data on a common timebase
    tMin = max(x['time'][0],y['time'][0])
    tMax = min(x['time'][-1],y['time'][-1])
    filt = (x['time']>=tMin) & (x['time']<=tMax)
    t = x['time'][filt]
    x = x['value'][filt]
    y = y['value'][(y['time']>=tMin) & (y['time']<=tMax)]
    num,den,res,rank,sv,mock = find_ARMA(x,y,[1,2,3,4],[1,2,3,4])
    # Transfer functions as ratios of polynomials in z^-1
    sysG = Ltid.fromNumDen(num,den)
    #
    K = 1000
    h = 0.2
    Ti = 10
    Td = 1
    N = 1000
    b = 0.1
    c = 1
    #
    p = Td/(Td + N*h)
    denC =  array([1.0,-(1.0+p),p])
    numCp = array([0.0,1.0,-(1.0+p),p])
    numCi = array([0.0,1.0,-p,0.0])
    numCd = array([0.0,1.0,-2.0,1.0])
    numC = K*(numCp + (h/Ti)*numCi + N*p*numCd)
    numCw = K*(b*numCp + (h/Ti)*numCi + c*N*p*numCd)
    #
    sysC = Ltid.fromNumDen(numC,denC)
    sysD = sysG.feedback(sysC)
    sysH = sysD.cascade(Ltid.fromNumDen(numCw,denC))
    #
    pylab.close('all')
    #
    step = ones(1000,dtype=float)
    y1 = sysG.simulate(step).A[0]
    pylab.figure(1)
    pylab.plot(y1)
    #
    y2 = sysD.simulate(step).A[0]
    pylab.figure(2)
    pylab.plot(y2)
    #
    y3 = sysH.simulate(step).A[0]
    pylab.figure(3)
    pylab.plot(y3)
    #
    wArray = linspace(0.0,pi,201)
    H = sysG.freqz(wArray)
    pylab.figure(4)
    pylab.plot(wArray,20*log10(abs(H)))
    pylab.grid(True)
    #
    pylab.show()
