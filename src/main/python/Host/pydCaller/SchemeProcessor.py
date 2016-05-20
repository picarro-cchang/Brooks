from Host.Common.SchemeProcessor import Scheme

if __name__ == "__main__":
    if len(argv)>1:
        fname = argv[1]
    else:    
        fname = raw_input("Name of scheme file")
    s = Scheme(fname)
    print "%-10d # Repetitions" % s.nrepeat
    print "%-10d # Scheme rows" % s.numEntries
    for i in range(s.numEntries):
        print "%11.5f,%6d,%6d, %1d,%6d,%6d,%8.4f, %d, %d, %d, %d" % (s.setpoint[i],\
                s.dwell[i],s.subschemeId[i],s.virtualLaser[i],s.threshold[i],s.pztSetpoint[i],\
                s.laserTemp[i],s.extra1[i],s.extra2[i],s.extra3[i],s.extra4[i])