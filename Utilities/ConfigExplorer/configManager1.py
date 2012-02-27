import wx
import os
import re
import tokenize
from configobj import ConfigObj
from ConfigManagerGui import ConfigManagerGui
import compiler

def evalStringLit(s):
    return compiler.parse(s,mode='eval').node.value
    
def getMatches(fName,matchRe,matchOpt=re.I):
    f = None
    f = open(fName,'r')
    matches = []
    try:
        for str in f:
            if str.strip().startswith("#"): continue
            patt = re.compile(matchRe,matchOpt)
            matches += patt.findall(str)
        return matches
    finally:
        if f: f.close()
        
def ConfigNodeFactory(filename,**kwds):
    """Construct an instance of a subclass ConfigNode for the specified file. The node 
       type may be specified as the non-None keyword argument nodeClass. Otherwise, it 
       is inferred from the file extension"""
       
    name,ext = os.path.splitext(filename)
    if 'nodeClass' in kwds: nodeClass = kwds['nodeClass']
    if nodeClass is not None:
        return nodeClass(filename,**kwds)
    else:
        if ext.lower() == '.ini': return DefIniConfigNode(filename,**kwds)
        elif ext.lower() == '.sch': return DefSchConfigNode(filename,**kwds)
        elif ext.lower() == '.py': return DefPyConfigNode(filename,**kwds)
        elif ext.lower() == '.mode': return DefModeConfigNode(filename,**kwds)

#
# For each node of the tree, we have the following structure
#
# Full path of file (configuration, script, scheme, mode etc.)
# List of positions in file containing references to children files
# List of children
# Override of base path for children files
# Method for obtaining children of this file (e.g. extensions of children, etc)
#

class ConfigNode(object):
    def __init__(self,fileName,**kwargs):
        """Construct a ConfigNode for the specified file. The parent of
           the node is passed by keyword, and the base path for the children
           of the node be changed from the file path by using the childBasePath
           keyword"""
        self.absPath = os.path.abspath(fileName)
        self.basePath,n = os.path.split(self.absPath)
        self.fileName = n
        self.childRefs = []
        self.children = []
        self.parent = kwargs.get('parent',None)
        childBasePath = kwargs.get('childBasePath',None)
        self.childBasePath = childBasePath if (childBasePath is not None) else self.basePath
        
    def addChild(self,p):
        f = os.path.join(self.childBasePath,p)
        n = ConfigNodeFactory(f,parent=self,
            childBasePath=self.getChildBasePath(),
            nodeClass=self.nodeClass(f))
        for c in self.children:
            if n.absPath == c.absPath: break
        else:
            self.children.append(n)
        
    def findChildren(self):
        print "Should be implemented in a subclass"
    
    def nodeClass(self,filename):
        return None

    def getChildBasePath(self):
        return None
        
class DefIniConfigNode(ConfigNode):
    # Default INI handler which looks for keys which have .ini, .py or .sch extensions
    
    def findChildren(self):
        self.children = []
        patt = re.compile(*self.pattRe())
        ini = ConfigObj(self.absPath)
        for sec in ini:
            options = ini[sec]
            if isinstance(options,str): continue
            for opt in options:
                val = ini[sec][opt]
                if isinstance(val,str):
                    for p in patt.findall(ini[sec][opt]):
                        self.addChild(p)
                    for p in self.extraChildren(sec,opt,ini[sec][opt]):
                        self.addChild(p)
                    
    def pattRe(self):
        return r".*?\.ini|.*?\.py|.*?\.sch",re.I
        
    def extraChildren(self,sec,opt,value):
        return []
        
class MeasSystemIniConfigNode(DefIniConfigNode):
    def pattRe(self):
        return r".*?\.ini|.*?\.py|.*?\.sch|.*?\.mode",re.I
        
class DataManagerIniConfigNode(DefIniConfigNode):
    def pattRe(self):
        return r".*?\.ini|.*?\.py|.*?\.sch|.*?\.mode",re.I
    
class FitterIniConfigNode(DefIniConfigNode):
    def nodeClass(self,filename):
        return FitterScriptConfigNode
    def getChildBasePath(self):
        return self.basePath

class SampleManagerIniConfigNode(DefIniConfigNode):
    def extraChildren(self,sec,opt,value):
        if opt.upper() == "SCRIPT_FILENAME":
            return [value.strip() + '.py']
        else:
            return []
            
class DefPyConfigNode(ConfigNode):
    # Default PY handler 
    def findChildren(self):
        self.children = []
        fp = None
        fp = open(self.absPath,"r")
        try:
            for typ,st,(srow,scol),(erow,ecol),line in tokenize.generate_tokens(self.readline(fp)):
                if typ == tokenize.STRING:
                    st = evalStringLit(st)
                    stl = st.lower()
                    if stl.endswith('.py') or stl.endswith('.ini'):
                        self.addChild(st)
        finally:
            fp.close()
            
    def readline(self,fp):
        return fp.readline

class FitterScriptConfigNode(DefPyConfigNode):
    pass
    
class DefSchConfigNode(DefPyConfigNode):
    # Default SCH handler 
    def readline(self,fp):
        def linesBetweenMarkers(marker):
            emitting = False
            for line in fp:
                if line.startswith(marker):
                    emitting = not emitting
                else:
                    if emitting: yield line
        g = linesBetweenMarkers("$$$")
        def readBetweenMarkers():
            try:
                return g.next()
            except StopIteration:
                return ""
        return readBetweenMarkers
        
