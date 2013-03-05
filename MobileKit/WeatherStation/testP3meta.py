import calendar
import re
import time

import getFromP3 as gp3
# Get lists of dat, peaks and analysis files available on p3 for an analyzer
if __name__ == "__main__":
    p3 = gp3.P3_Accessor("FCDS2006")
    startEtm = calendar.timegm(time.strptime("2012-03-23T00:00:00","%Y-%m-%dT%H:%M:%S"))
    endEtm   = calendar.timegm(time.strptime("2012-03-23T23:59:59","%Y-%m-%dT%H:%M:%S"))
    f = re.compile(".*?User_Minimal.dat")    
    #for m in p3.genAnzLogMeta("dat")(startEtm=startEtm,endEtm=endEtm):
    #    print m.data['name']
    #for m in p3.genAnzLogMeta("peaks")(startEtm=startEtm,endEtm=endEtm):
    #    print m.data['name']
    for m in p3.genAnzLogMeta("dat")(startEtm=startEtm,endEtm=endEtm):
        n = m.data['LOGNAME']
        d = m.data['durr']
        if f.match(n): 
            print "%s, duration %.0f" % (n,d)
        
    alog = raw_input("Name of logfile: ")
    fp = file(alog,'wb')
    acc = gp3.P3_Accessor_ByPos(alog)
    kList  = None
    for p in acc.genAnzLog("dat")(startPos=0,endPos=1000000):
        d = p.data
        if not kList:
            kList = sorted([k for k in d.keys() if d[k] is None or isinstance(d[k],(float,int))])
            for k in kList:
                fp.write("%26s" % k)
            fp.write("\n")
        for k in kList:
            fp.write("%26s" % (d[k] if d[k]!=None else "NaN",))
        fp.write("\n")
    fp.close()
    print "Done"