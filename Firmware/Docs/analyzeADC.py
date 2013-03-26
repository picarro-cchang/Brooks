from numpy import *
from pylab import *
import csv

fname = raw_input("File with ADC data? ")
reader = csv.reader(file(fname,"r"))
adc = []
ch = None
for r in reader:
    if "ADCout" in r:
        ch = r.index("ADCout")
    elif ch != None:
        adc.append(r[ch])
values = [int(v[:4],16) for v in adc[1:]]
print "Mean = %f" % (mean(values))
print "StdDev = %f" % (std(values))
plot(values)
xlabel("Sample number")
ylabel("ADC output")
savefig(fname + ".png")
