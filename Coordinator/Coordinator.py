"""
File Name: Coordinator.py
Purpose: Coordinator program for autosampler, evaporator and CRDS analyzer
                                                            
File History:
    08-06-02  sze  Initial version.
    08-12-04  alex Used CustomConfigObj to replace configobj. Monitored coordinator using Supervisor.
    09-01-30  alex moved the output file to ..\..\Log\PulseAnalyzerResults directory instead of the supervisor directory

Copyright (c) 2010 Picarro, Inc. All rights reserved 
"""             

APP_NAME = "Coordinator"
APP_DESCRIPTION = "Coordinator program for autosampler, evaporator and CRDS analyzer"
__version__ = 1.0

import wx
import os
import sys
import time
import getopt
import csv
import re
import threading
from Queue import Queue

from CoordinatorFrameGui import CoordinatorFrameGui
from CoordinatorParamGui import InitialParamDialogGui
from CoordinatorStateMachine import State, StateMachine, OK, EXCEPTION, TIMEOUT
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_COORDINATOR
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = os.path.abspath(sys.argv[0])
AppPath = os.path.abspath(AppPath)

LOG = 1
OUTFILE = 2
CONTROL = 3

class RpcServerThread(threading.Thread):
    def __init__(self, RpcServer, ExitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
            
class FsmThread(threading.Thread):
    def __init__(self,configFile,guiQueue,replyQueue,gui,editParamDict,*a,**k):
        threading.Thread.__init__(self,*a,**k)
        self.configFile = configFile
        self.guiQueue = guiQueue
        self.replyQueue = replyQueue
        self.gui = gui
        self.fsm = None
        self.editParamDict = editParamDict

    def fileDataFunc(self,dataList):
        # When sending data to the output file, 
        self.guiQueue.put((OUTFILE,dataList))
        wx.WakeUpIdle()
        
    def logFunc(self,str):
        self.guiQueue.put((LOG,str))
        wx.WakeUpIdle()
    
    def controlFunc(self,action):
        self.guiQueue.put((CONTROL,action))
        wx.WakeUpIdle()
        return self.replyQueue.get()
        
    def run(self):
        self.logFunc("\nFSM thread starts\n")
        self.fsm = StateMachine(iniFile=file(self.configFile),gui=self.gui,logFunc=self.logFunc,
                    fileDataFunc=self.fileDataFunc,controlFunc=self.controlFunc,editParamDict=self.editParamDict)
        try:
            self.fsm.run()
            self.logFunc("\nFSM thread finished")
        except Exception,e:
            self.logFunc("\nFSM thread exception %s" % e)

    def stop(self):
        if self.fsm.isRunning():
            self.fsm.stop()
            self.logFunc("\nFSM thread stopped by request")

    def isRunning(self):
        return self.fsm.isRunning()

    def turnOffRunningFlag(self):
        self.fsm.turnOffRunningFlag()

    def turnOnRunningFlag(self):
        self.fsm.turnOnRunningFlag()
        
class CoordinatorFrame(CoordinatorFrameGui):
    def __init__(self, hasSampleDescr, hasSampleNum, useSeptum, hasCloseOpt, hasPause, forcedClose, configFile, *a,**k):
        # The logfile and data file are opened in the main GUI thread. 
        #  They are written to by the control thread which runs the state machine via 
        #  Queues which buffer the writes. The control thread is reinitialized each
        #  time a new file is selected so that the system may be restarted in a known
        #  state.
        #  The data file contains a header with sample descriptions. This is a text area which
        #   can contain any information, but is typically a list of pairs of the form
        #  sample number, sample description
        #  Following the header are the actual data themselves. These data are also stored in the 
        #   list self.outputFileDataList so that we can rewrite the output file whenever the 
        #   sample description header changes.
        
        self.configFile = configFile
        self.config = CustomConfigObj(configFile, list_values = True)
        
        # Create editable param tuple llist
        self.paramTupleList = []
        self.numDispParams = 0
        try:
            editParamSection = self.config["UserEditableParams"]
            for id in range(len(editParamSection)-1):
                paramInfo = editParamSection[str(id)]
                paramTuple = (paramInfo[0], paramInfo[1], paramInfo[2])
                self.paramTupleList.append(paramTuple)
            self.numDispParams = int(editParamSection["num_disp_params"])   
        except:
            pass

        CoordinatorFrameGui.__init__(self, hasSampleDescr, hasSampleNum, useSeptum, hasPause, self.paramTupleList, self.numDispParams, *a, **k)
        self.guiQueue = Queue(0)
        self.replyQueue = Queue(0)
        self.fsmThread = None
        self.saveFileName = ""
        
        self.saveFp = None
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_IDLE,self.onIdle)
        # sampleDescriptionDict and sampleIndexDict are inverses of each other
        self.sampleDescriptionDict = {}
        self.sampleIndexDict = {}
        self.rewriteOutputFile = False
        self.outputFileDataList = []
        self.manualSampleNumber = 0
        self.sampleDescrComboBox.SetValue("Default description: sample 1")
        self.widthRe = re.compile("%(-?\d+)\D*")
        self.lineIndex = 0
        self.hasCloseOpt = hasCloseOpt
        self.forcedClose = forcedClose
        self.startServer()
        self.sampleNum = 1
        self.logFp = None
        
    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_COORDINATOR),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)                                                          
        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.shutdown)
        self.rpcThread.start()

    def popWarning(self, msg, title=""):
        warningThread = threading.Thread(target=self._showWarning, args = (msg,title,))
        warningThread.setDaemon(True)
        warningThread.start()
      
    def _showWarning(self, msg, title):
        d = wx.MessageDialog(None, msg, title, wx.ICON_WARNING)
        d.ShowModal()

    def shutdown(self):
        self.rpcServer.stop_server()
        
    def enableManualButton(self):
        self.manualButton.Enable()

    def disableManualButton(self):
        self.manualButton.Disable()
    
    def getManualButtonState(self):
        return self.manualButton.IsEnabled()

    def setManualButtonText(self,text):
        self.manualButton.SetLabel(text)

    def enableChangeSeptumButton(self):
        try:
            self.changeSeptumButton.Enable()
        except:
            pass
    def disableChangeSeptumButton(self):
        try:
            self.changeSeptumButton.Disable()
        except:
            pass
    def getChangeSeptumButtonState(self):
        try:
            return self.changeSeptumButton.IsEnabled()
        except:
            pass
    def setChangeSeptumButtonText(self,text):
        try:
            self.changeSeptumButton.SetLabel(text)
        except:
            pass
    def setChangeSampleNumText(self,text):
        try:
            self.textCtrlChangeSampleNum.SetValue(text)
        except:
            pass            
    def setStatusText(self,text):
        self.statusbar.SetStatusText(text)

    def getManualSampleNumber(self):
        return self.manualSampleNumber
    
    def run(self):
        self.setStatusText("")
        self.saveFileName = self.makeFilename()
        try:
            logFname = self.config["Files"]["log"]
            dirName = os.path.dirname(logFname)
            if not os.path.isdir(dirName):
                os.mkdir(dirName)
            self.logFp = file(time.strftime(logFname+"_%Y%m%d_%H%M%S.log",self.lastFileTime),"w")
        except:
            self.logFp = None
        
        self.manual = True
        try:
            if self.config["Mode"]["inject_mode"].lower() != "manual":
                self.panel_1.GetSizer().Hide(2)
                self.panel_1.GetSizer().Layout()
                self.manual = False
        except Exception,e:
            print "Run exception: %s" % e
            pass
            
        if self.manual and "Trays" in self.config:
            raise ValueError("Cannot use Trays with manual injection")
            
        self.saveFp = file(self.saveFileName,"wb")
        self.onWriteHeadings()
        self.startStateMachineThread(self.paramTupleList)

    def makeFilename(self):
        try:
            baseFname = self.config["Files"]["output"]
            dirName = os.path.dirname(baseFname)
            if not os.path.isdir(dirName):
                os.mkdir(dirName)
        except:
            baseFname = "PulseAnalysisResults"
        self.lastFileTime = time.localtime()
        return time.strftime(baseFname+"_%Y%m%d_%H%M%S.csv",self.lastFileTime)

    def onLoadSampleDescriptions(self,event):
        try:
            print "OnLoadSampleDescriptions"
            if "Trays" in self.config:
                trayNames = self.config["Trays"].values()
                for tray in trayNames:
                    self.getSampleDescriptionFile("Sample description file for tray %s" % (tray,),tray)
            else:
                self.getSampleDescriptionFile("Sample description file")
            event.Skip()
        except:
            pass

    def getSampleDescriptionFile(self,dialogTitle,trayName=None):             
        dlg = wx.FileDialog(
            self, message=dialogTitle, defaultDir=os.getcwd(), 
            wildcard="Comma separated value file (*.csv)|*.csv", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.sampleDescriptionFileName = dlg.GetPath()
            newDict = {}
            fp = file(self.sampleDescriptionFileName,"r")
            headings = ["Vial","description"]
            try:
                for i,row in enumerate(csv.reader(fp)):
                    if len(row)==0: continue
                    try:
                        int(row[0]) # Determine if this is a row of headings
                    except:
                        headings = [r.strip() for r in row]
                        continue
                    # At this stage, we have a row of real data
                    if len(row) > len(headings): # We must merge columns at end of row
                        row[len(headings)-1] = (",".join(row[len(headings)-1:])).strip()
                    dataDict = {}
                    for h,r in zip(headings,row):
                        dataDict[h] = r.strip()
                    if "Vial" in dataDict:
                        index = int(dataDict["Vial"])
                        if "description" not in dataDict:
                            dataDict["description"] = "Vial %s" % index
                        if trayName != None:
                            index = (trayName,index)
                        newDict[index] = dataDict
                        self.sampleIndexDict[dataDict["description"]] = index
                self.sampleDescriptionDict.update(newDict)
                self.updateSampleDescrComboBox()
                default = self.sampleDescrComboBox.GetString(0)
                self.sampleDescrComboBox.SetValue(default)
                self.rewriteOutputFile = True
            except Exception,e:
                print e
                fp.close()
                fp = file(self.sampleDescriptionFileName,"r")
                for j in range(i): fp.readline()
                wx.MessageBox("Error in line %d of sample description file:\n\n%s" % (i,fp.readline()),
                              "Error",wx.OK)
        dlg.Destroy()
        
    def updateSampleDescrComboBox(self):
        current = self.sampleDescrComboBox.GetValue()
        self.sampleDescrComboBox.Clear()
        for k in sorted(self.sampleDescriptionDict):
            self.sampleDescrComboBox.Append(self.sampleDescriptionDict[k]["description"])
        self.sampleDescrComboBox.SetValue(current)

    def onPause(self, event):
        self.fsmThread.turnOffRunningFlag()
            
    def onResume(self, event):
        self.fsmThread.turnOnRunningFlag()
        
    def onChangeSeptum(self,event):
        try:
            self.disableChangeSeptumButton()
            self.setChangeSeptumButtonText("Please Wait...")
        except:
            pass

    def onChangeSampleNum(self, event):
        try:
            self.sampleNum = int(event.GetString())
        except:
            pass
            
    def onManualButton(self,event):
        self.disableManualButton()
        maxIndex = max([0] + self.sampleDescriptionDict.keys())
        descr = self.sampleDescrComboBox.GetValue().strip()
        if not descr:
            descr = "Default description: sample %d" % (maxIndex+1,)
            self.sampleDescrComboBox.SetValue(descr)
        if descr not in self.sampleIndexDict:
            self.sampleDescriptionDict[maxIndex+1] = {"description":descr}
            self.sampleIndexDict[descr] = maxIndex+1
            self.updateSampleDescrComboBox()
            self.rewriteOutputFile = True
        self.manualSampleNumber = self.sampleIndexDict[descr]        
        
    def onWriteHeadings(self):
        notOpen = self.saveFp == None
        if notOpen:
            self.saveFp = file(self.saveFileName,"ab")
        try:
            writer = csv.writer(self.saveFp)
            head = []
            for k in self.config["Output"]:
                t, f = self.config["Output"][k]
                m = self.widthRe.match(f.strip())
                if m:
                    head.append(("%%%ss" % (m.group(1),)) % t)
                else:
                    raise ValueError("Format %s does not have a valid width specification" % f.strip())
            writer.writerow(head)
            for i,h in enumerate(head):
                self.fileDataListCtrl.InsertColumn(i,h.strip(),width=-1)
        finally:
            if notOpen:
                self.saveFp.close()
                self.saveFp = None
                
    def onNewFile(self,event):
        dlg = wx.FileDialog(
            self, message="File name for data ...", defaultDir=os.getcwd(), 
            defaultFile=self.makeFilename(), wildcard="Comma-separated value file (*.csv)|*.csv", style=wx.SAVE)
        # dlg.SetFilterIndex(2)
        if dlg.ShowModal() == wx.ID_OK:
            self.saveFileName = dlg.GetPath()
            if self.saveFp != None:
                self.saveFp.close()
                self.saveFp = None
            self.saveFp = file(self.saveFileName,"wb")
            self.terminateStateMachineThread()
            # Clear the data list
            self.outputFileDataList = []
            # Keep the file closed. It is briefly opened for append when required
            self.saveFp.close()
            self.saveFp = None
            self.rewriteOutputFile = True
            self.startStateMachineThread()
        dlg.Destroy()
        event.Skip()

    def setParamText(self,idx,text):
        try:
            self.paramTextCtrlList[idx].SetValue(text)
        except:
            pass 
            
    def terminateStateMachineThread(self):
        if self.fsmThread != None:
            self.fsmThread.stop()
            self.fsmThread.join()
            self.fsmThread = None
        # Flush guiQueue and replyQueue
        while not self.guiQueue.empty(): self.guiQueue.get()
        while not self.replyQueue.empty(): self.replyQueue.get()
        
    def startStateMachineThread(self, paramTupleList):
        guiParamDict = {}
        if len(paramTupleList) > 0:
            dlg = InitialParamDialogGui(paramTupleList, None, -1, "")
            getParamVals = (dlg.ShowModal() == wx.ID_OK)
            for idx in range(len(paramTupleList)):
                if getParamVals:
                    guiParamDict[dlg.nameList[idx]] = dlg.textCtrlList[idx].GetValue()
                else:
                    guiParamDict[dlg.nameList[idx]] = paramTupleList[idx][2]
                if idx < self.numDispParams:
                    self.setParamText(idx, guiParamDict[dlg.nameList[idx]])
            dlg.Destroy()
            print guiParamDict

        if self.fsmThread != None:
            self.terminateStateMachineThread()
        self.filenameTextCtrl.SetValue(os.path.split(self.saveFileName)[-1])
        self.fsmThread = FsmThread(configFile=self.configFile,gui=self,
            guiQueue=self.guiQueue,replyQueue=self.replyQueue,editParamDict=guiParamDict)
        self.fsmThread.setDaemon(True)
        self.fsmThread.start()

    def processData(self,data):
        if "sampleNum" not in data:
            data["sampleNum"] = self.sampleNum           
        try:
            data.update(self.sampleDescriptionDict[(data["trayName"],data["sampleNum"])])
        except:
            try:
                data.update(self.sampleDescriptionDict[data["sampleNum"]])
            except:
                pass
        if "Tray" in data and "Vial" in data:
            data["port"] = "%d-%02d" % (int(data["Tray"]),int(data["Vial"]))
        else:
            try:
                data["port"] = "%s-%02d" % (data["trayName"],int(data["sampleNum"]))
            except:
                pass
                
        h = []
        for k in self.config["Output"]:
            t, f = self.config["Output"][k]
            try:
                h.append(f % data[k])
            except:
                m = self.widthRe.match(f.strip())
                if m:
                    h.append(("%%%ss" % (m.group(1),)) % "")
                else:
                    raise ValueError("Bad format string %s" % f.strip())
        self.fileDataListCtrl.InsertStringItem(self.lineIndex,h[0].strip())
        for i,t in enumerate(h[1:]):
            self.fileDataListCtrl.SetStringItem(self.lineIndex,i+1,t.strip())
        self.fileDataListCtrl.EnsureVisible(self.lineIndex)
        self.lineIndex += 1
        notOpen = (self.saveFp == None)
        if notOpen:
            self.saveFp = file(self.saveFileName,"ab")
        try:
            w = csv.writer(self.saveFp)
            w.writerow(h)
        finally:
            if notOpen:
                self.saveFp.close()
                self.saveFp = None
        # Increase sample number by 1 when finishing processing a new data, not when description changes
        if not self.rewriteOutputFile:
            # In case the sampleNum was provided outside of Coordinator, we still want to align the self.sampleNum with it
            self.sampleNum = data["sampleNum"]
            self.sampleNum += 1
            self.setChangeSampleNumText(str(self.sampleNum))
            
    def onIdle(self,event):
        if self.rewriteOutputFile: # Descriptions have changed, rewrite file
            self.fileDataListCtrl.ClearAll()
            self.lineIndex = 0
            self.saveFp = file(self.saveFileName,"wb")
            try:
                self.onWriteHeadings()
                for data in self.outputFileDataList:
                    self.processData(data)
            finally:
                self.saveFp.close()
                self.saveFp = None
                self.rewriteOutputFile = False
        while not self.guiQueue.empty():
            type, data = self.guiQueue.get()
            if type == LOG:
                self.logTextCtrl.AppendText(data)
                if self.logFp is not None:
                    self.logFp.write(data)
            elif type == OUTFILE:
                self.outputFileDataList.append(data)
                self.processData(data)
            elif type == CONTROL:
                try:
                    result = data()
                    self.replyQueue.put((OK,result))
                except Exception,e:
                    self.replyQueue.put((EXCEPTION,e))
        if self.saveFp != None:
            self.saveFp.close()
            self.saveFp = None
        event.Skip()
    
    def onClose(self,event):
        if self.hasCloseOpt:
            dlg = wx.SingleChoiceDialog(self,"It may take longer to finish current state and run final state before closing.",
                                        "Shut down Coordinator?", choices = ["Shut down Coordinator in current state immediately",
                                        "Finish current state and run final state before shutting down"])
            shutdown = (dlg.ShowModal() == wx.ID_OK)
            if shutdown:
                if  dlg.GetSelection() == 1:
                    dlg2 = wx.ProgressDialog("Exit", "CRDS Coordinator is shutting down", maximum = 105)
                    countProgDialog(dlg2, 105)
                    self.terminateStateMachineThread()
                    self.Destroy()
                    dlg2.Destroy()
                else:
                    pass
                event.Skip()
            else:
                pass
            dlg.Destroy()
        else:
            if not self.forcedClose:
                dlg = wx.ProgressDialog("Exit", "CRDS Coordinator is shutting down", maximum = 105)
                countProgDialog(dlg, 105)
                self.terminateStateMachineThread()
                self.Destroy()
                dlg.Destroy()
            else:
                pass
            event.Skip()
        if self.logFp is not None: self.logFp.close(data)

def countProgDialog(dlg, maximum):
    count = 0.0
    while count < 0.8*maximum:
        time.sleep(0.1)
        count += 0.15*maximum
        dlg.Update(count)
                
HELP_STRING = \
"""\
Coordinator [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h                  Print this help.
-c                  Specify a different configuration file.  Default = "./Coordinator.ini"
--no_septum         Disable and remove "Change Septum" button
--no_sample_descr   Disable and remove "Load Sample Descriptions" button
--no_sample_num     Disable and remove "Sample Number" display
--has_close_opt     Provide two options to close Coordinator - immediately close or finish current state and 
                    run final state
--forced_close      Set the default way to close Coordinator as immediately close. It will be overwritten by "--has_close_opt".
--has_pause         Add Pause/Start buttons to clear/set internal runningFlag
"""
def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'c:h'
    longOpts = ["no_septum", "no_sample_descr", "no_sample_num", "has_close_opt", "has_pause", "forced_close", "help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit(0)

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + "Coordinator.ini"

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    useSeptum = "--no_septum" not in options
    hasSampleDescr = "--no_sample_descr" not in options
    hasSampleNum = "--no_sample_num" not in options
    hasPause = "--has_pause" in options
    forcedClose = "--forced_close" in options
    hasCloseOpt = "--has_close_opt" in options
    
    return (hasSampleDescr, hasSampleNum, useSeptum, hasCloseOpt, hasPause, forcedClose, configFile)

class App(wx.App):
    def OnInit(self):
        (hasSampleDescr, hasSampleNum, useSeptum, hasCloseOpt, hasPause, forcedClose, configFile) = handleCommandSwitches()
        self.coordinatorFrame = CoordinatorFrame(hasSampleDescr, hasSampleNum, useSeptum, hasCloseOpt, hasPause, forcedClose, configFile, None, -1, "")
        Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
        self.coordinatorFrame.run()
        self.coordinatorFrame.Show()
        self.SetTopWindow(self.coordinatorFrame)
        return True
        
if __name__ == "__main__":
    app = App(False)
    app.MainLoop()
    Log("Exiting program")
