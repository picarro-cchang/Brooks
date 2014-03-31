# Embedded file name: CentrisPumpPriming.py
from ctypes import windll, c_int
import serial
import time
import wx
import sys
import os
from CustomConfigObj import CustomConfigObj

class TimeoutError(Exception):
    pass


class SerIntrf(object):

    def __init__(self, port, baudrate = 9600, timeout = 5, xonxoff = 0):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout, xonxoff=xonxoff)
        print self.ser

    def open(self):
        self.ser.open()

    def close(self):
        self.ser.close()

    def flush(self):
        self.ser.flushInput()

    def sendString(self, str):
        self.ser.write(str + '\r')

    def getLine(self):
        line = []
        while True:
            ch = self.ser.read()
            if not ch:
                raise TimeoutError
            if ch != '\n':
                line.append(ch)
            else:
                return ''.join(line)


def waitForComplete(ser, pumpAddr, timeout = None):
    startTime = time.time()
    cont = False
    while not cont:
        if timeout != None:
            if time.time() - startTime > timeout:
                print 'Time out after %.2f seconds - pump %d is still busy.' % (timeout, pumpAddr)
                break
        ser.sendString('/%dQ\r\n' % pumpAddr)
        try:
            status = ser.getLine()
            if '@' not in status:
                print 'Pump %d is ready for next command' % pumpAddr
                cont = True
            else:
                time.sleep(0.5)
        except:
            time.sleep(0.5)

    return


if __name__ == '__main__':
    HELP_STRING = 'CentrisPumpPriming.py [-c<FILENAME>] [-h|--help]\n\n    Where the options can be a combination of the following:\n    -h, --help           print this help.\n    -c                   Specify a config file.  Default = "./CentrisPumpPriming.ini"\n    '

    def PrintUsage():
        print HELP_STRING


    def HandleCommandSwitches():
        import getopt
        shortOpts = 'hc:'
        longOpts = ['help']
        try:
            switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
        except getopt.GetoptError as E:
            print '%s %r' % (E, E)
            sys.exit(1)

        options = {}
        for o, a in switches:
            options.setdefault(o, a)

        if '/?' in args or '/h' in args:
            options.setdefault('-h', '')
        configFile = './CentrisPumpPriming.ini'
        if '-h' in options:
            PrintUsage()
            sys.exit()
        if '-c' in options:
            configFile = options['-c']
            print 'Config file specified at command line: %s' % configFile
        return configFile


    config = CustomConfigObj(HandleCommandSwitches())
    numCommands = config.getint('General', 'numCommands', '3')
    serialPort = config.getint('Communication', 'serialPort', '1')
    app = wx.App()
    app.MainLoop()
    dlg = wx.MultiChoiceDialog(None, 'Please ensure needle probes are NOT inserted into the vaporizer.\n\nPlease select the syringe pump(s) to be primed:', 'Syringe Pump Priming', ['Syringe pump 1', 'Syringe pump 2'])
    dlg.SetSelections([0, 1])
    startPump = dlg.ShowModal() == wx.ID_OK
    portList = dlg.GetSelections()
    numPumps = len(portList)
    if startPump:
        dlg.Destroy()
        pump = SerIntrf(port=serialPort, baudrate=9600, timeout=1, xonxoff=0)
        pump.open()
        for id in range(numPumps):
            pumpAddr = portList[id] + 1
            print '\nPriming pump %d...\n' % pumpAddr
            for comNum in range(numCommands):
                command, timeOut = config.get('General', str(comNum)).split(';')
                command = command.strip()
                timeOut = float(timeOut)
                pump.sendString('/%d%s\r\n' % (pumpAddr, command))
                print 'Command = %s, response = %s' % (command, pump.getLine())
                waitForComplete(pump, pumpAddr, timeOut)

        print '\nWait until both pumps are ready...\n'
        waitForComplete(pump, 1, 300)
        waitForComplete(pump, 2, 300)
        pump.close()
        print '\nPriming completed...\n'
        time.sleep(30)
    else:
        print 'Priming canceled'
        dlg.Destroy()