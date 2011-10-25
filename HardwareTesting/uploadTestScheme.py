from Host.Common import CmdFIFO, SharedTypes
from Host.autogen import interface
from numpy import *
import itertools

if __name__ == "__main__":
    serverURI = "http://localhost:%d" % (SharedTypes.RPC_PORT_DRIVER,)
    driver = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="uploadTestScheme")

    coarseCurrent = 36000
    fineCurrent = 32768
    laserParams = {'actualLaser': 1L, 
                   'ratio1Center': 0.6, 'ratio1Scale': 1.2, 'ratio2Center': 0.6, 'ratio2Scale': 1.2, 'phase': 0.0,
                   'tempSensitivity': 0.0, 'calTemp': 45.0,
                   'calPressure': 760.0, 'pressureC0': 0.0, 'pressureC1': 0.0, 'pressureC2': 0.0, 'pressureC3': 0.0}
    driver.wrVirtualLaserParams(5,laserParams)
    thList = linspace(-3*pi/4,-pi/4,321)
    thList = concatenate((thList,thList[::-1]))
    phase = -pi/2-thList  # Angle for WlmSim
    dwell = 3*ones(thList.shape)
    subschemeId = zeros(thList.shape)
    virtualLaser = (5-1)*ones(thList.shape)
    threshold = zeros(thList.shape)
    pztSetpoint = zeros(thList.shape)
    laserTemp = ((65536.0*phase)/(2*pi)-5.0*(coarseCurrent+0.5*fineCurrent))/18.0
    # Get the laser temperatures to be close to 20C by adding multiples of 65536.0/18.0
    period = 65536.0/18.0
    laserTemp = laserTemp + period * floor((20000.0-mean(laserTemp))/period + 0.5)
    # For wrScheme, the temperatures are in Celsius
    laserTemp = 0.001 * laserTemp
    repeats = 2
    driver.wrScheme(0,repeats,zip(thList,dwell,subschemeId,virtualLaser,threshold,pztSetpoint,laserTemp))

    thList = linspace(-pi/2,-pi/2,81)
    dwell = 10*ones(thList.shape)
    subschemeId = zeros(thList.shape)
    virtualLaser = (5-1)*ones(thList.shape)
    threshold = zeros(thList.shape)
    pztSetpoint = zeros(thList.shape)
    laserTemp = 18.204*ones(thList.shape)
    repeats = 1
    driver.wrScheme(3,repeats,zip(thList,dwell,subschemeId,virtualLaser,threshold,pztSetpoint,laserTemp))
