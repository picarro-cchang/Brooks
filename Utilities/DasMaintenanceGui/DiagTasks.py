# File Name  : DiagTasks.py
# Description: Various tasks
#
# File History:
# 06-09-12 ytsai   Created file
# 07-01-12 sze     Corrected conversion of local time to GMT
import os, sys
import re
import string
import operator
import tempfile
import shutil
import time
import ctypes
import pprint
import wx

from wizardhelper import WizardTitledLogoPage
import wx.lib.masked as masked

sys.path.append("../..")
sys.path.append("../../Common")
sys.path.append("../../Supervisor")
sys.path.append("../../Driver")

import ss_autogen as Global
import Common.CmdFIFO as CmdFIFO

from SharedTypes import RPC_PORT_ARCHIVER, RPC_PORT_DRIVER
from SystemInfo import SystemInfo
from ExecTask import ExecTask, ExecPage

secondsPerMinute = 60
secondsPerHour   = 60*secondsPerMinute
secondsPerDay    = (secondsPerHour*24)

INPUT_BACKGROUND_COLOR          = 'WHITE'

class tskPromptUserCommentsPage( ExecPage ):
    """ Page for prompting user for comments and time of occurrence """
    def __init__(self, parent, title=None, description=None, globals=None, pArgs=None, nArgs=None ):
        ExecPage.__init__(self, parent, title, description, globals, pArgs, nArgs )

        prompt = nArgs['prompt1']
        text = wx.StaticText( self, -1, prompt )
        self.sizer.Add( text  )

        self.comments = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE, size=(100,80) )
        self.comments.SetBackgroundColour(wx.NamedColour(INPUT_BACKGROUND_COLOR))

        self.sizer.Add( self.comments, 1, wx.EXPAND | wx.ALL | wx.ALIGN_TOP , border=1 )
        self.sizer.Add( (1,5) )

        prompt = nArgs['prompt2']
        text = wx.StaticText(self, -1, prompt )
        self.sizer.Add( text )
        self.sizer.Add( (1,3) )

        sizerH1    = wx.BoxSizer(wx.HORIZONTAL)
        self.time = masked.TimeCtrl( self, -1, name="?", fmt24hr=False)
        h = self.time.GetSize().height
        w = self.time.GetSize().width
        spin = wx.SpinButton( self, -1, wx.DefaultPosition, (-1,h), wx.SP_VERTICAL )
        self.time.BindSpinButton( spin )

        now = wx.DateTime_Now()
        self.time.SetValue( now )
        sizerH1.Add( self.time, 0, wx.ALIGN_LEFT )
        sizerH1.Add( spin, 0, wx.ALIGN_LEFT )
        sizerH1.Add( (5,5) )

        self.date = wx.DatePickerCtrl(self, size=(w,h),style=wx.DP_DROPDOWN)
        sizerH1.Add( self.date, 0 )
        self.sizer.Add( sizerH1, 0, wx.EXPAND|wx.ALL  )

        sizerH1.Add( (100,1),1 )
        button = wx.Button(self, 10, "Attach Files", (10,20))
        sizerH1.Add( button, 0, wx.ALIGN_RIGHT|wx.ALL )

        self.Bind(wx.EVT_BUTTON, self.OnAttachFiles, button )

    def OnPageChanging(self, evt):
        if evt.GetDirection():
            self._filelist = []
            self._dellist = []

            # Save comments
            comments = self.comments.GetValue()
            if len (comments):
                commentsfile = time.strftime( "Comments%s%Y%m%d_%H%M%S.txt", time.localtime())
                fp = file( commentsfile, 'w')
                fp.write( comments )
                fp.close()
                self._filelist.append(commentsfile)
                self._dellist.append(commentsfile)

            # get time/date
            tt=time.strptime(self.time.GetValue(),"%I:%M:%S %p")
            # td=time.gmtime(self.date.GetValue().GetTicks())
            # self.globals['IncidentTime'] =time.mktime( (td.tm_year, td.tm_mon, td.tm_mday, tt.tm_hour, tt.tm_min,tt.tm_sec, td.tm_wday,td.tm_yday,time.daylight))
            self.globals['IncidentTime'] = self.date.GetValue().GetTicks() + 3600*tt.tm_hour + 60*tt.tm_min + tt.tm_sec

    def OnAttachFiles(self, event):
        dlg = wx.FileDialog( self, message="Choose file(s) to attach", defaultDir=os.getcwd(),
                defaultFile="", wildcard='*.*', style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self._filelist.extend(dlg.GetPaths())


class tskPromptUser( ExecTask ):
    """ Task: prompts user for input """

    def Run(self, *pArgs, **nArgs ):

        status = True

        if nArgs.has_key('filepath') and nArgs.has_key('fileprefix'):
            filePath   = nArgs['filepath']
            filePrefix = nArgs['fileprefix']
            filename = time.strftime( filePath + filePrefix + "%Y%m%d_%H%M%S.log",time.localtime())
        else:
            filename = time.strftime("Sys%Y%m%d_%H%M%S.log",time.localtime())

        try:
            fp = file( filename, 'w')
        except:
            return False

        for arg in pArgs:
            tempdict = "{%s}" % str(arg)

            # Evaluate argument syntax
            try:
                args = eval( tempdict )
            except:
                self._error = "\nInvalid argument syntax for %s:\n%s %s\n%r\n" % (self._title, sys.exc_info()[0], sys.exc_info()[1],arg)
                self.printMsg (self._error)
                status = False
                break

            # Generate files from arguments
            try:
                dlg = wx.TextEntryDialog( None, args['Prompt'], args['Title'], args['Value'] )
                if dlg.ShowModal() == wx.ID_OK:
                    fp.write( "%s: %s\n" % (args['Title'], dlg.GetValue()) )
                else:
                    self.printMsg ("Cancelled.\n")
                    break
            except:
                self._error = "\nException running task %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                self.printMsg (self._error)
                status = False
                break

        fp.close()
        self._filelist = [ filename ]
        return status


class tskExpandFiles( ExecTask ):
    """ Task: Given path and file types, returns list of files matching criteria. """

    def Run(self, *pArgs, **nArgs ):
        for arg in pArgs:
            tempdict = "{%s}" % str(arg)

            # Evaluate argument syntax
            try:
                args = eval( tempdict )
            except:
                self._error = "\nInvalid argument syntax for %s:\n%s %s\n%r\n" % (self._title, sys.exc_info()[0], sys.exc_info()[1],arg)
                self.printMsg (self._error)
                return False

            if nArgs.has_key('gauge') :
                gauge = nArgs['gauge']
            else:
                gauge = None

            # Generate files from arguments
            try:
                self._filelist.extend(GenerateFilesList(gauge=gauge,**args))
            except:
                self._error = "\nException running task %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                self.printMsg (self._error)
                continue

        return True

class tskSaveSystemInfo( ExecTask ):
    """ Task: Saves system information. """

    def Run(self, *pArgs, **nArgs ):

        status=True
        if nArgs.has_key('filepath') and nArgs.has_key('fileprefix'):
            filePath   = nArgs['filepath']
            filePrefix = nArgs['fileprefix']
            filename = time.strftime( filePath + filePrefix + "%Y%m%d_%H%M%S.log",time.localtime())
        else:
            filename = time.strftime("Logs/Sys%Y%m%d_%H%M%S.log",time.localtime())

        try:
            os.system("systeminfo > %s" % filename )
            fp = file( filename, 'a+')
            si = SystemInfo()
            generalInfo = si.GetInfo()
            processInfo = si.GetProcess()
            fp.write("\nOs Info:\n")
            for k in generalInfo.keys():
                fp.write("%s: %r \n" % (k,generalInfo[k]))

            fp.write("\nProcess Info:\n")
            for k in processInfo.keys():
                fp.write("%s: %r \n" % (k,processInfo[k]))
        except:
            self._error = "\nException running task %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg (self._error)
            status=False
        fp.close()
        self._filelist.append(filename)
        self._dellist.append(filename)
        return status

class tskFileAttributes( ExecTask ):
    """ Task: Given path and file types, returns list of files matching criteria. """

    def Run(self, *pArgs, **nArgs ):
        if nArgs.has_key('filepath') and nArgs.has_key('fileprefix'):
            filePath   = nArgs['filepath']
            filePrefix = nArgs['fileprefix']
            filename = time.strftime( filePath + filePrefix + "%Y%m%d_%H%M%S.log",time.localtime())
        else:
            filename = time.strftime("FileAttr%Y%m%d_%H%M%S.log",time.localtime())

        try:
            fp = file( filename, 'w')
        except:
            self._error = "\nException running task %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg (self._error)
            return False

        if nArgs.has_key('gauge') :
            gauge = nArgs['gauge']
        else:
            gauge = None

        for arg in pArgs:
            tempdict = "{%s}" % str(arg)

            # Evaluate argument syntax
            try:
                args = eval( tempdict )
            except:
                self._error = "\nInvalid argument syntax for %s:\n%s %s\n%r\n" % (self._title, sys.exc_info()[0], sys.exc_info()[1],arg)
                self.printMsg (self._error)
                return False

            # Generate files from arguments
            try:
                fp.write("\nArgs %s\n" % tempdict )
                filelist = GenerateFilesList(gauge=gauge,**args)
            except:
                self._error = "\nException running task %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                self.printMsg (self._error)
                fp.close()
                return False

            if gauge != None:
                gauge.SetRange( len(filelist) )
                gauge.SetValue( 0 )
            for f in filelist:
                try:
                    fp.write("%s, c:[%s], m:[%s], a:[%s], size:%d\n" % (
                      f,
                      time.ctime(os.path.getctime(f)),
                      time.ctime(os.path.getmtime(f)),
                      time.ctime(os.path.getatime(f)),
                      os.path.getsize(f)))
                    if gauge!=None:
                        gauge.SetValue( gauge.GetValue()+1 )
                        wx.Yield()
                except:
                    self._error = "\nWarning: unable to get file attributes %s\n%s %s" % (f, sys.exc_info()[0], sys.exc_info()[1])
                    self.printMsg (self._error)

        fp.close()
        self._filelist.append(filename)
        self._dellist.append(filename)

        return True

class tskSaveDasRegisters( ExecTask ):
    """ Task: Saves DAS register information. """

    def Run(self, *pArgs, **nArgs ):

        if nArgs.has_key('userpc') and nArgs.has_key('userpc'):
            useRpc = eval(nArgs['userpc'])
        else:
            useRpc = False

        if useRpc == True:
            rpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "sDiag")
            rdDasReg = rpc.rdDasReg
        else:
            import DasInterface
            DasInterface.register_logger( LoggerPrint )
            DasInterface.register_terminator( Terminator )
            DasInterface.USB.UseUSBRecoveryLogic = False
            rdDasReg = DasInterface.rdDasReg

        try:
            if useRpc:
                versions = rpc.dasVersions()
                version = eval(versions['mcu'])
            else:
                version = DasInterface.rdPDasReg(Global.VERSION_REGISTER,Global.VERSION_mcu)
        except:
            self._error = "\nFailed to read MCU version: %s %s\n" % (sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg( self._error )
            return False

        if version < 2.5:
            self._error = "\nFailed. Invalid MCU version %0.2f\n" % version
            self.printMsg( self._error )
            return False

        if nArgs.has_key('filepath') and nArgs.has_key('fileprefix'):
            filePath   = nArgs['filepath']
            filePrefix = nArgs['fileprefix']
            filename = time.strftime( filePath + filePrefix + "%Y%m%d_%H%M%S.log",time.localtime())
        else:
            filename = time.strftime("DasReg%Y%m%d_%H%M%S.log",time.localtime())

        try:
            fp = file( filename, 'w')
            fp.write("Versions, %r\n" % versions )
        except:
            self._error = "%s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg( self._error )
            return False

        for register in range( Global.INTERFACE_NUMBER_OF_REGISTERS ) :

            registerInfo  = Global.register_info[register]

            if registerInfo.name.startswith("FPGA_"):
                fp.write("R%03d: Skipped %s\n" % (register,registerInfo.name))
                continue

            rtype = registerInfo.rtype
            if type(rtype) == type(ctypes.Structure):
                fp.write("R%03d: Ignored %s\n" % (register,registerInfo.name))
                continue

            if registerInfo.name.startswith("IOMGR_FLOAT") or\
              registerInfo.name.startswith("IOMGR_ADC")  or\
              registerInfo.name.startswith("IOMGR_DAC")  or\
              registerInfo.name.startswith("IOMGR_HEATER")    :
                fp.write("R%03d: Ignored %s" % (register,registerInfo.name))
                continue

            # Hard coded workaround - if register number is 592, DAS will reset.
            if version == 2.5 and register >= 592:
                return True

            if registerInfo.readable==True and registerInfo.haspayload==False:
                try:
                    value = rdDasReg( register )
                    fp.write("R%03d, %r, %s\n" % (register,value, registerInfo.name))
                except:
                    fp.write("R%03d, Failed, %s\n" % (register,registerInfo.name))
                    pass
            else:
                pass

        fp.close()
        self._filelist.append(filename)
        self._dellist.append(filename)
        return True

class tskSaveDasDiagnostics( ExecTask ):
    """ Task: Saves DAS diagnostics information. """

    def Run(self, *pArgs, **nArgs ):

        if nArgs.has_key('userpc') and nArgs.has_key('userpc'):
            useRpc = eval(nArgs['userpc'])
        else:
            useRpc = False

        if useRpc == True:
            rpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "sDiag")
        else:
            import DasInterface
            DasInterface.register_logger( LoggerPrint )
            DasInterface.register_terminator( Terminator )
            DasInterface.USB.UseUSBRecoveryLogic = False

        try:
            if useRpc:
                versions = rpc.dasVersions()
                version = eval(versions['mcu'])
            else:
                version = DasInterface.rdPDasReg(Global.VERSION_REGISTER,Global.VERSION_mcu)
        except:
            self._error = "\nFailed to read MCU version: %s %s\n" % (sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg( self._error )
            return False

        if version < 3.0:
            self.printMsg("Failed. Invalid MCU version %0.2f" % version )
            return False

        if nArgs.has_key('filepath') and nArgs.has_key('fileprefix'):
            filePath   = nArgs['filepath']
            filePrefix = nArgs['fileprefix']
            filename = time.strftime( filePath + filePrefix + "%Y%m%d_%H%M%S.log",time.localtime())
        else:
            filename = time.strftime("DasDiag%Y%m%d_%H%M%S.log",time.localtime())

        if useRpc:
            rpc.DIAG_SaveTables( filename )
        else:
            import DasDiag
            diag = DasDiag.Diag()
            diag.DIAG_SaveTables( filename )

        self._filelist.append(filename)
        self._dellist.append(filename)
        return True

class tskReadClocks( ExecTask ):
    """ Task: Reads ticks from DAS and time from system. """

    def Run(self, *pArgs, **nArgs ):

        if nArgs.has_key('userpc') and nArgs.has_key('userpc'):
            useRpc = eval(nArgs['userpc'])
        else:
            useRpc = False

        if useRpc == True:
            rpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "sDiag")
            rdDasReg = rpc.rdDasReg
        else:
            import DasInterface
            DasInterface.register_logger( LoggerPrint )
            DasInterface.register_terminator( Terminator )
            DasInterface.USB.UseUSBRecoveryLogic = False
            rdDasReg = DasInterface.rdDasReg

        try:
            if useRpc:
                versions = rpc.dasVersions()
                version = eval(versions['mcu'])
            else:
                version = DasInterface.rdPDasReg(Global.VERSION_REGISTER,Global.VERSION_mcu)
        except:
            self._error = "\nFailed to read MCU version: %s %s\n" % (sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg( self._error )
            return False

        if nArgs.has_key('filepath') and nArgs.has_key('fileprefix'):
            filePath   = nArgs['filepath']
            filePrefix = nArgs['fileprefix']
            filename = time.strftime( filePath + filePrefix + "%Y%m%d_%H%M%S.log",time.localtime())
        else:
            filename = time.strftime("Clock%Y%m%d_%H%M%S.log",time.localtime())

        try:
            fp = file( filename, 'w')
            fp.write("MCU Version, %00.2f\n" % version )
        except:
            self._error = "%s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg( self._error )
            return False

        clockList = []
        iterations = eval(nArgs['iterations'])
        try:
            for i in range(iterations):
                dasTicks  = rdDasReg( Global.CLOCK_TICKS_REGISTER )
                hostClock = time.time()
                clockList.append( (dasTicks, hostClock) )

            fp.write("DAS Ticks vs System Ticks\n")
            for i in range(iterations):
                fp.write("%r\t%r\n" % clockList[i])
        except:
            self._error = "%s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg( self._error )
            fp.close()
            return False

        fp.close()
        self._filelist.append(filename)
        self._dellist.append(filename)
        return True

class tskGetFilesFromLibrarian( ExecTask ):
    """ Task: Retrieves files from librarian. """

    def _CustomCopy( self, group, start, stop, skips, max, destDir, reverse, dontSkipPairs ):
        """ Custom Copy files. Skips - number of files to skip """

        # Get files from Librarian
        tempDir = tempfile.mkdtemp()
        count = self.rpc.CopyFileDates( group, start, stop, tempDir, True )
        if count==0:
            return 0

        # Get list of filenames/timestamps
        for root, dirs, files in os.walk(tempDir):
            tempList  = []
            for filename in files:
                fullfilename = root + '\\' + filename
                filetime = os.path.getmtime(fullfilename)
                tempList.append( (filetime, fullfilename) )

        # Sort according to timestamp,filename
        tempList.sort( reverse=reverse )

        # Move files to destination folders
        fcount=0
        findex=0
        prevPrefix=''
        for timestamp,filename in tempList:
            temp = filename.split('.')
            base = os.path.basename( temp[0] )
            prefixList = base.split('_',1)
            if len(prefixList)<=1:
                prefix=''
            else:
                prefix=prefixList[1]
            if (dontSkipPairs and prevPrefix == prefix) or operator.mod(findex,skips)==0:
                shutil.move( filename, destDir )
                fcount+=1
            prevPrefix = prefix
            findex += 1
            if fcount>(max):
                break
        shutil.rmtree( tempDir )
        return fcount

    def ConnectLibrarian( self, maxIterations, *pArgs, **nArgs ):

        # Check rpc
        iterations = 0
        LaunchLibrarianFlag = eval(nArgs['launchlibrarian'])
        EventManagerCmd = eval(nArgs['eventmanagercmd'])
        LibrarianCmd = eval(nArgs['librariancmd'])

        while iterations < maxIterations:

            if LaunchLibrarianFlag:
                try:
                    si = SystemInfo()
                    if si.ProcessRunning('EventManager',True)==False:
                        CreateProcess(EventManagerCmd)
                        time.sleep( 1 )
                    if si.ProcessRunning('Librarian',True)==False:
                        CreateProcess(LibrarianCmd)
                        time.sleep( 1 )
                except:
                    self._error = "\n%s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                    self.printMsg (self._error)

            try:
                rpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER, ClientName = "sDiag")
                rpc.GetGroupList()
                break
            except:
                self._error = "\n%s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                self.printMsg (self._error)
                status = False
                rpc=None
            iterations+=1
            time.sleep( 1 )

        if iterations>=maxIterations:
            return (False,None)
        return (True,rpc)

    def Run(self, *pArgs, **nArgs ):
        """ Execute Test """

        status = True
        useAlternateMethod = False
        useBackup = eval(nArgs['usebackup'])

        status,self.rpc = self.ConnectLibrarian(5, **nArgs)
        if status==False:
            useAlternateMethod = True

        total = 0
        # In case librarian not working.
        if useAlternateMethod == False:
            for arg in pArgs:

                copyCount = 0

                # Eval parameters for group
                try:
                    tempdict = "{%s}" % str(arg)
                    args = eval( tempdict )
                    libraryGroupInfo  = self.rpc.GetGroupInfo( args['Group'] )
                    libraryStorageDir = libraryGroupInfo['StorageDir']
                    tempDir = libraryStorageDir + '/TempCopy'
                except:
                    self._error = "Exception %s %s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                    self.printMsg (self._error)
                    status=False
                    useAlternateMethod=True
                    continue

                # Cleanup, create directory
                try:
                    if os.path.isdir( tempDir ):
                        shutil.rmtree( tempDir )
                    os.mkdir( tempDir )
                except:
                    self._error = "Exception creating folder %s %s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                    self.printMsg (self._error)
                    status=False
                    continue

                try:
                    if args.has_key('Group') == False:
                        self.printMsg("Arg: missing 'Group', ignored arguments: %r`\n" % args)
                        status=False
                        continue

                    if args.has_key('UseIncidentTime'):
                        useIncidentTime = args['UseIncidentTime']
                        itime = nArgs['globals']['IncidentTime']

                        if args.has_key('MatchPairs'):
                            matchPairs = args['MatchPairs']
                        else:
                            matchPairs = False

                        # Copy all files in small window
                        smallWindowDeltaTimeMins = args['SmallWindowDeltaTimeMins']
                        sStartTime = itime - smallWindowDeltaTimeMins* secondsPerMinute
                        sStopTime  = itime + smallWindowDeltaTimeMins* secondsPerMinute
                        copyCount += self.rpc.CopyFileDates( args['Group'], sStartTime, sStopTime, tempDir, True )

                        largeWindowDeltaTimeMins = args['LargeWindowDeltaTimeMins']
                        largeWindowSkipFiles = args['LargeWindowSkipFiles']
                        largeWindowMaxFiles = args['LargeWindowMaxFiles']/2

                        deltaMins = largeWindowDeltaTimeMins - smallWindowDeltaTimeMins

                        self.printMsg( "Copying files around - %s\n" % (time.ctime(itime)))

                        if largeWindowDeltaTimeMins > smallWindowDeltaTimeMins:

                            lStartTime1 = sStartTime - deltaMins * secondsPerMinute
                            lStopTime1  = sStartTime

                            lStartTime2 = sStopTime
                            lStopTime2  = sStopTime + deltaMins * secondsPerMinute

                            stime = lambda s: time.strftime("%X", time.localtime(s))
                            self.printMsg( "%s,%s - %s,%s (s:%d,m:%d)\n" % (stime(lStartTime1),stime(sStartTime),stime(sStopTime),stime(lStopTime2), largeWindowSkipFiles, largeWindowMaxFiles ) )

                            copyCount += self._CustomCopy( args['Group'], lStartTime1, lStopTime1,
                              largeWindowSkipFiles, largeWindowMaxFiles/2, tempDir, True, matchPairs )

                            copyCount += self._CustomCopy( args['Group'], lStartTime2, lStopTime2,
                              largeWindowSkipFiles, largeWindowMaxFiles/2, tempDir, False, matchPairs )

                    elif args.has_key('RecentDays'):
                        seconds = args['RecentDays'] * secondsPerDay
                        copyCount += self.rpc.CopyRecentFiles( args['Group'], seconds, tempDir, True )
                    elif args.has_key('RecentHours'):
                        seconds += args['RecentHours'] * secondsPerHour
                        copyCount = self.rpc.CopyRecentFiles( args['Group'], seconds, tempDir, True )
                    elif args.has_key('RecentMinutes'):
                        seconds += args['RecentMinutes'] * secondsPerMinute
                        copyCount = self.rpc.CopyRecentFiles( args['Group'], seconds, tempDir, True )
                    elif args.has_key('RecentSeconds'):
                        seconds += args['RecentSeconds']
                        copyCount = self.rpc.CopyRecentFiles( args['Group'], seconds, tempDir, True )
                    elif args.has_key('StartDate') and args.has_key('StopDate'):
                        startDate = args['StartDate']
                        stopDate = args['StopDate']
                        startTime = ConvertDateToTime( startDate )
                        stopTime = ConvertDateToTime( stopDate )
                        copyCount += self.rpc.CopyFileDates( args['Group'], startTime, stopTime, tempDir, True )
                    else:
                        copyCount += self.rpc.CopyAllFiles( args['Group'], tempDir, True )

                    self.printMsg( "[%s]: Copied %d files\n" % (args['Group'],copyCount) )
                    total += copyCount

                except:
                    self._error = "Exception running task %s %s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                    self.printMsg (self._error)
                    status=False
                    useAlternateMethod=True
                    continue

                # Add all files in tempDir
                for root, dirs, files in os.walk(tempDir):
                    for name in files:
                        self._filelist.append(os.path.join(root, name))
                        self._dellist.append(os.path.join(root, name))

        if useBackup and (total == 0 or useAlternateMethod==True):
            self.printMsg("\nNo files copied or some Librarian calls failed. Using alternative method.\n")
            for arg in nArgs:
                if arg.startswith('alt_arg'):
                    tempdict = "{%s}" % str(nArgs[arg])
                    alt_args = eval( tempdict )
                    list = GenerateFilesList(**alt_args)
                    self._filelist.extend( list )
        return status

