#!/usr/bin/python
#
"""
File Name: RecipeEditor.py
Purpose: The editor to help user design recipes for IM-CRDS (MBW)

File History:
    2011-09-07 Alex Lee  Created
    
Copyright (c) 2011 Picarro, Inc. All rights reserved
"""
import os
import sys
import pprint
import random
import time
import wx
import getopt
from numpy import *
from Host.Common.CustomConfigObj import CustomConfigObj

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

DEFAULT_CONFIG_NAME = "RecipeEditor.ini"

# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.artist import *

COEFF_MAPPING = [["Coefficient A:", "polyA", "0.0"], ["Coefficient B:", "polyB", "0.0"], ["Coefficient C:", "polyC", "0.0"],
                 ["Heat Time (sec):", "heatTime", "600.0"], ["Pre-Heat Time (sec):", "preheatTime", "5.0"], 
                 ["Low Threshold (ppm):", "h2oLowThreshold", "1000.0"], ["End Threshold (ppm):", "h2oEndHeatThreshold", "800.0"]] 
class RecipeEditor(wx.Frame):
    """ The main frame of the application
    """
    title = 'Picarro IM-CRDS Recipe Editor'
    
    def __init__(self, configFile, *args, **kwds):
        cp = CustomConfigObj(configFile)
        try:
            self.recipeConfig = CustomConfigObj(cp.get("Main", "recipeIniPath", "C:/Picarro/G2000/AppConfig/Config/Coordinator/RecipeMBW.ini"))
            self.holderConfig = CustomConfigObj(cp.get("Main", "holderIniPath", "C:/Picarro/G2000/AppConfig/Config/Coordinator/SampleHolder.ini"))
        except Exception, err:
            print err
            d = wx.MessageDialog(None, "Recipe or Sample Holder INI file not found", "Error", wx.ICON_ERROR|wx.STAY_ON_TOP)
            d.ShowModal()
            return
        kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, None, -1, self.title, **kwds)
        self.numCoeff = len(COEFF_MAPPING)
        self.slope = 1.0
        self.offset = 0.0
        self.createMenu()
        self.createMainPanel()
        self.bindEvents()
        self.onComboBox(None)
        self.drawFigure()

    def createMenu(self):
        self.menubar = wx.MenuBar()
        
        menuFile = wx.Menu()
        self.mSavePlot = menuFile.Append(-1, "Save plot")
        
        menuHelp = wx.Menu()
        self.mAbout = menuHelp.Append(-1, "About Recipe Editor")
        
        self.menubar.Append(menuFile, "&File")
        self.menubar.Append(menuHelp, "&Help")
        self.SetMenuBar(self.menubar)

    def createMainPanel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """
        self.panel1 = wx.Panel(self)
        self.panel1.SetBackgroundColour("#E0FFFF")
        
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.labelFooter = wx.StaticText(self.panel2, -1, "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0], style=wx.ALIGN_CENTER)
        
        # Create the mpl Figure and FigCanvas objects. 
        self.dpi = 100
        self.fig = Figure((6.0, 5.0), dpi=self.dpi)
        self.canvas = FigCanvas(self.panel1, -1, self.fig)
        self.sp = self.fig.add_subplot(1,1,1)
        self.textlabels = []
        self.textboxes = []
        for i in range(self.numCoeff):
            self.textlabels.append(wx.StaticText(self.panel1, -1, COEFF_MAPPING[i][0], style=wx.ALIGN_RIGHT))
            self.textboxes.append(wx.TextCtrl(self.panel1, size=(150,-1), style=wx.TE_PROCESS_ENTER|wx.ALIGN_RIGHT))
        
        self.drawbutton = wx.Button(self.panel1, -1, "Draw", size=(150,-1))
        self.savebutton = wx.Button(self.panel1, -1, "Save Recipe", size=(150,-1))
        self.removebutton = wx.Button(self.panel1, -1, "Remove Recipe", size=(150,-1))
            
        self.recipeList = self.recipeConfig.list_sections() + ["NEW"]
        self.holderList = self.holderConfig.list_sections()
        self.recipeLabel = wx.StaticText(self.panel1, -1, "Recipe:", style=wx.ALIGN_RIGHT)
        self.holderLabel = wx.StaticText(self.panel1, -1, "Sample Holder:", style=wx.ALIGN_RIGHT)
        self.recipeComboBox = wx.ComboBox(self.panel1, -1, choices = self.recipeList, value = self.recipeList[0], size = (150, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        self.holderComboBox = wx.ComboBox(self.panel1, -1, choices = self.holderList, value = self.holderList[0], size = (150, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)

        # Create the navigation toolbar, tied to the canvas
        self.toolbar = NavigationToolbar(self.canvas)
        
        # Layout with box sizers
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer = wx.FlexGridSizer(0, 2)

        grid_sizer.AddSpacer(10)
        grid_sizer.AddSpacer(10)
        grid_sizer.Add(self.recipeLabel, 0, border=5, flag= wx.ALIGN_RIGHT| wx.ALL)
        grid_sizer.Add(self.recipeComboBox, 0, border=5, flag= wx.ALIGN_LEFT | wx.ALL)
        grid_sizer.Add(self.holderLabel, 0, border=5, flag= wx.ALIGN_RIGHT| wx.ALL)
        grid_sizer.Add(self.holderComboBox, 0, border=5, flag= wx.ALIGN_LEFT | wx.ALL)
        for i in range(self.numCoeff):
            grid_sizer.Add(self.textlabels[i], 0, border=5, flag= wx.ALIGN_RIGHT| wx.ALL)
            grid_sizer.Add(self.textboxes[i], 0, border=5, flag= wx.ALIGN_LEFT | wx.ALL)
        grid_sizer.Add((0,0))
        grid_sizer.Add(self.drawbutton, 0, border=5, flag= wx.ALIGN_LEFT | wx.ALL)
        grid_sizer.Add((0,0))
        grid_sizer.Add(self.savebutton, 0, border=5, flag= wx.ALIGN_LEFT | wx.ALL)
        grid_sizer.Add((0,0))
        grid_sizer.Add(self.removebutton, 0, border=5, flag= wx.ALIGN_LEFT | wx.ALL)

        self.vbox.AddSpacer(10)
        self.vbox.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.toolbar, 0, wx.EXPAND)
        
        self.hbox.Add((10,0))
        self.hbox.Add(grid_sizer, 0)
        self.hbox.Add(self.vbox, 0)
        self.panel1.SetSizer(self.hbox)
        
        self.hbox2.Add(self.labelFooter, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.panel2.SetSizer(self.hbox2)
        
        self.vbox2.Add(self.panel1, 0, wx.EXPAND, 0)
        self.vbox2.Add(self.panel2, 0, wx.EXPAND, 0)
        self.SetSizer(self.vbox2)
        self.vbox2.Fit(self)
    
    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onSavePlot, self.mSavePlot)
        self.Bind(wx.EVT_MENU, self.onAbout, self.mAbout)
        for i in range(self.numCoeff):
            self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter, self.textboxes[i])
        self.Bind(wx.EVT_BUTTON, self.onDrawButton, self.drawbutton)
        self.Bind(wx.EVT_BUTTON, self.onSaveButton, self.savebutton)
        self.Bind(wx.EVT_BUTTON, self.onRemoveButton, self.removebutton)
        self.Bind(wx.EVT_COMBOBOX, self.onComboBox, self.recipeComboBox)
        self.Bind(wx.EVT_COMBOBOX, self.onComboBox, self.holderComboBox)

    def drawFigure(self):
        """ Redraws the figure
        """
        coeff = [float(t.GetValue()) for t in self.textboxes[:3]]
        x = arange(float(self.textboxes[3].GetValue()))
        y = coeff[0]*x**2+coeff[1]*x+coeff[2]
        # Set 50 as the upper limit
        y = choose(greater(y, 50.0), (y, 50.0)) 
        y = self.offset + self.slope * (255 - (y/100)*255)
        # clear the axes and redraw the plot anew
        self.sp.clear()        
        self.sp.grid(True)
        line = self.sp.plot(x, y) 
        setp(line, linewidth=2)
        self.sp.set_title("Recipe: %s (%s)" % (self.recipeComboBox.GetValue(), self.holderComboBox.GetValue()))
        self.sp.set_xlabel("Time [seconds]")
        self.sp.set_ylabel("Temperature [C]")
        self.canvas.draw()

    def onDrawButton(self, event):
        self.drawFigure()  
    
    def onTextEnter(self, event):
        self.drawFigure()

    def onComboBox(self, event):
        recipe = self.recipeComboBox.GetValue()
        if recipe != "NEW":
            for i in range(self.numCoeff):
                self.textboxes[i].SetValue(self.recipeConfig.get(recipe, COEFF_MAPPING[i][1]))
        else:
            for i in range(self.numCoeff):
                self.textboxes[i].SetValue(COEFF_MAPPING[i][2])
        holder = self.holderComboBox.GetValue()
        self.slope = self.holderConfig.getfloat(holder, "slope")
        self.offset = self.holderConfig.getfloat(holder, "offset")
        self.drawFigure()
        
    def onSaveButton(self, event):
        recipe = self.recipeComboBox.GetValue()
        timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
        if recipe == "NEW":
            recipe = "Recipe_" + timestamp
            
        dlg = wx.TextEntryDialog(self, "Save recipe as...", "Save recipe as...", recipe)
        if dlg.ShowModal() == wx.ID_OK:
            newRecipe = dlg.GetValue()
            if newRecipe not in self.recipeConfig.list_sections():
                self.recipeConfig.add_section(newRecipe)
                self.recipeComboBox.Insert(newRecipe, len(self.recipeList)-1)
            else:
                d = wx.MessageDialog(self, "Replace existing recipe '%s' ?" % newRecipe, "Replace existing recipe", wx.ICON_EXCLAMATION|wx.YES_NO|wx.NO_DEFAULT|wx.STAY_ON_TOP)
                if d.ShowModal() != wx.ID_YES:
                    return
            for i in range(self.numCoeff):
                self.recipeConfig.set(newRecipe, COEFF_MAPPING[i][1], self.textboxes[i].GetValue())
            self.recipeConfig.write()
            self.recipeList = self.recipeConfig.list_sections() + ["NEW"]
            d = wx.MessageDialog(self, "Recipe '%s' saved" % newRecipe, "Confirmation", wx.ICON_INFORMATION|wx.OK|wx.STAY_ON_TOP)
            d.ShowModal()
            self.recipeComboBox.SetStringSelection(newRecipe)
            self.onComboBox(None)

    def onRemoveButton(self, event):
        recipe = self.recipeComboBox.GetValue()
        if recipe == "NEW":
            d = wx.MessageDialog(self, "Select an existing recipe to be removed", "Select recipe", wx.ICON_INFORMATION|wx.OK|wx.STAY_ON_TOP)
            d.ShowModal()
            return
        d = wx.MessageDialog(self, "Remove recipe '%s' ?" % recipe, "Remove recipe", wx.ICON_EXCLAMATION|wx.YES_NO|wx.NO_DEFAULT|wx.STAY_ON_TOP)
        if d.ShowModal() != wx.ID_YES:
            return
        self.recipeConfig.remove_section(recipe)
        self.recipeConfig.write()
        removeIdx = self.recipeList.index(recipe)
        self.recipeComboBox.Delete(removeIdx)
        self.recipeList = self.recipeConfig.list_sections() + ["NEW"]
        d = wx.MessageDialog(self, "Recipe '%s' removed" % recipe, "Confirmation", wx.ICON_INFORMATION|wx.OK|wx.STAY_ON_TOP)
        d.ShowModal()
        self.recipeComboBox.SetSelection(removeIdx)
        self.onComboBox(None)
            
    def onSavePlot(self, event):
        file_choices = "PNG (*.png)|*.png"
        recipe = self.recipeComboBox.GetValue()
        holder = self.holderComboBox.GetValue()
        dlg = wx.FileDialog(self, message="Save plot as...", defaultDir=os.getcwd(), defaultFile="%s-%s.png" % (recipe, holder), wildcard=file_choices, style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
        
    def onAbout(self, event):
        msg = """Editor that allows user review and design recipes for IM-CRDS (MBW)
        
        Copyright 1999-2011 Picarro Inc. All rights reserved.
        The copyright of this computer program belongs to Picarro Inc.
        Any reproduction or distribution of this program requires permission from Picarro Inc.
        """
        dlg = wx.MessageDialog(self, msg, "About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

def handleCommandSwitches():
    shortOpts = "c:"
    longOpts = []
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME
    
    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        
    return configFile
    
if __name__ == '__main__':
    configFile = handleCommandSwitches()
    app = wx.PySimpleApp()
    app.frame = RecipeEditor(configFile)
    app.frame.Show()
    app.MainLoop()


