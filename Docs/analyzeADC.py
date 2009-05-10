from numpy import *
from pylab import *
import csv

fname = raw_input("File with ADC data? ")
reader = csv.reader(file(fname,"r"))
adc = []
for r in reader:
    if len(r)>=6:
        adc.append(r[5])
values = [int(v[:4],16) for v in adc[1:]]
print "Mean = %f" % (mean(values))
print "StdDev = %f" % (std(values))
plot(values)
xlabel("Sample number")
ylabel("ADC output")
savefig(fname + ".png")