class tskCheckApp( ExecTask ):
    """ Task: Check if app running """

    def Run(self, *pArgs, **nArgs ):

        processName = nArgs['processname']
        failtitle   = nArgs['failtitle']
        failmsg     = nArgs['failmsg']
        maxAttempts = eval(nArgs['maxattempts'])
        verbose     = eval(nArgs['verbose'])

        attempts=0
        si = SystemInfo()
        while attempts<=maxAttempts:
            if si.ProcessRunning(processName,verbose)==True:
                if verbose:
                    self.printMsg("Task running: %s\n" % processName )
                time.sleep(1)
                return True
            else:
                self.printMsg(failmsg)
                dlg = wx.MessageDialog(self.parent, failmsg, failtitle, wx.OK | wx.ICON_INFORMATION )
                dlg.ShowModal()
                dlg.Destroy()
                self.error= "Task not running: %s\n" % processName
            attempts+=1
            time.sleep(0.5)
        return False

class tskStartApp( ExecTask ):
    """ Task: Start up applications if not already started """

    def Run(self, *pArgs, **nArgs ):

        checkProcessFlag = eval(nArgs['checkprocess'])
        processName      = nArgs['processname']
        commandLine      = eval(nArgs['commandline'])
        verbose          = eval(nArgs['verbose'])
        maxAttempts      = eval(nArgs['maxattempts'])

        attempts=0
        si = SystemInfo()
        while attempts<=maxAttempts:
            if si.ProcessRunning(processName,verbose)==True:
                if verbose:
                    self.printMsg(" Task running ")
                return True

            # Shut down other python apps so they won't interfere with downloads
            try:
                CreateProcess( commandLine )
            except:
                self._error = "\nTaskError: %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                self.printMsg (self._error)
            attempts+=1
            time.sleep(1)

        return False

