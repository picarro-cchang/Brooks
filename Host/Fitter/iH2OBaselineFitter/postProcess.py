import cPickle
from struct import unpack
from numpy import asarray, mean, std
from pylab import *

fname = 'FitterOutput.dat'
basename = 'baseline'
fp = file(fname,'rb')
results = []
while True:
    try:
        l, = unpack('i',fp.read(4))
        results.append(cPickle.loads(fp.read(l)))
    except:
        break
        
arrays = {}        
for r in results:
    for k in r:
        if k not in arrays:
            arrays[k] = []
        arrays[k].append(r[k])
for k in arrays:
    x = asarray(arrays[k])
    arrays[k] = dict(data=x,mean=mean(x),std=std(x))

figure()
subplot(2,1,1)
a = arrays['amp_ripp_1']
plot(a['data'])
grid(True)
title('function 1000 Amplitude, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['phase_ripp_1']
plot(a['data'])
grid(True)
title('function 1000 Phase, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_ripp1.png')

figure()
subplot(2,1,1)
a = arrays['amp_ripp_2']
plot(a['data'])
grid(True)
title('function 1001 Amplitude, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['phase_ripp_2']
plot(a['data'])
grid(True)
title('function 1001 Phase, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_ripp2.png')

figure()
subplot(2,1,1)
a = arrays['base0']
plot(a['data'])
grid(True)
title('Base 0, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['base1']
plot(a['data'])
grid(True)
title('Base 1, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_base.png')

figure()
subplot(2,1,1)
a = arrays['h2o_ppmv']
plot(a['data'])
grid(True)
title('H2O Conc (ppmv), Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['stddevres']
plot(a['data'])
grid(True)
title('Residuals, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_misc.png')

output = []
output.append("[function1000]")
output.append("functional_form=sinusoid")
output.append("a0=%.3f" % arrays['amp_ripp_1']['mean'])
output.append("a1=7184.0")
output.append("a2=%.6f" % arrays['freq_ripp_1']['mean'])
output.append("a3=%.6f" % arrays['phase_ripp_1']['mean'])
output.append("[function1001]")
output.append("functional_form=sinusoid")
output.append("a0=%.3f" % arrays['amp_ripp_2']['mean'])
output.append("a1=7184.0")
output.append("a2=%.6f" % arrays['freq_ripp_2']['mean'])
output.append("a3=%.6f" % arrays['phase_ripp_2']['mean'])

print "\n".join(output)
print>>file(basename+".ini","w"), "\n".join(output)
