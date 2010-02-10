#!/usr/bin/python
#
# File Name: Autocal1.py
# Purpose: Utilities for automatic calibration of the wavelength monitor for CRDS.
#
# Notes:
#
# File History:
# 06-11-07 sze   Created file
# 07-01-02 sze   Added WLM_OFFSET into INI file to avoid overuse of NVRAM
# 07-01-26 sze   Back ported into new hostcore code
# 07-11-05 sze   Added original spline coefficients in the autocal INI file and a relaxTowardsOriginal function
#                 for WLM calibration.
# 08-09-18 alex  Replaced SortedConfigParser with CustomConfigObj
# 08-12-03 alex  Update it with the newer Autocal1 (merge)
# 10-02-10 sze   Backported CPU reduction code fix from Apache G1000 code (Ticket #16)

from numpy import *
from calUtilities import WlmFile, parametricEllipse
from calUtilities import bestFit, bestFitCentered
from calUtilities import bspEval, bspInverse, bspUpdate
from calUtilities import getFitParameters, setFitParameters
from CustomConfigObj import CustomConfigObj
import cPickle
import threading
import time
AutocalStatus_NonMonotonic = 1

class AutoCal(object):
    # Calibration requires us to store:
    # Laser calibration constants which map laser temperature to WLM angle
    # WLM constants: ratio1Center, ratio2Center, ratio1Scale, ratio2Scale, wlmPhase, wlmTempSensitivity, tEtalonCal
    # Spline scaling constants: dTheta, thetaBase
    # Linear term for spline: sLinear
    thetaMeasured = None
    wavenumberMeasured = None

    def __init__(self):
        self.lock = threading.Lock() # Protects access to the parameters
        self.offset = 0
        self.autocalStatus = 0  #  If this is non-zero, an error has occured in the frequency-angle conversion
                                #  Currently bit 0 indicates a non-monotonic spline for frequency conversion
                                #  Reset whenever the Autocal object is reloaded from an INI or WLM file

    def loadFromWlm(self,wlmFileName,dTheta = pi/16):
        wlmFileData = WlmFile(wlmFileName)
        self.lock.acquire()
        try:
            # Fit ratios to a parametric ellipse
            self.ratio1Center,self.ratio2Center,self.ratio1Scale,self.ratio2Scale,self.wlmPhase = \
                parametricEllipse(wlmFileData.Ratio1,wlmFileData.Ratio2)
            # Ensure that both ratioScales are larger than 1.05 to avoid issues with ratio multipliers exceeding 1
            factor = 1.05/min([self.ratio1Scale,self.ratio2Scale])
            self.ratio1Scale *= factor
            self.ratio2Scale *= factor
            self.tEtalonCal = wlmFileData.Tcal
            # Calculate the unwrapped WLM angles
            X = wlmFileData.Ratio1 - self.ratio1Center
            Y = wlmFileData.Ratio2 - self.ratio2Center
            thetaCalMeasured = unwrap(arctan2(
              self.ratio1Scale * Y - self.ratio2Scale * X * sin(self.wlmPhase),
              self.ratio2Scale * X * cos(self.wlmPhase)))
            # Extract parameters of angle vs laser temperature
            self.__laserTemp2ThetaCal = bestFitCentered(wlmFileData.TLaser,thetaCalMeasured,3)
            self.__thetaCal2LaserTemp = bestFitCentered(thetaCalMeasured,wlmFileData.TLaser,3)
            # Extract parameters of wavenumber against angle
            thetaCal2WaveNumber = bestFit(thetaCalMeasured,wlmFileData.WaveNumber,1)
            # Include Burleigh data in object for plotting and debug
            AutoCal.thetaMeasured = thetaCalMeasured
            AutoCal.wavenumberMeasured = wlmFileData.WaveNumber
            # Extract spline scaling constants
            self.thetaBase = thetaCalMeasured.min()
            self.dTheta = dTheta
            self.sLinear0 = array([thetaCal2WaveNumber.coeffs[0]*self.dTheta,
                                  thetaCal2WaveNumber([self.thetaBase])[0]],dtype="d")
            self.sLinear = self.sLinear0 + array([0.0,self.offset])
            # Find number of spline coefficients needed and initialize the coefficients to zero
            self.nCoeffs = int(ceil(ptp(thetaCalMeasured)/self.dTheta))
            self.coeffs = zeros(self.nCoeffs,dtype="d")
            self.coeffsOrig = zeros(self.nCoeffs,dtype="d")
            # Temperature sensitivity of etalon
            self.wlmTempSensitivity = -0.185 * (mean(wlmFileData.WaveNumber)/6158.0)# radians/degC
            self.autocalStatus = 0
        finally:    
            self.lock.release()
        return self

    def getAutocalStatus(self):
        return self.autocalStatus

    def ratios2thetaCal(self,ratio1,ratio2,tEtalon):
        """Apply etalon temperature correction to vectors of measured ratios in order to obtain WLM angles at the
        reference temperature"""
        self.lock.acquire()
        try:
            X = ratio1 - self.ratio1Center
            Y = ratio2 - self.ratio2Center
            return self.wlmTempSensitivity * (tEtalon - self.tEtalonCal) + arctan2(
              self.ratio1Scale * Y - self.ratio2Scale * X * sin(self.wlmPhase),
              self.ratio2Scale * X * cos(self.wlmPhase))
        finally:
            self.lock.release()

    def thetaCal2WaveNumber(self,thetaCal):
        """Look up in current calibration to get wavenumbers from WLM angles"""
        self.lock.acquire()
        try:
            x = (thetaCal-self.thetaBase)/self.dTheta
            return bspEval(self.sLinear,self.coeffs,x)
        finally:
            self.lock.release()

    def thetaCalAndLaserTemp2WaveNumber(self,thetaCal,tLaser):
        """Use laser temperature to place calibrated angles on the correct revolution and look up in current calibration to get
        wavenumbers"""
        self.lock.acquire()
        try:
            thetaHat = self.__laserTemp2ThetaCal(tLaser)
            thetaCal += 2*pi*floor((thetaHat-thetaCal)/(2*pi)+0.5)
            x = (thetaCal-self.thetaBase)/self.dTheta
            return bspEval(self.sLinear,self.coeffs,x)
        finally:
            self.lock.release()

    def laserTemp2ThetaCal(self,laserTemp):
        """Determine calibrated WLM angle associated with given laser temperature"""
        self.lock.acquire()
        try:
            return self.__laserTemp2ThetaCal(laserTemp)
        finally:
            self.lock.release()

    def thetaCal2LaserTemp(self,thetaCal):
        """Determine laser temperature to target to achieve a particular calibrated WLM angle"""
        self.lock.acquire()
        try:            
            return self.__thetaCal2LaserTemp(thetaCal)
        finally:
            self.lock.release()

    def waveNumber2ThetaCal(self,waveNumbers):
        """Look up current calibration to find WLM angle for a given wavenumber"""
        self.lock.acquire()
        try: 
            result, monotonic = bspInverse(self.sLinear,self.coeffs,waveNumbers)
            if not monotonic: self.autocalStatus |= AutocalStatus_NonMonotonic
            return self.thetaBase + self.dTheta * result
        finally:
            self.lock.release()

    def thetaCal2RatioMultipliers(self,thetaCal,tEtalon):
        """Calculate locking parameters for a particular set of WLM angles"""
        self.lock.acquire()
        try: 
            theta = thetaCal - self.wlmTempSensitivity * (tEtalon - self.tEtalonCal)
            ratio1Multiplier = -sin(theta + self.wlmPhase)/(self.ratio1Scale * cos(self.wlmPhase))
            ratio2Multiplier = cos(theta)/(self.ratio2Scale * cos(self.wlmPhase))
            return (ratio1Multiplier,ratio2Multiplier)
        finally:
            self.lock.release()

    def updateWlmCal(self,thetaCal,waveNumbers,weights=1,relax=5e-3,relative=True,relaxDefault=5e-3,relaxZero=5e-5):
        """Update the calibration coefficients
        thetaCal      array of calibrated WLM angles
        waveNumbers   array of waveNumbers to which these angles map
        weights       array of weights. The wavenumber residuals are DIVIDED by these before being used for correction.
        relax         relaxation parameter of update
        relative      True if only waveNumber differences are significant
                      False if absolute waveNumbers are specified
        relaxDefault  Factor used to relax coefficients towards the original default values.
                      Relaxation takes place with Laplacian regularization.
        """
        self.lock.acquire()
        try: 
            nExtra = 10
            x = (thetaCal-self.thetaBase)/self.dTheta
            currentWaveNumbers = bspEval(self.sLinear,self.coeffs,x)
            res = waveNumbers - currentWaveNumbers
            if relative:
                res = res - mean(res)

            res = res/weights
            # Pad out x and res so that the edges taper linearly to zero. This helps avoid
            #  discontinuities and non-monotonicity in the WLM model
            # imin = x.argmin()
            # imax = x.argmax()
            # sepAverage = (x[imax]-x[imin])/len(x)
            # xminExtra = x[imin] - xsepAverage*(arange(0,nExtra) + 1)
            # xmaxExtra = x[imax] + xsepAverage*(arange(0,nExtra) + 1)
            # rminExtra = res[imin] * (nExtra - arange(0,nExtra))/(nExtra+1.0)
            # rmaxExtra = res[imax] * (nExtra - arange(0,nExtra))/(nExtra+1.0)

            #self.coeffs += relax*bspUpdate(self.nCoeffs,
            #                  concatenate(seq=(x,xminExtra,xmaxExtra),axis=None),
            #                  concatenate(seq=(res,rminExtra,rmaxExtra),axis=None))

            update = relax*bspUpdate(self.nCoeffs,x,res)
            self.coeffs += update
            # print "Maximum change from PZT data: %s" % (abs(update).max(),)
            # update = self.coeffs.copy()

            # Apply regularization, becoming more and more aggressive if the result is non-increasing
            self.relaxTowardsOriginal(relaxDefault,relaxZero)
            # print "Maximum change from relaxation to default: %s" % (abs(self.coeffs-update).max(),)

        finally:
            self.lock.release()

    MAX_ITER = 20
    def relaxTowardsOriginal(self,relax,relaxZero=0,n=MAX_ITER):
        """Relax the new coefficients towards the original, using a Laplacian term for regularization"""
        for i in range(n):
            dev = self.coeffsOrig - self.coeffs
            self.coeffs[1:-1] = self.coeffs[1:-1] + relax*(dev[1:-1]-0.5*dev[2:]-0.5*dev[:-2]) + relaxZero*dev[1:-1]
            if relax<0.5: relax += relax
            if self.isIncreasing(): break

    def isIncreasing(self):
        """Determine if the current coefficients + linear model results in a monotonically increasing angle to
        wavenumber transformation at the knots"""
        ygrid = self.sLinear[0]*arange(1,self.nCoeffs-1) + (self.coeffs[:-2] + 4*self.coeffs[1:-1] + self.coeffs[2:])/6.0
        return (diff(ygrid)>=0).all()

    def replaceCurrent(self):
        """Replace current values with copy of originals"""
        self.coeffs = self.coeffsOrig.copy()

    def replaceOriginal(self):
        """Replace original values with copy of current values"""
        self.coeffsOrig = self.coeffs.copy()

    def setOffset(self,offset):
        """Apply a spectroscopically determined wavelength monitor offset."""
        self.lock.acquire()
        try: 
            self.offset = offset
            self.sLinear = self.sLinear0 + array([0.0,self.offset])
        finally:
            self.lock.release()

    def getOffset(self):
        """Returns the current value of the offset."""
        self.lock.acquire()
        try: 
            return self.offset
        finally:
            self.lock.release()

    def shiftWlmCal(self,thetaCal,waveNumber,relax=0.1):
        """Shift entire calibration table on basis of a known waveNumber
        thetaCal      calibrated WLM angle
        waveNumber    wavenumber to which it corresponds
        relax         relaxation parameter for update"""
        self.lock.acquire()
        try: 
            x = (thetaCal-self.thetaBase)/self.dTheta
            currentWaveNumber = bspEval(self.sLinear,self.coeffs,[x])[0]
            res = waveNumber - currentWaveNumber
            self.sLinear[1] += relax * res
            offset = self.sLinear[1] - self.sLinear0[1]
        finally:
            self.lock.release()

    def putToIni(self,ini,index):
        """Create sections and keys in "ini" to describe the current AutoCal object,
        using the specified "index" to indicate which wavelength monitor (or laser)
        is used"""
        if self.lock.locked():
            return
        self.lock.acquire()
        try: 
            if not ini.has_section("LASER_TEMP_TO_ANGLE_%02d" % (index,)):
                ini.add_section("LASER_TEMP_TO_ANGLE_%02d" % (index,))
            if not ini.has_section("ANGLE_TO_LASER_TEMP_%02d" % (index,)):
                ini.add_section("ANGLE_TO_LASER_TEMP_%02d" % (index,))
            if not ini.has_section("LASER_BASED_PARAMS_%02d" % (index,)):
                ini.add_section("LASER_BASED_PARAMS_%02d" % (index,))
            if not ini.has_section("WLM_CALIBRATION_%02d" % (index,)):
                ini.add_section("WLM_CALIBRATION_%02d" % (index,))
            if not ini.has_section("WLM_ORIGINAL_%02d" % (index,)):
                ini.add_section("WLM_ORIGINAL_%02d" % (index,))

            secName = "LASER_TEMP_TO_ANGLE_%02d" % (index,)
            coeffs,cen,scale = getFitParameters(self.__laserTemp2ThetaCal)
            ini.set(secName,"TCEN","%.12g" % (cen,))
            ini.set(secName,"TSCALE","%.12g" % (scale,))
            for i in range(len(coeffs)):
                ini.set(secName,"COEFF%03d" % (i,),"%.12g" % (coeffs[i],))
                time.sleep(0)

            secName = "ANGLE_TO_LASER_TEMP_%02d" % (index,)
            coeffs,cen,scale = getFitParameters(self.__thetaCal2LaserTemp)
            ini.set(secName,"ACEN","%.12g" % (cen,))
            ini.set(secName,"ASCALE","%.12g" % (scale,))
            for i in range(len(coeffs)):
                ini.set(secName,"COEFF%03d" % (i,),"%.12g" % (coeffs[i],))
                time.sleep(0)

            secName = "LASER_BASED_PARAMS_%02d" % (index,)
            ini.set(secName,"RATIO1_CENTER","%.12g" % (self.ratio1Center,))
            ini.set(secName,"RATIO2_CENTER","%.12g" % (self.ratio2Center,))
            ini.set(secName,"RATIO1_SCALE","%.12g" % (self.ratio1Scale,))
            ini.set(secName,"RATIO2_SCALE","%.12g" % (self.ratio2Scale,))
            ini.set(secName,"PHASE","%.12g" % (self.wlmPhase,))
            ini.set(secName,"CAL_TEMP","%.12g" % (self.tEtalonCal,))
            ini.set(secName,"TEMP_SENSITIVITY","%.12g" % (self.wlmTempSensitivity,))

            secName = "WLM_CALIBRATION_%02d" % (index,)
            ini.set(secName,"ANGLE_BASE","%.12g" % (self.thetaBase,))
            ini.set(secName,"ANGLE_INCREMENT","%.12g" % (self.dTheta,))
            ini.set(secName,"LINEAR_MODEL_SLOPE","%.12g" % (self.sLinear0[0],))
            ini.set(secName,"LINEAR_MODEL_OFFSET","%.12g" % (self.sLinear0[1],))
            ini.set(secName,"WLM_OFFSET","%.12g" % (self.offset,))
            ini.set(secName,"NCOEFFS","%d" % (len(self.coeffs),))
            for i in range(len(self.coeffs)):
                #ini.set(secName,"COEFF%05d" % (i,),"%.12g" % (self.coeffs[i],))
                #ini.set("WLM_ORIGINAL_%02d" % (index,),"COEFF%05d" % (i,),"%.12g" % (self.coeffsOrig[i],))

                # Need to be careful about the upper/lower cases because there is no more 
                # case handling in set() function.
                ini[secName]["coeff%05d" % (i,)] = "%.12g" % (self.coeffs[i],)
                ini["WLM_ORIGINAL_%02d" % (index,)]["coeff%05d" % (i,)] = "%.12g" % (self.coeffsOrig[i],)
                time.sleep(0)
        finally:
            self.lock.release()

    def getFromIni(self,ini,index):
        """Fill up the AutoCal structure based on the information in the .ini file"""
        self.lock.acquire()
        try: 
            secName = "LASER_TEMP_TO_ANGLE_%02d" % (index,)
            cen = float(ini.get(secName,"TCEN",None))
            scale = float(ini.get(secName,"TSCALE",None))
            coeffs = []
            i = 0
            while True:
                try:
                    coeffs.append(float(ini.get(secName,"COEFF%03d" % (i,),None)))
                    i += 1
                except:
                    break
            coeffs = array(coeffs)
            self.__laserTemp2ThetaCal = setFitParameters(coeffs,cen,scale)

            secName = "ANGLE_TO_LASER_TEMP_%02d" % (index,)
            cen = float(ini.get(secName,"ACEN",None))
            scale = float(ini.get(secName,"ASCALE",None))
            coeffs = []
            i = 0
            while True:
                try:
                    coeffs.append(float(ini.get(secName,"COEFF%03d" % (i,),None)))
                    i += 1
                except:
                    break
            coeffs = array(coeffs)
            self.__thetaCal2LaserTemp = setFitParameters(coeffs,cen,scale)

            secName = "LASER_BASED_PARAMS_%02d" % (index,)
            self.ratio1Center = float(ini.get(secName,"RATIO1_CENTER",None))
            self.ratio2Center = float(ini.get(secName,"RATIO2_CENTER",None))
            self.ratio1Scale = float(ini.get(secName,"RATIO1_SCALE",None))
            self.ratio2Scale = float(ini.get(secName,"RATIO2_SCALE",None))
            self.wlmPhase = float(ini.get(secName,"PHASE",None))
            self.tEtalonCal = float(ini.get(secName,"CAL_TEMP",None))
            self.wlmTempSensitivity = float(ini.get(secName,"TEMP_SENSITIVITY",None))

            secName = "WLM_CALIBRATION_%02d" % (index,)
            self.thetaBase = float(ini.get(secName,"ANGLE_BASE",None))
            self.dTheta = float(ini.get(secName,"ANGLE_INCREMENT",None))
            self.sLinear0 = array([float(ini.get(secName,"LINEAR_MODEL_SLOPE",None)),float(ini.get(secName,"LINEAR_MODEL_OFFSET",None))])
            self.offset = float(ini.get(secName,"WLM_OFFSET",0.0))
            self.sLinear = self.sLinear0 + array([0.0,self.offset])
            self.nCoeffs = int(ini.get(secName,"NCOEFFS",None))
            self.coeffs = []
            for i in range(self.nCoeffs):
                self.coeffs.append(float(ini.get(secName,"COEFF%05d" % (i,),None)))
            self.coeffs = array(self.coeffs)
            self.autocalStatus = 0

            secName = "WLM_ORIGINAL_%02d" % (index,)
            if not ini.has_section(secName):
                secName = "WLM_CALIBRATION_%02d" % (index,)
            self.coeffsOrig = []
            for i in range(self.nCoeffs):
                self.coeffsOrig.append(float(ini.get(secName,"COEFF%05d" % (i,),None)))
            self.coeffsOrig = array(self.coeffsOrig)
            return self

        finally:
            self.lock.release()