class tskShutdownHostApps( ExecTask ):
    """ Task: Shutdown host applications through Supervisor """

    def Run(self, *pArgs, **nArgs ):
        if nArgs.has_key('promptuser') :
            promptUser = eval(nArgs['promptuser'])
        else:
            promptUser = False

        # Shut down other python apps so they won't interfere with downloads
        try:
            from Supervisor import RPC_SERVER_PORT_MASTER
            rpcServer = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_SERVER_PORT_MASTER, ClientName = self._title )
            if promptUser == True:
                dlg = wx.SingleChoiceDialog(None, "Terminate Host App(s)?" ,'Warning',['Yes','No'], wx.CHOICEDLG_STYLE)
                if dlg.ShowModal() == wx.ID_OK:
                    if dlg.GetStringSelection() == 'Yes':
                        rpcServer.TerminateApplications()
            else:
                rpcServer.TerminateApplications()
            time.sleep( 3 )
            return True
        except:
            self._error = "\nTaskError: %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
            self.printMsg (self._error)
            return False

class tskSetDasKeepaliveFlag( ExecTask ):
    """ Task: set keepalive flag """

    def Run(self, *pArgs, **nArgs ):

        keepalive  = eval(nArgs['keepalive'])
        iterations = eval(nArgs['iterations'])
        interval   = eval(nArgs['interval'])
        useRpc = eval(nArgs['userpc'])

        if useRpc == True:
            rpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "sDiag")
            rdDasReg = rpc.rdDasReg
            wrDasReg = rpc.wrDasReg
        else:
            import DasInterface
            DasInterface.register_logger( LoggerPrint )
            DasInterface.register_terminator( Terminator )
            DasInterface.USB.UseUSBRecoveryLogic = False
            rdDasReg = DasInterface.rdDasReg
            wrDasReg = DasInterface.wrDasReg

        status = True
        for i in range(iterations):
            try:
                if useRpc==False:
                    DasInterface.USB.startUSB()
                if keepalive:
                    wrDasReg( Global.KEEPALIVE_ENABLE_REGISTER, 1)
                else:
                    wrDasReg( Global.KEEPALIVE_ENABLE_REGISTER, 0)
                if useRpc==False:
                    DasInterface.USB.stopUSB()
                break
            except:
                self._error = "\nTaskError: %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                self.printMsg (self._error)
                status = False
            time.sleep( interval )
        return status

