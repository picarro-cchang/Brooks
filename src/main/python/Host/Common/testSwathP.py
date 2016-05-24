from pylab import *
import Host.Common.SwathProcessor as SwathProcessor
import swathP as sp

stabClass = 'C'
stabClassAsInt = ord(stabClass)-ord('A')
Q = 1.0
u = 2.0
x = linspace(0,1000,1001);
y = asarray([sp.getConc(stabClassAsInt, Q, u, xx) for xx in x])
y1 = asarray([SwathProcessor.pga.getConc(stabClass,Q,u,xx) for xx in x])
figure(1)
loglog(x,y,x,y1)
xlabel('Distance')
ylabel('Concentration')
grid(True)

Qlist = linspace(0.1,10.0,100);
u0 = 0.5
a = 1
q = 2
d = asarray([sp.getMaxDist(stabClassAsInt,Q,u,0.03,u0,a,q) for Q in Qlist])
d1 = asarray([SwathProcessor.pga.getMaxDist(stabClass,Q,u,0.03,u0,a,q) for Q in Qlist])
figure(2)
plot(Qlist,d,Qlist,d1)
xlabel('Minimum leak rate')
ylabel('distance')
grid(True)
show()