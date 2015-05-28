import cPickle
from struct import unpack
from numpy import asarray, mean, std
from pylab import *
import time

fname = 'FitterOutput.dat'
basename = 'FitterConfig_iH2O7200'
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
a = arrays['amp_ripp_1']
plot(a['data'])
grid(True)
title('function 1000 Amplitude, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['phase_ripp_1']
x = cos(a['data'])
y = sin(a['data'])
p1 = arctan2(mean(y),mean(x))
print p1
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
print p2
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
a = arrays['base3']
plot(a['data'])
grid(True)
title('Frequency shift, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_misc.png')
avg_shift = a['mean']
f_corrected = arrays['center_ripp_1']['mean']-avg_shift

output = []
output.append("Autodetect_enable = 0")
output.append("N2_flag = 0")
output.append(" ")
output.append("# Fitter configuration parameters from step test performed ")
output.append(" ")
output.append("AIR_offset1 = 0.0")
output.append("AIR_offset2 = 0.0")
output.append("AIR_offset3 = 0.0")
output.append("AIR_G1_quadratic = 0.0")
output.append("AIR_G2_quadratic = 0.0")
output.append("AIR_G3_quadratic = 0.0")
output.append("N2_offset1 = 0.0")
output.append("N2_offset2 = 0.0")
output.append("N2_offset3 = 0.0")
output.append("N2_G1_quadratic = 0.0")
output.append("N2_G2_quadratic = 0.0")
output.append("N2_G3_quadratic = 0.0")
output.append(" ")
output.append("# Instrument-independent parameters")
output.append(" ")
output.append("AIR_y1_at_zero = 0.3611")
output.append("AIR_y1_self = 1.16e-5")
output.append("AIR_y2_at_zero = 0.4032")
output.append("AIR_y2_self = 1.30e-5")
output.append("AIR_y3_at_zero = 0.2181")
output.append("AIR_y3_self = 1.44e-5")
output.append("N2_y1_at_zero = 0.4015")
output.append("N2_y1_self = 1.16e-5")
output.append("N2_y2_at_zero = 0.4493")
output.append("N2_y2_self = 1.30e-5")
output.append("N2_y3_at_zero = 0.2585")
output.append("N2_y3_self = 1.44e-5")
output.append("Water_linear = 10.886")
output.append("AIR_Methane_offset = 0.0")
output.append("N2_Methane_water_offset = 0.0")
output.append("AIR_Methane_water_linear = 3.273e-7")
output.append("N2_Methane_water_linear = 9.27e-8")
output.append(" ")
output.append("# Fitter configuration parameters from baseline fit "+time.asctime())
output.append(" ")
output.append("Baseline_level = %.6f" % arrays['base0']['mean'])
output.append("Baseline_slope = %.6f" % arrays['base1']['mean'])
output.append("Sine0_ampl = %.3f" % arrays['amp_ripp_1']['mean'])
output.append("Sine0_freq = %.3f" % f_corrected)
output.append("Sine0_period = %.6f" % arrays['freq_ripp_1']['mean'])
output.append("Sine0_phase = %.6f" % p1)
output.append("Sine1_ampl = %.3f" % arrays['amp_ripp_2']['mean'])
output.append("Sine1_freq = %.3f" % f_corrected)
output.append("Sine1_period = %.6f" % arrays['freq_ripp_2']['mean'])
output.append("Sine1_phase = %.6f" % p2)

print "\n".join(output)
print>>file(basename+".ini","w"), "\n".join(output)