class DefModeConfigNode(DefIniConfigNode):
    # Default MODE handler 
    def findChildren(self):
        DefIniConfigNode.findChildren(self)
        ini = ConfigObj(self.absPath)
        if 'AVAILABLE_MODES' in ini:
            modeSec = ini['AVAILABLE_MODES']
            nModes = int(modeSec['ModeCount'])
            for i in range(nModes):
                modeName = modeSec['Mode_%d' % (i+1,)].strip()
                f = os.path.join(self.childBasePath,modeName+'.mode')
                n = ConfigNodeFactory(f,parent=self,
                    childBasePath=self.getChildBasePath(),
                    nodeClass=self.nodeClass(f))
                for c in self.children:
                    if n.absPath == c.absPath: break
                else:
                    self.children.append(n)
        
    def pattRe(self):
        return r".*?\.py|.*?\.sch",re.I

class SupervisorConfigNode(ConfigNode):
    # Handles supervisor ini files which have an [Applications] section
    #  which lists the active applications. We only consider the sections
    #  for these active applications and look at the LaunchArgs options
    def findChildren(self):
        self.children = []
        patt = re.compile(r"\S*?\.ini",re.I)
        ini = ConfigObj(self.absPath)
        if 'Applications' in ini:
            for a in ini['Applications']:
                if 'LaunchArgs' in ini[a]:
                    s = ini[a]['LaunchArgs']
                    e = ini[a]['Executable']
                    for p in patt.findall(s):
                        f = os.path.join(self.childBasePath,p)
                        n = ConfigNodeFactory(f,parent=self,
                        childBasePath=self.getChildBasePath(),
                        nodeClass=self.nodeClass(e))
                        for c in self.children:
                            if n.absPath == c.absPath: break
                        else:
                            self.children.append(n)
                            
    def nodeClass(self,execName):
        if execName.lower().find('fitter')>=0: return FitterIniConfigNode
        elif execName.lower().find('meassystem')>=0: return MeasSystemIniConfigNode
        elif execName.lower().find('datamanager')>=0: return DataManagerIniConfigNode
        elif execName.lower().find('samplemanager')>=0: return SampleManagerIniConfigNode
        else: return DefIniConfigNode
        
class ConfigManager(ConfigManagerGui):
    def __init__(self,*a,**k):
        ConfigManagerGui.__init__(self,*a,**k)
        # self.Bind(wx.EVT_TREE_ITEM_EXPANDED,self.onItemExpanded,self.treeCtrlFiles)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED,self.onItemCollapsed,self.treeCtrlFiles)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING,self.onItemExpanding,self.treeCtrlFiles)
        self.Bind(wx.EVT_TREE_SEL_CHANGED,self.onSelChanged,self.treeCtrlFiles)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED,self.onEditorSelected,self.notebookEditors)
        self.notebookEditorPanels = [self.notebookEditor1]
        self.notebookEditorTextCtrls = [self.textCtrlEditor1]
        self.notebookEditorNodes = [None]   # One ConfigNode per editor (most recent)
        
    def run(self,rootNode):
        r = self.treeCtrlFiles.AddRoot(rootNode.fileName)
        rootNode.findChildren()
        self.treeCtrlFiles.SetItemHasChildren(r,True)
        self.treeCtrlFiles.SetItemPyData(r,rootNode)
    
    def onItemCollapsed(self,evt):
        self.treeCtrlFiles.DeleteChildren(evt.GetItem())
    
    def onItemExpanding(self,evt):
        self.addTreeNodes(evt.GetItem())
        
    def onSelChanged(self,evt):
        selNode = self.treeCtrlFiles.GetItemPyData(evt.GetItem())
        # If node is not currently open, open in a new tab
        for i,n in enumerate(self.notebookEditorNodes):
            if n and n.absPath == selNode.absPath: # Found the correct panel
                self.notebookEditorNodes[i] = selNode
                break
        else:
            i = len(self.notebookEditorNodes)
            self.notebookEditorNodes.append(selNode)
            # Create a new editor panel with a text control within a sizer
            p = wx.Panel(self.notebookEditors, -1)
            self.notebookEditorPanels.append(p)
            t = wx.TextCtrl(p, -1, "", style=wx.TE_MULTILINE)
            self.notebookEditorTextCtrls.append(t)
            sizerEditor = wx.BoxSizer(wx.HORIZONTAL)
            sizerEditor.Add(t, 1, wx.EXPAND, 0)
            p.SetSizer(sizerEditor)
            self.notebookEditors.AddPage(p, selNode.fileName)

            # Read the contents of the file into the new editor panel
            f = None
            try:
                f = open(selNode.absPath,"r")
                t.SetValue(f.read())
            except:
                print "Cannot find file"
            finally:
                if f: f.close()
        # Set the focus to the i'th tab
        self.notebookEditors.SetSelection(i)
        
    def addTreeNodes(self,parentItem):
        top = self.treeCtrlFiles.GetItemPyData(parentItem)
        for c in top.children:
            c.findChildren()
            node = self.treeCtrlFiles.AppendItem(parentItem,c.fileName)
            self.treeCtrlFiles.SetItemPyData(node,c)
            self.treeCtrlFiles.SetItemHasChildren(node,bool(c.children))
    
    def onEditorSelected(self,evt):
        # Place absolute path name in status bar
        n = self.notebookEditorNodes[evt.GetSelection()]
        self.frameMainStatusbar.SetStatusText(n.absPath, 0)
        
        
if __name__ == "__main__":
    appConfigManager = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frameMain = ConfigManager(None, -1, "")
    appConfigManager.SetTopWindow(frameMain)
    r = SupervisorConfigNode(r"C:\Picarro\G2000\AppConfig\Config\Supervisor\supervisorEXE_CFADS_mobile.ini",
                             childBasePath=r"C:\Picarro\G2000\HostExe")
    frameMain.run(r)
    frameMain.Show()
    appConfigManager.MainLoop()
    