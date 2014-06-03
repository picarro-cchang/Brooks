"""
Copyright (c) 2014 Picarro, Inc. All rights reserved
"""

import threading
import traceback
import serial
import time

from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_MOBILE_KIT_ARDUINO
from Host.Common import CmdFIFO
from Host.Common.EventManagerProxy import Log, LogExc, EventManagerProxy_Init

APP_NAME = "MobileKitMonitor"

EventManagerProxy_Init(APP_NAME)

class MobileKitMonitor(object):
    def __init__(self):
        self.ser = None
        self.arduinoCmds = [("B","BACKUP_BATT_VOLT"), ("C", "CAR_BATT_VOLT"), 
                            ("F","FAN1_SPEED"), ("G","FAN2_SPEED"),
                            ("I","IGNITION_STAT"),
                            ("L","MOBILE_FLOW"),("M","MOBILE_TEMPERATURE"),
                            ("P","PUMP_1"),("Q","PUMP_2"),("U","UPS_STAT"),("Z","CHASSIS_VOLT")]
        self.spectrumCollector = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,
                                    APP_NAME, IsDontCareConnection=False)
        self.generateDummyData()
        pass
    
    def setTagalong(self,header,value):
        try:
            self.spectrumCollector.setTagalongData(header,value)
        except:
            pass
            
    def scanPorts(self):
        startingCom = 2
        endingCom = 20
        for comInd in range(startingCom,endingCom+1,1):
            try:
                ser = serial.Serial(comInd, baudrate=115200, timeout=5)  # open first serial port
                time.sleep(2)
                ser.write("D")
                identStr = ser.readline()
                if identStr.startswith("Picarro Mobile Kit"):
                    self.ser = ser
                    return
                else:
                    continue

            except serial.SerialException:
                continue
            except ValueError:
                LogExc("Serial port parameters out of range!")
                raise

        Log("Mobile Kit Arduino not found on any serial port!")

    def generateDummyData(self):
        for cmd, header in self.arduinoCmds:
            self.setTagalong(header, -9999.0)

    def main(self):
        while True:
            for cmd, header in self.arduinoCmds:
                while not self.ser:
                    self.scanPorts()
                    if self.ser:
                        break
                    else:
                        time.sleep(10)
                try:
                    self.ser.write(cmd)
                    value = float(self.ser.readline())
                    self.setTagalong(header, value)
                except:
                    LogExc("Connection dropped! Check Arduino USB cable connection and/or flow sensor connection to Arduino.")
                    self.ser.close()
                    self.generateDummyData()
                    self.ser = None
                    time.sleep(1)

            time.sleep(2)



def main():
    mobileKitArduino = MobileKitMonitor()
    # make a new thread to execute mobile kit arduino main function
    th = threading.Thread(target=mobileKitArduino.main)
    th.setDaemon(True) # child is killed if parent dies
    th.start()
    # listen on given port
    rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_MOBILE_KIT_ARDUINO),
                                       ServerName="MobileKitMonitor",
                                       ServerDescription="MobileKitMonitor",
                                       ServerVersion="1.0",
                                       threaded=True)
    try:
        while True:
            rpcServer.daemon.handleRequests(0.5) #handle rpc request 2hz
            if not th.isAlive(): break
        Log("Supervised MobileKitMonitor died", Level=2)
    except:
        LogExc("CmdFIFO for MobileKitMonitor stopped", Level=2)
    finally:
        mobileKitArduino.close()
        raw_input("Press <Enter> to continue")   
if __name__ == '__main__':
    main()
