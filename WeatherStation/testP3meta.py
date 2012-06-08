import calendar
import getFromP3 as gp3
import time
# Get lists of dat, peaks and analysis files available on p3 for an analyzer
if __name__ == "__main__":
    p3 = gp3.P3_Accessor("FCDS2008")
    startEtm = calendar.timegm(time.strptime("2012-05-01T00:00:00","%Y-%m-%dT%H:%M:%S"))
    endEtm   = calendar.timegm(time.strptime("2012-05-31T23:59:59","%Y-%m-%dT%H:%M:%S"))    
    #for m in p3.genAnzLogMeta("dat")(startEtm=startEtm,endEtm=endEtm):
    #    print m.data['name']
    #for m in p3.genAnzLogMeta("peaks")(startEtm=startEtm,endEtm=endEtm):
    #    print m.data['name']
    for m in p3.genAnzLogMeta("analysis")(startEtm=startEtm,endEtm=endEtm):
        print m
        raw_input()
        
    #for m in p3.genAnzLog("analysis")(startEtm=startEtm,endEtm=endEtm):
    #    print m
