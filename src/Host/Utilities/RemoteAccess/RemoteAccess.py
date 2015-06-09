"""
File Name: RemoteAccess.py
Purpose:
    Program for establishing dialup connection to Internet, performing
    time synchronization and e-mailing contents of a results directory

File History:
    06-08-29 sze   Created file
    07-02-27 sze   Send only one attached file per e-mail message
    07-03-15 sze   Send e-mail message even if no files are present in directory
    08-09-18 alex  Replaced ConfigParser with CustomConfigObj
    10-11-03 alex  Get instrument ID from EEPROM

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "RemoteAccess"
APP_DESCRIPTION = "E-mails the contents of a results directory"
__version__ = 1.0

COMMASPACE = ', '

import sys
import os
import mimetypes
from email import Encoders
from email.Message import Message
from email.MIMEAudio import MIMEAudio
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.MIMEText import MIMEText
import logging
import logging.handlers
import socket
import smtplib
from struct import pack, unpack
from time import time, ctime, mktime

from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                             APP_NAME,
                                             IsDontCareConnection = False)

def getRequiredOption(configParser,section,option):
    """Get a key from a configParser object, complaining if it does not exist"""
    try:
        return configParser.get(section,option)
    except KeyError:
        logging.error("No option %s in %s section." % (option,section,))
        sys.exit()

__all__=('sntp_time',)
_TIME1970 = 2208988800L      # Thanks to F.Lundh
_data = '\x1b' + 47*'\0'

#typedef struct _SYSTEMTIME {  // st
#    WORD wYear;
#    WORD wMonth;
#    WORD wDayOfWeek;
#    WORD wDay;
#    WORD wHour;
#    WORD wMinute;
#    WORD wSecond;
#    WORD wMilliseconds;
#} SYSTEMTIME;
#VOID GetSystemTime(
#  LPSYSTEMTIME lpSystemTime   // address of system time structure
#);
#SYSTEMTIME st;
#GetSystemTime(&st);
#SetSystemTime(&st);

from ctypes import windll, Structure, c_ushort, byref, c_ulong, c_long
kernel32_GetSystemTime = windll.kernel32.GetSystemTime
kernel32_SetSystemTime = windll.kernel32.SetSystemTime
kernel32_SystemTimeToFileTime=windll.kernel32.SystemTimeToFileTime
kernel32_FileTimeToSystemTime=windll.kernel32.FileTimeToSystemTime
class SYSTEMTIME(Structure):
    _fields_ =  (
                ('wYear', c_ushort),
                ('wMonth', c_ushort),
                ('wDayOfWeek', c_ushort),
                ('wDay', c_ushort),
                ('wHour', c_ushort),

                ('wMinute', c_ushort),
                ('wSecond', c_ushort),
                ('wMilliseconds', c_ushort),
                )
    def __str__(self):
        return '%4d%02d%02d%02d%02d%02d.%03d' % (self.wYear,self.wMonth,self.wDay,self.wHour,self.wMinute,self.wSecond,self.wMilliseconds)
class LONG_INTEGER(Structure):
    _fields_ =  (
            ('low', c_ulong),
            ('high', c_long),
            )

def GetSystemTime():
    st = SYSTEMTIME(0,0,0,0,0,0,0,0)
    kernel32_GetSystemTime(byref(st))
    return st

def SetSystemTime(st):
    return kernel32_SetSystemTime(byref(st))

def GetSystemFileTime():
    ft = LONG_INTEGER(0,0)
    st = GetSystemTime()
    if kernel32_SystemTimeToFileTime(byref(st),byref(ft)):
        return (long(ft.high)<<32)|ft.low
    return None

def SetSystemFileTime(ft):
    st = SYSTEMTIME(0,0,0,0,0,0,0,0)
    ft = LONG_INTEGER(ft&0xFFFFFFFFL,ft>>32)
    r = kernel32_FileTimeToSystemTime(byref(ft),byref(st))
    if r: SetSystemTime(st)
    return r

def _L2U32(L):
    return unpack('=l',pack('=L',L))[0]

_UTIME1970 = _L2U32(_TIME1970)
def _time2ntp(t):
    s = int(t)
    return pack('!II',s+_UTIME1970,_L2U32((t-s)*0x100000000L))

def _ntp2time((s,f)):
    return s-_TIME1970+float((f>>4)&0xfffffff)/0x10000000

def sntp_time(server):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        #originate timestamp 6:8
        #receive timestamp   8:10
        #transmit timestamp 10:12
        t1 = time()
        s.sendto(_data, (server,123))
        data, address = s.recvfrom(1024)
        data = unpack('!12I', data)
        t4 = time()
        t2 = _ntp2time(data[8:10])
        t3 = _ntp2time(data[10:12])
        delay = (t4 - t1) - (t2 - t3)
        offset = ((t2 - t1) + (t3 - t4)) / 2.
        return address[0], delay, offset
    except:
        return 3*(None,)

class RemoteAccess(object):
    def __init__(self, configFile):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y%m%d %H:%M:%S')
        self.configFilename = configFile
        try:
            self.config = CustomConfigObj(self.configFilename)
        except IOError:
            logging.error("Cannot open initialization file %s." % (self.configFilename,))
            sys.exit()
        self.basePath = os.path.split(configFile)[0]
        self.useDialUp = self.config.has_section('DIALUP')
        self.sendEmail = self.config.has_section('EMAIL')
        self.syncClock = self.config.has_section('NTP')
        logFilepath = getRequiredOption(self.config,'LOGGING','Logfile')
        logDir = os.path.dirname(logFilepath)
        if not os.path.isdir(logDir):
            os.mkdir(logDir)
        handler = logging.handlers.RotatingFileHandler(logFilepath,maxBytes=65536,backupCount=10)
        handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(message)s',datefmt='%Y%m%d %H:%M:%S'))
        logging.getLogger('').addHandler(handler)

        # Plug analyzer name in "from address" and "subject" of emails
        try:
            analyzerName = CRDS_Driver.fetchInstrInfo("analyzername")
        except:
            analyzerName = None
        self.subject = self.config.get("EMAIL", "Subject", "")
        if self.subject == "":
            if analyzerName != None:
                self.subject = "%s: data from Picarro instrument" % analyzerName
                self.config.set("EMAIL", "Subject", self.subject)
                self.config.write()
            else:
                pass
        self.fromAddr = self.config.get("EMAIL", "From", "")
        if self.fromAddr == "":
            if analyzerName != None:
                self.fromAddr = "%s@picarro.com" % analyzerName
                self.config.set("EMAIL", "From", self.fromAddr)
                self.config.write()
            else:
                logging.error("Error: A valid \"From\" address is required!")
                sys.exit()

    def dialConnection(self):
        if not self.useDialUp: return
        cmd = ["rasdial"]
        cmd.append('"' + getRequiredOption(self.config,'DIALUP','ConnectionName') + '"')
        cmd.append(getRequiredOption(self.config,'DIALUP','UserName'))
        cmd.append(getRequiredOption(self.config,'DIALUP','PassWord'))
        cmd.append("/phone:" + getRequiredOption(self.config,'DIALUP','Number'))
        errorNumber = os.system(" ".join(cmd))
        if errorNumber != 0:
            logging.error("Unable to establish dial-up connection, error number %d" % (errorNumber,))
        else:
            logging.info("Established dial-up connection")

    def closeConnection(self):
        if not self.useDialUp: return
        cmd = ["rasdial"]
        cmd.append('"' + getRequiredOption(self.config,'DIALUP','ConnectionName') + '" /d')
        errorNumber = os.system(" ".join(cmd))
        if errorNumber != 0:
            logging.error("Unable to close dial-up connection, error number %d" % (errorNumber,))
        else:
            logging.info("Dial-up connection closed")

    def syncTime(self):
        if not self.syncClock: return
        logging.info("Interrogating time servers")
        # Compile list of servers
        servers = []
        for option in self.config.list_options('NTP'):
            if option[:6].upper() == "SERVER":
                try:
                    index = int(option[6:])
                    servers.append(self.config.get('NTP',option))
                except ValueError:
                    logging.warning("Unrecognized option %s ignored" % (option,))
        t0 = time()
        mu = 0
        ss = 0
        n = 0
        data = []
        for server in servers:
            address, delay, offset = sntp_time(server)
            if address:
                n += 1
                data.append((server, address, delay, offset))
        # Find statistics of offsets
        for (server, address, delay, offset) in data:
            logging.info('%s: delay=%.3f offset=%.3f' % (server,delay,offset))
            mu += offset
            ss += offset*offset
        if n:
            mu = mu/n
            ss = (ss/n - mu*mu)**0.5
            # Find median
            med = sorted([offset for (server, address, delay, offset) in data])
            if n & 1:
                med = med[(n-1)//2]
            else:
                med = 0.5*(med[n//2-1] + med[n//2])
            logging.info("Median clock offset = %.3f s (Mean = %.3f s, Sdev = %.3f s)" % (med,mu,ss))
            try:
                updateClock = self.config.getboolean('NTP','UpdateClock')
            except:
                updateClock = True
            if updateClock:
                r = SetSystemFileTime(GetSystemFileTime()+long(med*10000000L))   #100 nanosecond units (since 16010101)
                logging.info("Clock adjustment %s" % (r and 'carried out' or 'failed'))
            else:
                logging.info("Clock adjustment has been disabled in INI file")
        else:
            logging.info("No timeservers available")

    def sendMail(self):
        if not self.sendEmail: return
        smtpHostname = getRequiredOption(self.config,'EMAIL','Server')
        toAddrList = []
        for option in self.config.list_options('EMAIL'):
            if option[:2].upper() == "TO":
                try:
                    index = int(option[2:])
                    toAddrList.append(self.config.get('EMAIL',option))
                except ValueError:
                    logging.warning("Unrecognized option %s ignored" % (option,))
        dir = os.path.join(self.basePath, getRequiredOption(self.config,'EMAIL','Directory'))

        fnameList = []
        for filename in os.listdir(dir):
            tnow = time()
            path = os.path.join(dir, filename)
            if not os.path.isfile(path):
                continue
            # If the file was modified within the last minute, do not include
            #  it in the list of files to send (i.e., wait for next time)
            if tnow - os.stat(path).st_mtime < 60.0:
                continue
            fnameList.append(filename)
        if len(fnameList) == 0:
            if self.subject != "":
                subject = self.subject + " No files to send"
            else:
                subject = "No files in directory %s" % (os.path.abspath(dir),)
            logging.info("E-mailing with no files in directory %s" % (os.path.abspath(dir),))
            self.sendMessage(smtpHostname,toAddrList,subject)
        else:
            for i in range(len(fnameList)):
                filename = fnameList[i]
                path = os.path.join(dir, filename)
                # Send a separate e-mail message for each file in the directory
                if self.subject != "":
                    subject = self.subject + " (File %d of %d)" % (i+1,len(fnameList),)
                else:
                    subject = "File %s in directory %s (File %d of %d)" % (filename,os.path.abspath(dir),i+1,len(fnameList))
                logging.info("E-mailing file %s in directory %s" % (filename,os.path.abspath(dir)))
                self.sendMessage(smtpHostname,toAddrList,subject,path)

    def sendMessage(self,smtpHostname,toAddrList,subject,path=None):
        # Create the enclosing (outer) message
        outer = MIMEMultipart()
        outer['Subject'] = subject
        outer['To'] = COMMASPACE.join(toAddrList)
        outer['From'] = self.fromAddr
        outer.preamble = '\n'
        # To guarantee the message ends with a newline
        outer.epilogue = ''
        if path is not None:
            dir,filename = os.path.split(path)
            # Guess the content type based on the file's extension.  Encoding
            # will be ignored, although we should check for simple things like
            # gzip'd or compressed files.
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            if maintype == 'text':
                fp = open(path)
                # Note: we should handle calculating the charset
                msg = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'image':
                fp = open(path, 'rb')
                msg = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'audio':
                fp = open(path, 'rb')
                msg = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(path, 'rb')
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
                fp.close()
                # Encode the payload using Base64
                Encoders.encode_base64(msg)
            logging.info("Attaching file: %s" % (filename,))
            # Set the filename parameter
            msg.add_header('Content-Disposition', 'attachment', filename=filename)
            outer.attach(msg)
        try:
            self.mailServer = smtplib.SMTP(smtpHostname)
            try:
                useSSL = self.config.getboolean('EMAIL','UseSSL')
            except:
                useSSL = False
            if useSSL:
                self.mailServer.ehlo()
                self.mailServer.starttls()
                self.mailServer.ehlo()
            # self.mailServer.set_debuglevel(True)
            try:
                authenticationNeeded = self.config.getboolean('EMAIL','UseAuthentication')
            except:
                authenticationNeeded = False
            if authenticationNeeded:
                self.mailServer.login(getRequiredOption(self.config,'EMAIL','UserName'),getRequiredOption(self.config,'EMAIL','PassWord'))
            failedReceipients = self.mailServer.sendmail(self.fromAddr,toAddrList,outer.as_string())
            self.mailServer.quit()
            successList = toAddrList[:]
            failedList = []
            for key in failedReceipients.keys():
                failedList.append(key)
                successList.remove(key)
            logging.info("Sent e-mail to: %s" % ", ".join(successList))
            for key in sorted(failedList):
                logging.info("Error sending to %s: %s" % (key,failedReceipients[key]))
            if path is not None:
                # Delete the files which have been e-mailed
                try:
                    os.remove(path)
                except:
                    logging.info("Could not delete file %s" % (path,))
        except smtplib.SMTPException, msg:
            logging.error("Error while sending e-mail: %s" % (msg,))

if __name__ == "__main__":
    usage = "Usage: RemoteAccess.py <.ini file>"
    defaultPath = "AppConfig/Config/RemoteAccess/RemoteAccess.ini"
    if len(sys.argv) == 2:
        configFile = sys.argv[1]
    elif len(sys.argv) == 1:
        if os.path.isfile("../../../" + defaultPath):
            configFile = "../../../" + defaultPath
        elif os.path.isfile("../../" + defaultPath):
            configFile = "../../" + defaultPath
        else:
            assert 0, usage
    else:
        assert 0, usage
    print "Config file is %s" % configFile
    r = RemoteAccess(configFile)
    try:
        r.dialConnection()
        r.syncTime()
        r.sendMail()
    finally:
        r.closeConnection()