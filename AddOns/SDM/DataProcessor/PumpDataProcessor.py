"""
File name: PumpDataProcessor.py
Purpose: Post-process output data from syringe pump system

File History:
    2010-03-12 alex  Remove the "remove spikes" function
                     Make default starting time as 5 minutes regardless of the flow rate
    2014-03-31 tw    Extracted from WinXP release
"""

import os
import sys
import wx
from numpy import *
import time
from PumpDataProcessorFrame import PumpDataProcessorFrame
from matplotlib import pyplot
import getopt
import threading
import copy

ROLL_WIN_SIZE = 30.0
TIME_FORMAT1 = '%Y/%m/%d %H:%M:%S'
TIME_FORMAT2 = '%m/%d/%Y %H:%M:%S'
CONC_LABELS = ['H2O', 'D_1816', 'D_DH']

SRC_TO_IDX = {'pump1-conc1': (0, 0),
 'pump1-conc2': (1, 0),
 'pump1-conc3': (2, 0),
 'pump2-conc1': (0, 1),
 'pump2-conc2': (1, 1),
 'pump2-conc3': (2, 1)}

IDX_TO_SRC = ['pump1-conc1',
 'pump1-conc2',
 'pump1-conc3',
 'pump2-conc1',
 'pump2-conc2',
 'pump2-conc3']

DEFAULT_LIQUID_START_TIME_MINUTES = 6


def filterData(dataList, liquid):
    if not liquid:
        for i in range(len(dataList)):
            dataList[i] = [dataList[i][0],
             float(dataList[i][3]),
             float(dataList[i][4]),
             float(dataList[i][5]),
             float(dataList[i][6])]

    outputData = []
    dataWin = []
    for data in dataList:
        dataWin.append(data)
        if data[0] - dataWin[0][0] > ROLL_WIN_SIZE:
            outputData.append(mean(dataWin[:-1], 0))
            while data[0] - dataWin[0][0] > ROLL_WIN_SIZE:
                dataWin = dataWin[1:]

    return outputData


def nonoverlapWinAverage(filtDataList, winSize):
    outputData = []
    dataWin = [filtDataList[0]]
    for data in filtDataList[1:]:
        if data[0] - dataWin[0][0] > winSize:
            outputData.append(mean(dataWin, 0))
            dataWin = [data]
        else:
            dataWin.append(data)

    return outputData


def getRange(dataList):
    rangeList = []
    dataArray = array(dataList)
    dataArray = dataArray.transpose()
    for i in [2, 3, 4]:
        try:
            rangeList.append(max(dataArray[i]) - min(dataArray[i]))
        except:
            rangeList.append(0.0)

    return rangeList


def getSlope(dataList):
    slopeList = []
    dataArray = array(dataList)
    dataArray = dataArray.transpose()
    for i in [2, 3, 4]:
        try:
            slopeList.append(polyfit(dataArray[0], dataArray[i], 1)[0])
        except:
            slopeList.append(0.0)

    return slopeList


