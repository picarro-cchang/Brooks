# -*- coding: utf-8 -*-
"""
Created on Sun Jan 20 10:06:40 2013

@author: ttsai

To understand Plume Scanner data
Takes in either pickled or unpickled data files
2. Takes the closest 0 to determine the final tape beginnings and endings

Input file columns:
    0: Time
    1: CH4_dry concentration
    2: H2O concentration
    3: Valve Mask
    4: "SpectrumID"
    5:["WS_WIND_LAT"]
    6:"WS_WIND_LON"]
    7:["CAR_SPEED"])
    8: GPS Lat
    9: GPS Long
    10: CO2

Output:
    0: Filename
    1: Carspeed
    2: Std Carspeed
    3: Weighted average wind speed
    4: Std wind speed
    5: Deltavol realignment
    6: Startends
    7: Background
    8: Peak values
    9: Hellman factor
    10: ans
    11: sec ans
    12: plumestartends
    13: lat
    14: long
    15: FWHM
    
v22 Has weighted average
v24 Takes into account the CO2 push gas and the CFADS upgrade
Output changed as windspeed is swapped for weightedaverage
Average carspeed, stdcar, and stdwind ONLY includes those interpolated
Replace error with plume startends
v24_vol: Utilize volume and timing to reconstruct pixels
"""

from numpy import *
from optparse import OptionParser
# replace this with wx
#import easygui as eg
import wx

import string
import pdb
import pylab
import scipy
import scipy.integrate
import time
from SavitzkyGolay import savitzky_golay as sv
from scipy.interpolate import griddata

###############################
#Open pickled .dat file or unpickled .txt file
#fileopenbox is to use a GUI to find the file
import little_reader


def typey(x):
    print x


