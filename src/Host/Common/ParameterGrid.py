#!/usr/bin/python
#
# FILE:
#   ParameterGrid.py
#
# DESCRIPTION:
#   Supporting class for ParameterDialog.py
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   06-Jan-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#

import wx
import wx.grid

class ParameterGrid(wx.grid.Grid):
    """ Grid for editing parameter values. The grid has three columns for the parameter name,
        the value and its units. Only cells in the value column may be edited, and navigation
        between parameters can be done via the keyboard using TAB and SHIFT-TAB """
    def makeGrid(self,nrows):
        self.CreateGrid(nrows, 3)   # Only three columns in grid
        self.SetRowLabelSize(0)     # No row labels
        self.EnableDragColSize(0)   # Cannot resize
        self.EnableDragRowSize(0)
        self.EnableDragGridSize(0)
        # Column labels
        self.SetColLabelValue(0, "Name")
        self.SetColLabelValue(1, "Value")
        self.SetColLabelValue(2, "Units")
        # Register event handlers
        self.Bind(wx.EVT_IDLE, self.onIdle)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

    def onIdle(self,e):
        """ Prevent cursor from moving away from value column """
        col = self.GetGridCursorCol()
        if col>=0 and col != 1:
            row = self.GetGridCursorRow()
            self.SetGridCursor(row,1)
        else: e.Skip()

    def onKeyDown(self, e):
        """ Allow TAB and SHIFT TAB to be used for navigating between parameters """
        if e.KeyCode == wx.WXK_TAB:
            if e.ShiftDown(): self.MoveCursorUp(False)
            else: self.MoveCursorDown(False)
            return
        else: e.Skip()