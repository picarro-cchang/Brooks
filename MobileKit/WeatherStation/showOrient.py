import numpy as np
import pylab as pl

fp = open("c:/temp/orient.txt","r")
rot1, rot2 = [], []
for l in fp:
    if l.startswith("Rotation:"):
        d,r1,d,r2,d,d,d = l.split()
        rot1.append(r1)
        rot2.append(r2)
rot1 = np.asarray(rot1)
rot2 = np.asarray(rot2)
pl.plot(range(len(rot1)),rot1,range(len(rot2)),rot2)
pl.show()
