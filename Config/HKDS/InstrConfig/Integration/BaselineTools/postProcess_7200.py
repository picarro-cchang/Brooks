#  Post processor to prepare the FitterConfig.ini for the new HKDS analyzer (LCT, strength fiiting, O-17 at 7193 wvn)

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
output.append("# Fitter configuration parameters from step test performed ")
output.append(" ")
output.append("AIR_offset11 = 0.0")
output.append("AIR_offset13 = 0.0")
output.append("AIR_G11_quadratic = 0.0")
output.append("AIR_G13_quadratic = 0.0")
output.append("N2_offset11 = 0.0")
output.append("N2_offset13 = 0.0")
output.append("N2_G11_quadratic = 0.0")
output.append("N2_G13_quadratic = 0.0")
output.append(" ")
output.append("# Instrument-independent parameters from LCT fine scans 29 Mar and 2 Apr 2013")
output.append(" ")
output.append("AIR_y1_at_zero = 0.3611")
output.append("AIR_y1_self = 7.93e-6")
output.append("AIR_y2_at_zero = 0.4044")
output.append("AIR_y2_self = 8.88e-6")
output.append("AIR_y3_at_zero = 0.2189")
output.append("AIR_y3_self = 1.000e-5")
output.append("AIR_z1_at_zero = 0.1588")
output.append("AIR_z1_self = 1.44e-6")
output.append("AIR_z2_at_zero = 0.1927")
output.append("AIR_z2_self = 3.93e-6")
output.append("AIR_z3_at_zero = 0.0780")
output.append("AIR_z3_self = 9.75e-6")
output.append("N2_y1_at_zero = 0.4068")
output.append("N2_y1_self = 7.08e-6")
output.append("N2_y2_at_zero = 0.4555")
output.append("N2_y2_self = 7.93e-6")
output.append("N2_y3_at_zero = 0.2764")
output.append("N2_y3_self = 8.93e-6")
output.append("N2_z1_at_zero = 0.1735")
output.append("N2_z1_self = 1.46e-6")
output.append("N2_z2_at_zero = 0.2385")
output.append("N2_z2_self = 3.27e-6")
output.append("N2_z3_at_zero = 0.1336")
output.append("N2_z3_self = 9.19e-6")
output.append("Water_linear = 7.6334")
output.append("Water_quadratic = -5.804e-5")
output.append("AIR_Methane_offset = 0.0000272")
output.append("N2_Methane_offset = -0.0000033")
output.append("AIR_Methane_water_linear = 1.12e-7")
output.append("N2_Methane_water_linear = 2.18e-8")
output.append(" ")
output.append("AIR_y11_at_zero = 0.3176")
output.append("AIR_y11_self = 7.08e-6")
output.append("AIR_y12_at_zero = 0.4189")
output.append("AIR_y12_self = 7.28e-6")
output.append("AIR_y13_at_zero = 0.2638")
output.append("AIR_y13_self = 5.44e-6")
output.append("AIR_y14_at_zero = 0.1725")
output.append("AIR_y14_self = 5.38e-6")
output.append("AIR_z11_at_zero = 0.1410")
output.append("AIR_z11_self = 2.41e-6")
output.append("AIR_z13_at_zero = 0.0751")
output.append("AIR_z13_self = 1.79e-6")
output.append("N2_y11_at_zero = 0.3595")
output.append("N2_y11_self = 6.21e-6")
output.append("N2_y12_at_zero = 0.4637")
output.append("N2_y12_self = 6.75e-6")
output.append("N2_y13_at_zero = 0.2933")
output.append("N2_y13_self = 4.66e-6")
output.append("N2_y14_at_zero = 0.1947")
output.append("N2_y14_self = 6.97e-6")
output.append("N2_z11_at_zero = 0.1542")
output.append("N2_z11_self = 1.92e-6")
output.append("N2_z13_at_zero = 0.0831")
output.append("N2_z13_self = 1.55e-6")
output.append(" ")
output.append("# Fitter configuration parameters from baseline fit "+time.asctime())
output.append(" ")
output.append("7200_Baseline_level = %.6f" % arrays['base0']['mean'])
output.append("7200_Baseline_slope = %.6f" % arrays['base1']['mean'])
output.append("7200_Sine0_ampl = %.3f" % arrays['amp_ripp_1']['mean'])
output.append("7200_Sine0_freq = %.3f" % arrays['center_ripp_1']['mean'])
output.append("7200_Sine0_period = %.6f" % arrays['freq_ripp_1']['mean'])
output.append("7200_Sine0_phase = %.6f" % arrays['phase_ripp_1']['mean'])
output.append("7200_Sine1_ampl = %.3f" % arrays['amp_ripp_2']['mean'])
output.append("7200_Sine1_freq = %.3f" % arrays['center_ripp_2']['mean'])
output.append("7200_Sine1_period = %.6f" % arrays['freq_ripp_2']['mean'])
output.append("7200_Sine1_phase = %.6f" % arrays['phase_ripp_2']['mean'])

print "\n".join(output)
print>>file("FitterConfig_with_7193.ini","w"), "\n".join(output)
