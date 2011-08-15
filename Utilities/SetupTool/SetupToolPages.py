import os
import sys
import wx
from datetime import datetime
import wx.lib.agw.aui as aui
from wx.lib.masked.timectrl import TimeCtrl
from Host.Common.CustomConfigObj import CustomConfigObj
                                            
PAGE1_LEFT_MARGIN = 80
PAGE2_LEFT_MARGIN = 140
PAGE3_LEFT_MARGIN = 140
PAGE4_LEFT_MARGIN = 120
PAGE5_LEFT_MARGIN = 140
PAGE6_LEFT_MARGIN = 140
PAGE7_LEFT_MARGIN = 140

COMMENT_BOX_SIZE = (400, 100)

def printError(errMsg1, errTitle, errMsg2="Action cancelled."):
    if errMsg2 != "":
        errMsg = errMsg1+"\n"+errMsg2
    else:
        errMsg = errMsg1
    d = wx.MessageDialog(None, errMsg, errTitle, wx.STAY_ON_TOP|wx.OK|wx.ICON_ERROR)
    d.ShowModal()
    d.Destroy()
                
def strToList(inStr):
    if not inStr:
        return []
    retList = [i.strip() for i in inStr.split(",")]
    return retList
    
#----------------------------------------------------------------------------------------------------------------------------------------#
class Page1(wx.Panel):
    def __init__(self, parent, quickGuiRpc, *args, **kwds):
        self.parent = parent
        self.quickGuiRpc = quickGuiRpc
        wx.Panel.__init__(self, *args, **kwds)
        self.labelTitle = wx.StaticText(self, -1, "Data Logger Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.buttonGet = wx.Button(self, -1, "Get Complete Data Columns")   
        self.buttonGet.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))       
        self.buttonGet.SetMinSize((250, 25))
        self.buttonGet.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonGet.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.onGetButton, self.buttonGet)
        self.targetIni = None
        self.cp = None
        self.archiverCp = None
        self.dataColsCp = None
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.dataLogSections = []
        self.mailboxChoices = ["YES", "NO"]
        self.quantumChoices = ["YEAR", "YEAR/ MONTH", "YEAR/ MONTH/ DAY", "YEAR/ MONTH/ DAY/ HOUR", "YEAR/ MONTH/ DAY/ HOUR/ MINUTE"]
        self.maxSizeChoices = ["1", "5", "10", "15", "20", "25", "30", "35", "40"]
        self.enFlag = True
        self.fullInterface = False
        
    def _sortDataList(self, reservedList, dataList):
        addList = [d for d in dataList if d not in reservedList]
        return reservedList + addList
                
    def onGetButton(self, event):
        try:
            dataKeyDict = self.quickGuiRpc.getDataKeys()
        except:
            printError("Data columns not available.", "Error", "Please make sure analyzer software is running and taking measurements.")
            return
        try:
            self.dataColsCp["DataCols"] = {}
            for source in dataKeyDict:
                dataKeys = dataKeyDict[source]
                dataKeys.sort()
                if source in self.resdataDict:
                    self.dataColsCp["DataCols"][source] = self._sortDataList(self.resdataDict[source], dataKeys)
                else:
                    self.dataColsCp["DataCols"][source] = dataKeys
            self.dataColsCp.write()
            # Reset the data col config obj
            self.dataColsCp = CustomConfigObj(self.dataColsFile)
        except Exception, err:
            print "%r" % err
            return
            
        self.updateLayout()
        self.showCurValues()
        # Update the Command Interface and Data Streaming pages as well
        self.parent.pages[4].updateDataSourceCols()
        self.parent.pages[4].updateLayout()
        self.parent.pages[4].showCurValues()
        self.parent.pages[5].updateDataSourceCols()
        self.parent.pages[5].updateLayout()
        self.parent.pages[5].showCurValues()
        
        d = wx.MessageDialog(None, "Data columns saved for scource(s):\n%s" % "\n".join(dataKeyDict.keys()), "Data Columns Saved", wx.OK|wx.ICON_INFORMATION)
        d.ShowModal()
        d.Destroy()
                
    def onCheckListBox(self, event):
        return
        # eventObj = event.GetEventObject()
        # if self.fullInterface:
            # return
        # else:
            # index = event.GetSelection()
            # item = eventObj.GetString(index)
            # dataLogIdx = self.checkListBoxIdList.index(eventObj.GetId())
            # print self.resdataList[dataLogIdx], item
            # if item not in self.resdataList[dataLogIdx]:
                # return
            # else:
                # checkedList = list(eventObj.GetChecked())
                # checkedList.append(index)
                # eventObj.SetChecked(checkedList)
            
    def onDataDuration(self, event):
        eventObj = event.GetEventObject()
        newVal = float(eventObj.GetValue())
        if newVal < 0.01 or newVal > 24.0:
            eventObj.SetForegroundColour("red")
        else:
            eventObj.SetForegroundColour("black")
            
    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(0, 2)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for dataLog in self.dataLogSections:
            gridSizer1.Add((-1,20))
            gridSizer1.Add((-1,20))
            for idx in range(len(self.labelDict[dataLog])):
                gridSizer1.Add(self.labelDict[dataLog][idx], 0, wx.LEFT|wx.RIGHT, 20)
                gridSizer1.Add(self.controlDict[dataLog][idx], 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
                gridSizer1.Add((-1,4))
                gridSizer1.Add((-1,4))
        gridSizer1.Add((-1,-1))
        gridSizer1.Add(self.buttonGet, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer2.Add(gridSizer1, 0)
        sizer2.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer3.Add(sizer2, 0, wx.LEFT, PAGE1_LEFT_MARGIN)
        self.SetSizer(sizer3)
        sizer3.Fit(self)
        self.Layout()

    def __clear_layout(self):
        try:
            for dataLog in self.labelDict:
                for idx in range(len(self.labelDict[dataLog])):
                    self.labelDict[dataLog][idx].Destroy()
                    self.controlDict[dataLog][idx].Destroy()
        except:
            pass
        
    def __createGUIElements(self):
        self.dataCols = []
        self.labelDict = {} # For each dataLog, the labels are [Data Columns, Hours of Each Log File, Archived Directory Structure, Log Storage Size]
        self.controlDict = {}
        self.dataLogSections = self.cp.list_sections()
        self.dataSources = []
        self.numDataLogSections = len(self.dataLogSections)
        if self.numDataLogSections == 1:
            dataColumnBoxHeight = 340
        else:
            dataColumnBoxHeight = 230.0/self.numDataLogSections
        #self.resdataList = []
        self.resdataDict = {}
        #self.checkListBoxIdList = []
        for dataLog in self.dataLogSections:
            dataSource = self.cp.get(dataLog, "sourcescript")
            self.dataSources.append(dataSource)
            stddataList = strToList(self.cp.get(dataLog, "datalist"))
            resdata = strToList(self.cp.get(dataLog, "reservedlist", ""))
            #self.resdataList.append(resdata)
            self.resdataDict[dataSource] = resdata
            try:
                fulldataList = self._sortDataList(resdata, strToList(self.dataColsCp.get("DataCols", dataSource)))
            except Exception, err:
                print "%r" % err
                fulldataList = self._sortDataList(resdata, stddataList)
            self.dataCols.append(fulldataList)
            
            self.labelDict[dataLog] = []
            self.controlDict[dataLog] = []
            
            if self.fullInterface:
                datalistChoices = fulldataList
            else:
                datalistChoices = self._sortDataList(resdata, stddataList)
            label = wx.StaticText(self, -1, "Data Columns (%s)" % dataLog, style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            newId = wx.NewId()
            #self.checkListBoxIdList.append(newId)
            dataCheckListBox = wx.CheckListBox(self, newId, choices = datalistChoices, size = (250, dataColumnBoxHeight))
            self.controlDict[dataLog].append(dataCheckListBox)
            self.Bind(wx.EVT_CHECKLISTBOX, self.onCheckListBox, dataCheckListBox)
            
            label = wx.StaticText(self, -1, "Hours of Each Log File (0.01~24)", style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.TextCtrl(self, -1, size = (230, -1)))
            self.Bind(wx.EVT_TEXT, self.onDataDuration, self.controlDict[dataLog][-1])
            
            label = wx.StaticText(self, -1, "Enable Mailbox Archiving", style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.ComboBox(self, -1, choices = self.mailboxChoices, size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN))
            
            label = wx.StaticText(self, -1, "Archived Directory Structure", style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.ComboBox(self, -1, choices = self.quantumChoices, size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN))

            label = wx.StaticText(self, -1, "Total User Log Storage Size (GB)", style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.ComboBox(self, -1, choices = self.maxSizeChoices, size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN))
            
    def setIni(self, iniList):
        if self.targetIni == iniList[0]:
            return
        self.targetIni = iniList[0]
        self.archiverIni = iniList[1]
        self.dataColsFile = iniList[2]
        try:
            self.cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            return
        try:
            self.archiverCp = CustomConfigObj(self.archiverIni)
        except Exception, err:
            print "%r" % err
            return
        try:
            dataColsDir = os.path.dirname(self.dataColsFile)
            if not os.path.isdir(dataColsDir):
                os.makedirs(dataColsDir)
            self.dataColsCp = CustomConfigObj(self.dataColsFile, create_empty = True, file_error = False)
        except Exception, err:
            print "%r" % err
            
        self.updateLayout()

    def updateLayout(self):
        self.__clear_layout()
        self.__createGUIElements()
        self.__do_layout()
        
    def showCurValues(self):
        if self.cp == None or self.archiverCp == None:
            return False
        
        for idx in range(self.numDataLogSections):
            dataLog = self.dataLogSections[idx]
            curDataList = strToList(self.cp.get(dataLog, "datalist", ""))
            updateDataLog = False
            for data in curDataList:
                if data not in self.dataCols[idx]:
                    # self.dataCols contains the full list
                    curDataList.remove(data)
                    updateDataLog = True
            if updateDataLog:
                checkedList = ""
                for data in curDataList:
                    checkedList += "%s," % data
                self.cp.set(dataLog, "datalist", checkedList[:-1])
                self.cp.write()
            self.controlDict[dataLog][0].SetCheckedStrings(curDataList)
            
            dataDuration = self.cp.get(dataLog, "maxlogduration_hrs")
            self.controlDict[dataLog][1].SetValue(dataDuration)
            
            try:
                setVal = "NO"
                if self.cp.getboolean(dataLog, "mailboxenable"):
                    setVal = "YES"
            except Exception, err:
                print "%r" % err
                setVal = ""
            self.controlDict[dataLog][2].SetValue(setVal)
        
            quantumIdx = int(self.archiverCp.get(dataLog, "Quantum"))-1
            self.controlDict[dataLog][3].SetValue(self.quantumChoices[quantumIdx])
            
            maxSize = str(int(float(self.archiverCp.get(dataLog, "MaxSize_MB"))/1000.0))
            self.controlDict[dataLog][4].SetValue(maxSize)
        return True
                
    def apply(self):
        if self.cp == None or self.archiverCp == None:
            return False
            
        for idx in range(self.numDataLogSections):
            dataLog = self.dataLogSections[idx]
            dataDuration = self.controlDict[dataLog][1].GetValue()
            mailboxenable = self.controlDict[dataLog][2].GetValue()
            if float(dataDuration) < 0.01 or float(dataDuration) > 24.0:
                printError("Log file duration must be between 0.01 and 24.0 hours", "Invalid Log File Duration")
                return False
                
            # Update Data Logger
            try:
                writeCp = False
                checkedList = ",".join(self.controlDict[dataLog][0].GetCheckedStrings())
                if self.cp.get(dataLog, "dataList") != checkedList:
                    self.cp.set(dataLog, "datalist", checkedList)
                    writeCp = True
                if self.cp.get(dataLog, "maxlogduration_hrs") != dataDuration:
                    self.cp.set(dataLog, "maxlogduration_hrs", dataDuration)
                    writeCp = True
                if mailboxenable == "YES" and not self.cp.getboolean(dataLog, "mailboxenable"):
                    self.cp.set(dataLog, "mailboxenable", "True")
                    writeCp = True
                elif mailboxenable == "NO" and self.cp.getboolean(dataLog, "mailboxenable"):
                    self.cp.set(dataLog, "mailboxenable", "False")
                    writeCp = True
                if writeCp:
                    self.cp.write()
            except Exception, err:
                print "%r" % err

            # Update Archiver
            try:
                writeArchCp = False
                quantumIdx = self.quantumChoices.index(self.controlDict[dataLog][3].GetValue())
                if self.archiverCp.get(dataLog, "Quantum") != str(quantumIdx+1):
                    self.archiverCp.set(dataLog, "Quantum", quantumIdx+1)
                    writeArchCp = True
                maxSize = int(self.controlDict[dataLog][4].GetValue())*1000
                if self.archiverCp.get(dataLog, "MaxSize_MB") != str(maxSize):
                    self.archiverCp.set(dataLog, "MaxSize_MB", maxSize)
                    writeArchCp = True
                if writeArchCp:
                    self.archiverCp.write()
            except Exception, err:
                print "%r" % err
                
        return True
        
    def enable(self, idxList, en):
        self.enFlag = en
        for dataLog in self.dataLogSections:
            for idx in idxList:
                self.controlDict[dataLog][idx].Enable(en)
        if 0 in idxList:
            # Use 0 to identify that this is for Data Logger section
            self.buttonGet.Enable(en and self.fullInterface)
        
    def setComment(self, comment):
        self.comment.SetValue(comment)

    def setFullInterface(self, full):
        self.fullInterface = full
        self.updateLayout()
        self.buttonGet.Enable(self.enFlag and self.fullInterface)
        self.showCurValues()

    def getDataSourceCols(self):
        return self.dataSources, self.dataLogSections, self.dataCols
            
#----------------------------------------------------------------------------------------------------------------------------------------#
class Page2(wx.Panel):
    def __init__(self, comPortList, coordinatorPortList, hasReadGPSWS, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.coordinatorPortList = coordinatorPortList
        self.keyLabelStrings = ["Data Streaming", "Valve Sequencer MPV", "Command Interface"]
        self.choiceLists = [comPortList, comPortList, comPortList[:-1]+["TCP"]+[comPortList[-1]]]
        for i in range(len(coordinatorPortList)):
            self.keyLabelStrings.append("Coordinator (%s)" % coordinatorPortList[i])
            self.choiceLists.append(comPortList)
        if hasReadGPSWS:
            self.keyLabelStrings += ["GPS", "Anemometer"]
            self.choiceLists += [comPortList, comPortList]
        self.labelTitle = wx.StaticText(self, -1, "Serial/Socket Port Manager", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.keyLabelList = []
        self.comboBoxIdList = []
        self.comboBoxList = []
        
        for i in range(len(self.keyLabelStrings)):
            label = wx.StaticText(self, -1, self.keyLabelStrings[i], style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.keyLabelList.append(label)
            newId = wx.NewId()
            self.comboBoxIdList.append(newId)
            self.comboBoxList.append(wx.ComboBox(self, newId, choices = self.choiceLists[i], size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN))

        self.portAppDict = {}
        
        self.__do_layout()
        self.bindEvents()

    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(0, 2)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for i in range(len(self.keyLabelList)):
            gridSizer1.Add(self.keyLabelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.comboBoxList[i], 0, wx.EXPAND)
        sizer1.Add(gridSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer1.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.LEFT, PAGE2_LEFT_MARGIN)
        self.SetSizer(sizer2)
        sizer2.Fit(self)
        
    def bindEvents(self):
        for combo in self.comboBoxList:
            combo.Bind(wx.EVT_COMBOBOX, self.onComboBox)
        
    def setIni(self, iniList):
        try:
            (self.dataMgrIni, self.valveIni, self.cmdIni, self.coordinatorIni, self.readGPSWSIni) = iniList
        except:
            (self.dataMgrIni, self.valveIni, self.cmdIni, self.coordinatorIni) = iniList
            self.readGPSWSIni = None
        if type(self.coordinatorIni) != type([]):
            self.coordinatorIni = [self.coordinatorIni]
        
    def showCurValues(self):
        try:
            cp = CustomConfigObj(self.dataMgrIni)
            if not cp.has_section("SerialOutput"):
                setVal = "OFF"
                self.comboBoxList[0].Enable(False)
            else:
                if cp.getboolean("SerialOutput", "Enable"):
                    setVal = cp.get("SerialOutput", "Port")
                else:
                    setVal = "OFF"
        except Exception, err:
            print "Data streaming port Exception: %r" % err
            setVal = ""
        self.comboBoxList[0].SetStringSelection(setVal)
        self._updatePortDict(self.keyLabelStrings[0], setVal)
            
        try:
            cp = CustomConfigObj(self.valveIni)
            setVal = cp.get("MAIN", "comPortRotValve")
            try:
                setVal = "COM%d" % (int(val)+1)
            except:
                pass
        except Exception, err:
            print "MPV port Exception: %r" % err
            setVal = ""
        self.comboBoxList[1].SetStringSelection(setVal)
        self._updatePortDict(self.keyLabelStrings[1], setVal)
        
        try:
            cp = CustomConfigObj(self.cmdIni)
            if cp.get("HEADER", "interface") == "SerialInterface":
                setVal = cp.get("SERIALINTERFACE", "port")
                try:
                    setVal = eval(setVal) # In case setVal = "'COM1'" etc
                except:
                    pass
            elif cp.get("HEADER", "interface") == "SocketInterface":
                setVal = "TCP"
            else:
                setVal = "OFF"
        except Exception, err:
             print "Command interface port Exception: %r" % err
             setVal = ""
        self.comboBoxList[2].SetStringSelection(setVal)
        self._updatePortDict(self.keyLabelStrings[2], setVal)

        try:
            portDict = {}
            for coorIni in self.coordinatorIni:
                cp = CustomConfigObj(coorIni, list_values = True)
                for coorPortName in self.coordinatorPortList:
                    try:
                        setVal = cp.get("SerialPorts", coorPortName)
                        if coorPortName not in portDict:
                            portDict[coorPortName] = setVal
                        elif portDict[coorPortName] != setVal:
                            portDict[coorPortName] = ""
                    except:
                        pass
            for i in range(len(self.coordinatorPortList)):
                coorPortName = self.coordinatorPortList[i]
                self.comboBoxList[3+i].SetStringSelection(portDict[coorPortName])
                self._updatePortDict(self.keyLabelStrings[3+i], portDict[coorPortName])
        except Exception, err:
             print "Coordinator port Exception: %r" % err
             
        if self.readGPSWSIni:
            try:
                cp = CustomConfigObj(self.readGPSWSIni)
                if cp.getboolean("Enable", "enableGPS"):
                    gpsPort = cp.get("Serial", "portGPS")
                else:
                    gpsPort = "OFF"
                if cp.getboolean("Enable", "enableWS"):
                    wsPort = cp.get("Serial", "portWS")
                else:
                    wsPort = "OFF"
            except Exception, err:
                 print "GPSWS port Exception: %r" % err
                 gpsPort = ""
                 wsPort = ""
            self.comboBoxList[-2].SetStringSelection(gpsPort)
            self._updatePortDict(self.keyLabelStrings[-2], gpsPort)
            self.comboBoxList[-1].SetStringSelection(wsPort)
            self._updatePortDict(self.keyLabelStrings[-1], wsPort)
        
        return True
             
    def apply(self):
        conflict = False
        for p in self.portAppDict:
            if p != "OFF" and len(self.portAppDict[p]) > 1:
                conflict = True
                break
        if conflict:
            d = wx.MessageDialog(None, "Conflicting port assignment found.\nDo you still want to apply the changes?", "Conflicting Ports", 
                                wx.STAY_ON_TOP|wx.YES|wx.NO|wx.ICON_WARNING)
            yesClicked = d.ShowModal() == wx.ID_YES
            d.Destroy()
            if not yesClicked:
                return False
                    
        streamPort = self.comboBoxList[0].GetValue()
        try:
            cp = CustomConfigObj(self.dataMgrIni)
            if cp.has_section("SerialOutput") and streamPort != "":
                if streamPort == "OFF":
                    cp.set("SerialOutput", "Enable", "False")
                else:
                    cp.set("SerialOutput", "Enable", "True")
                    cp.set("SerialOutput", "Port", streamPort)
                cp.write()
            else:
                pass
        except Exception, err:
            print "Data streaming port Exception: %r" % err
            
        mpvPort = self.comboBoxList[1].GetValue()
        if mpvPort != "":
            try:
                cp = CustomConfigObj(self.valveIni)
                cp.set("MAIN", "comPortRotValve", mpvPort)
                cp.write()
            except Exception, err:
                print "MPV port Exception: %r" % err
        
        cmdPort = self.comboBoxList[2].GetValue()
        if cmdPort != "":
            try:
                cp = CustomConfigObj(self.cmdIni)
                if cmdPort.startswith("COM"):
                    cp.set("HEADER", "interface", "SerialInterface")
                    cp.set("SERIALINTERFACE", "port", cmdPort)
                elif cmdPort == "TCP":
                    cp.set("HEADER", "interface", "SocketInterface")
                else:
                    cp.set("HEADER", "interface", "OFF")
                cp.write()
            except Exception, err:
                 print "Command interface port Exception: %r" % err

        for ini in self.coordinatorIni:
            try:
                cp = CustomConfigObj(ini, list_values = True)
                if "SerialPorts" not in cp:
                    continue
                for i in range(len(self.coordinatorPortList)):
                    coorPortName = self.coordinatorPortList[i]
                    try:
                        port = self.comboBoxList[3+i].GetStringSelection()
                        if coorPortName in cp["SerialPorts"]:
                            cp["SerialPorts"][coorPortName] = port
                    except:
                        pass
                cp.write()
            except Exception, err:
                 print "Coordinator port Exception: %r" % err

        if self.readGPSWSIni:
            gpsPort = self.comboBoxList[-2].GetValue()
            if gpsPort != "":
                try:
                    cp = CustomConfigObj(self.readGPSWSIni)
                    if gpsPort != "OFF":
                        cp.set("Enable", "enableGPS", "True")
                        cp.set("Serial", "portGPS", gpsPort)
                    else:
                        cp.set("Enable", "enableGPS", "False")
                    cp.write()
                except Exception, err:
                     print "GPS port Exception: %r" % err
            wsPort = self.comboBoxList[-1].GetValue()
            if wsPort != "":
                try:
                    cp = CustomConfigObj(self.readGPSWSIni)
                    if wsPort != "OFF":
                        cp.set("Enable", "enableWS", "True")
                        cp.set("Serial", "portWS", wsPort)
                    else:
                        cp.set("Enable", "enableWS", "False")
                    cp.write()
                except Exception, err:
                     print "WS port Exception: %r" % err
            
        return True
        
    def enable(self, idxList, en):
        for idx in idxList:
            self.comboBoxList[idx].Enable(en)

    def setComment(self, comment):
        self.comment.SetValue(comment)

    def setFullInterface(self, full):
        pass
        
    def onComboBox(self, event):
        eventObj = event.GetEventObject()
        curId = eventObj.GetId()
        curIdx = self.comboBoxIdList.index(curId)
        curApp = self.keyLabelStrings[curIdx]
        curPort = eventObj.GetValue()
        self._updatePortDict(curApp, curPort)

    def _getIdxFromAppLabel(self, label):
        return self.keyLabelStrings.index(label)
        
    def _updateFontColor(self, idx, color):
        self.keyLabelList[idx].SetLabel(self.keyLabelList[idx].GetLabel())
        self.keyLabelList[idx].SetForegroundColour(color)
        
    def _updatePortDict(self, app, port):
        if port == "":
            return
            
        if port not in self.portAppDict:
            self.portAppDict[port] = [app]
        elif app not in self.portAppDict[port]:
            self.portAppDict[port].append(app)

        for otherPort in [p for p in self.portAppDict.keys() if p != port]:
            if app in self.portAppDict[otherPort]:
                self.portAppDict[otherPort].remove(app)

        for p in self.portAppDict:
            if p != "OFF" and len(self.portAppDict[p]) > 1:
                for i in [self._getIdxFromAppLabel(app) for app in self.portAppDict[p]]:
                    self._updateFontColor(i,"red")
            else:
                for i in [self._getIdxFromAppLabel(app) for app in self.portAppDict[p]]:
                    self._updateFontColor(i,"black")
   
#----------------------------------------------------------------------------------------------------------------------------------------#   
class Page3(wx.Panel):
    def __init__(self, driverRpc, *args, **kwds):
        self.driverRpc = driverRpc
        wx.Panel.__init__(self, *args, **kwds)
        self.keyLabelStrings = ["Use SSL", "Use Authentication", "Server", "User Name", "Password", "From", "To", "Subject", 
                                "Data Directory"]
        self.choiceLists = [["YES","NO"], ["YES","NO"]]
        self.labelTitle = wx.StaticText(self, -1, "Data Delivery Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        
        self.buttonGet = wx.Button(self, -1, "Get Default Configurations")   
        self.buttonGet.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))       
        self.buttonGet.SetMinSize((240, 25))
        self.buttonGet.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonGet.Enable(False)
        self.buttonDir = wx.Button(self, -1, "Data Directory")   
        self.buttonDir.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))       
        self.buttonDir.SetMinSize((240, 25))
        self.buttonDir.SetBackgroundColour(wx.Colour(237, 228, 199))
        if self.checkRemoteAccessScheduled():
            self.buttonSch = wx.Button(self, -1, "Stop Delivery Scheduler") 
        else:
            self.buttonSch = wx.Button(self, -1, "Start Delivery Scheduler")   
        self.buttonSch.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))       
        self.buttonSch.SetMinSize((240, 25))
        self.buttonSch.SetBackgroundColour(wx.Colour(237, 228, 199))
        
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.comboBoxLabelList = []
        self.comboBoxIdList = []
        self.comboBoxList = []
        self.textCtrlLabelList = []
        self.textCtrlIdList = []
        self.textCtrlList = []
        self.targetIni = None
        self.cp = None
        self.enFlag = True
        self.fullInterface = False
        
        for i in range(len(self.keyLabelStrings)):
            label = wx.StaticText(self, -1, self.keyLabelStrings[i], style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            newId = wx.NewId()
            if i < len(self.choiceLists):
                self.comboBoxLabelList.append(label)
                self.comboBoxIdList.append(newId)
                self.comboBoxList.append(wx.ComboBox(self, newId, choices = self.choiceLists[i], value = self.choiceLists[i][-1], size = (240,-1), style = wx.CB_READONLY|wx.CB_DROPDOWN))
            else:
                self.textCtrlLabelList.append(label)
                self.textCtrlIdList.append(newId)
                self.textCtrlList.append(wx.TextCtrl(self, newId, size = (240,-1)))
        
        self.startTimeLabel = wx.StaticText(self, -1, "Delivery Start Time", style=wx.ALIGN_LEFT)
        self.startTimeLabel.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.spinButtonStartTime = wx.SpinButton(self, -1, size=(17,22), style=wx.SP_VERTICAL)
        self.ctrlStartTime = TimeCtrl(self, -1, fmt24hr=True, value="00:00:05", spinButton=self.spinButtonStartTime)

        f1=os.popen("echo %userdomain%","r")
        f2=os.popen("echo %username%","r")
        d=f1.read().strip()
        u=f2.read().strip()
        # Required for Windows scheduler
        self.user = "%s\%s" % (d,u)
        self.password = "picarro"
        
        self.textCtrlList[6].Enable(False)
        self.bindEvents()
        self.__do_layout()

    def onGetButton(self, event):
        if self.cp == None:
            printError("INI file not found", "Missing INI file")
            return
            
        # Plug analyzer name in "from address" and "subject" of emails
        try:
            analyzerName = self.driverRpc.fetchInstrInfo("analyzername")
        except:
            printError("Analyzer name not available.", "Error", "Please make sure analyzer software is running.")
            return
            
        subject = self.cp.get("EMAIL", "Subject", "")
        if subject == "":
            if analyzerName != None:
                subject = "%s: data from Picarro instrument" % analyzerName
                self.cp.set("EMAIL", "Subject", subject)
                self.cp.write()
            else:
                pass
                
        fromAddr = self.cp.get("EMAIL", "From", "")
        if fromAddr == "":
            if analyzerName != None:
                fromAddr = "%s@picarro.com" % analyzerName
                self.cp.set("EMAIL", "From", fromAddr)
                self.cp.write()
            else:
                pass
        self.showCurValues()
        
    def onDirButton(self, event):
        d = wx.DirDialog(None,"Select the source directory where the log files will be delivered from", style=wx.DD_DEFAULT_STYLE,
                         defaultPath=self.dataDir)
        if d.ShowModal() == wx.ID_OK:
            self.dataDir = d.GetPath().replace("\\", "/")
            self.cp.set("EMAIL", "Directory", self.dataDir)
            self.cp.write()
            d = wx.MessageDialog(None, "New Data Directory applied.   ", "Changes Applied", wx.STAY_ON_TOP|wx.OK|wx.ICON_INFORMATION)
            d.ShowModal()
            d.Destroy()
        self.showCurValues()
                    
    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizerTime = wx.BoxSizer(wx.HORIZONTAL)
        gridSizer1 = wx.FlexGridSizer(0, 2)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        gridSizer1.Add(self.startTimeLabel, 0, wx.RIGHT|wx.BOTTOM, 15)
        sizerTime.Add(self.ctrlStartTime, 10)
        sizerTime.Add(self.spinButtonStartTime, 0)
        gridSizer1.Add(sizerTime, 0, wx.EXPAND)
        for i in range(len(self.comboBoxLabelList)):
            gridSizer1.Add(self.comboBoxLabelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.comboBoxList[i], 0, wx.EXPAND)
        for i in range(len(self.textCtrlLabelList)):
            gridSizer1.Add(self.textCtrlLabelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.textCtrlList[i], 0)
        gridSizer1.Add((-1,-1))
        gridSizer1.Add(self.buttonDir, 0)
        gridSizer1.Add((-1,-1))
        gridSizer1.Add(self.buttonSch, 0, wx.TOP, 10)
        gridSizer1.Add((-1,-1))
        gridSizer1.Add(self.buttonGet, 0, wx.TOP, 10)
        sizer1.Add(gridSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer1.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.LEFT, PAGE3_LEFT_MARGIN)
        self.SetSizer(sizer2)
        sizer2.Fit(self)
        
    def bindEvents(self):
        self.Bind(wx.EVT_BUTTON, self.onDirButton, self.buttonDir)
        self.Bind(wx.EVT_BUTTON, self.onGetButton, self.buttonGet)
        self.Bind(wx.EVT_BUTTON, self.onSchButton, self.buttonSch)
        self.Bind(wx.EVT_COMBOBOX, self.onAuthComboBox, self.comboBoxList[1])
        
    def onSchButton(self, event):
        print self.checkRemoteAccessScheduled()
        if self.checkRemoteAccessScheduled():
            os.system(r'schtasks.exe /delete /tn RemoteAccess /f')
            os.system(r'schtasks.exe /delete /tn RemoteAccessLogOn /f')
            self.buttonSch.SetLabel("Start Delivery Scheduler")
        else:
            startTime = self.ctrlStartTime.GetValue()
            os.system(r'schtasks.exe /delete /tn RemoteAccess /f')
            os.system(r'schtasks.exe /create /tn RemoteAccess /tr "C:\Picarro\G2000\HostExe\RemoteAccess.exe %s" /sc DAILY /st %s /ru %s /rp %s' % (self.targetIni, startTime, self.user, self.password))
            os.system(r'schtasks.exe /delete /tn RemoteAccessLogOn /f')
            os.system(r'schtasks.exe /create /tn RemoteAccessLogOn /tr "C:\Picarro\G2000\HostExe\RemoteAccess.exe %s" /sc ONLOGON /ru %s /rp %s' % (self.targetIni, self.user, self.password))
            self.buttonSch.SetLabel("Stop Delivery Scheduler")
            
    def checkRemoteAccessScheduled(self):
        schQuery = os.popen("schtasks.exe /query /fo CSV","r")
        r = schQuery.read()
        r = r.replace("\n","").replace("\"",",").split(",")
        if ("RemoteAccess" in r) or ("RemoteAccessLogOn" in r):
            return True
        else:
            return False
            
    def onAuthComboBox(self, event):
        if event:
            eventObj = event.GetEventObject()
        else:
            eventObj = self.comboBoxList[1]
        if eventObj.GetValue() == "YES":
            self.textCtrlList[1].Enable(True)
            self.textCtrlList[2].Enable(True)
        else :
            self.textCtrlList[1].Enable(False)
            self.textCtrlList[2].Enable(False)

    def setIni(self, iniList):
        if self.targetIni == iniList[0]:
            return
        self.targetIni = iniList[0]
        try:
            self.cp = CustomConfigObj(self.targetIni, list_values = True)
        except Exception, err:
            print "%r" % err
            
    def showCurValues(self):
        if self.cp == None:
            return False
            
        try:
            setVal = "NO"
            if self.cp.getboolean("EMAIL", "UseSSL"):
                setVal = "YES"
        except Exception, err:
            print "%r" % err
            setVal = ""
        self.comboBoxList[0].SetValue(setVal)

        try:
            setVal = "NO"
            if self.cp.getboolean("EMAIL", "UseAuthentication"):
                setVal = "YES"
        except Exception, err:
            print "%r" % err
            setVal = ""
        self.comboBoxList[1].SetValue(setVal)
        self.onAuthComboBox(None)
        
        self.textCtrlList[0].SetValue(self.cp.get("EMAIL", "Server", ""))
        self.textCtrlList[1].SetValue(self.cp.get("EMAIL", "UserName", ""))
        self.textCtrlList[2].SetValue(self.cp.get("EMAIL", "Password", ""))
        self.textCtrlList[3].SetValue(self.cp.get("EMAIL", "From", ""))
        self.textCtrlList[4].SetValue(self.cp.get("EMAIL", "To1", ""))
        self.textCtrlList[5].SetValue(self.cp.get("EMAIL", "Subject", ""))
        self.dataDir = self.cp.get("EMAIL", "Directory", "")
        self.textCtrlList[6].SetValue(self.dataDir)
        
        return True

    def apply(self):
        if self.cp == None:
            return False
            
        try:
            if self.comboBoxList[0].GetValue() == "YES":
                self.cp.set("EMAIL", "UseSSL", "True")
            else:
                self.cp.set("EMAIL", "UseSSL", "False")
            if self.comboBoxList[1].GetValue() == "YES":
                self.cp.set("EMAIL", "UseAuthentication", "True")
            else:
                self.cp.set("EMAIL", "UseAuthentication", "False")
            self.cp.set("EMAIL", "Server", self.textCtrlList[0].GetValue())
            self.cp.set("EMAIL", "UserName", self.textCtrlList[1].GetValue())
            self.cp.set("EMAIL", "Password", self.textCtrlList[2].GetValue())
            self.cp.set("EMAIL", "From", self.textCtrlList[3].GetValue())
            self.cp.set("EMAIL", "To1", self.textCtrlList[4].GetValue())
            self.cp.set("EMAIL", "Subject", self.textCtrlList[5].GetValue())
            self.cp.set("EMAIL", "Directory", self.dataDir)
            self.cp.write()
            return True
        except Exception, err:
            print "%r" % err
            return False

    def enable(self, en):
        self.enFlag = en
        for i in range(len(self.comboBoxLabelList)):
            self.comboBoxList[i].Enable(en)
        for i in range(len(self.textCtrlLabelList)):
            if i not in [6]:
                self.textCtrlList[i].Enable(en)
        self.buttonDir.Enable(en)
        self.buttonGet.Enable(self.enFlag and self.fullInterface)

    def setComment(self, comment):
        self.comment.SetValue(comment)

    def setFullInterface(self, full):
        self.fullInterface = full
        self.buttonGet.Enable(self.enFlag and self.fullInterface)
   
#----------------------------------------------------------------------------------------------------------------------------------------#   
class Page4(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.keyLabelStrings = ["Number of Graphs", "Enable Control of Valve Sequencer"]
        self.choiceLists = [["1","2","3","4"], ["Yes", "No"]]
        self.labelTitle = wx.StaticText(self, -1, "GUI Properties", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.keyLabelList = []
        self.comboBoxIdList = []
        self.comboBoxList = []
        self.targetIni = None
        self.cp = None
        self.enFlag = True
        self.fullInterface = False
                
        for i in range(len(self.keyLabelStrings)):
            label = wx.StaticText(self, -1, self.keyLabelStrings[i], style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.keyLabelList.append(label)
            newId = wx.NewId()
            self.comboBoxIdList.append(newId)
            self.comboBoxList.append(wx.ComboBox(self, newId, choices = self.choiceLists[i], size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN))

        self.comboBoxList[1].Enable(False)
            
        self.__do_layout()

    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(0, 2)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for i in range(len(self.keyLabelList)):
            gridSizer1.Add(self.keyLabelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.comboBoxList[i], 0, wx.EXPAND)
        sizer1.Add(gridSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer1.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.LEFT, PAGE4_LEFT_MARGIN)
        self.SetSizer(sizer2)
        sizer2.Fit(self)

    def setIni(self, iniList):
        if self.targetIni == iniList[0]:
            return
        self.targetIni = iniList[0]
        try:
            self.cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            
    def showCurValues(self):
        if self.cp == None:
            return False
        
        try:
            setVal = self.cp.get("Graph", "NumGraphs")
        except Exception, err:
            print "%r" % err
            setVal = ""
        self.comboBoxList[0].SetValue(setVal)
        
        try:
            setVal = self.cp.getboolean("ValveSequencer", "Enable")
            if not setVal:
                self.comboBoxList[1].SetValue("No")
            else:
                self.comboBoxList[1].SetValue("Yes")
        except Exception, err:
            print "%r" % err
            self.comboBoxList[1].SetValue("Yes")
        
        return True
        
    def apply(self):
        if self.cp == None:
            return False
            
        try:
            self.cp.set("Graph", "NumGraphs", self.comboBoxList[0].GetValue())
            val = self.comboBoxList[1].GetValue()
            try:
                self.cp.set("ValveSequencer", "Enable", str(val == "Yes"))
            except:
                pass
            self.cp.write()
            return True
        except Exception, err:
            print "%r" % err
            return False
            
    def enable(self, en):
        self.enFlag = en
        self.comboBoxList[0].Enable(en)
        self.comboBoxList[1].Enable(self.enFlag and self.fullInterface)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)
        
    def setFullInterface(self, full):
        self.fullInterface = full
        self.comboBoxList[1].Enable(self.enFlag and self.fullInterface)
       
#----------------------------------------------------------------------------------------------------------------------------------------#       
class Page5(wx.Panel):
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.parent = parent
        self.labelTitle = wx.StaticText(self, -1, "Command Interface", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.targetIni = None
        self.cp = None
        self.idx = 0

    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(0, 2)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for i in range(len(self.labelList)):
            gridSizer1.Add(self.labelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.controlList[i], 0, wx.EXPAND)
        sizer1.Add(gridSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer1.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.LEFT, PAGE5_LEFT_MARGIN)
        self.SetSizer(sizer2)
        sizer2.Fit(self)
        self.Layout()
        
    def __clear_layout(self):
        try:
            for comboBox in self.controlList:
                comboBox.Destroy()
        except:
            pass
        
    def __createGUIElements(self):
        self.labelList = []
        self.controlList = []
        label = wx.StaticText(self, -1, "Output Data Source", style=wx.ALIGN_LEFT)
        label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelList.append(label)
        combo = wx.ComboBox(self, -1, choices = self.dataSec, value = self.dataSec[self.idx], size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        combo.Bind(wx.EVT_COMBOBOX, self.onSelectDataSource)
        self.controlList.append(combo)

        label = wx.StaticText(self, -1, "Output Data Columns", style=wx.ALIGN_LEFT)
        label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelList.append(label)
        self.controlList.append(wx.CheckListBox(self, -1, choices = self.dataCols[self.idx], size = (250, 400)))
    
    def onSelectDataSource(self, event):
        eventObj = event.GetEventObject()
        newDataSource = self.secSourceDict[eventObj.GetValue()]
        newDataCols = self.sourceColDict[newDataSource]
        self.idx = self.dataSources.index(newDataSource)
        self.updateLayout()
        self.showCurValues()
       
    def updateDataSourceCols(self):
        (self.dataSources, self.dataSec, self.dataCols) = self.parent.pages[0].getDataSourceCols()
        self.secSourceDict = dict(zip(self.dataSec, self.dataSources))
        self.sourceColDict = dict(zip(self.dataSources, self.dataCols))
        
    def updateLayout(self):
        self.__clear_layout()
        self.__createGUIElements()
        self.__do_layout()
        
    def setIni(self, iniList):
        if self.targetIni == iniList[0]:
            return
        self.targetIni = iniList[0]
        try:
            self.cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
           
        self.updateDataSourceCols()
        try:
            curDataSource = self.cp.get("HEADER", "meas_source")
            self.idx = self.dataSources.index(curDataSource)
        except:
            self.idx = 0
        self.updateLayout()
        
    def showCurValues(self):
        if self.cp == None:
            return False

        curDataSource = self.cp.get("HEADER", "meas_source", "")
        curDataList = strToList(self.cp.get("HEADER", "meas_label", ""))
        if self.idx == self.dataSources.index(curDataSource):
            updateDataLog = False
            for data in curDataList:
                if data not in self.sourceColDict[curDataSource]:
                    curDataList.remove(data)
                    updateDataLog = True
            if updateDataLog:
                checkedList = ""
                for data in curDataList:
                    checkedList += "%s," % data
                self.cp.set("HEADER", "meas_label", checkedList[:-1])
                self.cp.write()
          
            self.controlList[1].SetCheckedStrings(curDataList)
        else:
            pass
        return True
        
    def apply(self):
        if self.cp == None:
            return False
            
        dataSource = self.dataSources[self.idx]
        dataCols = self.sourceColDict[dataSource]
        try:
            checkedList = ""
            for i in self.controlList[1].GetChecked():
                checkedList += "%s," % dataCols[i]
            writeCp = False
            if self.cp.get("HEADER", "meas_label", "") != checkedList[:-1]:
                self.cp.set("HEADER", "meas_label", checkedList[:-1])
                writeCp = True
            if self.cp.get("HEADER", "meas_source", "") != dataSource:
                self.cp.set("HEADER", "meas_source", dataSource)
                writeCp = True
            if writeCp:
                self.cp.write()
        except Exception, err:
            print "%r" % err
        return True
        
    def enable(self, en):
        for comboBox in self.controlList:
            comboBox.Enable(en)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)
        
    def setFullInterface(self, full):
        pass
     
#----------------------------------------------------------------------------------------------------------------------------------------#     
class Page6(wx.Panel):
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.parent = parent
        self.labelTitle = wx.StaticText(self, -1, "Data Streaming", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.targetIni = None
        self.cp = None
        self.idx = 0

    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(0, 2)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for i in range(len(self.labelList)):
            gridSizer1.Add(self.labelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.controlList[i], 0, wx.EXPAND)
        sizer1.Add(gridSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer1.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.LEFT, PAGE6_LEFT_MARGIN)
        self.SetSizer(sizer2)
        sizer2.Fit(self)
        self.Layout()
        
    def __clear_layout(self):
        try:
            for comboBox in self.controlList:
                comboBox.Destroy()
        except:
            pass
        
    def __createGUIElements(self):
        self.labelList = []
        self.controlList = []
        label = wx.StaticText(self, -1, "Data Stream Source", style=wx.ALIGN_LEFT)
        label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelList.append(label)
        combo = wx.ComboBox(self, -1, choices = self.dataSec, value = self.dataSec[self.idx], size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        combo.Bind(wx.EVT_COMBOBOX, self.onSelectDataSource)
        self.controlList.append(combo)

        label = wx.StaticText(self, -1, "Data Stream Columns", style=wx.ALIGN_LEFT)
        label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelList.append(label)
        self.controlList.append(wx.CheckListBox(self, -1, choices = self.dataCols[self.idx], size = (250, 400)))
    
    def onSelectDataSource(self, event):
        eventObj = event.GetEventObject()
        newDataSource = self.secSourceDict[eventObj.GetValue()]
        newDataCols = self.sourceColDict[newDataSource]
        self.idx = self.dataSources.index(newDataSource)
        self.updateLayout()
        self.showCurValues()
       
    def updateDataSourceCols(self):
        (self.dataSources, self.dataSec, self.dataCols) = self.parent.pages[0].getDataSourceCols()
        for idx in range(len(self.dataCols)):
            for data in self.dataCols[idx]:
                if data.lower() in ["time", "ymd", "hms"]:
                    self.dataCols[idx].remove(data)
        self.secSourceDict = dict(zip(self.dataSec, self.dataSources))
        self.sourceColDict = dict(zip(self.dataSources, self.dataCols))
        
    def updateLayout(self):
        self.__clear_layout()
        self.__createGUIElements()
        self.__do_layout()
        
    def setIni(self, iniList):
        if self.targetIni == iniList[0]:
            return
        self.targetIni = iniList[0]
        try:
            self.cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            
        self.updateDataSourceCols()
        try:
            curDataSource = self.cp.get("SerialOutput", "Source")
            self.idx = self.dataSources.index(curDataSource)
        except:
            self.idx = 0
        self.updateLayout()
        
    def __writeColumns(self, colList, dataSource=None):
        colList += ["ymd", "hms"]
        # Clean current columns before updating
        for col in [i for i in self.cp.list_options("SerialOutput") if i.lower().startswith("column")]:
            colName = self.cp.get("SerialOutput", col)
            if colName.lower() not in ["time"]:
                self.cp.remove_option("SerialOutput", col)
                
        for idx in range(len(colList)):
            self.cp.set("SerialOutput", "Column%d" % (idx+1), colList[idx])
        dataFormat=r'"%15.2f' + ' %10.4f'*len(colList) + r'\r\n"'
        self.cp.set("SerialOutput", "Format", dataFormat)
        if dataSource != None:
            self.cp.set("SerialOutput", "Source", dataSource)
        self.cp.write()
        
    def showCurValues(self):
        if self.cp == None:
            return False

        if "SerialOutput" not in self.cp.list_sections():
            self.enable(False)
            return True
            
        curDataSource = self.cp.get("SerialOutput", "Source", "")
        curDataList = []
        for curData in [self.cp.get("SerialOutput", i) for i in self.cp.list_options("SerialOutput") if i.lower().startswith("column")]:
            if curData.lower() not in ["time", "ymd", "hms"]:
                curDataList.append(curData)
        if self.idx == self.dataSources.index(curDataSource):
            updateDataLog = False
            for data in curDataList:
                if data not in self.sourceColDict[curDataSource]:
                    curDataList.remove(data)
                    updateDataLog = True
            if updateDataLog:
                self.__writeColumns(curDataList)
            self.controlList[1].SetCheckedStrings(curDataList)
        else:
            pass
        return True
        
    def apply(self):
        if self.cp == None:
            return False
            
        dataSource = self.dataSources[self.idx]
        dataCols = self.sourceColDict[dataSource]
        try:
            checkedList = []
            for i in self.controlList[1].GetChecked():
                checkedList.append(dataCols[i])
            self.__writeColumns(checkedList, dataSource)
        except Exception, err:
            print "%r" % err
        return True
        
    def enable(self, en):
        for comboBox in self.controlList:
            comboBox.Enable(en)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)
        
    def setFullInterface(self, full):
        pass
        
#----------------------------------------------------------------------------------------------------------------------------------------#   
class Page7(wx.Panel):
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.parent = parent
        self.keyLabelStrings = ["Analog Output Channel", "Data Source", "Data Columns", "Mode", "Slope", "Offset", "Manual Voltage (0~10V)", "Min Voltage (0~10V)", 
                                "Max Voltage (0~10V)", "Invalid Value Voltage (0~10V)"]
        self.labelTitle = wx.StaticText(self, -1, "Electrical Interface", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.targetIni = None
        self.cp = None
        self.channel = "0"
        self.channelDataDict = {}
        self.channelConfigDict = {}
        self.ctrlConfigDict = {3: "BOOTMODE", 4: "SLOPE",  5: "OFFSET", 6: "BOOTVALUE", 7: "MIN", 8: "MAX", 9: "INVALIDVALUE"}
        self.configCtrlDict = {"BOOTMODE": 3, "SLOPE": 4,  "OFFSET": 5, "BOOTVALUE": 6, "MIN": 7, "MAX": 8, "INVALIDVALUE": 9}

    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(0, 2)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for i in range(len(self.labelList)):
            gridSizer1.Add(self.labelList[i], 0, wx.RIGHT|wx.BOTTOM, 10)
            gridSizer1.Add(self.controlList[i], 0, wx.RIGHT|wx.BOTTOM, 10)
        sizer1.Add(gridSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer1.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.LEFT, PAGE7_LEFT_MARGIN)
        self.SetSizer(sizer2)
        sizer2.Fit(self)
        self.Layout()
        
    def __clear_layout(self):
        try:
            for comboBox in self.controlList:
                comboBox.Destroy()
        except:
            pass
        
    def __createGUIElements(self, newDataSource):
        self.labelList = []
        self.controlList = []
        self.controlId = []
        
        if newDataSource:
            srcIdx = self.dataSources.index(newDataSource)
        else:
            srcIdx = 0
            
        for s in self.keyLabelStrings:
            label = wx.StaticText(self, -1, s, style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelList.append(label)
        
        newId = wx.NewId()
        self.controlId.append(newId)
        combo = wx.ComboBox(self, newId, choices = [str(i) for i in range(4)], value = self.channel, size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        combo.Bind(wx.EVT_COMBOBOX, self.onSelectChannel)
        self.controlList.append(combo)
        
        newId = wx.NewId()
        self.controlId.append(newId)
        combo = wx.ComboBox(self, newId, choices = self.dataSec, value = self.dataSec[srcIdx], size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        combo.Bind(wx.EVT_COMBOBOX, self.onSelectDataSource)
        self.controlList.append(combo)

        newId = wx.NewId()
        self.controlId.append(newId)
        checklist = wx.CheckListBox(self, newId, choices = self.dataCols[srcIdx], size = (230, 200))
        checklist.Bind(wx.EVT_CHECKLISTBOX, self.onSelectDataCol)
        self.controlList.append(checklist)

        newId = wx.NewId()
        self.controlId.append(newId)
        combo = wx.ComboBox(self, newId, choices = ["Manual", "Tracking"], value = "Tracking", size = (230, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        combo.Bind(wx.EVT_COMBOBOX, self.onBootMode)
        self.controlList.append(combo)

        for i in range(6):
            newId = wx.NewId()
            self.controlId.append(newId)
            self.controlList.append(wx.TextCtrl(self, newId, size = (230, -1)))
            self.controlList[i+4].Bind(wx.EVT_TEXT, self.onEntry)
        
    def onEntry(self, event):
        eventObj = event.GetEventObject()
        eventId = eventObj.GetId()
        controlListIdx = self.controlId.index(eventId)
        if controlListIdx >= 6:
            # Force the voltages to be within 0~10 V
            try:
                if float(eventObj.GetValue()) > 10.0:
                    eventObj.SetValue("10.0")
                if float(eventObj.GetValue()) < 0.0:
                    eventObj.SetValue("0.0")
            except:
                pass
        self.channelConfigDict["ANALOG_OUTPUT_CHANNEL"+self.channel][self.ctrlConfigDict[controlListIdx]] = eventObj.GetValue()
        
    def onBootMode(self, event):
        self.channelConfigDict["ANALOG_OUTPUT_CHANNEL"+self.channel]["BOOTMODE"] = str(int(event.GetEventObject() == "Tracking"))
        
    def onSelectChannel(self, event):
        eventObj = event.GetEventObject()
        self.channel = eventObj.GetValue()
        self.updateLayout()
        self.showCurValues()
        
    def onSelectDataSource(self, event):
        eventObj = event.GetEventObject()
        self.updateLayout(self.secSourceDict[eventObj.GetValue()])
        self.showCurValues()

    def onSelectDataCol(self, event):
        eventObj = event.GetEventObject()
        curDataCols = [self.channelDataDict["ANALOG_OUTPUT_CHANNEL"+self.channel][1]]
        newData = [i for i in eventObj.GetCheckedStrings() if i not in curDataCols]
        if not newData:
            return
        else: 
            eventObj.SetCheckedStrings(newData)
            self.channelDataDict["ANALOG_OUTPUT_CHANNEL"+self.channel][0] =  self.secSourceDict[self.controlList[1].GetValue()]
            self.channelDataDict["ANALOG_OUTPUT_CHANNEL"+self.channel][1] = newData[0]
            
    def updateDataSourceCols(self):
        (self.dataSources, self.dataSec, self.dataCols) = self.parent.pages[0].getDataSourceCols()
        for idx in range(len(self.dataCols)):
            for data in self.dataCols[idx]:
                if data.lower() in ["time", "ymd", "hms"]:
                    self.dataCols[idx].remove(data)
        self.secSourceDict = dict(zip(self.dataSec, self.dataSources))
        self.sourceColDict = dict(zip(self.dataSources, self.dataCols))
        
    def updateLayout(self, newDataSource=None):
        self.__clear_layout()
        self.__createGUIElements(newDataSource)
        self.__do_layout()
        
    def setIni(self, iniList):
        if self.targetIni == iniList[0]:
            return
        self.targetIni = iniList[0]
        try:
            self.cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            
        self.updateDataSourceCols()
        self.updateLayout()
        
        # Set up the channel dictionaries
        for channel in ["ANALOG_OUTPUT_CHANNEL%d" % i for i in range(4)]:
            self.channelDataDict[channel] = self.cp.get(channel, "SOURCE").split(",")
            self.channelConfigDict[channel] = self.cp[channel]
            self.channelConfigDict[channel].pop("SOURCE")
        
    def showCurValues(self):
        if self.cp == None:
            return False

        if "ANALOG_OUTPUT_CHANNEL"+self.channel not in self.cp.list_sections():
            self.enable(False)
            return False
            
        [curDataSource, curData] = self.channelDataDict["ANALOG_OUTPUT_CHANNEL"+self.channel]
        if self.secSourceDict[self.controlList[1].GetValue()] == curDataSource:
            self.controlList[2].SetCheckedStrings([curData])
            
        curConfig = self.channelConfigDict["ANALOG_OUTPUT_CHANNEL"+self.channel]
        for key in curConfig:
            try:
                if key == "BOOTMODE":
                    if curConfig[key].strip() == "0":
                        self.controlList[self.configCtrlDict[key]].SetValue("Manual")
                    else:
                        self.controlList[self.configCtrlDict[key]].SetValue("Tracking")
                self.controlList[self.configCtrlDict[key]].SetValue(curConfig[key])
            except:
                pass
                
        return True

    def apply(self):
        if self.cp == None:
            return False
        try:
            for i in range(4):
                channel = "ANALOG_OUTPUT_CHANNEL%s" % i
                self.cp[channel].update(self.channelConfigDict[channel])
                self.cp[channel]["SOURCE"] =  ",".join(self.channelDataDict[channel])
            self.cp.write()
        except Exception, err:
            print "%r" % err
        return True
        
    def enable(self, en):
        for comboBox in self.controlList:
            comboBox.Enable(en)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)
        
    def setFullInterface(self, full):
        pass
       