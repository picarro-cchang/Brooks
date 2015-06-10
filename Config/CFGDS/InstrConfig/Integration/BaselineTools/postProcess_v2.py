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
a = arrays['h2o_peak']
plot(a['data'])
grid(True)
title('H2O Peak (ppb/cm), Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['peak87']
plot(a['data'])
grid(True)
title('CO2 Peak 87 (ppb/cm), Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_residual_h2o.png')

figure()
subplot(2,1,1)
a = arrays['cm_shift']
plot(a['data'])
grid(True)
title('Frequency shift, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
subplot(2,1,2)
a = arrays['stddevres']
plot(a['data'])
grid(True)
title('Residuals, Mean %.3f, StdDev %.3f' % (a['mean'],a['std']))
savefig(basename+'_misc.png')


output = []
output.append("# Fitter configuration parameters from step test")
output.append("Peak88_offset = 0.0")
output.append("Peak88_water_linear = -1.93E-4")
output.append("Peak88_bilinear = -1.29E-6")
output.append("Methane_spline_offset = 0.0")
output.append("Peak88_methane_linear = -1.72364E-5")
output.append("Peak88_methane_quadratic = 0.0")
output.append("Peak88_methane_H2O_bilinear = 0.0")
output.append(" ")
output.append("# Fitter configuration parameters from baseline fit "+time.asctime())
output.append("C12_baseline = %.6f" % arrays['base87']['mean'])
output.append("C13_baseline = %.6f" % arrays['base88']['mean'])
output.append("Baseline_slope = %.6f" % arrays['base1']['mean'])
output.append("Sine0_ampl =%.3f" % arrays['amp_ripp_1']['mean'])
output.append("Sine0_freq = %.3f" % arrays['center_ripp_1']['mean'])
output.append("Sine0_period = %.6f" % arrays['freq_ripp_1']['mean'])
output.append("Sine0_phase = %.6f" % p1)
output.append("Sine1_ampl = %.3f" % arrays['amp_ripp_2']['mean'])
output.append("Sine1_freq = %.3f" % arrays['center_ripp_2']['mean'])
output.append("Sine1_period = %.6f" % arrays['freq_ripp_2']['mean'])
output.append("Sine1_phase = %.6f" % p2)
output.append(" ")
output.append("# Instrument-independent fitter parameters")
output.append("Peak88_quad_linear = 0.0")
output.append("Peak87_offset = 0.0")
output.append("Peak87_water = -0.002132")
output.append("Peak96_offset = 0.0")
output.append("Peak96_water = 3.21879E-5")
output.append("Peak91_offset = 0.0")
output.append("Water_lin = 0.0148")
output.append("Water_quad = 0.0")
output.append("Water_lin_wd = -0.0123")
output.append("Water_quad_wd = -0.0002888")
output.append("C12_lin = 1.68307")
output.append("C13_lin = 0.64382458")
output.append("Methane_lin = 0.998")
output.append("Methane_water = 0.07183")
output.append(" ")
output.append("#Only for compatibility with old CBDS methane measurement")
output.append("Methane_offset = 0.0")
output.append("Methane_co2 = 0.0")
output.append("Methane_bilinear = 0.0")
output.append("Peak88_methane_1 = -35.119")
output.append("Peak88_methane_2 = -20.0")

print "\n".join(output)
print>>file(basename+".ini","w"), "\n".join(output)
