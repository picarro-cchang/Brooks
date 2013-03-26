from numpy import *
# Make an ABS scheme file

thList = linspace(-3*pi/4,-pi/4,321)
dwell = 3*ones(thList.shape,dtype=int)
subschemeId = zeros(thList.shape,dtype=int)
virtualLaser = 4*ones(thList.shape,dtype=int)
threshold = zeros(thList.shape)
pztSetpoint = zeros(thList.shape)
laserTemp = 24.0*ones(thList.shape)
repeats = 2

fp = file("../../Schemes/simple1.abs","w")
print >>fp, repeats
print >>fp, len(thList)
for x in zip(thList,dwell,subschemeId,virtualLaser,threshold,pztSetpoint,laserTemp):
    print >>fp, " ".join(["%s" % xx for xx in x])
fp.close()

thList = linspace(-3*pi/4,-pi/4,81)
dwell = 10*ones(thList.shape,dtype=int)
subschemeId = zeros(thList.shape,dtype=int)
virtualLaser = 4*ones(thList.shape,dtype=int)
threshold = zeros(thList.shape)
pztSetpoint = zeros(thList.shape)
laserTemp = 24.0*ones(thList.shape)
repeats = 1

fp = file("../../Schemes/simple2.abs","w")
print >>fp, repeats
print >>fp, len(thList)
for x in zip(thList,dwell,subschemeId,virtualLaser,threshold,pztSetpoint,laserTemp):
    print >>fp, " ".join(["%s" % xx for xx in x])
fp.close()
