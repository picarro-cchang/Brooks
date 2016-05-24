import wx
from SideBar import SideBar
from PlotAreaOne import PlotAreaOne
from PlotAreaTwo import PlotAreaTwo

class Page(wx.Panel):
    def __init__(self,parent,main_frame,flag):

        self.flag = flag
        flag_for_page_one = 1
        flag_for_page_two = 2

        minimum_pane_size = 450
        sash_position = 500
        
        wx.Panel.__init__(self,parent)
        self.parent = parent
        self.main_frame = main_frame

        splitter = wx.SplitterWindow(self)
        if self.flag == flag_for_page_one:
            self.sidebar = SideBar(splitter,self.main_frame,self.flag)
            self.plot_area = PlotAreaOne(splitter, self.main_frame, self.sidebar)
        elif self.flag == flag_for_page_two:
            self.sidebar = SideBar(splitter,self.main_frame,self.flag)
            self.plot_area = PlotAreaTwo(splitter, self.main_frame, self.sidebar)
        else:
            self.sidebar = None
            self.plot_area = None

        if self.sidebar is not None and self.plot_area is not None:
            splitter.SplitVertically(self.sidebar, self.plot_area)
            splitter.SetMinimumPaneSize(minimum_pane_size)
            splitter.SetSashPosition(sash_position)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(splitter,1,wx.EXPAND)
            self.SetSizerAndFit(sizer)
            self.SetAutoLayout(True)






