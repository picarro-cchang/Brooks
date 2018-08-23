import cPickle
import time
from struct import unpack
from numpy import asarray, mean, std
from pylab import *

fname = 'FitterOutput.dat'
basename = 'FitterConfig'
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
    
#good = asarray(arrays['h2o_ppmv']['data'] < 80)
#print good
 
figure()
subplot(2,1,1)
a = arrays['amp_ripp_1']
plot(a['data'])
grid(True)
title('function 1000 Amplitude, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['phase_ripp_1']
x = cos(a['data'])
y = sin(a['data'])
p1 = arctan2(mean(y),mean(x))
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
x = cos(a['data'])
y = sin(a['data'])
p2 = arctan2(mean(y),mean(x))
plot(a['data'])
grid(True)
title('function 1001 Phase, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_ripp2.png')

figure()
subplot(2,1,1)
a = arrays['freq_ripp_1']
plot(a['data'])
grid(True)
title('function 1000 Period, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['freq_ripp_2']
plot(a['data'])
grid(True)
title('function 1001 Period, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_periods.png')

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
a = arrays['peak25']
plot(a['data'])
grid(True)
title('H2O Peak 25, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['base3']
plot(a['data'])
grid(True)
title('Frequency shift, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_misc.png')

output = []
output.append("# Fitter configuration parameters from baseline fit "+time.asctime())
output.append("NH3_Baseline_level = %.6f" % arrays['base0']['mean'])
output.append("NH3_Baseline_slope = %.6f" % arrays['base1']['mean'])
output.append("NH3_Sine0_ampl =%.3f" % arrays['amp_ripp_1']['mean'])
output.append("NH3_Sine0_freq = %.4f" % arrays['center_ripp_1']['mean'])
output.append("NH3_Sine0_period = %.6f" % arrays['freq_ripp_1']['mean'])
output.append("NH3_Sine0_phase = %.6f" % p1)
output.append("NH3_Sine1_ampl = %.3f" % arrays['amp_ripp_2']['mean'])
output.append("NH3_Sine1_freq = %.4f" % arrays['center_ripp_2']['mean'])
output.append("NH3_Sine1_period = %.6f" % arrays['freq_ripp_2']['mean'])
output.append("NH3_Sine1_phase = %.6f" % p2)

print "\n".join(output)
print>>file(basename+".ini","w"), "\n".join(output)
