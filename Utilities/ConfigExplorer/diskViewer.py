import wx
import os
from ConfigManagerGui import ConfigManagerGui

class DiskViewer(ConfigManagerGui):
    def __init__(self,*a,**k):
        ConfigManagerGui.__init__(self,*a,**k)
        # self.Bind(wx.EVT_TREE_ITEM_EXPANDED,self.onItemExpanded,self.treeCtrlFiles)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED,self.onItemCollapsed,self.treeCtrlFiles)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING,self.onItemExpanding,self.treeCtrlFiles)
        
    def run(self):
        r = self.treeCtrlFiles.AddRoot("C:\\")
        self.treeCtrlFiles.SetItemHasChildren(r,True)
        self.treeCtrlFiles.SetItemPyData(r,"C:\\")
    
    def onItemCollapsed(self,evt):
        self.treeCtrlFiles.DeleteChildren(evt.GetItem())
    
    def onItemExpanding(self,evt):
        self.addTreeNodes(evt.GetItem())
    
    def addTreeNodes(self,parentItem):
        top = self.treeCtrlFiles.GetItemPyData(parentItem)
        try:
            root,dirs,files = os.walk(top).next()
            for d in dirs:
                name = os.path.join(root,d)
                node = self.treeCtrlFiles.AppendItem(parentItem,d)
                self.treeCtrlFiles.SetItemPyData(node,name)
                self.treeCtrlFiles.SetItemHasChildren(node,True)
            if not dirs:
                self.treeCtrlFiles.SetItemHasChildren(parentItem,False)
        except StopIteration:
            self.treeCtrlFiles.SetItemHasChildren(parentItem,False)
        
# end of class ConfigManagerGui
if __name__ == "__main__":
    appDiskViewer = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frameMain = DiskViewer(None, -1, "")
    appDiskViewer.SetTopWindow(frameMain)
    frameMain.run()
    frameMain.Show()
    appDiskViewer.MainLoop()
    