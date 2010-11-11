import os
import sys
import wx
import wx.lib.agw.aui as aui
from Host.Common.CustomConfigObj import CustomConfigObj
                                            
PAGE1_LEFT_MARGIN = 35
PAGE2_LEFT_MARGIN = 110
PAGE3_LEFT_MARGIN = 110
PAGE4_LEFT_MARGIN = 80

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
    retList = inStr.split(",")
    for i in range(len(retList)):
        retList[i] = retList[i].strip()
    return retList
    
class Page1(wx.Panel):
    def __init__(self, quickGuiRpc, *args, **kwds):
        self.quickGuiRpc = quickGuiRpc
        wx.Panel.__init__(self, *args, **kwds)
        self.labelTitle = wx.StaticText(self, -1, "Data Logger Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.buttonGet = wx.Button(self, -1, "Get Complete Data Columns")   
        self.buttonGet.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))       
        self.buttonGet.SetMinSize((250, 25))
        self.buttonGet.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonGet.Enable(False)
        self.buttonAdd = wx.Button(self, -1, "Add New Data from External Device") 
        self.buttonAdd.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))           
        self.buttonAdd.SetMinSize((250, 25))
        self.buttonAdd.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonAdd.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.onGetButton, self.buttonGet)
        self.Bind(wx.EVT_BUTTON, self.onAddButton, self.buttonAdd)
        self.targetIni = None
        self.cp = None
        self.archiverCp = None
        self.dataColsCp = None
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)
        self.dataLogSections = []
        self.quantumChoices = ["YEAR", "YEAR/ MONTH", "YEAR/ MONTH/ DAY", "YEAR/ MONTH/ DAY/ HOUR", "YEAR/ MONTH/ DAY/ HOUR/ MINUTE"]
        self.maxSizeChoices = ["1", "5", "10", "15", "20", "25", "30", "35", "40"]
        
    def onGetButton(self, event):
        dataKeyDict = self.quickGuiRpc.getDataKeys()
        try:
            if not os.path.isfile(self.dataColsFile):
                fd = open(self.dataColsFile, "wb")
                fd.close()
            if not self.dataColsCp:
                self.dataColsCp = CustomConfigObj(self.dataColsFile)
            self.dataColsCp["DataCols"] = {}
            for source in dataKeyDict:
                dataKeys = dataKeyDict[source]
                dataKeys.sort()
                self.dataColsCp["DataCols"][source] = dataKeys
            self.dataColsCp.write()
            
            try:
                for idx in range(self.numDataLogSections):
                    dataLog = self.dataLogSections[idx]
                    source = self.cp.get(dataLog, "sourcescript")
                    dataKeys = dataKeyDict[source]
                    dataKeys.sort()
                    self.dataCols[idx] = dataKeys
            except:
                pass
            d = wx.MessageDialog(None, "Data columns saved for scource(s):\n%s" % "\n".join(dataKeyDict.keys()), "Data Columns Saved", wx.OK|wx.ICON_INFORMATION)
            d.ShowModal()
            d.Destroy()
        except Exception, err:
            print "%r" % err
            return
           
    def onAddButton(self, event):
        if self.cp == None:
            printError("INI file not found", "Missing INI file")
            return
        d = wx.TextEntryDialog(self, 'New Data Column Name: ','Add New Data from External Device', '', wx.OK | wx.CANCEL)
        okClicked = d.ShowModal() == wx.ID_OK
        d.Destroy()
        if not okClicked:
            return
        else:
            newData = d.GetValue()

        for idx in range(self.numDataLogSections):
            dataLog = self.dataLogSections[idx]
            if (newData != "") and (newData not in self.dataCols[idx]):
                self.controlDict[dataLog][0].Insert(newData, len(self.dataCols[idx]))
                self.dataCols[idx].append(newData)
                # Update the complete data column list
                try:
                    dataSource = self.cp.get(dataLog, "sourcescript")
                    dataList = self.dataColsCp.get("DataCols", dataSource)
                    if newData not in dataList:
                        dataList += ", %s" % newData
                        self.dataColsCp.set("DataCols", dataSource, dataList)
                        self.dataColsCp.write()
                except Exception, err:
                    print "%r" % err
                
    def onDataDuration(self, event):
        eventObj = event.GetEventObject()
        newVal = float(eventObj.GetValue())
        if newVal < 0.01 or newVal > 24.0:
            eventObj.SetForegroundColour("red")
        else:
            eventObj.SetForegroundColour("black")
            
    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(-1, 2)
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
        gridSizer1.Add(self.buttonGet, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        gridSizer1.Add(self.buttonAdd, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer2.Add(gridSizer1, 0)
        sizer2.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer3.Add(sizer2, 0, wx.LEFT, PAGE1_LEFT_MARGIN)
        self.SetSizer(sizer3)
        sizer3.Fit(self)

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
        self.numDataLogSections = len(self.dataLogSections)
        if self.numDataLogSections == 1:
            dataColumnBoxHeight = 300
        else:
            dataColumnBoxHeight = 200.0/self.numDataLogSections
        for dataLog in self.dataLogSections:
            dataSource = self.cp.get(dataLog, "sourcescript")
            try:
                dataList = strToList(self.dataColsCp.get("DataCols", dataSource))
            except Exception, err:
                print "%r" % err
                dataList = strToList(self.cp.get(dataLog, "datalist"))
            self.dataCols.append(dataList)
            
            self.labelDict[dataLog] = []
            self.controlDict[dataLog] = []
            
            label = wx.StaticText(self, -1, "Data Columns (%s)" % dataLog, style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.CheckListBox(self, -1, choices = dataList, size = (250, dataColumnBoxHeight)))
            
            label = wx.StaticText(self, -1, "Hours of Each Log File (0.01~24)", style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.TextCtrl(self, -1, size = (230,-1)))
            self.Bind(wx.EVT_TEXT, self.onDataDuration, self.controlDict[dataLog][-1])
            
            label = wx.StaticText(self, -1, "Archived Directory Structure", style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.ComboBox(self, -1, choices = self.quantumChoices, size = (230,-1), style = wx.CB_READONLY|wx.CB_DROPDOWN))

            label = wx.StaticText(self, -1, "Total User Log Storage Size (GB)", style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.labelDict[dataLog].append(label)
            self.controlDict[dataLog].append(wx.ComboBox(self, -1, choices = self.maxSizeChoices, size = (230,-1), style = wx.CB_READONLY|wx.CB_DROPDOWN))
            
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
            self.dataColsCp = CustomConfigObj(self.dataColsFile)
        except Exception, err:
            print "%r" % err
            
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
                    curDataList.remove(data)
                    updateDataLog = True
            if updateDataLog:
                checkedList = ""
                for data in curDataList:
                    checkedList += "%s, " % data
                self.cp.set(dataLog, "datalist", checkedList[:-2])
                self.cp.write()
            self.controlDict[dataLog][0].SetCheckedStrings(curDataList)
            dataDuration = self.cp.get(dataLog, "maxlogduration_hrs")
            self.controlDict[dataLog][1].SetValue(dataDuration)
            quantumIdx = int(self.archiverCp.get(dataLog, "Quantum"))-1
            self.controlDict[dataLog][2].SetValue(self.quantumChoices[quantumIdx])
            maxSize = str(int(float(self.archiverCp.get(dataLog, "MaxSize_MB"))/1000.0))
            self.controlDict[dataLog][3].SetValue(maxSize)
        return True
                
    def apply(self):
        if self.cp == None or self.archiverCp == None:
            return False
            
        for idx in range(self.numDataLogSections):
            dataLog = self.dataLogSections[idx]
            dataDuration = self.controlDict[dataLog][1].GetValue()
            if float(dataDuration) < 0.01 or float(dataDuration) > 24.0:
                printError("Data file duration must be between 0.01 and 24.0 hours", "Invalid Data File Duration")
                return False
                
            # Update Data Logger
            try:
                checkedList = ""
                for i in self.controlDict[dataLog][0].GetChecked():
                    checkedList += "%s, " % self.dataCols[idx][i]
                writeCp = False
                if self.cp.get(dataLog, "dataList") != checkedList[:-2]:
                    self.cp.set(dataLog, "datalist", checkedList[:-2])
                    writeCp = True
                if self.cp.get(dataLog, "maxlogduration_hrs") != dataDuration:
                    self.cp.set(dataLog, "maxlogduration_hrs", dataDuration)
                    writeCp = True
                if writeCp:
                    self.cp.write()
            except Exception, err:
                print "%r" % err

            # Update Archiver
            try:
                writeArchCp = False
                quantumIdx = self.quantumChoices.index(self.controlDict[dataLog][2].GetValue())
                if self.archiverCp.get(dataLog, "Quantum") != str(quantumIdx+1):
                    self.archiverCp.set(dataLog, "Quantum", quantumIdx+1)
                    writeArchCp = True
                maxSize = int(self.controlDict[dataLog][3].GetValue())*1000
                if self.archiverCp.get(dataLog, "MaxSize_MB") != str(maxSize):
                    self.archiverCp.set(dataLog, "MaxSize_MB", maxSize)
                    writeArchCp = True
                if writeArchCp:
                    self.archiverCp.write()
            except Exception, err:
                print "%r" % err
                
        return True
        
    def enable(self, idxList, en):
        for dataLog in self.dataLogSections:
            for idx in idxList:
                self.controlDict[dataLog][idx].Enable(en)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)

    def setFullInterface(self, full):
        if full:
            try:
                self.quickGuiRpc.getDataKeys()
                self.buttonGet.Enable(True)
            except:
                self.buttonGet.Enable(False)
            self.buttonAdd.Enable(True)
        else:
            self.buttonGet.Enable(False)
            self.buttonAdd.Enable(False)
            
class Page2(wx.Panel):
    def __init__(self, comPortList, coordinatorPortList, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.coordinatorPortList = coordinatorPortList
        self.keyLabelStrings = ["Data Streaming", "Valve Sequencer MPV", "Command Interface"]
        self.choiceLists = [comPortList, comPortList, comPortList[:-1]+["TCP"]+[comPortList[-1]]]
        for i in range(len(coordinatorPortList)):
            self.keyLabelStrings.append("Coordinator (%s)" % coordinatorPortList[i])
            self.choiceLists.append(comPortList)
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
            self.comboBoxList.append(wx.ComboBox(self, newId, choices = self.choiceLists[i], size = (230,-1), style = wx.CB_READONLY|wx.CB_DROPDOWN))

        self.portAppDict = {}
        
        self.__do_layout()
        self.bindEvents()

    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(-1, 2)
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
        (self.dataMgrIni, self.valveIni, self.cmdIni, self.coordinatorIni) = iniList
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
            print "Data streaming port Exception: ", err
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
            print "MPV port Exception: ",err
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
             print "Command interface port Exception: ",err
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
             print "Coordinator port Exception: ",err
             
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
            print "Data streaming port Exception: ", err
            
        mpvPort = self.comboBoxList[1].GetValue()
        if mpvPort != "":
            try:
                cp = CustomConfigObj(self.valveIni)
                cp.set("MAIN", "comPortRotValve", mpvPort)
                cp.write()
            except Exception, err:
                print "MPV port Exception: ",err
        
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
                 print "Command interface port Exception: ",err

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
                 print "Coordinator port Exception: ",err
                 
        return True
        
    def enable(self, idxList, en):
        for idx in idxList:
            self.comboBoxList[idx].Enable(en)

    def setComment(self, comment):
        self.comment.SetValue(comment)
        
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
        
class Page3(wx.Panel):
    def __init__(self, driverRpc, *args, **kwds):
        self.driverRpc = driverRpc
        wx.Panel.__init__(self, *args, **kwds)
        self.keyLabelStrings = ["Use SSL", "Use Authentication", "Server", "User Name", "Password", "From", "To", "Subject"]
        self.choiceLists = [["YES","NO"], ["YES","NO"]]
        self.labelTitle = wx.StaticText(self, -1, "Data Delivery Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.buttonGet = wx.Button(self, -1, "Get Default Configurations")   
        self.buttonGet.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))       
        self.buttonGet.SetMinSize((230, 25))
        self.buttonGet.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonGet.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.onGetButton, self.buttonGet)
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
        
        for i in range(len(self.keyLabelStrings)):
            label = wx.StaticText(self, -1, self.keyLabelStrings[i], style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            newId = wx.NewId()
            if i < len(self.choiceLists):
                self.comboBoxLabelList.append(label)
                self.comboBoxIdList.append(newId)
                self.comboBoxList.append(wx.ComboBox(self, newId, choices = self.choiceLists[i], value = self.choiceLists[i][0], size = (230,-1), style = wx.CB_READONLY|wx.CB_DROPDOWN))
            else:
                self.textCtrlLabelList.append(label)
                self.textCtrlIdList.append(newId)
                self.textCtrlList.append(wx.TextCtrl(self, newId, size = (230,-1)))
        
        self.en = True
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
            analyzerName = None
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
        
    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(-1, 2)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for i in range(len(self.comboBoxLabelList)):
            gridSizer1.Add(self.comboBoxLabelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.comboBoxList[i], 0, wx.EXPAND)
        for i in range(len(self.textCtrlLabelList)):
            gridSizer1.Add(self.textCtrlLabelList[i], 0, wx.RIGHT|wx.BOTTOM, 15)
            gridSizer1.Add(self.textCtrlList[i], 0)
        gridSizer1.Add((-1,-1))
        gridSizer1.Add(self.buttonGet, 0, wx.TOP, 15)
        sizer1.Add(gridSizer1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer1.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(sizer1, 0, wx.LEFT, PAGE3_LEFT_MARGIN)
        self.SetSizer(sizer2)
        sizer2.Fit(self)
        
    def bindEvents(self):
        self.comboBoxList[1].Bind(wx.EVT_COMBOBOX, self.onAuthComboBox)
        
    def onAuthComboBox(self, event):
        if not self.en:
            return
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
            self.cp.write()
            return True
        except Exception, err:
            print "%r" % err
            return False

    def enable(self, en):
        self.en = en
        for i in range(len(self.comboBoxLabelList)):
            self.comboBoxList[i].Enable(en)
        for i in range(len(self.textCtrlLabelList)):
            self.textCtrlList[i].Enable(en)

    def setComment(self, comment):
        self.comment.SetValue(comment)

    def setFullInterface(self, full):
        if full:
            try:
                self.driverRpc.fetchInstrInfo("analyzername")
                self.buttonGet.Enable(True)
            except:
                self.buttonGet.Enable(False)
        else:
            self.buttonGet.Enable(False)
            
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
                
        for i in range(len(self.keyLabelStrings)):
            label = wx.StaticText(self, -1, self.keyLabelStrings[i], style=wx.ALIGN_LEFT)
            label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.keyLabelList.append(label)
            newId = wx.NewId()
            self.comboBoxIdList.append(newId)
            self.comboBoxList.append(wx.ComboBox(self, newId, choices = self.choiceLists[i], size = (230,-1), style = wx.CB_READONLY|wx.CB_DROPDOWN))

        self.__do_layout()

    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(-1, 2)
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
            if val == "Yes":
                self.cp.set("ValveSequencer", "Enable", "True")
            else:
                self.cp.set("ValveSequencer", "Enable", "False")
            self.cp.write()
            return True
        except Exception, err:
            print "%r" % err
            return False
            
    def enable(self, en):
        for i in range(len(self.keyLabelList)):
            self.comboBoxList[i].Enable(en)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)