class DataPlotter(object):

    def __init__(self):
        self.plotElemDict = {}

    def run(self, dataList, source, maxNumOverlaps):
        if source not in self.plotElemDict:
            self.plotElemDict[source] = dict(H2O=[], D_1816=[], D_DH=[])
        for i in range(len(dataList)):
            dataList[i] = [dataList[i][0],
             float(dataList[i][3]),
             float(dataList[i][4]),
             float(dataList[i][5]),
             float(dataList[i][6])]

        dataArray = array(dataList)
        dataArray = dataArray.transpose()
        for concIdx in range(3):
            if len(self.plotElemDict[source][CONC_LABELS[concIdx]]) == 0:
                self.plotElemDict[source][CONC_LABELS[concIdx]].append([])
            elif len(self.plotElemDict[source][CONC_LABELS[concIdx]][-1]) == maxNumOverlaps:
                self.plotElemDict[source][CONC_LABELS[concIdx]].append([])
            startTime = dataArray[0][0]
            self.plotElemDict[source][CONC_LABELS[concIdx]][-1].append(((dataArray[0] - startTime) / 60.0, dataArray[concIdx + 2]))

    def plot(self, srcToCalStdDict):
        figIdx = 0
        for sourceIdx in range(len(IDX_TO_SRC)):
            source = IDX_TO_SRC[sourceIdx]
            startFigIdx = figIdx
            for concIdx in range(3):
                conc = CONC_LABELS[concIdx]
                subplotNum = concIdx + 1
                figIdx = startFigIdx
                try:
                    for plotSeq in self.plotElemDict[source][conc]:
                        fig = pyplot.figure(figIdx)
                        fig.subplots_adjust(hspace=0.8)
                        sp = fig.add_subplot(3, 1, subplotNum)
                        if subplotNum == 1:
                            sp.set_title(srcToCalStdDict[source])
                        for dataSet in plotSeq:
                            sp.plot(dataSet[0], dataSet[1])

                        sp.set_xlabel('Time (minutes)')
                        sp.set_ylabel('%s Conc (ppmv)' % conc)
                        sp.grid()
                        figIdx += 1

                except:
                    pass

        pyplot.show()

    def clearPlotDict(self):
        self.plotElemDict = {}


