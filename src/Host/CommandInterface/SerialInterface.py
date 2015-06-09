"""
File Name: SerialInterface.py
Purpose: Handles serial/rs232 interface communication.

File History:
    06-11-16 ytsai   Created file

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import time
import serial

class SerialInterface(object):
    def __init__(self):
        """ Initializes Serial Interface """
        self.terminate     = False

    def config( self,
      port=None,                     #number of device, numbering starts at
                                     #zero. if everything fails, the user
                                     #can specify a device string, note
                                     #that this isn't portable anymore
                                     #if no port is specified an unconfigured
                                     #an closed serial port object is created
      baudrate=9600,                 #baudrate
      bytesize=serial.EIGHTBITS,     #number of databits
      parity=serial.PARITY_NONE,     #enable parity checking
      stopbits=serial.STOPBITS_ONE,  #number of stopbits
      timeout=None,                  #set a timeout value, None for waiting forever
      xonxoff=0,                     #enable software flow control
      rtscts=0):                     #enable RTS/CTS flow control
        self.serial = serial.Serial ( port, baudrate, bytesize, parity, stopbits, timeout, xonxoff, rtscts )

    def open( self ):
        """ Opens port """
        if self.serial != None:
            if self.serial.isOpen() == False:
                self.serial.open()

    def close( self ):
        """ Closes port """
        if self.serial != None:
            if self.serial.isOpen()==True:
                self.serial.close()

    def read( self ):
        return self.serial.read()

    def write(self, msg):
        self.serial.write(msg)

if __name__ == "__main__" :
    s = SerialInterface()
    s.config( port='COM1', timeout=1 )
    s.open()
    print s.write("Hello from PySerial\r\n")
    print s.read()
    s.close()