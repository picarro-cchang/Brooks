import os
import sys
import wx
import wx.lib.agw.aui as aui
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_QUICK_GUI

CRDS_QuickGui = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_QUICK_GUI,
                                            "SetupTool",
                                            IsDontCareConnection = False)
                                            
PAGE1_LEFT_MARGIN = 35
PAGE2_LEFT_MARGIN = 110
PAGE3_LEFT_MARGIN = 110
PAGE4_LEFT_MARGIN = 100

COMMENT_BOX_SIZE = (400, 100)

def printError(errMsg, errTitle):
    d = wx.MessageDialog(None, errMsg+"\nAction cancelled.", errTitle, wx.OK|wx.ICON_ERROR)
    d.ShowModal()
    d.Destroy()
                
class Page1(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.targetIni = None
        self.labelTitle = wx.StaticText(self, -1, "Data Logger Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.buttonGet = wx.Button(self, -1, "Get Complete Data Columns")                  
        self.buttonGet.SetMinSize((200, 20))
        self.buttonGet.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonGet.Enable(False)
        self.comment = wx.TextCtrl(self, -1, "", size = COMMENT_BOX_SIZE, style = wx.TRANSPARENT_WINDOW|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH|wx.ALIGN_LEFT)
        self.comment.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comment.SetForegroundColour("red")
        self.comment.Enable(False)

    def onGetButton(self, event):
        dataKeyDict = CRDS_QuickGui.getDataKeys()
        try:
            if not os.path.isfile(self.dataColsFile):
                fd = open(self.dataColsFile, "wb")
                fd.close()
            cp = CustomConfigObj(self.dataColsFile)
            cp["DataCols"] = {}
            for source in dataKeyDict:
                dataKeys = dataKeyDict[source]
                dataKeys.sort()
                cp["DataCols"][source] = dataKeys
            cp.write()
            d = wx.MessageDialog(None, "Data columns saved for scource(s):\n%s" % "\n".join(dataKeyDict.keys()), "Data Columns Saved", wx.OK|wx.ICON_INFORMATION)
            d.ShowModal()
            d.Destroy()
        except Exception, err:
            print "%r" % err
            return
        
    def onDataDuration(self, event):
        eventObj = event.GetEventObject()
        newVal = float(eventObj.GetValue())
        if newVal < 0.01 or newVal > 24.0:
            eventObj.SetForegroundColour("red")
        else:
            eventObj.SetForegroundColour("black")
            
    def onDirLevel(self, event):
        eventObj = event.GetEventObject()
        newVal = int(eventObj.GetValue())
        if newVal < 0 or newVal > 6:
            eventObj.SetForegroundColour("red")
        else:
            eventObj.SetForegroundColour("black")
            
    def __do_layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        gridSizer1 = wx.FlexGridSizer(-1, 2)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.labelTitle, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        for idx in range(self.numDataLogSections):
            gridSizer1.Add(self.labelData[idx], 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
            gridSizer1.Add(self.dataColumnBox[idx], 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
            gridSizer1.Add((-1,5))
            gridSizer1.Add((-1,5))
            gridSizer1.Add(self.labelAddData[idx], 0, wx.LEFT|wx.RIGHT, 20)
            gridSizer1.Add(self.textCtrlAddData[idx], 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
            gridSizer1.Add((-1,5))
            gridSizer1.Add((-1,5))
            gridSizer1.Add(self.labelDataDuration[idx], 0, wx.LEFT|wx.RIGHT, 20)
            gridSizer1.Add(self.textCtrlDataDuration[idx], 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
            gridSizer1.Add((-1,5))
            gridSizer1.Add((-1,5))
            gridSizer1.Add(self.labelDirLevel[idx], 0, wx.LEFT|wx.RIGHT, 20)
            gridSizer1.Add(self.textCtrlDirLevel[idx], 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
        sizer2.Add(sizer1, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer2.Add(gridSizer1, 0)
        sizer2.Add(self.buttonGet, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer2.Add(self.comment, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)
        sizer3.Add(sizer2, 0, wx.LEFT, PAGE1_LEFT_MARGIN)
        self.SetSizer(sizer3)
        sizer3.Fit(self)

    def __clear_layout(self):
        try:
            for idx in range(self.numDataLogSections):
                self.labelData[idx].Destroy()
                self.dataColumnBox[idx].Destroy()
                self.labelAddData[idx].Destroy()
                self.textCtrlAddData[idx].Destroy()
        except:
            pass
        
    def setIni(self, iniList):
        if self.targetIni == iniList[0]:
            return
        self.__clear_layout()
        self.targetIni = iniList[0]
        self.archiverIni = iniList[1]
        self.dataColsFile = iniList[-1]
        try:
            cp = CustomConfigObj(self.targetIni, list_values = True)
        except Exception, err:
            print "%r" % err
            return
        try:
            dataColsCp = CustomConfigObj(self.dataColsFile, list_values = True)
        except Exception, err:
            print "%r" % err
        self.dataCols = []
        self.labelData = []
        self.dataColumnBox = []
        self.labelAddData = []
        self.textCtrlAddData = []
        self.labelDataDuration = []
        self.textCtrlDataDuration = []
        self.labelDirLevel = []
        self.textCtrlDirLevel = []
        self.dataLogSections = cp.list_sections()
        self.numDataLogSections = len(self.dataLogSections)
        for dataLog in self.dataLogSections:
            dataSource = cp.get(dataLog, "sourcescript")
            try:
                dataList = dataColsCp.get("DataCols", dataSource)
            except Exception, err:
                print "%r" % err
                dataList = cp.get(dataLog, "datalist")
            self.dataCols.append(dataList)
            self.labelData.append(wx.StaticText(self, -1, "Data Columns (%s)" % dataLog, style=wx.ALIGN_LEFT))
            self.labelData[-1].SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.dataColumnBox.append(wx.CheckListBox(self, -1, choices = dataList, size = (250, 100)))
            self.labelAddData.append(wx.StaticText(self, -1, "Add New Data", style=wx.ALIGN_LEFT))
            self.labelAddData[-1].SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.textCtrlAddData.append(wx.TextCtrl(self, -1, size = (230,-1)))
            self.labelDataDuration.append(wx.StaticText(self, -1, "Data File Duration (Hours)", style=wx.ALIGN_LEFT))
            self.labelDataDuration[-1].SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.textCtrlDataDuration.append(wx.TextCtrl(self, -1, size = (230,-1)))
            self.labelDirLevel.append(wx.StaticText(self, -1, "Archived Directory Level", style=wx.ALIGN_LEFT))
            self.labelDirLevel[-1].SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.textCtrlDirLevel.append(wx.TextCtrl(self, -1, size = (230,-1)))
            self.Bind(wx.EVT_TEXT, self.onDataDuration, self.textCtrlDataDuration[-1])
            self.Bind(wx.EVT_TEXT, self.onDirLevel, self.textCtrlDirLevel[-1])
        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.onGetButton, self.buttonGet)
           
    def showCurValues(self):
        try:
            cp = CustomConfigObj(self.targetIni, list_values = True)
        except Exception, err:
            print "%r" % err
            return
        try:
            archiverCp = CustomConfigObj(self.archiverIni)
        except Exception, err:
            print "%r" % err
            return
            
        for idx in range(self.numDataLogSections):
            dataLog = self.dataLogSections[idx]
            curDataList = cp.get(dataLog, "datalist", "")
            dataDuration = cp.get(dataLog, "maxlogduration_hrs")
            numDirLevels = archiverCp.get(dataLog, "Quantum")
            self.dataColumnBox[idx].SetCheckedStrings(curDataList)
            self.textCtrlDataDuration[idx].SetValue(dataDuration)
            self.textCtrlDirLevel[idx].SetValue(numDirLevels)
                
    def apply(self):
        try:
            cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            return False
        try:
            archiverCp = CustomConfigObj(self.archiverIni)
        except Exception, err:
            print "%r" % err
            return False
        try:
            dataColsCp = CustomConfigObj(self.dataColsFile)
        except Exception, err:
            print "%r" % err
        for idx in range(self.numDataLogSections):
            dataLog = self.dataLogSections[idx]
            newData = self.textCtrlAddData[idx].GetValue()
            dataDuration = self.textCtrlDataDuration[idx].GetValue()
            if float(dataDuration) < 0.01 or float(dataDuration) > 24.0:
                printError("Data file duration must be between 0.01 and 24.0 hours", "Invalid Data File Duration")
                self.showCurValues()
                return False
            numDirLevels = self.textCtrlDirLevel[idx].GetValue()
            if int(numDirLevels) < 0 or int(numDirLevels) > 6:
                printError("Archived directory level must be an integer between 0 and 6", "Invalid Archived Directory Level")
                self.showCurValues()
                return False
            checkNewData = False
            if (newData != "") and (newData not in self.dataCols[idx]):
                self.dataColumnBox[idx].Insert(newData, len(self.dataCols[idx]))
                self.dataCols[idx].append(newData)
                self.textCtrlAddData[idx].SetValue("")
                checkNewData = True
            try:
                checkedList = ""
                for i in self.dataColumnBox[idx].GetChecked():
                    checkedList += "%s, " % self.dataCols[idx][i]
                if checkNewData:
                    checkedList += "%s, " % self.dataCols[idx][-1]
                cp.set(dataLog, "datalist", checkedList[:-2])
                cp.set(dataLog, "maxlogduration_hrs", dataDuration)
                cp.write()
            except Exception, err:
                print "%r" % err
            # Update the complete data column list
            dataSource = cp.get(dataLog, "sourcescript")
            try:
                dataList = dataColsCp.get("DataCols", dataSource)
                if checkNewData:
                    dataList += ", %s" % self.dataCols[idx][-1]
                dataColsCp.set("DataCols", dataSource, dataList)
                dataColsCp.write()
            except Exception, err:
                print "%r" % err
            try:
                archiverCp.set(dataLog, "Quantum", numDirLevels)
                archiverCp.write()
            except Exception, err:
                print "%r" % err
  
        self.showCurValues()
        return True
        
    def enable(self, idxList, en):
        controlList = [self.dataColumnBox, self.textCtrlAddData, self.textCtrlDataDuration, self.textCtrlDirLevel]
        for logIdx in range(self.numDataLogSections):
            for idx in idxList:
                controlList[idx][logIdx].Enable(en)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)
        if comment == "":
            self.comment.Hide()
        else:
            self.comment.Show()
            
    # Special functions for Page1
    def setFullInterface(self, full):
        if full:
            try:
                CRDS_QuickGui.getDataKeys()
                self.buttonGet.Enable(True)
            except:
                self.buttonGet.Enable(False)
        else:
            self.buttonGet.Enable(False)
        
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
            cp = CustomConfigObj(self.coordinatorIni[0], list_values = True)
            for i in range(len(self.coordinatorPortList)):
                try:
                    setVal = cp["SerialPorts"][self.coordinatorPortList[i]]
                except:
                    setVal = "OFF"
                self.comboBoxList[3+i].SetStringSelection(setVal)
                self._updatePortDict(self.keyLabelStrings[3+i], setVal)
        except Exception, err:
             print "Coordinator port Exception: ",err
             
    def apply(self):
        for p in self.portAppDict:
            if p != "OFF" and len(self.portAppDict[p]) > 1:
                printError("Conflicting port assignment found.", "Conflicting Ports")
                self.showCurValues()
                return False
                    
        streamPort = self.comboBoxList[0].GetValue()
        try:
            cp = CustomConfigObj(self.dataMgrIni)
            if cp.has_section("SerialOutput") and streamPort != "":
                if streamPort == "OFF":
                    cp["SerialOutput"]["Enable"] = "False"
                else:
                    cp["SerialOutput"]["Enable"] = "True"
                    cp["SerialOutput"]["Port"] = streamPort
                cp.write()
            else:
                pass
        except Exception, err:
            print "Data streaming port Exception: ", err
            
        mpvPort = self.comboBoxList[1].GetValue()
        if mpvPort != "":
            try:
                cp = CustomConfigObj(self.valveIni)
                cp["MAIN"]["comPortRotValve"] = mpvPort
                cp.write()
            except Exception, err:
                print "MPV port Exception: ",err
        
        cmdPort = self.comboBoxList[2].GetValue()
        if cmdPort != "":
            try:
                cp = CustomConfigObj(self.cmdIni)
                if cmdPort.startswith("COM"):
                    cp["HEADER"]["interface"] = "SerialInterface"
                    cp["SERIALINTERFACE"]["port"] = cmdPort
                elif cmdPort == "TCP":
                    cp["HEADER"]["interface"] = "SocketInterface"
                else:
                    cp["HEADER"]["interface"] = "OFF"
                cp.write()
            except Exception, err:
                 print "Command interface port Exception: ",err

        for ini in self.coordinatorIni:
            try:
                cp = CustomConfigObj(ini, list_values = True)
                if "SerialPorts" not in cp:
                    cp["SerialPorts"]  ={}
                for i in range(len(self.coordinatorPortList)):
                    try:
                        port = self.comboBoxList[3+i].GetStringSelection()
                        cp["SerialPorts"][self.coordinatorPortList[i]] = port
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
        if comment == "":
            self.comment.Hide()
        else:
            self.comment.Show()
        
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
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.targetIni = None
        self.keyLabelStrings = ["Use SSL", "Use Authentication", "Server", "User Name", "Password", "From", "To", "Subject"]
        self.choiceLists = [["YES","NO"], ["YES","NO"]]
        self.labelTitle = wx.StaticText(self, -1, "Data Delivery Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
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
           
    def showCurValues(self):
        try:
            cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            return
            
        try:
            setVal = "NO"
            if cp.getboolean("EMAIL", "UseSSL"):
                setVal = "YES"
        except Exception, err:
            print "%r" % err
            setVal = ""
        self.comboBoxList[0].SetValue(setVal)

        try:
            setVal = "NO"
            if cp.getboolean("EMAIL", "UseAuthentication"):
                setVal = "YES"
        except Exception, err:
            print "%r" % err
            setVal = ""
        self.comboBoxList[1].SetValue(setVal)
        self.onAuthComboBox(None)
        
        self.textCtrlList[0].SetValue(cp.get("EMAIL", "Server", ""))
        self.textCtrlList[1].SetValue(cp.get("EMAIL", "UserName", ""))
        self.textCtrlList[2].SetValue(cp.get("EMAIL", "Password", ""))
        self.textCtrlList[3].SetValue(cp.get("EMAIL", "From", ""))
        self.textCtrlList[4].SetValue(cp.get("EMAIL", "To1", ""))
        self.textCtrlList[5].SetValue(cp.get("EMAIL", "Subject", ""))

    def apply(self):
        try:
            cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            return False
            
        try:
            if self.comboBoxList[0].GetValue() == "YES":
                cp["EMAIL"]["UseSSL"] = "True"
            else:
                cp["EMAIL"]["UseSSL"] = "False"
            if self.comboBoxList[1].GetValue() == "YES":
                cp["EMAIL"]["UseAuthentication"] = "True"
            else:
                cp["EMAIL"]["UseAuthentication"] = "False"
            cp["EMAIL"]["Server"] = self.textCtrlList[0].GetValue()
            cp["EMAIL"]["UserName"] = self.textCtrlList[1].GetValue()
            cp["EMAIL"]["Password"] = self.textCtrlList[2].GetValue()
            cp["EMAIL"]["From"] = self.textCtrlList[3].GetValue()
            cp["EMAIL"]["To1"] = self.textCtrlList[4].GetValue()
            cp["EMAIL"]["Subject"] = self.textCtrlList[5].GetValue()
            cp.write()
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
        if comment == "":
            self.comment.Hide()
        else:
            self.comment.Show()
        
class Page4(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.targetIni = None
        self.keyLabelStrings = ["Number of Graphs"]
        self.choiceLists = [["1","2","3","4"]]
        self.labelTitle = wx.StaticText(self, -1, "GUI Properties", style=wx.ALIGN_CENTRE)
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
        
    def showCurValues(self):
        try:
            cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            return
            
        try:
            setVal = cp.get("Graph", "NumGraphs")
        except Exception, err:
            print "%r" % err
            setVal = ""
        self.comboBoxList[0].SetValue(setVal)
        
    def apply(self):
        try:
            cp = CustomConfigObj(self.targetIni)
        except Exception, err:
            print "%r" % err
            return False
            
        try:
            cp.set("Graph", "NumGraphs", self.comboBoxList[0].GetValue())
            cp.write()
            return True
        except Exception, err:
            print "%r" % err
            return False
            
    def enable(self, en):
        for i in range(len(self.keyLabelList)):
            self.comboBoxList[i].Enable(en)
            
    def setComment(self, comment):
        self.comment.SetValue(comment)
        if comment == "":
            self.comment.Hide()
        else:
            self.comment.Show()