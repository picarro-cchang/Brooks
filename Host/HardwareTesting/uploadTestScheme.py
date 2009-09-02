from Host.Common import CmdFIFO, SharedTypes
from Host.autogen import interface
from numpy import *
from pylab import *

if __name__ == "__main__":
    serverURI = "http://localhost:%d" % (SharedTypes.RPC_PORT_DRIVER,)
    driver = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="uploadTestScheme")

    laserParams = {'actualLaser': 2L, 
                   'ratio1Center': 0.6, 'ratio1Scale': 1.2, 'ratio2Center': 0.6, 'ratio2Scale': 1.2, 'phase': 0.0,
                   'tempCenter': 29.0, 'tempScale': 12.14, 'tempToAngleC0': -0.0408069075214, 
                   'tempToAngleC1': -0.168487230259, 'tempToAngleC2': -21.9584615861, 'tempToAngleC3': -37.7690972829, 
                   'angleCenter': -37.9375827011, 'angleScale': 22.0325170965, 'angleToTempC0': 0.0211568074598, 
                   'angleToTempC1': -0.0921171449063, 'angleToTempC2': -12.178321532, 'angleToTempC3': 29.0929396524, 
                   'tempSensitivity': 0.0, 'calTemp': 45.0,
                   'calPressure': 760.0, 'pressureC0': 0.0, 'pressureC1': 0.0, 'pressureC2': 0.0, 'pressureC3': 0.0}
    driver.wrVirtualLaserParams(4,laserParams)
    thList = linspace(-3*pi/4,-pi/4,321)
    dwell = 3*ones(thList.shape)
    subschemeId = zeros(thList.shape)
    laserUsed = 4*ones(thList.shape)
    threshold = zeros(thList.shape)
    pztSetpoint = zeros(thList.shape)
    laserTemp = 24.0*ones(thList.shape)
    repeats = 2
    driver.wrScheme(0,repeats,zip(thList,dwell,subschemeId,laserUsed,threshold,pztSetpoint,laserTemp))

    thList = linspace(-3*pi/4,-pi/4,81)
    dwell = 10*ones(thList.shape)
    subschemeId = zeros(thList.shape)
    laserUsed = 4*ones(thList.shape)
    threshold = zeros(thList.shape)
    pztSetpoint = zeros(thList.shape)
    laserTemp = 24.0*ones(thList.shape)
    repeats = 1
    driver.wrScheme(3,repeats,zip(thList,dwell,subschemeId,laserUsed,threshold,pztSetpoint,laserTemp))

    driver.wrSchemeSequence([0,3,0,3],0)