def CreateProcess( command ):
    import win32con
    import win32api
    import win32process

    lpApplicationName = None
    lpCommandLine = command
    lpProcessAttributes = None
    lpThreadAttributes = None
    bInheritHandles = False
    dwCreationFlags = win32process.NORMAL_PRIORITY_CLASS #| win32process.CREATE_NO_WINDOW
    lpEnvironment = None
    lpCurrentDirectory = None
    lpStartupInfo = win32process.STARTUPINFO()
    hProcess, hThread, dwProcessId, dwThreadId =  win32process.CreateProcess(
      lpApplicationName,
      lpCommandLine,
      lpProcessAttributes,
      lpThreadAttributes,
      bInheritHandles,
      dwCreationFlags,
      lpEnvironment,
      lpCurrentDirectory,
      lpStartupInfo
      )
    return dwProcessId

def GenerateFilesList( Path, Expr, Recursive=False, MaxFiles=None, StartTime=None, StopTime=None, StartDate=None,StopDate=None, RecentDays=None, RecentHours=None, RecentMinutes=None, RecentSeconds=None, Debug=False, gauge=None ):
    """ returns list of files matching expression """

    if RecentDays or RecentHours or RecentMinutes or RecentSeconds:
        if ((RecentDays!=None) ^ (RecentHours!=None) ^ (RecentMinutes!=None) ^ (RecentSeconds!=None)) == False:
            sys.exit('Invalid arguments. Not allowed to have mutiple Recent parameters.')
    elif StartTime or StopTime or StartDate or StopDate:
        if (StartTime or StartDate) and ((StartTime!=None) ^ (StartDate!=None))==False:
            sys.exit('Invalid arguments. Not allowed to have mutiple Start Time/Date parameters.')
        if StartDate!=None:
            StartTime = ConvertDateToTime( StartDate )
        if (StartTime or StartDate) and ((StopTime!=None) ^ (StopDate!=None))==False:
            sys.exit('Invalid arguments. Not allowed to have mutiple Stop Time/Date parameters.')
        if StopDate!=None:
            StopTime = ConvertDateToTime( StopDate ) * secondsPerDay # inclusive

    if RecentDays != None:
        StopTime  = time.time()
        StartTime = StopTime - secondsPerDay*RecentDays
    elif RecentHours!= None:
        StopTime  = time.time()
        StartTime = StopTime - secondsPerHour*RecentHours
    elif RecentMinutes!= None:
        StopTime  = time.time()
        StartTime = StopTime - secondsPerMinute*RecentMinutes
    elif RecentSeconds!= None:
        StopTime  = time.time()
        StartTime = StopTime - RecentSeconds

    if not os.path.isdir(Path):
        sys.exit(Path + ' is not a valid dir to walk.')

    try:
        cre = re.compile(Expr)
    except:
        sys.exit("Exception compiling expr %s %s %s" % (Expr, sys.exc_info()[0], sys.exc_info()[1]))

    if Debug:
        print("StartTim: %r, StopTime: %r\n" % (StartTime,StopTime))

    filesList = []
    for root, dirs, files in os.walk( Path ):

        if gauge != None:
            gauge.SetRange( len(files) )
            gauge.SetValue( 0 )

        tempList  = []
        for filename in files:

            if gauge!=None:
                gauge.SetValue( gauge.GetValue()+1 )
                wx.Yield()

            fullfilename = root + '\\' + filename
            try:
                filetime = os.path.getmtime(fullfilename)

                # Does file match wildcard/type?
                if cre.search(filename)==None:
                    if Debug: print "-m %r" % (fullfilename)
                    continue

                # Match Time
                if StartTime != None and filetime < StartTime:
                    if Debug: print "-t %r, %r" % (time.ctime(filetime),fullfilename)
                    continue
                if StopTime  != None and filetime > StopTime:
                    if Debug: print "-t %r, %r" % (time.ctime(filetime),fullfilename)
                    continue

                if Debug: print "++ %r, %r" % (time.ctime(filetime),fullfilename)
                tempList.append( (filetime, fullfilename) )

            except:
                self._error = "\nTaskError: %s\n%s %s" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
                print (self._error)


        # Sort files according to time and return files (max count)
        c= 0
        tempList.sort()
        for t,f in tempList:
            if MaxFiles != None and c >= MaxFiles:
                break;
            filesList.append( f )
            c+=1

        # Take care of directories
        if Recursive == False:
            break

    if Debug: pprint.pprint ("\n:RESULTS: \n %s" % filesList )
    return filesList

