# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 15:03:40 2013

@author: ttsai

Takes in a string of the pickled info that you would like to output and retrieve from pickled file

Takes in pickled data file and unpickles it into
0. Time (Epoch) obj["data"]["time"]
1. CH4 Dry obj["data"]["CH4_dry"]
2. H2O obj["data"]["H2O"]
3. Valve mask obj["data"]["ValveMask"]
4. Spectrum ID
5. "WS_WIND_LAT"
6. WS_WIND_LON
7. Carspeed
8. GPS Lat
9. GPS Long
10. CO2
"""
import easygui as eg
import cPickle
import pdb
import string
import pylab
import numpy


def printpretty (floatnum):
    return string.ljust(str(floatnum), 12)

def readfunc(filename, peakplot = 'y', savefileyn = 'y', outputvar = ""):
    time = []
    ch4 = []
    h2o =[]
    co2 = []
    carspeed = []
    windlat = []
    gpslat =[]
    gpslong = []
    stdwindir = []
    var = []
    savefilename = filename.replace(".dat","_unpickled.txt")
    if savefileyn == 'y':
        f = open(savefilename, "w")
    else:
        pass
    try:
        with open(filename,'rb') as fileo:
            while True:
                try: 
                    obj = cPickle.load(fileo)
                    if obj["data"]["SpectrumID"] == 25:
                        if savefileyn == 'y':
                            f.write(printpretty(obj["data"]["time"])+"\t"+ \
                            printpretty(obj["data"]["CH4_dry"])+"\t"+ \
                            printpretty(obj["data"]["H2O"])+"\t"+ \
                            printpretty(obj["data"]["ValveMask"])+"\t"+ \
                            printpretty(obj["data"]["SpectrumID"])+"\t")
                            #print printpretty(obj["data"]["time"]), "\t", printpretty(obj["data"]["CH4_dry"])
                            time.append(obj["data"]["time"])
                            ch4.append(obj["data"]["CH4_dry"])
                            h2o.append(obj["data"]["H2O"])
                            try:
                                f.write(printpretty(obj["data"]["WS_WIND_LAT"])+"\t"+ \
                                printpretty(obj["data"]["WS_WIND_LON"])+"\t"+ \
                                printpretty(obj["data"]["CAR_SPEED"])+"\t"+ \
                                printpretty(obj["data"]["GPS_ABS_LAT"])+"\t" +\
                                printpretty(obj["data"]["GPS_ABS_LONG"])+"\t")
                                carspeed.append(obj["data"]["CAR_SPEED"])
                                windlat.append(obj["data"]["WS_WIND_LAT"])
                                stdwindir.append(obj["data"]["WIND_DIR_SDEV"])
                                gpslat.append(obj["data"]["GPS_ABS_LAT"])
                                gpslong.append(obj["data"]["GPS_ABS_LONG"])
                                try:
                                    f.write(printpretty(obj["data"]["CO2"])+"\n")                            
                                    co2.append(obj["data"]["CO2"])
                                    erroro = "End of file reached"
                                except:
                                    f.write("\n")
                                    erroro = 'Missing CO2 data'
                            except:
                                try:                             
                                    f.write(printpretty(obj["data"]["CO2"])+"\n")                            
                                    co2.append(obj["data"]["CO2"])
                                    erroro = "Missing Wind and Car speed data"
                                except:
                                    erroro = "Missing Wind and Car speed and CO2 data"
                                try:
                                    pdb.set_trace()
                                    var.append(obj["data"][outputvar])
                                except:
                                    var.append('')
                        else:
                            erroro = 'No output'                            
                            time.append(obj["data"]["time"])
                            ch4.append(obj["data"]["CH4_dry"])
                            h2o.append(obj["data"]["H2O"])
                            co2.append(obj["data"]["CO2"])
                            carspeed.append(obj["data"]["CAR_SPEED"])
                            windlat.append(obj["data"]["WS_WIND_LAT"])
                            stdwindir.append(obj["data"]["WIND_DIR_SDEV"])
                            try:
                                var.append(obj["data"][outputvar])
                            except:
                                var.append('')
                        
                except: 
                    print erroro
                    if savefileyn == 'y':
                        f.close()
                    else:
                        pass
                    #pdb.set_trace()
                    if peakplot == 'y':
                        pylab.figure("Concentrations")
                        pylab.subplot(3,1,1)
                        pylab.plot(time, ch4)
                        pylab.title("Concentrations")
                        pylab.ylabel ("CH4 (ppm)")
                        pylab.subplot(3,1,2)
                        pylab.plot(time, h2o)
                        pylab.ylabel("H2O")
                        pylab.subplot(3,1,3)
                        pylab.plot(time, co2)
                        pylab.xlabel("Epoch Time")
                        pylab.ylabel("CO2")
                        pylab.figure("Peripherals") #Assuming that the valves are off for first 50 pts
                        pylab.subplot(2,1,1)
                        pylab.plot(carspeed[:50])
                        pylab.title("Car speed")
                        pylab.subplot(2,1,2)
                        pylab.plot(windlat[:50])
                        pylab.title("Wind Lat")
                        pylab.figure("Std Wind Dev")
                        pylab.plot(stdwindir[:50])
                        pylab.show()
                    break
    except:
        True
    #print savefilename
    return savefilename, var

if __name__ == "__main__":
    filename = eg.fileopenbox(msg="File to unpickle") 
    readfunc(filename, 'n','y', '')
#    filename = r'C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\EPA\for paper\batch\plume_1368624776_2013_5_15__6_32.dat'
#    test = readfunc(filename,'n','n','WIND_DIR_SDEV')
#    conc =readfunc(filename,'n','n','CH4_dry')
#    speed = readfunc(filename,'n','n','CAR_SPEED')
#    pylab.subplot(3,1,1)
#    pylab.plot(conc[1][:50])
#    pylab.subplot(3,1,2)
#    pylab.plot(speed[1][:50])
#    pylab.subplot(3,1,3)
#    pylab.plot(test[1][:50])
#    pylab.show()