def plume_analyzer(filenamepickle):
    if filenamepickle == '':
        d = wx.FileDialog(None, "File to unpickle",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                          wildcard="txt files (*.txt)|*.txt")

        if d.ShowModal() == wx.ID_OK:
            filenamepickle = d.GetPath()

            if filenamepickle[len(filenamepickle)-3:] == 'txt':
                filenamepickle = filenamepickle.replace("_unpickled.txt", ".dat")
            d.Destroy()
        else:
            # User canceled, bail
            d.Destroy()
            return

    #filenamepickle = eg.fileopenbox(msg="File to unpickle")
    ##filenamepickle = r'C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\Santa Clara Test\plume_1374778428_2013_7_25__11_53_unpickled.txt'
    ##filedir = r'C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\data\batch'
    ##usefulfilename = \
    ##'plume_1359662434_2013_1_31__13_0_unpickled.txt'
    ##filenamepickle = filedir+'\\'+usefulfilename

    #if filenamepickle[len(filenamepickle)-3:] == 'txt':
    #    filenamepickle = filenamepickle.replace("_unpickled.txt", ".dat")
        
    filename = little_reader.readfunc(filenamepickle, 'n', 'y', "CH4_dry")[0]

    #####
    #User set variable options. Set to "y" if you want to set variables
    upside = 'n'        # If push gas is positive, set to "y"

    backgroundyn = 'n'  # If background is mnaually input, set to "y"
    backgroundset = 1.93

    plumeset = 'n'      # If determining plume setpoints manually, set to "y"

    # Initially these were plumestart = 76 and plumeend = 100
    # TODO: Ask TracyT why they changed so much
    plumestart = 6
    plumeend = 98

    fwhmcalc = 'y'      # If calculating FWHM of plume width, set to "y" If set to "n', output is -1

    print filename

    #####################################
    #Pixel heights and vertical wind gradient corrections
    a = 0.17        # Hellman factor for vertical wind calculations

    def windfunc(a):
        """
        Power Law equation which returns scaling factor
        Anemoeter on Toyota 4Runner is measured 111 in above the ground
        Nissan Patrol anemometer is measured 117.5 in or 2.98 m from ground
        """
        #pixelheights = [1.01, 2.23, 3.45, 4.67]     #For Australia
        pixelheights = [0, 1.01, 2.23, 3.45, 4.67]  # For Australia
        #pixelheights = [0.5, 1.72, 2.94, 4.16]
        #pixelheights = [0, 0.5, 1.72, 2.94, 4.16]   #To include ground in calculations
        #pixelheights = [0, 0.432, 1.09, 1.75, 2.44]  #Plume Scanner Jr
        #ha = 2.82
        ha = 2.98
        w = [(i/ha)**a for i in pixelheights]
        return w, pixelheights

    w = windfunc(a)[0]
    pixelheights = windfunc(a)[1]
    #print "Adjust wind factors are: ", w

    ###################################################################
    #Loading data
    data = loadtxt(filename)
    valves = [x for x in data[:, 3]]    # converts the ndarray into a list
    onindex = valves.index(3)           # determines the index when the valves turn on completely
    pretape = data[1:onindex+10, :]     # Give ten points extra due to trigger happening so close to peak
    print "Data truncated at row %i" % onindex
    tapes = data[onindex:, :]
    samplerate = average(data[1:, 0] - data[:len(data) - 1, 0])
    #pylab.plot(tapes[:,1])
    #pylab.show()

    ####################################################################
    #Search for push gas to splice tapes
    def searchtapesbackground(tape, thres, upside='n'):
        """
        Utilizing background to find startends. This will only work if zero gas is negative
        """
        if upside == 'y':
            d = (tape-thres)*-1
        else:
            d = tape-thres
        #inisearch = [200, 400, 600]    # for old system
        inisearch = [300, 600, 1000]    # for new after first EPA campaign
        refinedsearch = [0]
        for i in inisearch:
            refinedsearch.append(argmin(d[i:i+100])+i)
        refinedsearch.sort()
        refinedsearch.append(1350)
        #refinedsearch.append(850)
        #print "Refined search areas are: ", refinedsearch
        secderiv = gradient(gradient(sv(tape, 15, 3)))
        startend = []
        for i in refinedsearch:
            if i > 50:
                ini = i - 50
            else:
                ini = i
            fin = i + 50
            temp = secderiv[ini:fin].argsort()[:2]+ini
            #to ensure that adjacent points aren't chosen
            count = 1
            while abs(temp[0] - temp[1]) <= 10:
                count += 1
                temp[1] = secderiv[ini:fin].argsort()[count+1]+ini
            temp[0] = temp[0]
            temp[1] = temp[1]
            startend.extend(temp)
    #        pylab.plot(tape[ini:fin])
    #        pylab.twinx()
    #        pylab.plot(secderiv[ini:fin])
    #        pylab.show()
    #        pdb.set_trace()
        return startend

    #startend = searchtapesbackground(tapes[:, 1],min(pretape[:, 1]))      # Use if CH4 is used as push gas
    startend = searchtapesbackground(tapes[:, 10], min(pretape[:, 10]))   # Use if CO2 is used as push gas
    #pdb.set_trace()
    #startend = searchtapesbackground(tapes[:,10],min(pretape[:,2]), upside)
    startend = startend[1:len(startend)-1]
    startend.sort()
    print startend
    if startend[0] < 10:
        startend[0] = startend[0] + 20
        print startend

    def searchbetter(tape, tempstartend, threshold, buff, upside='n'):
        """
        Find nearest "0"
        Assuming that it is negative zero gas
        """
        #pdb.set_trace()
        startend = []
        secderiv = gradient(gradient(tape))
        # threshold for determining 0ness
        for index, item in enumerate(tempstartend):
            if index % 2 != 0:  # odd number indices
                temptest = secderiv[item-buff:item]
                if upside == 'n':
                    startend.append(item - buff + [ind for ind, it in enumerate(temptest) if abs(it) < threshold][-1])   # assuming that it is monotonically decreasing
                else:
                    startend.append(item-buff+[ind for ind, it in enumerate(temptest) if abs(it) < threshold][0])    # assuming that it is monotonically increasing
            else:
                temptest = secderiv[item:item+buff]
                if upside == 'n':
                    startend.append(item+[ind for ind, it in enumerate(temptest) if abs(it) < threshold][0])         # assuming that it is monotonically increasing
                else:
                    startend.append(item+[ind for ind, it in enumerate(temptest) if abs(it) < threshold][-1])        # assuming that it is monotonically decreasing
        return startend

    try:
        #startendnew = searchbetter(tapes[:, 1], startend, 0.01, 10)             # for nice peaks
        startendnew = searchbetter(tapes[:, 10], startend, 0.05, 50, upside)    # Using CO2
        #startendnew = searchbetter(tapes[:, 1], startend,0.05, 15, upside)
    except:
        print "Automatic startends fail"
        startendnew = startend

    ########################################################################
    #Set up GUI to determine startends
    import Tkinter
    root = Tkinter.Tk()
    root.withdraw()
    import tkSimpleDialog

    pylab.figure("Tape startpoints")
    pylab.subplot(3, 1, 1)        # Top plot will be with CH4
    pylab.ylabel("CH4 search")
    pylab.xlabel("Row numbers")
    pylab.scatter(startendnew, tapes[startendnew, 1])
    pylab.plot(tapes[:, 1])
    pylab.subplot(3, 1, 2)        # CO2
    pylab.ylabel("C02 search")
    pylab.scatter(startendnew, tapes[startendnew, 10])
    pylab.plot(tapes[:, 10])
    pylab.ion()
    pylab.show()

    tempstartend = tkSimpleDialog.askstring("Fix startends", str(startend), initialvalue=str(startend))
    startendnew = [float(i.strip()) for i in tempstartend.lstrip('[').rstrip(']').split(',')]
    startend = startendnew

    pylab.subplot(3, 1, 3)
    #pylab.plot(gradient(gradient(sv(tapes[:,1], 15,3))))
    #pylab.scatter(startend, gradient(gradient(sv(tapes[:,1], 15,3)))[startend])
    pylab.ylabel("CH4 another search")
    pylab.xlabel("Row numbers")
    pylab.scatter(startendnew, tapes[startendnew, 1])
    pylab.plot(tapes[:, 1])
    pylab.ioff()

    #####################################################
    #Spliced tapes, NOT reconstructed with respect to distance
    tapeA = tapes[startend[1]:startend[0]:-1, :]    # TapeA is played in reverse so reversed here
    tapeB = tapes[startend[2]:startend[3], :]
    tapeC = tapes[startend[5]:startend[4]:-1, :]    # TapeC is played in reverse so reversed here
    tapeD = tapes[startend[6]:startend[7], :]

    """
    Wind selection for average; use first derivatives in pretape to determine
    where the CH4 plume occurred and use those wind measurements for diagnostics
    """
    firstderiv = diff(pretape[:, 1])
    if plumeset == 'n':
        tempplumestart = argmax(firstderiv)
        tempplumeend = argmin(firstderiv[5:]) + 5
        plumestartend = sort(searchbetter(pretape[:, 1], [tempplumestart, tempplumeend], 1, 7, 'y'))
        plumestart = plumestartend[0]
        plumeend = plumestartend[1]

    delay = 4*2  # approx anemometer delay is 4 s, considering about 2 pts per second
    windstart = plumestart + delay
    windend = plumestart + delay + (plumeend-plumestart)

    print "max: %i, min: %i" % (windstart, windend)
    stdwind = std(data[windstart:windend, 5])
    carspeed = average(data[plumestart:plumeend, 7])
    stdcar = std(data[plumestart:plumeend, 7])

    ####################################################################################\
    #Calculate background
    def backgroundcalc(pretape, tapearray):
        """
        2% oflowest values. It only takes in 1D array of ch4
        """
        pretapemin = min(pretape)       # lowest 2% of 50 pts is barely 1 pt
        backgroundarray = [pretapemin]
        for i in tapearray:
            #if the background in tapes is 5% too different then its prob zero gas
            if (min(i) < pretapemin * (1 - 0.05)) or (min(i) > pretapemin * (1 + 0.05)):
                print "Poor tape cut affecting background calc"
            else:
                #cutoff = int(round(0.02*len(i)))
                # Had to use 5% to account for the poor tape cutting
                cutoff = int(round(0.5*len(i)))

                # 5pt buffer for poor tape cutting
                backgroundarray.append(average(sort(i)[5:cutoff]))
        background = min(backgroundarray)
        return background

    """
    Plume reconstruction
    Flow corrections would be in this section of code
    """

    def volumizer(tape, flow):
        """
        Calculating volume for all tapes
        time array is in seconds and must be first column in tape input
        Flow is in sccm
        t = 0 when the tape "ends" since you chose to reverse the time for the tapes
        because you reversed the time for the instrument intake by taking when valves switch on
        to mean t = 0 for instrument inlet. Physically incorrect but two wrongs make a right
        """
        temptape = tape
        initime = tape[len(tape)-1, 0]
        for i in range(len(tape)):
            temptape[i, 0] = abs(temptape[i, 0]-initime) * (1/60.0) * flow
        return temptape

    tapeAplot = volumizer(tapeA, 390.0)      # The instrument flow analyzed is 390 sccm
    tapeBplot = volumizer(tapeB, 390.0)
    tapeCplot = volumizer(tapeC, 390.0)
    tapeDplot = volumizer(tapeD, 390.0)

    temptime = pretape[onindex, 0]      # Use t=0 at which valves switch on
    pretapetime = pretape[:, 0]
    pretapevol = [(temptime - i) * (1/60.0) * 1070.0 for i in pretapetime]      # 1070 sccm recording flow
    pylab.figure("peak realignment")
    pylab.subplot(2, 1, 1)
    pylab.xlabel("Vol (scc)")
    pylab.ylabel("CH4 conc (ppm)")
    pylab.plot(tapeAplot[:, 0], tapeAplot[:, 1], label='tapeA')
    pylab.plot(tapeBplot[:, 0], tapeBplot[:, 1], label='tapeB')
    pylab.plot(tapeCplot[:, 0], tapeCplot[:, 1], label='tapeC')
    pylab.plot(tapeDplot[:, 0], tapeDplot[:, 1], label='tapeD')
    pylab.plot(pretapevol, pretape[:, 1], label='pretape')
    pylab.legend(loc='upper right')

    """
    align volumes with pixel B, assuming pixel B is co-located with instrument monitoring tube for pretape
    """
    deltavol = pretapevol[argmax(pretape[:, 1])] - tapeBplot[argmax(tapeBplot[:, 1]), 0]
    print "Vol adjusted by %f scc" % (deltavol)
    pretapevol = pretapevol - deltavol
    pretaperecon = pretape
    pretaperecon[:, 0] = pretapevol

    def interpolator(tapedeck, pretaperecon):
        """
        Interpolate tape points onto the sparser point grid of pretape
        """
        newx = pretaperecon[:, 0]
        newtapedeck = []
        minarray = []
        maxarray = []
        for i in tapedeck:
            points = i[:, 0]
            values = i[:, 1]
            intertape = griddata(points, values, newx, method='linear')
            temptape = transpose(vstack([newx, intertape]))
            temptape = temptape[~isnan(temptape).any(1)]     # get rid of NAN
            #print temptape[0, 0], temptape[len(temptape)-1, 0]
            maxarray.append(temptape[0, 0])
            minarray.append(temptape[len(temptape) - 1, 0])
            newtapedeck.append(temptape)
        #pdb.set_trace()
        print "Min vol and max vol on pretape: %f scc and %f scc" % (pretaperecon[len(pretaperecon)-1, 0], pretaperecon[0, 0])
        minvol = max(minarray)
        maxvol = min(maxarray)
        newerx = []
        indexarray = []
        for index, item in enumerate(pretaperecon[:, 0]):
            if item <= maxvol and item >= minvol:
                newerx.append(item)
                indexarray.append(index)
        print "new min and max time: %f scc and %f scc" % (minvol, maxvol)
        newertapedeck = []
        for i in tapedeck:
            points = i[:, 0]
            values = i[:, 1]
            intertape = griddata(points, values, newx, method='linear')
            temptape = transpose(vstack([newerx, intertape[indexarray]]))
            newertapedeck.append(temptape)
        return newertapedeck, indexarray, minvol, maxvol

    tempans = interpolator([tapeAplot, tapeBplot, tapeCplot, tapeDplot], pretaperecon)
    newtapedeck = tempans[0]
    indexarray = tempans[1]
    minvol = tempans[2]
    maxvol = tempans[3]
    pretapetrunc = pretaperecon[indexarray, :]
    #pylab.plot(newtapedeck[0][:,0], newtapedeck[0][:,1], label = 'tapeA')
    #pylab.plot(newtapedeck[1][:,0], newtapedeck[1][:,1], label = 'tapeB')
    #pylab.plot(newtapedeck[2][:,0], newtapedeck[2][:,1], label = 'tapeC')
    #pylab.plot(newtapedeck[3][:,0], newtapedeck[3][:,1], label ='tapeD')
    #pylab.plot(pretaperecon[:,0], pretaperecon[:,1], label = 'pretape')
    #pylab.legend(loc = 'upper right')
    #pylab.show()

    """
    !!!! BACKGROUND HERE !!!!!!!!!!!!!!!!!!!!
    """
    if backgroundyn == 'y':
        print "Using set background"
        background = backgroundset
    else:
        print "Using automatic background"
        # (Rounding to the third decimal)
        background = round(backgroundcalc(pretape[:50, 1], [tapeAplot[:, 1], tapeBplot[:, 1], tapeCplot[:, 1], tapeDplot[:, 1]])*1000)*10**-3
    print "Background is %f ppm" % background

    def distanceGPS(pretape):
        """
        calculate distance based on GPS coords
        Assuming a flat surface since elevation isn't taken into account
        Col 8 is Lat
        col 9 is long
        """
        import math
        lat = pretape[:, 8] * (math.pi/180)
        lon = pretape[:, 9] * (math.pi/180)
        dist = [0]
        for index in range(len(lat)-1):
            rd = 6371*10**3     # radius of earth
            # Using the spherical law of cosines
            tempdist = math.acos(sin(lat[index])*math.sin(lat[index+1]) +
                                 math.cos(lat[index])*math.cos(lat[index+1]) * math.cos(lon[index+1]-lon[index])) * rd
            dist.append(tempdist + dist[index])
        return dist

    dist = distanceGPS(pretapetrunc)
    tapeAdist = transpose(vstack([dist, newtapedeck[0][:, 1]]))
    tapeBdist = transpose(vstack([dist, newtapedeck[1][:, 1]]))
    tapeCdist = transpose(vstack([dist, newtapedeck[2][:, 1]]))
    tapeDdist = transpose(vstack([dist, newtapedeck[3][:, 1]]))

    def backgrounder(tape, background):
        """
        subtract background without going negative
        """
        y = []
        x = [t for t in tape[:, 0]]
        tracker = 0
        for item in tape[:, 1]:
            if item - background < 0:
                y.append(0)
                tracker += 1
            else:
                y.append(item-background)
        print "Percentage negative: %f" % ((tracker/float(len(tape)))*100)
        return transpose(vstack([x, array(y)]))
        
    tapeArecon = backgrounder(tapeAdist, background)
    tapeBrecon = backgrounder(tapeBdist, background)
    tapeCrecon = backgrounder(tapeCdist, background)
    tapeDrecon = backgrounder(tapeDdist, background)

    pylab.subplot(2, 1, 2)
    pylab.xlabel("Reconstructed tapes without background (m)")
    pylab.ylabel("CH4 conc (ppm) - %f ppm" % background)
    pylab.plot(tapeArecon[:, 0], tapeArecon[:, 1], label='tapeA')
    pylab.plot(tapeBrecon[:, 0], tapeBrecon[:, 1], label='tapeB')
    pylab.plot(tapeCrecon[:, 0], tapeCrecon[:, 1], label='tapeC')
    pylab.plot(tapeDrecon[:, 0], tapeDrecon[:, 1], label='tapeD')
    pylab.legend(loc='upper left')
    pylab.ioff()

    """
    Wind used for flux calculations used here
    """
    windindex = [x+delay for x in indexarray]
    windlat = data[windindex, 5]
    pylab.figure("Carspeed and windspeed")
    ax1 = pylab.subplot(3, 1, 1)    # Top plot will be with CH4
    pylab.ylabel("CH4")
    pylab.plot(data[:100, 1])
    pylab.scatter([plumestart, plumeend], [data[plumestart, 1], data[plumeend, 1]], s=40, marker='^', c='r')
    pylab.subplot(3, 1, 2, sharex=ax1)
    pylab.ylabel("Carspeed")
    pylab.plot(data[:100, 7])
    pylab.scatter(indexarray, data[indexarray, 7])
    pylab.scatter([plumestart, plumeend], [data[plumestart, 7], data[plumeend, 7]], s=40, marker='^', c='r')
    pylab.subplot(3, 1, 3, sharex=ax1)
    pylab.ylabel("Wind")
    pylab.xlabel("Row numbers")
    pylab.plot(data[:100, 5])
    pylab.scatter(windindex, data[windindex, 5])
    pylab.scatter([windstart, windend], [data[windstart, 5], data[windend, 5]], s=40, marker='^', c='r')
    pylab.xlim([0, len(data[:100])])
    pylab.ion()
    pylab.show()
    pylab.ioff()

    ##################################################
    """
    Weighted average
    """

    def weightaverage(tapeB, windlat):
        """
        Use tapeB since co-located with instrument monitoring inlet tube so I can
        avoid using pretape
        For simplicity, ignore the power law
        """
        #winner = max(tapeB[:,1])
        #numerator = sum([(x/winner) for x in tapeB[:,1]]*windlat)
        numerator = sum([(x) for x in tapeB[:, 1]]*windlat)
        denominator = sum([x for x in tapeB[:, 1]])
        return average(numerator/denominator)

    #weightaverage = weightaverage([tapeArecon, tapeBrecon, tapeCrecon, tapeDrecon], windlat, w)
    weightaverage = weightaverage(tapeBrecon, windlat)
    print "\nWeighted average is %f" % weightaverage

    #Use Simpson rule for integration. The format is integrate y over x axis is simps.(y,x)
    #Utilize a wind correction factor, w

    def piecewiseIntegrator(tape, windfactor, windlat):
        sums = []
        for i in range(len(tape)-2):
            windbit = average(windlat[i:i+2])
            sums.append(scipy.integrate.simps(tape[i:i+2, 1], tape[i:i+2, 0])*windfactor*windbit)
        return sum(sums)
            
    ################For use if ground included
    
    tapeAint = piecewiseIntegrator(tapeArecon, w[1], windlat)
    tapeBint = piecewiseIntegrator(tapeBrecon, w[2], windlat)
    tapeCint = piecewiseIntegrator(tapeCrecon, w[3], windlat)
    tapeDint = piecewiseIntegrator(tapeDrecon, w[4], windlat)
    zarray = transpose(vstack([pixelheights, array([0, tapeAint, tapeBint, tapeCint, tapeDint])]))
    
    ###############For use if ground is NOT included
    '''
    tapeAint = piecewiseIntegrator(tapeArecon, w[0], windlat)
    tapeBint = piecewiseIntegrator(tapeBrecon, w[1], windlat)
    tapeCint = piecewiseIntegrator(tapeCrecon, w[2], windlat)
    tapeDint = piecewiseIntegrator(tapeDrecon, w[3], windlat)
    zarray = transpose(vstack([pixelheights, array([tapeAint, tapeBint, tapeCint, tapeDint])]))
    '''
    #pylab.figure("Y line integrations wrt height")
    #pylab.xlabel("Height (m)")
    #pylab.ylabel("Y line integration")
    #pylab.plot(zarray[:,0], zarray[:,1])
    #pylab.show()
    #Use trapezoidal integration
    ans = abs(scipy.integrate.trapz(zarray[:, 1], x=zarray[:, 0])*10**-6)
    print "%f liters per sec" % (ans*10**3)
    #err = sqrt((stdcar/carspeed)**2+(stdwind/windspeed)**2) #Error is calculated only for wind and car and is decimal percentage
    err = -1
    """
    According the weather.gov, at 11:53am in Vernal, UT
    Temperature = 22F or -5.6C
    Wind = E at 6mph
    Uintah basin has typical elevation of 5,000 to 5,500 feet or 1524 to 1676.4 m
    Pick the highest point but use typical alitude/pressure equation: 101325*(1 - 2.25577*10**-5*h)**5.25588
    """
    #Converting to g/s using ideal gas law in Vernal, UT
    p = 101325*(1 - 2.25577*10**-5*1676.4)**5.25588     # in Pa units
    T = -5.6 + 273.15   # in Kelvin
    R = 8.3144621       # in Pa*m^3*K-1*mol-1
    M = 16.04           # g/mol molar mass of methane
    mass = (p*ans*M)/(T*R)
    #print "%f g/s" %mass
    #print "%f SCFH" %(ans*10**3*3600/28.32)
    #secans =(ans*10**3*3600/28.32)
    print "%f slpm" % (ans*10**3*60)
    secans = ans*10**3*60

    def widthinator(tapelist, background=0):
        """
        tapelist must be in the order of A, B, C, and D
        Determine the FWHM of the plume with the highest peak concentration
        """
        maxarray = []
        for i in tapelist:
            maxarray.append(max(i[:, 1]))
        winner = argmax(maxarray)
        hmax = ((maxarray[winner]-background)/2.0)
        print hmax

        # Note: txtlabel is assigned but never used
        if winner == 0:
            txtlabel = "TapeA"
            tape = tapelist[0]
        elif winner == 1:
            txtlabel = "TapeB"
            tape = tapelist[1]
        elif winner == 2:
            txtlabel = "TapeC"
            tape = tapelist[2]
        elif winner == 3:
            txtlabel = "TapeD"
            tape = tapelist[3]
        else:
            print "I don't know what is going on here."
        peakloc = argmax(tape[:, 1])
        width = []
        width.append(argsort(abs(tape[:peakloc, 1]-hmax-background))[0])
        width.append(argsort(abs(tape[peakloc:, 1]-hmax-background))[0]+peakloc)
    #    print width
    #    pylab.figure(txtlabel)
    #    pylab.scatter(tape[width, 0], tape[width, 1])
    #    pylab.scatter(tape[peakloc, 0],tape[peakloc, 1])
    #    pylab.plot(tape[:, 0], tape[:, 1])
    #    pylab.show()
        return tape[width[1], 0]-tape[width[0], 0]

    if fwhmcalc == 'y':
        try:
            fwhm = widthinator([tapeAdist, tapeBdist, tapeCdist, tapeDdist], background)
            print "FWHM is %f m" % (fwhm)
        except:
            print "Fail"
            fwhm = -1.0
    else:
        fwhm = -1.0

    """
    Getting GPS info of the highest peak point
    """
    peakindex = argmax(pretape[:, 1])
    gpslat = pretape[peakindex, 8]
    gpslong = pretape[peakindex, 9]
    print '\n'

    #plot3D = raw_input("Plot 3D? \n")
    plot3D = 'y'

    if plot3D == 'y':
        """Setting plot dimensions"""
        #userDefinedXMin = raw_input("Input YMin \n") #X is horizontal i.e. it is y axis in Tracy convention
        userDefinedXMin = 'n'
        if userDefinedXMin.isalpha() is True:
            minDistance = min(tapeAdist[:, 0])
        else:
            minDistance = float(userDefinedXMin)
        #userDefinedXMax = raw_input("Input YMax \n")
        userDefinedXMax = 'n'
        if userDefinedXMax.isalpha() is True:
            maxDistance = max(tapeAdist[:, 0])
            
        else:
            maxDistance = float(userDefinedXMax)

        if maxDistance-minDistance < 50:
            aspect = 2.
        elif maxDistance-minDistance > 50 and maxDistance-minDistance < 100:
            aspect = 4.
        elif maxDistance-minDistance > 100 and maxDistance-minDistance < 200:
            aspect = 6.
        elif maxDistance-minDistance > 200 and maxDistance-minDistance < 250:
            aspect = 10.
        elif maxDistance-minDistance > 351:
            aspect = 20.
        else:
            aspect = 10.
        
        YCoords = []
        """Default heights of the pixels: plume scanner configuration from Uinta trip in February 2013"""
        #z0 = 20*2.54/100.
        z0 = 1.01   # Australia car was really high
        dz = 48*2.54/100.
        '''For Plume Scanner Jr'''
    #    z0 = 0.432  # Include the bottom point for calculations
    #    dz = 27*2.54/100.
        for i in range(4):
            YCoords.append(z0 + i*dz)
        yPad = 0.001
        maxHeight = YCoords[len(YCoords)-1] + yPad
        minHeight = YCoords[0] - yPad
        nY = 8j
        nX = 0
        xInterpFactor = 0.8

        def getPoints(tape, YCoordindex):
            """getting all the plot points: selected points that did NOT have
            background subtracted"""
            points = []
            for i in range(len(tape)):
                y = YCoords[YCoordindex]
                points.append((tape[i, 0], y))
            return points
                
        pointsA = getPoints(tapeAdist, 0)
        pointsB = getPoints(tapeBdist, 1)
        pointsC = getPoints(tapeCdist, 2)
        pointsD = getPoints(tapeDdist, 3)
        points = vstack([pointsA, pointsB, pointsC, pointsD])
        points = [n for n in points]    # convert to list
        values = hstack([tapeAdist[:, 1], tapeBdist[:, 1], tapeCdist[:, 1], tapeDdist[:, 1]])
        values = [v for v in values]    # convert to list
        """Interperlating data for plotting"""
        nInterp = nX
        if nX == 0 and len(YCoords) > 0:
            nInterp = (1j) * int(xInterpFactor*(len(points)/len(YCoords)))
            nX = nInterp
            nInterp = xInterpFactor*(1j)*int(len(points)/4)
        grid_x, grid_y = mgrid[minDistance:maxDistance:nInterp, minHeight:maxHeight:nY]
        grid_z1 = griddata(points, values, (grid_x, grid_y), method='linear')
        interpGridX = grid_x
        interpGridY = grid_y
        interpGridZ = grid_z1
        grid_x = interpGridX
        grid_y = interpGridY
        grid_z = interpGridZ
        
        """Plotting"""
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        mpl.rcParams['font.size'] = 16
        fig = plt.figure(figsize=(20, 10), dpi=80)
        cax = plt.imshow(grid_z.T, extent=(minDistance, maxDistance, minHeight-yPad, maxHeight+yPad), aspect=aspect, origin='lower')
        plt.xlim(minDistance, maxDistance)
        plt.ylim(minHeight, maxHeight)
        points = array(points)      # It has to be reconverted into array!!
        values = array(values)
        plt.plot(points[:, 0], points[:, 1], 'k.', ms=3)
        plt.xlabel('Horizontal Position [m]', fontsize='large')
        plt.ylabel('Vertical Position [m]', fontsize='large')
        cbar = fig.colorbar(cax, orientation='horizontal')
        cbar.set_label('CH4 Concentration [ppm]', fontsize='large')
        plt.draw()
        plt.figtext(0.01, 0.96, filename)
        plt.figtext(0.01, 0.93, "v24sr_vol saved " + time.asctime(time.localtime()))
        plt.figtext(0.01, 0.90, "Carspeed %f m/s with %f m/s" % (carspeed, stdcar))
        plt.figtext(0.01, 0.87, "Windspeed %s m/s with %f m/s and weighted average of %f" % (weightaverage, stdwind, weightaverage))
        plt.figtext(0.01, 0.84, "Background %f ppm" % background)
        plt.figtext(0.01, 0.81, "GPS Lat: %f; GPS Long: %f" % (gpslat, gpslong))
        plt.figtext(0.01, 0.78, "Flux: %f L/s or %f lpm" % ((ans*10**3), secans))
        #print aspect
        #print max(maxarray)
        #savePlot = raw_input("Save plot? \n")
        savePlot = 'y'
        if savePlot == 'y':
            fn = filename[:len(filename)-14]+'_v24_vol_figure.png'
            fig.savefig(fn)
        plt.show()

    root = Tkinter.Tk()
    root.withdraw()

    import tkSimpleDialog
    test = tkSimpleDialog.askstring("Ans",
                                    filename[filename.rfind('\\')+1:] + "\t" +
                                    string.ljust(str(carspeed), 12) + "\t" +
                                    string.ljust(str(stdcar), 12) + "\t" +
                                    string.ljust(str(weightaverage), 12)+"\t" +
                                    string.ljust(str(stdwind), 12)+"\t" +
                                    string.ljust(str(deltavol), 12)+"\t" +
                                    string.ljust(str(startend), 12)+"\t" +
                                    string.ljust(str(background), 12)+"\t" +
                                    '[' + "%.2f" % (max(tapeArecon[:, 1]+background)) + ", %.2f" % (max(tapeBrecon[:, 1]+background)) + ", %.2f" % (max(tapeCrecon[:, 1])+background) + ", %.2f" % (max(tapeDrecon[:, 1])+background) + ']' + "\t" +
                                    string.ljust(str(a), 12) + "\t" +
                                    string.ljust(str(ans*10**3), 12) + "\t" +
                                    string.ljust(str(secans), 12) + "\t" +
                                    string.ljust('['+str(plumestart) + ',' + str(plumeend)+']', 12) + "\t" +
                                    string.ljust(str(gpslat), 12) + "\t" +
                                    string.ljust(str(gpslong), 12) + "\t" +
                                    string.ljust(str(fwhm), 12),
                                    initialvalue=filename[filename.rfind('\\')+1:] + "\t" +
                                    string.ljust(str(carspeed), 12) + "\t" +
                                    string.ljust(str(stdcar), 12) + "\t" +
                                    string.ljust(str(weightaverage), 12) + "\t" +
                                    string.ljust(str(stdwind), 12) + "\t" +
                                    string.ljust(str(deltavol), 12) + "\t" +
                                    string.ljust(str(startend), 12) + "\t" +
                                    string.ljust(str(background), 12) + "\t" +
                                    '[' + "%.2f" % (max(tapeArecon[:, 1]+background)) + ", %.2f" % (max(tapeBrecon[:, 1]+background)) + ", %.2f" % (max(tapeCrecon[:, 1])+background)+", %.2f" % (max(tapeDrecon[:, 1])+background)+']'+"\t" +
                                    string.ljust(str(a), 12) + "\t" +
                                    string.ljust(str(ans*10**3), 12) + "\t" +
                                    string.ljust(str(secans), 12) + "\t" +
                                    string.ljust('['+str(plumestart) + ',' + str(plumeend) + ']', 12) + "\t" +
                                    string.ljust(str(gpslat), 12) + "\t" +
                                    string.ljust(str(gpslong), 12) + "\t" +
                                    string.ljust(str(fwhm), 12))
    return ans, filename

#def main():
#    parser = OptionParser()
#    parser.add_option("-f", dest="filename", default='',
#        help="Filename and address")
#    (options, args) = parser.parse_args()
#    myfunc = plume_analyzer(options.filename)
#
#if __name__ == "__main__":
#    main()
if __name__ == "__main__":
    filename = eg.fileopenbox(msg="File to unpickle")
    plume_analyzer(filename)
