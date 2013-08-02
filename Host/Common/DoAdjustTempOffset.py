#!/usr/bin/python
#
"""
Description: Worker function to adjust the laser temperature offset value to compensate
             for laser aging.

Arguments:   instr      [in]  a dictionary, typically _INSTR_ on the instrument (instrument params dict)

             data       [in]  a dictionary, typically _DATA_ on the instrument

             freqConv   [in]  a dictionary, typically a FrequencyConv class object on the instrument,
                              contains getLaserTempOffset(vLaserNum) and
                              setLaserTempOffset(vLaserNum, value) methods to get/set
                              an offset value for virtual laser vLaserNum

             report     [out] a dictionary, typically _REPORT_ on the instrument

Copyright (c) 2013 Picarro, Inc. All rights reserved.
"""

APP_NAME = "doAdjustTempOffset"

from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
EventManagerProxy_Init(APP_NAME)


def doAdjustTempOffset(instr=None, data=None, freqConv=None, report=None):
    allLasersDict = {}

    # All arguments are required.
    if instr is None:
        Log("instr dict is None")
        raise RuntimeError("instr dict is None")
    elif data is None:
        Log("instr dict is None")
        raise RuntimeError("data dict is None")
    elif freqConv is None:
        Log("instr dict is None")
        raise RuntimeError("freqConv object argument is None")
    elif report is None:
        Log("instr dict is None")
        raise RuntimeError("report argument is None")

    gain = float(instr.get("la_fineLaserCurrent_gain", 0))
    maxStep = float(instr.get("la_fineLaserCurrent_maxStep", 0))

    # these settings should always be found; just in case they aren't
    # assign something reasonable (though rather extreme) defaults
    minFineCurrent = float(instr.get("la_fineLaserCurrent_minFineCurrent", 1000))
    maxFineCurrent = float(instr.get("la_fineLaserCurrent_maxFineCurrent", 60000))
    laIsEnabled = float(instr.get("la_enabled", 0))

    # Note: "ch4_interval" is indeed available in data if we need it (CFKADS)
    #       to shut off the control loop if the interval exceeds a time value
    #       What is this interval for other instruments? What should the limit be?
    #       Should fitScriptLaserCurrentAverage.py copy it to a more generic name used
    #       by this script?

    for v in range(8):
        vLaserNum = v + 1
        name = "la_fineLaserCurrent_%d_target" % vLaserNum

        if name in instr:
            laserDict = {}
            
            # Change this to median if using instead of mean (must also change
            # laserTempOffsets ini file as target values should be higher)
            target = float(instr[name])
            fineCurrent = data.get("fineLaserCurrent_%d_mean" % vLaserNum, target)
            dev = fineCurrent - target

            #print "vLaserNum=%d fineCurrent=%f target=%f  minFineCurrent=%f maxFineCurrent=%f" %
            #     (vLaserNum, fineCurrent, target, minFineCurrent, maxFineCurrent)

            curValue = freqConv.getLaserTempOffset(vLaserNum)
            
            # save off values in laser dict
            laserDict["target"] = target
            laserDict["dev"] = dev
            laserDict["curValue"] = curValue
            laserDict["newValue"] = curValue    # init current and new offset setting to current
            laserDict["gain"] = gain
            laserDict["maxStep"] = maxStep
            laserDict["minFineCurrent"] = minFineCurrent
            laserDict["maxFineCurrent"] = maxFineCurrent
            
            # set some initial defaults
            laserDict["controlOn"] = False

            # Set temp offset only if fine current below threshold. Prevents wraparound
            # and larger and larger negative temp offsets being applied
            if (laIsEnabled > 0):
                laserDict["controlOn"] = True
                
                if fineCurrent > minFineCurrent and fineCurrent < maxFineCurrent:
                    #print "in limits, fineCurrent=%f min=%f" % (fineCurrent, minFineCurrent)
                    
                    # compute adjustment needed
                    delta = gain * dev
                    deltaAbs = abs(delta)

                    # limit step size if necessary
                    if (maxStep > 0.0 and deltaAbs > maxStep):
                        deltaAbs = maxStep
                        deltaOrig = delta   # only needed for printing below
                        
                        if (delta >= 0.0):
                            delta = maxStep
                        else:
                            delta = -maxStep
                        
                        Log("Limiting step size to maxStep=%f, deltaOrig=%f  delta=%f" % (maxStep, deltaOrig, delta))
                        
                    # apply change to the current laser temp offset
                    newValue = curValue + delta
                    laserDict["newValue"] = newValue
                else:
                    #print "not in limits, fineCurrent=%f min=%f max=%f" % (fineCurrent, minFineCurrent, maxFineCurrent)
                    laserDict["controlOn"] = False
                    
                    if fineCurrent <= minFineCurrent:
                        Log("  vLaser=%d fineCurrent=%f is less than or equal to minimum fine current mean of %f" %
                            (vLaserNum, fineCurrent, minFineCurrent), Level=2)
                    else:
                        Log("  vLaser=%d fineCurrent=%f is greater than or equal to maximum fine current mean of %f" %
                            (vLaserNum, fineCurrent, maxFineCurrent), Level=2)
                    
                    if fineCurrent <= minFineCurrent:
                        Log("  vLaser=%d fineCurrent=%f is less than or equal to minimum fine current mean of %f" %
                            (vLaserNum, fineCurrent, minFineCurrent), Level=2)
                    else:
                        Log("  vLaser=%d fineCurrent=%f is greater than or equal to maximum fine current mean of %f" %
                            (vLaserNum, fineCurrent, maxFineCurrent), Level=2)
                    
            else:
                laserDict["controlOn"] = False
            
            # save off dictionary for this laser in the all lasers dictionary
            allLasersDict[vLaserNum] = laserDict

    # Look through the all lasers dictionary for existing lasers, setting all lasers good flag to False
    # if any are bad. They will also all be "bad" if the control loop is not enabled.
    allControlOn = True
    for v in range(8):
        vLaserNum = v + 1
        
        if vLaserNum in allLasersDict:
            laserDict = allLasersDict[vLaserNum]

            isLaserGood = laserDict.get("controlOn", False)
            if not isLaserGood:
                allControlOn = False

    if laIsEnabled <= 0:
        # controlled from ini config file
        Log("Laser temp offset control is disabled")
        allControlOn = False
    elif not allControlOn:
        Log("Problem detected for at least one laser, turned off temperature control loop for all lasers", Level=2)

    # save off info in the report and set the laser offset if all is good
    #
    for v in range(8):
        vLaserNum = v + 1
        
        if vLaserNum in allLasersDict:
            laserDict = allLasersDict[vLaserNum]
            
            dev = laserDict["dev"]
            newValue = laserDict["newValue"]
            curValue = laserDict["curValue"]

            #print " setLaserTempOffset vLaserNum=%d oldtempOffset=%f newTempOffset=%f" % (vLaserNum, curValue, newValue)
            
            # set the laser temp offset if controlling all lasers
            if allControlOn:
                #Log(" setLaserTempOffset vLaserNum=%d oldtempOffset=%f newTempOffset=%f" % (vLaserNum, curValue, newValue))
                freqConv.setLaserTempOffset(vLaserNum, newValue)
            else:
                # else we're not changing the setting, so the new value must be unchanged
                newValue = curValue

            # save off results in the report
            report["fineLaserCurrent_%d_dev" % vLaserNum] = dev
            report["fineLaserCurrent_%d_offset" % vLaserNum] = newValue

            # Save off some other stuff in the report
            controlEnabled = float(laserDict["controlOn"])
            if not allControlOn:
                controlEnabled = False
            report["fineLaserCurrent_%d_controlOn" % vLaserNum] = controlEnabled
