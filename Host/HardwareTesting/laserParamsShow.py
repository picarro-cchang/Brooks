from numpy import *
from scipy import *
from pylab import *

# Calculate relationship between laser temperature and WLM angle using the polynomial coefficients
#  specified in the virtual laser parameters

if __name__ == "__main__":
    laserParams = {'actualLaser': 3L, 
                   'ratio1Center': 0.6, 'ratio1Scale': 1.2, 'ratio2Center': 0.6, 'ratio2Scale': 1.2, 'phase': 0.0,
                   'tempCenter': 29.0, 'tempScale': 12.14, 'tempToAngleC0': -0.0408069075214, 
                   'tempToAngleC1': -0.168487230259, 'tempToAngleC2': -21.9584615861, 'tempToAngleC3': -37.7690972829, 
                   'angleCenter': -37.9375827011, 'angleScale': 22.0325170965, 'angleToTempC0': 0.0211568074598, 
                   'angleToTempC1': -0.0921171449063, 'angleToTempC2': -12.178321532, 'angleToTempC3': 29.0929396524, 
                   'tempSensitivity': -0.187353533489, 'calTemp': 45.0,
                   'calPressure': 760.0, 'pressureC0': 0.0, 'pressureC1': 0.0, 'pressureC2': 0.0, 'pressureC3': 0.0}

    tempList = linspace(8.0,50.0,1001)
    pTempToAngle = array([laserParams['tempToAngleC%d' % c] for c in range(0,4)])
    tempCenter, tempScale = laserParams['tempCenter'], laserParams['tempScale']    
    angle = polyval(pTempToAngle,(tempList-tempCenter)/tempScale)
    pAngleToTemp = array([laserParams['angleToTempC%d' % c] for c in range(0,4)])
    angleCenter, angleScale = laserParams['angleCenter'], laserParams['angleScale']    
    newTemp = polyval(pAngleToTemp,(angle-angleCenter)/angleScale)
    