# File Name: wizardhelper.py
# Purpose: Some routines for creating wizard pages
#
# File History:
# 06-05-02 ytsai   Created file
# 06-05-29 ytsai   Added last page property


import wx
import wx.wizard as wiz

class WizardTitledLogoPage(wiz.PyWizardPage):
    def __init__(self, parent, title):
        wiz.PyWizardPage.__init__(self, parent)
        self.next = None
        self.prev = None
        self.last = None

        sizerH = wx.BoxSizer(wx.HORIZONTAL)
        sizerV = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizerV)
        title = wx.StaticText(self, -1, title, (0,0) )
        title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        bmp  = wx.Image( "P_RGB_WHITEBCKGRND.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        sbmp = wx.StaticBitmap( self, -1, bmp, (0, 0), (bmp.GetWidth(), bmp.GetHeight()))
        sizerH.Add( sbmp,  0, wx.ALIGN_LEFT|wx.ALL, 1)
        sizerH.Add( title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizerV.Add(sizerH,0, wx.ALIGN_LEFT|wx.ALL, 1)
        sizerV.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        self.sizer = sizerV

    def SetNext(self, next):
        self.next = next

    def SetPrev(self, prev):
        self.prev = prev

    def SetLast(self, last):
        self.last = last

    def GetNext(self):
        return self.next

    def GetPrev(self):
        return self.prev

    def GetLast(self):
        return self.last