class PumpDataProcessor(PumpDataProcessorFrame):

    def __init__(self, outputDir, *args, **kwds):
        PumpDataProcessorFrame.__init__(self, *args, **kwds)
        self.outputDir = outputDir
        self.dataPlotter = DataPlotter()
        self.srcToCalStdDict = {}
        self.header = ''
        self.defaultPath = None
        self.filenames = []
        self.pumpData = []
        self.liquidDataBlockList = []
        self.vaporData = []
        self.vaporDataBlockList = []
        self.bindEvents()
        self.timeFmt = TIME_FORMAT1
        self.dataParsed = False
        self.liquidVaporFilename = ''
        self.liquidFilename = ''
        self.vaporAverageFilename = ''
        self.maxNumOverlaps = 1
        self.iShowPlots.Enable(False)
        self.iClosePlots.Enable(False)
        return

    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onLoadFileMenu, self.iLoadFile)
        self.Bind(wx.EVT_MENU, self.onClosePlotsMenu, self.iClosePlots)
        self.Bind(wx.EVT_MENU, self.onShowPlotsMenu, self.iShowPlots)
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_BUTTON, self.onProcLiquidButton, self.procLiquidButton)
        self.Bind(wx.EVT_BUTTON, self.onProcVaporButton, self.procVaporButton)
        self.Bind(wx.EVT_BUTTON, self.onProcessButton, self.processButton)
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.closeButton)
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrlLiquid, self.textCtrlLiquidMsg)
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrlVapor, self.textCtrlVaporMsg)

    def enableAllProcButtons(self, onFlag):
        if onFlag:
            self.procLiquidButton.Enable(True)
            self.procVaporButton.Enable(True)
            self.processButton.Enable(True)
        else:
            self.procLiquidButton.Enable(False)
            self.procVaporButton.Enable(False)
            self.processButton.Enable(False)

    def onOverUrlLiquid(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrlLiquidMsg.GetRange(event.GetURLStart() + 5, event.GetURLEnd())
            print urlString
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()

    def onOverUrlVapor(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrlVaporMsg.GetRange(event.GetURLStart() + 5, event.GetURLEnd())
            print urlString
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()

    def onProcessButton(self, evt):
        self.onProcLiquidButton(evt)
        self.onProcVaporButton(evt)

    def onCloseButton(self, evt):
        print 'Data processing canceled...\n'
        sys.exit(0)
        self.Destroy()

    def onProcLiquidButton(self, evt):
        if self._isDataReady():
            print 'Liquid data analysis started...\n'
            procLiquidThread = threading.Thread(target=self.procLiquid)
            procLiquidThread.setDaemon(True)
            procLiquidThread.start()

    def onProcVaporButton(self, evt):
        if self._isDataReady():
            print 'Vapor data analysis started...\n'
            procVaporThread = threading.Thread(target=self.procVapor)
            procVaporThread.setDaemon(True)
            procVaporThread.start()

    def onClosePlotsMenu(self, evt):
        pyplot.close('all')
        self.iShowPlots.Enable(True)
        self.iClosePlots.Enable(False)

    def onShowPlotsMenu(self, evt):
        maxNumOverlaps = int(self.textCtrlNumOverlaps.GetValue())
        maxNumOverlaps = max(1, min(maxNumOverlaps, 4))
        self.textCtrlNumOverlaps.SetValue('%d' % maxNumOverlaps)
        if self.maxNumOverlaps != maxNumOverlaps:
            self.onProcLiquidButton(evt)
            self.maxNumOverlaps = maxNumOverlaps
        self.dataPlotter.plot(self.srcToCalStdDict)
        self.iShowPlots.Enable(False)
        self.iClosePlots.Enable(True)

    def onAboutMenu(self, evt):
        d = wx.MessageDialog(None, 'Copyright 1999-2010 Picarro Inc. All rights reserved.\n\nVersion: 0.01\n\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.', 'About Syringe Pump Data Processor', wx.OK)
        d.ShowModal()
        d.Destroy()
        return

    def onLoadFileMenu(self, evt):
        if not self.defaultPath:
            self.defaultPath = os.getcwd()
        dlg = wx.FileDialog(self, 'Select Data File or Directory...', self.defaultPath, wildcard='*.csv', style=wx.OPEN | wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filenames = dlg.GetPaths()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.defaultPath = dlg.GetDirectory()
        pumpData = []
        header = ''
        numFiles = len(self.filenames)
        if numFiles > 1:
            self.filenames.sort()
            outputFilename = self.filenames[0].split('.')[0] + '_%dFiles' % numFiles
        else:
            outputFilename = self.filenames[0].split('.')[0]
        if os.path.isdir(self.outputDir):
            self.liquidVaporFilename = os.path.abspath(os.path.join(self.outputDir, os.path.basename(outputFilename) + '_Liquid_Vapor.csv'))
            self.liquidFilename = os.path.abspath(os.path.join(self.outputDir, os.path.basename(outputFilename) + '_Liquid.csv'))
            self.vaporAverageFilename = os.path.abspath(os.path.join(self.outputDir, os.path.basename(outputFilename) + '_Vapor_Average.csv'))
        else:
            self.liquidVaporFilename = outputFilename + '_Liquid_Vapor.csv'
            self.liquidFilename = outputFilename + '_Liquid.csv'
            self.vaporAverageFilename = outputFilename + '_Vapor_Average.csv'
        try:
            for filename in self.filenames:
                fd = open(filename, 'r')
                newLines = fd.readlines()
                if not header:
                    header = newLines[0].split(',', 1)[1]
                pumpData += newLines[1:]
                pumpData.append('EndFile')
                fd.close()

        except Exception as errMsg:
            wx.MessageBox('Loading %s failed!\nPython Error: %s' % (self.filename, errMsg))
            return

        self.pumpData = pumpData
        self.header = header
        try:
            time.mktime(time.strptime('%s %s' % (pumpData[0].split(',')[1].strip(), pumpData[0].split(',')[2].strip()), TIME_FORMAT1))
            self.timeFmt = TIME_FORMAT1
        except ValueError:
            self.timeFmt = TIME_FORMAT2

        self.textCtrlLiquidMsg.Clear()
        self.textCtrlLiquidMsg.WriteText('Loaded:\n')
        self.textCtrlVaporMsg.Clear()
        self.textCtrlVaporMsg.WriteText('Loaded:\n')
        for filename in self.filenames:
            self.textCtrlLiquidMsg.WriteText('%s\n' % filename)
            self.textCtrlVaporMsg.WriteText('%s\n' % filename)

        self.parseData()
        self.dataParsed = True

    def _isDataReady(self):
        if not self.dataParsed:
            dlg = wx.MessageDialog(None, 'Please load data file(s) first.   ', 'Data Processing Error', style=wx.ICON_EXCLAMATION | wx.STAY_ON_TOP | wx.OK)
            confirm = dlg.ShowModal() == wx.ID_OK
            if confirm:
                dlg.Destroy()
            return False
        else:
            return True
        return

    def parseData(self):
        self.liquidDataBlockList = []
        self.vaporData = []
        self.vaporDataBlockList = []
        liquidBlock = []
        vaporBlock = []
        lastSource = None
        for line in self.pumpData:
            if line != 'EndFile':
                parsedLine = line.split(',')
                if len(parsedLine) != 13:
                    continue
                for idx in range(len(parsedLine)):
                    parsedLine[idx] = parsedLine[idx].strip()

                parsedLine[0] = self._getTimeFromStamps(parsedLine[1], parsedLine[2])
                dasTemp, injSpeed, rotVal, solVal, calStd, source = parsedLine[-6:]
                source_lower = source.lower()
                if source_lower not in self.srcToCalStdDict:
                    self.srcToCalStdDict[source_lower] = calStd
                parsedLine[-1] += '\n'
                if source != lastSource and lastSource != None:
                    if liquidBlock and 'AMBIENT' not in lastSource:
                        self.liquidDataBlockList.append(liquidBlock)
                        liquidBlock = []
                    elif vaporBlock and 'AMBIENT' in lastSource:
                        self.vaporDataBlockList.append(vaporBlock)
                        vaporBlock = []
                if 'AMBIENT' not in source:
                    liquidBlock.append(copy.copy(parsedLine))
                else:
                    self.vaporData.append(copy.copy(parsedLine))
                    vaporBlock.append(copy.copy(parsedLine))
                lastSource = source
            elif liquidBlock and 'AMBIENT' not in lastSource:
                self.liquidDataBlockList.append(liquidBlock)
                liquidBlock = []
            elif vaporBlock and 'AMBIENT' in lastSource:
                self.vaporDataBlockList.append(vaporBlock)
                vaporBlock = []

        return

    def procLiquid(self):
        self.textCtrlLiquidMsg.Clear()
        try:
            pyplot.close('all')
            self.dataPlotter.clearPlotDict()
            self.iShowPlots.Enable(False)
            self.iClosePlots.Enable(False)
            filteredLiquid = []
            statList = []
            liquidVaporList = []
            plotNum = 0
            for dataBlock in self.liquidDataBlockList:
                for i in range(len(dataBlock)):
                    for j in range(1, len(dataBlock[i])):
                        dataBlock[i][j] = dataBlock[i][j].strip()

                dasTemp, injSpeed, rotVal, solVal, calStd, source = dataBlock[0][-6:]
                source_lower = source.lower()
                try:
                    measWin = self._extractMeasWindow(dataBlock, source_lower)
                    maxNumOverlaps = int(self.textCtrlNumOverlaps.GetValue())
                    maxNumOverlaps = max(1, min(maxNumOverlaps, 4))
                    self.textCtrlNumOverlaps.SetValue('%d' % maxNumOverlaps)
                    self.maxNumOverlaps = maxNumOverlaps
                    self.dataPlotter.run(measWin, source_lower, maxNumOverlaps)
                    plotNum += 1
                    filteredData = filterData(measWin, True)
                except Exception as e:
                    print '%s %r' % (e, e)
                    continue

                if not filteredData:
                    continue
                meanFilteredData = mean(filteredData, 0)
                stdFilteredData = std(filteredData, 0)
                medianFilteredData = median(filteredData, 0)
                rangeFilteredData = getRange(filteredData)
                slopeFilteredData = getSlope(filteredData)
                dateStamp, timeStamp = self._getTimeStamps(meanFilteredData[0])
                liquidData = [meanFilteredData[0],
                 '%10s' % dateStamp,
                 '%10s' % timeStamp,
                 '%14.5f' % meanFilteredData[1],
                 '%14.3f' % medianFilteredData[2],
                 '%14.3f' % medianFilteredData[3],
                 '%14.3f' % medianFilteredData[4],
                 '%7s' % dasTemp,
                 '%15s' % injSpeed,
                 '%15s' % rotVal,
                 '%15s' % solVal,
                 '%20s' % calStd,
                 '%15s\n' % source]
                statData = '%10s,%10s,%14.5f,' % (dateStamp, timeStamp, meanFilteredData[1])
                for col in [2, 3, 4]:
                    statData += '%15.3f,%15.3f,%15.3f,%15.4E,%15.3f,' % (meanFilteredData[col],
                     medianFilteredData[col],
                     stdFilteredData[col],
                     slopeFilteredData[col - 2],
                     rangeFilteredData[col - 2])

                statData += '%7s,%15s,%15s,%15s,%20s,%15s\n' % (dasTemp,
                 injSpeed,
                 rotVal,
                 solVal,
                 calStd,
                 source)
                statList.append([meanFilteredData[0], statData])
                filteredLiquid.append(liquidData)

            liquidVaporList = filteredLiquid + self.vaporData
            liquidVaporList.sort()
            for i in range(len(liquidVaporList)):
                liquidVaporList[i] = '%10s,%10s,%14s,%14s,%14s,%14s,%7s,%15s,%15s,%15s,%20s,%15s' % tuple(liquidVaporList[i][1:])

            fd = open(self.liquidVaporFilename, 'w')
            fd.write(self.header)
            fd.writelines(liquidVaporList)
            fd.close()
            statList.sort()
            for i in range(len(statList)):
                statList[i] = statList[i][1]

            fd = open(self.liquidFilename, 'w')
            headerList = self.header.split(',')
            fd.write('%10s,%10s,%14s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%15s,%7s,%15s,%15s,%15s,%20s,%15s\n' % (headerList[0],
             headerList[1],
             headerList[2],
             'H2O_MEAN',
             'H2O_MEDIAN',
             'H2O_SD',
             'H2O_SLOPE',
             'H2O_RANGE',
             'd(18_16)_MEAN',
             'd(18_16)_MEDIAN',
             'd(18_16)_SD',
             'd(18_16)_SLOPE',
             'd(18_16)_RANGE',
             'd(D_H)_MEAN',
             'd(D_H)_MEDIAN',
             'd(D_H)_SD',
             'd(D_H)_SLOPE',
             'd(D_H)_RANGE',
             'DAS Temp',
             'Injection Speed',
             'Rot Valve Mask',
             'Sol Valve Mask',
             'Calibration Standard',
             'Source'))
            fd.writelines(statList)
            fd.close()
            self.textCtrlLiquidMsg.WriteText('Liquid_Vapor File (pulse analysis results of liquid calibration standards AND raw vapor data in chronological order):\nfile:%s' % (self.liquidVaporFilename + '\n'))
            self.textCtrlLiquidMsg.WriteText('Liquid File (pulse analysis results of liquid calibration standards):\nfile:%s' % (self.liquidFilename + '\n'))
            self.iShowPlots.Enable(True)
            print 'Liquid data analysis done...\n'
        except Exception as e:
            print '%s %r' % (e, e)
            self.textCtrlLiquidMsg.WriteText('%r' % e)

    def procVapor(self):
        self.textCtrlVaporMsg.Clear()
        try:
            aveVaporList = []
            for dataBlock in self.vaporDataBlockList:
                for i in range(len(dataBlock)):
                    for j in range(1, len(dataBlock[i])):
                        dataBlock[i][j] = dataBlock[i][j].strip()

                dasTemp, injSpeed, rotVal, solVal, calStd, source = dataBlock[0][-6:]
                try:
                    measWin = self._extractMeasWindow(dataBlock, 'vapor')
                    filteredData = filterData(measWin, False)
                except Exception as e:
                    print '%s %r' % (e, e)
                    continue

                if not filteredData:
                    continue
                winSize = float(self.textCtrlVaporWinSize.GetValue()) * 60
                averagedData = nonoverlapWinAverage(filteredData, winSize)
                for aveData in averagedData:
                    dateStamp, timeStamp = self._getTimeStamps(aveData[0])
                    vaporData = [aveData[0],
                     '%10s' % dateStamp,
                     '%10s' % timeStamp,
                     '%14.5f' % aveData[1],
                     '%14.3f' % aveData[2],
                     '%14.3f' % aveData[3],
                     '%14.3f' % aveData[4],
                     '%7s' % dasTemp,
                     '%15s' % injSpeed,
                     '%15s' % rotVal,
                     '%15s' % solVal,
                     '%20s' % calStd,
                     '%15s\n' % source]
                    aveVaporList.append(vaporData)

            aveVaporList.sort()
            for i in range(len(aveVaporList)):
                aveVaporList[i] = '%10s,%10s,%14s,%14s,%14s,%14s,%7s,%15s,%15s,%15s,%20s,%15s' % tuple(aveVaporList[i][1:])

            fd = open(self.vaporAverageFilename, 'w')
            fd.write(self.header)
            fd.writelines(aveVaporList)
            fd.close()
            self.textCtrlVaporMsg.WriteText('Vapor_Average File (30 second block-averaged data of vapor measurements):\nfile:%s' % (self.vaporAverageFilename + '\n'))
            print 'Vapor data analysis done...\n'
        except Exception as e:
            print '%s %r' % (e, e)
            self.textCtrlLiquidMsg.WriteText('%r' % e)

    def _modifyDefaultStartTime(self, speed, source):
        """Not used for now. May be useful in the future"""
        defaultStartTime = '5.0'
        self.gridLiquidStartTime.SetCellValue(SRC_TO_IDX[source][0], SRC_TO_IDX[source][1], defaultStartTime)

    def _extractMeasWindow(self, dataList, source):
        firstTime, lastTime = dataList[0][0], dataList[-1][0]
        if source != 'vapor':
            try:
                beginWindow = float(self.gridLiquidStartTime.GetCellValue(SRC_TO_IDX[source][0], SRC_TO_IDX[source][1])) * 60
            except:
                beginWindow = firstTime + DEFAULT_LIQUID_START_TIME_MINUTES * 60

            beginWindowTime = firstTime + beginWindow
            endWindowTime = lastTime - float(self.textCtrlLiquidEndTime.GetValue()) * 60
        else:
            beginWindowTime = firstTime + float(self.textCtrlVaporStartTime.GetValue()) * 60
            endWindowTime = lastTime - float(self.textCtrlVaporEndTime.GetValue()) * 60
        selectedData = []
        for data in dataList:
            if data[0] >= beginWindowTime and data[0] <= endWindowTime:
                selectedData.append(data)

        return selectedData

    def _getTimeFromStamps(self, dateStamp, timeStamp):
        try:
            return time.mktime(time.strptime('%s %s' % (dateStamp, timeStamp), self.timeFmt))
        except ValueError:
            if self.timeFmt == TIME_FORMAT1:
                self.timeFmt = TIME_FORMAT2
            else:
                self.timeFmt = TIME_FORMAT1
            return time.mktime(time.strptime('%s %s' % (dateStamp, timeStamp), self.timeFmt))

    def _getTimeStamps(self, timeSeconds):
        try:
            return time.strftime(self.timeFmt, time.localtime(timeSeconds)).split()
        except ValueError:
            if self.timeFmt == TIME_FORMAT1:
                self.timeFmt = TIME_FORMAT2
            else:
                self.timeFmt = TIME_FORMAT1
            return time.strftime(self.timeFmt, time.localtime(timeSeconds)).split()


def handleCommandSwitches():
    shortOpts = 'o:'
    longOpts = []
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError as data:
        print '%s %r' % (data, data)
        sys.exit(1)

    options = {}
    for o, a in switches:
        options[o] = a

    outputDir = ''
    if '-o' in options:
        outputDir = options['-o']
        print 'Output files will be saved in: %s' % outputDir
    return outputDir


if __name__ == '__main__':
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    outputDir = handleCommandSwitches()
    frame = PumpDataProcessor(outputDir, None, -1, '')
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()