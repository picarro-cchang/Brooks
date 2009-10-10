from Host.Common import CmdFIFO, SharedTypes

if __name__ == "__main__":
    serverURI = "http://localhost:%d" % (SharedTypes.RPC_PORT_DRIVER,)
    driver = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="configLaser")

    laser1Params = {'actualLaser': 1L, 
                   'ratio1Center': 0.6, 'ratio1Scale': 1.2, 'ratio2Center': 0.6, 'ratio2Scale': 1.2, 'phase': 1.58,
                   'tempSensitivity': 0.0, 'calTemp': 45.0,
                   'calPressure': 760.0, 'pressureC0': 0.0, 'pressureC1': 0.0, 'pressureC2': 0.0, 'pressureC3': 0.0}
    laser5Params = {'actualLaser': 2L, 
                   'ratio1Center': 0.6, 'ratio1Scale': 1.2, 'ratio2Center': 0.6, 'ratio2Scale': 1.2, 'phase': 1.58,
                   'tempSensitivity': 0.0, 'calTemp': 45.0,
                   'calPressure': 760.0, 'pressureC0': 0.0, 'pressureC1': 0.0, 'pressureC2': 0.0, 'pressureC3': 0.0}
    driver.wrVirtualLaserParams(0,laser1Params)
    driver.wrVirtualLaserParams(4,laser5Params)