if __name__ == "__main__":
    ac = None
    while True:
        print "0 = Exit"
        print "1 = Read in WLM file"
        print "2 = Read in INI calibration file"
        print "3 = Write out INI calibration file"
        print "4 = Translate frequency-based scheme"
        print "5 = Generate equally-spaced angle scheme"
        print "6 = Plot calibration data"
        try:
            choice = int(raw_input("Select option: "))
        except:
            continue
        if choice == 0: break
        elif choice == 1:
            wlmFilename = raw_input("Name of WLM file to read? ")
            dThetaString = raw_input("WLM angle between knots [0.05 rad/FSR default]? ").strip()
            if dThetaString:
                dTheta = float(dThetaString)
            else:
                dTheta = 0.05
            ac = AutoCal().loadFromWlm(wlmFilename,dTheta)
        elif choice == 2:
            iniFilename = raw_input("Name of INI calibration file to read? ")
            ini = CustomConfigObj(iniFilename)
            ac = AutoCal().getFromIni(ini,1)
        elif choice == 3:
            iniFilename = raw_input("Name of INI calibration file to write? ")
            ip = file(iniFilename,"wb")
            ini = CustomConfigObj()
            ac.putToIni(ini,1)
            ini.write(ip)
            ip.close()
        elif choice == 4:
            schFilename = raw_input("Frequency based scheme file to read? ")
            sp = file(schFilename,"r")
            lbsFilename = raw_input("Laser based scheme file to write? ")
            lp = file(lbsFilename,"w")
            print >>lp, int(sp.readline()) # nrepeat
            numEntries = int(sp.readline())
            print >>lp, numEntries
            for i in range(numEntries):
                toks = sp.readline().split()
                toks += (6-len(toks)) * ["0"]
                thetaCal = ac.waveNumber2ThetaCal([float(toks[0])])
                tLaser = ac.thetaCal2LaserTemp(thetaCal)
                toks[0] = "%.4f" % (float(thetaCal[0]),)
                toks[5] = "%.4f" % (float(tLaser[0]),)
                print >>lp, " ".join(toks)
            sp.close()
            lp.close()
        elif choice == 5:
            start = float(raw_input("Starting wavenumber? "))
            dtheta = float(raw_input("Angle increment (radians)? "))
            nsteps = int(raw_input("Number of steps? "))
            lbsFilename = raw_input("Laser based scheme file to write? ")
            lp = file(lbsFilename,"w")
            print >>lp, 1 # nrepeat
            numEntries = 2*nsteps
            print >>lp, numEntries
            theta_start = ac.waveNumber2ThetaCal([start])[0]
            toks = 6 * ["0"]
            for i in range(nsteps+1):
                theta = theta_start + i*dtheta
                tLaser = ac.thetaCal2LaserTemp(array([theta]))[0]
                toks[0] = "%.4f" % (float(theta),)
                toks[1] = "5" # Dwell
                toks[5] = "%.4f" % (float(tLaser),)
                print >>lp, " ".join(toks)
            for i in range(nsteps,0,-1):
                theta = theta_start + i*dtheta
                tLaser = ac.thetaCal2LaserTemp(array([theta]))[0]
                toks[0] = "%.4f" % (float(theta),)
                toks[1] = "5" # Dwell
                toks[5] = "%.4f" % (float(tLaser),)
                print >>lp, " ".join(toks)
            lp.close()
        #elif choice == 6:
            #assert isinstance(ac,AutoCal)
            #x = linspace(0.0,ac.nCoeffs,3*ac.nCoeffs)
            #y = bspEval(array([0.0,0.0]),ac.coeffs,x)
            #plot(ac.thetaBase+ac.dTheta*x,y)
            #if ac.thetaMeasured != None:
                #xm = (ac.thetaMeasured-ac.thetaBase)/ac.dTheta
                #plot(ac.thetaMeasured,ac.wavenumberMeasured - polyval(ac.sLinear,xm),'r.')
            #grid()
            #xlabel("Angle")
            #ylabel("Deviation from linear model")
            #show()
