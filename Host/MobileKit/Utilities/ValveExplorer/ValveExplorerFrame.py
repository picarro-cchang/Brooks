"""
Copyright 2012, Picarro Inc.

UI for MobileKit valve timing utility.
"""

from __future__ import with_statement

import time
import os.path
import pprint
import csv

import wx

#pylint: disable=W0401,W0614
from Host.autogen.interface import *
#pylint: enable=W0401,W0614

import ValveExplorer
from Host.Common import GraphPanel
from Host.Common import timestamp


class ValveExplorerFrame(wx.Frame):

    VALVE_STATES = [['Ignore', 'Pull to Loop (-)', 'Off (+)'],
                    ['Ignore', 'From Inlet (-)', 'From Loop (+)'],
                    ['Ignore', 'Off (-)', 'Inject (+)']]

    VALVE_COLORS = ['blue', 'red', 'green']

    FONTS = None


    def __init__(self, *args, **kwds):
        kwds['style'] = wx.DEFAULT_FRAME_STYLE
        super(ValveExplorerFrame, self).__init__(*args, **kwds)

        assert len(self.VALVE_STATES) == ValveExplorer.ValveExplorer.N_VALVES

        self.FONTS = {
            'std' : wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                            faceName='Arial'),
            'bold' : wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD,
                             faceName='Arial')
        }

        self.rows = []

        # Overall
        base = wx.BoxSizer(wx.VERTICAL)

        # Top control row
        topRow = wx.BoxSizer(wx.HORIZONTAL)

        self.btnRun = wx.Button(self, -1, 'Run', size=(150,46))
        self.btnRun.SetFont(self.FONTS['bold'])
        topRow.Add(self.btnRun, 0, wx.ALIGN_LEFT)
        base.Add(topRow, 0, wx.ALL, 11)

        # Valve selection area
        self.valveArea = wx.BoxSizer(wx.VERTICAL)

        valveRow = wx.BoxSizer(wx.HORIZONTAL)

        self.btnAddValve = wx.Button(self, -1, '+', size=(32,32))
        self.btnAddValve.SetFont(self.FONTS['std'])
        valveRow.Add(self.btnAddValve, 0, wx.ALIGN_LEFT)

        self.btnSaveSequence = wx.Button(self, -1, 'Save Sequence...',
                                         size=(104,32))
        self.btnSaveSequence.SetFont(self.FONTS['std'])
        valveRow.Add(self.btnSaveSequence, 0)

        self.btnLoadSequence = wx.Button(self, -1, 'Load Sequence...',
                                         size=(104,32))
        self.btnLoadSequence.SetFont(self.FONTS['std'])
        valveRow.Add(self.btnLoadSequence, 0)

        self.btnExportData = wx.Button(self, -1, 'Export Data...',
                                       size=(104,32))
        self.btnExportData.SetFont(self.FONTS['std'])
        valveRow.Add(self.btnExportData, 0)

        self.valveArea.Add(valveRow, 0, wx.BOTTOM, 11)

        base.Add(self.valveArea, 0, wx.ALL, 11)

        self._addValveRow()

        # Log window
        self.teLog = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE)
        base.Add(self.teLog, 1, wx.EXPAND)

        # Valve mask and processed loss
        self.pnlMaskLoss = GraphPanel.GraphPanel(self, -1)
        self.pnlMaskLoss.SetGraphProperties(
            ylabel='Processed Loss (ppm/cm)', timeAxes=(True,False))
        base.Add(self.pnlMaskLoss, 2, wx.EXPAND)

        self.SetTitle('MobileKit Valve Timing Explorer')

        self.SetAutoLayout(True)
        self.SetSizer(base)
        self.Layout()

        self.plotTimer = wx.Timer(self)
        self.plotTimer.Start(milliseconds=1000)

        self.lossSeries = GraphPanel.Series(10000)
        self.pnlMaskLoss.AddSeriesAsLine(self.lossSeries, colour='black',
                                         width=1)
        # Plot the status of each valve independently
        self.valveSeries = []
        for i in range(ValveExplorer.ValveExplorer.N_VALVES):
            self.valveSeries.append(GraphPanel.Series(10000))
            self.pnlMaskLoss.AddSeriesAsLine(self.valveSeries[-1],
                                             colour=self.VALVE_COLORS[i],
                                             width=2)

        self._bindEvents()

        self.v = ValveExplorer.ValveExplorer(self._logMessage,
                                             self._updateSeries)

    def _updateSeries(self, sensor, t, v):
        if sensor == STREAM_ProcessedLoss1:
            self.lossSeries.Add(timestamp.unixTime(t), v)

        elif sensor == STREAM_ValveMask:
            for i in range(ValveExplorer.ValveExplorer.N_VALVES):
                if (int(v) & (1 << i)) > 0:
                    state = 1.0
                else:
                    state = 0.0

                self.valveSeries[i].Add(timestamp.unixTime(t), state)

    def _logMessage(self, msg):
        self.teLog.AppendText(msg)

    def _bindEvents(self):
        self.Bind(wx.EVT_BUTTON, self._addValveRow, self.btnAddValve)
        self.Bind(wx.EVT_BUTTON, self._startAcquisition, self.btnRun)
        self.Bind(wx.EVT_BUTTON, self._saveSequence, self.btnSaveSequence)
        self.Bind(wx.EVT_BUTTON, self._loadSequence, self.btnLoadSequence)
        self.Bind(wx.EVT_BUTTON, self._exportData, self.btnExportData)
        self.Bind(wx.EVT_TIMER, self._onUpdatePlotTimer, self.plotTimer)

    def _exportData(self, evt=None):
        dlg = wx.FileDialog(self, message='Export data as...',
                            wildcard='*.csv', style=wx.SAVE)

        if dlg.ShowModal() != wx.ID_OK:
            self._logMessage("Data export cancelled.\n")
            return

        noteDlg = wx.TextEntryDialog(self, message='Data Note',
                                     caption='Description:',
                                     style=wx.OK | wx.CANCEL)

        fullFilename = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
        self._logMessage("Saving '%s'...\n" % fullFilename)

        if noteDlg.ShowModal() == wx.ID_OK:
            note = noteDlg.GetValue()
        else:
            note = None

        # Only use the minimum # of points any of the streams has
        counts = [c.x.count for c in self.valveSeries]
        counts.append(self.lossSeries.x.count)

        header = ['processed_loss_1_time','processed_loss_1']
        for i in range(ValveExplorer.ValveExplorer.N_VALVES):
            header.append("valve_%d_time" % (i + 1))
            header.append("valve_%d" % (i + 1))

        with open(fullFilename, 'w') as fp:
            fp.write("# %s " % time.asctime(time.localtime()))
            if note is not None:
                fp.write(note)
            fp.write("\n")

        fp = csv.writer(open(fullFilename, 'ab'))
        fp.writerow(header)
        for i in xrange(min(counts)):
            row = [self.lossSeries.GetX()[i], self.lossSeries.GetY()[i]]
            for j in range(ValveExplorer.ValveExplorer.N_VALVES):
                row.append(self.valveSeries[j].GetX()[i])
                row.append(self.valveSeries[j].GetY()[i])
            fp.writerow(row)

    def _saveSequence(self, evt=None):
        dlg = wx.FileDialog(self, message='Save Valve Sequence as...',
                            wildcard='*.txt', style=wx.SAVE)

        if dlg.ShowModal() != wx.ID_OK:
            self._logMessage("Save cancelled.\n")
            return


        fullFilename = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
        self._logMessage("Saving '%s'...\n" % fullFilename)
        self.v.saveSequence(fullFilename)

    def _loadSequence(self, evt=None):
        dlg = wx.FileDialog(self, message='Load Valve Sequence',
                            wildcard='*.txt', style=wx.OPEN)

        if dlg.ShowModal() == wx.ID_OK:
            fullFilename = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            self._logMessage("Loading '%s'...\n" % fullFilename)
            self.v.loadSequence(fullFilename)

            self._updateValveRowsFromSequence()

    def _updateValveRowsFromSequence(self):
        for r in self.rows:
            for c in r:
                c.Destroy()

        self.rows = []

        # For display purposes, ignore the final Idle step
        for r in self.v.valveSeq[:-1]:
            print "Adding row..."
            pprint.pprint(r)
            self._addValveRow()
            for i in range(ValveExplorer.ValveExplorer.N_VALVES):
                mask = r[0]
                if (mask & (1 << i)) > 0:
                    self.rows[-1][i + 1].SetSelection(((r[1] >> i) & 0x1) + 1)
                else:
                    self.rows[-1][i + 1].SetSelection(0)

            self.rows[-1][-2].SetValue(str(r[2] * 0.2))

        self.Layout()

    def _onUpdatePlotTimer(self, evt):
        self.pnlMaskLoss.Update(delay=0)

    def _startAcquisition(self, evt=None):
        if self.v.isRunning():
            self.btnRun.Disable()
            self.v.interruptDataAcquisition()
            self.btnRun.SetLabel('Run')
            self.btnRun.Enable()

        else:
            self.btnRun.Disable()

            # Translate UI into something the explorer can use.
            steps = []
            for r in self.rows:
                # N valves + time + 2 labels
                assert len(r) == ValveExplorer.ValveExplorer.N_VALVES + 3
                step = []
                for i in range(ValveExplorer.ValveExplorer.N_VALVES):
                    step.append(r[i + 1].GetSelection())
                step.append(float(r[-2].GetValue()))
                steps.append(step)

            self.v.genValveSequence(steps)
            self.v.downloadValveSequence()
            self._clear()
            self.v.doDataAcquisition(self._dataAcquisitionEndCb)

            self.btnRun.SetLabel('Stop')
            self.btnRun.Enable()

    def _dataAcquisitionEndCb(self):
        self.btnRun.SetLabel('Run')

    def _clear(self):
        self.lossSeries.Clear()
        for s in self.valveSeries:
            s.Clear()

    def _addValveRow(self, evt=None):
        newRow = wx.BoxSizer(wx.HORIZONTAL)

        self.rows.append([])
        self.rows[-1].append(wx.StaticText(self, -1, "%s" % len(self.rows))),
        newRow.Add(self.rows[-1][-1], 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 7)

        for i in range(ValveExplorer.ValveExplorer.N_VALVES):
            self.rows[-1].append(wx.ComboBox(self, -1,
                                             value=self.VALVE_STATES[i][0],
                                             choices=self.VALVE_STATES[i],
                                             style=wx.CB_READONLY|
                                             wx.CB_DROPDOWN,
                                             size=(110,23)))
            newRow.Add(self.rows[-1][-1], 0,
                       wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 7)

        self.rows[-1].append(wx.TextCtrl(self, -1, value='0.0',
                                         size=(50,23)))
        newRow.Add(self.rows[-1][-1], 1, wx.ALIGN_CENTER_VERTICAL)

        self.rows[-1].append(wx.StaticText(self, -1, 's', size=(5,23)))
        newRow.Add(self.rows[-1][-1], 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 7)

        self.valveArea.Add(newRow, 0)
        self.Layout()


def main():
    app = wx.PySimpleApp()
    frame = ValveExplorerFrame(None)
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