def ConvertDateToTime(date):
    """ Convert date string('month day year') to time in seconds """
    timetuple = time.strptime( date,"%b %d %Y")
    return time.mktime( timetuple )

def LoggerPrint( Desc, Data = "", Level = 1, Code = -1, AccessLevel = 0, Verbose = "", SourceTime = 0):
    global LogMsg
    LogMsg (Desc)

def Terminator():
    global LogMsg
    LogMsg ("Termination requested.")

if __name__ == "__main__" :
    #StartTime = ConvertDateToTime( 'Sep 18 2005' )
    #StopTime = ConvertDateToTime( 'Sep 20 2006' )
    #files = GenerateFilesList('C:/data/view/pfw/Silverstone/_HostCore/Utilities/DasMaintenanceGui','.*\.pyc$', Recursive=True, MaxFiles=10, StartTime=StartTime, StopTime=StopTime,Debug=True )
    #GenerateFilesList('C:/data/view/pfw/Silverstone/_HostCore/Utilities/DasMaintenanceGui','.*\.py$', Recursive=True, MaxFiles=100, RecentDays=1,Debug=True )
    #GenerateFilesList('C:/data/view/pfw/Silverstone/_HostCore/Utilities/DasMaintenanceGui','.*\.py$', Recursive=True, MaxFiles=100, RecentHours=4,Debug=True )
    #GenerateFilesList('C:/data/view/pfw/Silverstone/_HostCore/Utilities/DasMaintenanceGui','.*\.py$', Recursive=True, MaxFiles=100, RecentMinutes=1,Debug=True )
    #GenerateFilesList('C:/data/view/pfw/Silverstone/_HostCore/Utilities/DasMaintenanceGui','.*\.py$', Recursive=True, MaxFiles=100, RecentSeconds=30,Debug=True )
    pass
