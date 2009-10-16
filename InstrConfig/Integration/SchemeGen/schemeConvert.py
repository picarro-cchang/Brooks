fname="CFBDS02_FSR_H2O.sch"
oname="CFBDS02_FSR_H2O_new.sch"

fp = file(fname,"r")
op = file(oname,"w")

print >> op, fp.readline().strip()
print >> op, fp.readline().strip()

cen = [6237.408,6057.800]
newFSR = 0.0205943889388

for l in fp.readlines():
	freq,dwell,id,laser,pzt = l.split()
	cenFreq = cen[int(laser)]
	freqNew = round((float(freq)-cenFreq)/newFSR)*newFSR + cenFreq
	print >>op, "%.5f %s %s %s %s" % (freqNew,dwell,id,laser,pzt)

fp.close()
op.close()