# timeP3 measures how long it takes to fetch a number of documents from the P3 server

import getFromP3 as gp3
import numpy as np
import calendar
import time

# Results of run on 20120415, 1220, using limits 1-1000 and 1-2000
# AnalyzerData (18 columns):  [ 0.00198091  1.15010028][ 0.00157737  1.28472036]
# GpsData (6 columns):        [ 0.0015775   1.03771753][ 0.00121437  1.15650542]
# WsData (8 columns):         [ 0.00133081  1.25674723][ 0.00102763  1.40802565]

p3 = gp3.P3_Accessor("FCDS2006")
startEtm = calendar.timegm(time.strptime("2012-03-23T02:00:00","%Y-%m-%dT%H:%M:%S"))
endEtm = calendar.timegm(time.strptime("2012-03-23T03:00:00","%Y-%m-%dT%H:%M:%S"))
# limits = np.asarray([1,100,200,300,400,500,600,700,800,900,1000])
limits = np.asarray([1,200,400,600,800,1000,1500,2000])

result = []
for iter in range(4):
    run = []
    for limit in limits:
        start = time.clock()
        p3.genGpsData(startEtm,limit=limit).next()
        run.append(time.clock()-start)
    print "Completing run", iter
    result.append(run)
result = np.asarray(result)
np.savez("timeP3",limits=limits,result=result)
print "Regression coeffients: ",np.polyfit(limits,np.mean(result,axis=0),1)
