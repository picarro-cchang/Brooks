import wx
from DemoCodeEditor import DemoCodeEditor
import wx.stc as stc 
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
        try:
            fp = open(self.absPath,"r")
        except:
            return
        try:
            for typ,st,(srow,scol),(erow,ecol),line in tokenize.generate_tokens(self.readline(fp)):
                if typ == tokenize.STRING:
                    st = evalStringLit(st)
                    stl = st.lower()
                    if stl.endswith('.py') or stl.endswith('.ini'):
                        self.addChild(st)
        finally:
            if fp: fp.close()
            
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
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED,self.onSelChanged,self.treeCtrlFiles)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED,self.onEditorSelected,self.notebookEditors)
        self.notebookEditorPanels = []
        self.notebookEditorTextCtrls = []
        self.notebookEditorFileAbsPaths = []
        self.treeNodesByFileAbsPath = {}
        self.whichEditor = -1
        self.finddlg = None
        self.finddata = wx.FindReplaceData()
        self.finddata.SetFlags(wx.FR_DOWN)
        self.Bind(wx.EVT_FIND, self.onFind)
        self.Bind(wx.EVT_FIND_NEXT, self.onFindNext)
        self.Bind(wx.EVT_FIND_CLOSE, self.onFindClose)
        self.Bind(wx.EVT_FIND_REPLACE, self.onFindReplace)
        self.Bind(wx.EVT_FIND_REPLACE_ALL, self.onFindReplaceAll)
        
    def run(self,rootNode):
        self.treeRoot = self.treeCtrlFiles.AddRoot(rootNode.fileName)
        if rootNode.absPath not in self.treeNodesByFileAbsPath:
            self.treeNodesByFileAbsPath[rootNode.absPath] = []
        self.treeNodesByFileAbsPath[rootNode.absPath].append(self.treeRoot)
        rootNode.findChildren()
        self.treeCtrlFiles.SetItemHasChildren(self.treeRoot,True)
        self.treeCtrlFiles.SetItemPyData(self.treeRoot,rootNode)

    def traverse(self, traverseroot, function):
        child, cookie = self.treeCtrlFiles.GetFirstChild(traverseroot)
        while child:
            function(child)
            if self.treeCtrlFiles.ItemHasChildren(child):
                self.traverse(child, function)
            child,cookie = self.treeCtrlFiles.GetNextChild(traverseroot,cookie)
        
    def removeChildren(self,treeNode):
        self.treeCtrlFiles.DeleteChildren(treeNode)
        allNodes = []
        def collect(node):
            allNodes.append(node)
        self.traverse(self.treeRoot,collect)
        for p in self.treeNodesByFileAbsPath:
            self.treeNodesByFileAbsPath[p] = [n for n in self.treeNodesByFileAbsPath[p] if n in allNodes]
        
    def onItemCollapsed(self,evt):
        self.removeChildren(evt.GetItem())
    
    def onItemExpanding(self,evt):
        self.addTreeNodes(evt.GetItem())
        
    def onSelChanged(self,evt):
        selNode = self.treeCtrlFiles.GetItemPyData(evt.GetItem())
        # If node is not currently open, open in a new tab
        for i,n in enumerate(self.notebookEditorFileAbsPaths):
            if n == selNode.absPath: # Found the correct panel
                break
        else:
            i = len(self.notebookEditorFileAbsPaths)
            self.notebookEditorFileAbsPaths.append(selNode.absPath)
            # Create a new editor panel with a text control within a sizer
            p = wx.Panel(self.notebookEditors, -1)
            self.notebookEditorPanels.append(p)
            # t = wx.TextCtrl(p, -1, "", style=wx.TE_MULTILINE)
            
            #t = stc.StyledTextCtrl(p,-1)
            #t.StyleSetSpec(stc.STC_STYLE_DEFAULT, "size:%d,face:%s" % (10, 'Courier New'))
            # line numbers in the margin
            #t.SetMarginType(0, stc.STC_MARGIN_NUMBER)
            #t.SetMarginWidth(0, 30)
            #t.SetMarginWidth(1, 0)
            #t.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:%d,face:%s" % (8, 'Courier New'))

            ext = os.path.splitext(selNode.absPath)[1]
            t = DemoCodeEditor(p)
            if ext.lower() in ['.ini','.mode']:
                t.SetLexer(stc.STC_LEX_PROPERTIES)
            #t = PythonSTC(p,-1)
            t.RegisterModifiedEvent(self.onEditChange)
            t.RegisterKeyPressedHandler(self.onKeyPressed)
            self.notebookEditorTextCtrls.append(t)
            sizerEditor = wx.BoxSizer(wx.HORIZONTAL)
            sizerEditor.Add(t, 1, wx.EXPAND, 0)
            p.SetSizer(sizerEditor)
            self.notebookEditors.AddPage(p, selNode.fileName)

            # Read the contents of the file into the new editor panel
            f = None
            try:
                f = open(selNode.absPath,"r")
                t.SetText(f.read())
                t.SetSavePoint()
                t.EmptyUndoBuffer()
            except:
                print "Cannot find file"
            finally:
                if f: f.close()
        # Set the focus to the i'th tab
        self.notebookEditors.SetSelection(i)
        self.treeCtrlFiles.SetFocus()
        
    def addTreeNodes(self,parentItem):
        top = self.treeCtrlFiles.GetItemPyData(parentItem)
        for c in top.children:
            c.findChildren()
            node = self.treeCtrlFiles.AppendItem(parentItem,c.fileName)
            if c.absPath not in self.treeNodesByFileAbsPath:
                self.treeNodesByFileAbsPath[c.absPath] = []
            self.treeNodesByFileAbsPath[c.absPath].append(node)
            self.treeCtrlFiles.SetItemPyData(node,c)
            self.treeCtrlFiles.SetItemHasChildren(node,bool(c.children))
    
    def onEditorSelected(self,evt):
        # Place absolute path name in status bar
        self.whichEditor = evt.GetSelection()
        p = self.notebookEditorFileAbsPaths[self.whichEditor]
        t = self.notebookEditorTextCtrls[self.whichEditor]
        self.frameMainStatusbar.SetStatusText(p, 2)
        mod = t.GetModify()
        self.frameMainStatusbar.SetStatusText("Mod" if mod else "",1)
    
    def onEditChange(self,evt):
        mod = evt.GetEventObject().GetModify()
        self.frameMainStatusbar.SetStatusText("Mod" if mod else "",1)
        
    def onHelpFind(self,evt):
        if self.finddlg != None:
            return
        t = self.notebookEditorTextCtrls[self.whichEditor]
        t.SetSelectionEnd(t.GetAnchor())
        self.finddlg = wx.FindReplaceDialog(self, self.finddata, "Find")
        self.finddlg.Show(True)

    def onHelpReplace(self,evt):
        if self.finddlg != None:
            return
        t = self.notebookEditorTextCtrls[self.whichEditor]
        t.SetSelectionEnd(t.GetAnchor())
        self.finddlg = wx.FindReplaceDialog(self, self.finddata, "Replace", wx.FR_REPLACEDIALOG|wx.FR_NOUPDOWN)
        self.finddlg.Show(True)
        
    def cvtFlags(self,frFlags):
        flags = 0
        flags += stc.STC_FIND_WHOLEWORD if 0 != frFlags & wx.FR_WHOLEWORD else 0
        flags += stc.STC_FIND_MATCHCASE if 0 != frFlags & wx.FR_MATCHCASE else 0
        return flags
        
    def onFind(self,evt):
        self.onFindNext(evt)
            
    def onFindNext(self,evt):
        t = self.notebookEditorTextCtrls[self.whichEditor]
        s = self.finddata.GetFindString()
        f = self.finddata.GetFlags()
        cf = self.cvtFlags(f)
        ss = t.GetSelectionStart()
        se = t.GetSelectionEnd()
        if f & wx.FR_DOWN:
            t.SetSelectionStart(t.GetSelectionEnd())
            t.SearchAnchor()
            loc = t.SearchNext(cf,s)
        else:
            t.SearchAnchor()
            loc = t.SearchPrev(cf,s)
        if loc>=0:
            t.SetSelection(loc,loc+len(s))
        else:
            t.SetSelection(ss,se)
            evt.GetDialog().Hide()
            dlg = wx.MessageDialog(self, 'String not found in specified direction',
                          'Find String Not Found',
                          wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            evt.GetDialog().Show()
        t.EnsureCaretVisible()
        
    def onFindReplace(self,evt):
        t = self.notebookEditorTextCtrls[self.whichEditor]
        s = self.finddata.GetFindString()
        r = self.finddata.GetReplaceString()
        f = self.finddata.GetFlags()
        if t.GetSelectedText() == s if (0 != (f & wx.FR_MATCHCASE)) else t.GetSelectedText().lower() == s.lower():
            t.ReplaceSelection(r)            
        self.onFindNext(evt)
        
    def onFindReplaceAll(self,evt):
        t = self.notebookEditorTextCtrls[self.whichEditor]
        s = self.finddata.GetFindString()
        r = self.finddata.GetReplaceString()
        f = self.finddata.GetFlags()
        cf = self.cvtFlags(f)
        ss = t.GetSelectionStart()
        se = t.GetSelectionEnd()
        nReplace = 0
        while True:
            if t.GetSelectedText() == s if (0 != (f & wx.FR_MATCHCASE)) else t.GetSelectedText().lower() == s.lower():
                ss = t.GetSelectionStart()
                t.ReplaceSelection(r)            
                se = t.GetSelectionEnd()
                nReplace += 1
            t.SetSelectionStart(t.GetSelectionEnd())
            t.SearchAnchor()
            loc = t.SearchNext(cf,s)
            if loc>=0:
                t.SetSelection(loc,loc+len(s))
            else:
                break
        t.SetSelection(ss,se)
        t.EnsureCaretVisible()
        evt.GetDialog().Hide()
        dlg = wx.MessageDialog(self, '%d replacements made' % nReplace,
                      'Result of Replace All', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        evt.GetDialog().Show()
            
    def onFindClose(self,evt):
        evt.GetDialog().Destroy()
        self.finddlg = None
    
    def onSave(self,evt):
        t = self.notebookEditorTextCtrls[self.whichEditor]
        mod = t.GetModify()
        p = self.notebookEditorFileAbsPaths[self.whichEditor]
        if mod:
            f = None
            try:
                f = open(p,"w")
                f.write(t.GetText())
                t.SetSavePoint()
                t.EmptyUndoBuffer()
            finally:
                if f: f.close()
            # Update the tree to reflect the changes in the file
            #  by collapsing all the nodes associated with this path
            for n in self.treeNodesByFileAbsPath[p]:
                self.treeCtrlFiles.Collapse(n)
                # Find the new children of the updated node
                configNode = self.treeCtrlFiles.GetItemPyData(n)
                configNode.findChildren()
                self.treeCtrlFiles.SetItemHasChildren(n,bool(configNode.children))
        mod = t.GetModify()
        self.frameMainStatusbar.SetStatusText("Mod" if mod else "",1)

    def onSaveAs(self,evt):
        t = self.notebookEditorTextCtrls[self.whichEditor]
        ap = self.notebookEditorFileAbsPaths[self.whichEditor]
        p,f = os.path.split(ap)
        d,e = os.path.splitext(ap)
        
        dlg = wx.FileDialog(self,"Save file as",p,f,"*%s"%e,wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetFilename()
            dname = dlg.GetDirectory()
            name = os.path.join(dname,fname)
        
            f = None
            try:
                try:
                    f = open(name,"w")
                    f.write(t.GetText())
                except:
                    dlg.Destroy()
                    dlg = wx.MessageDialog(self, 'Error writing %s' % name,
                                  'Error writing file',
                                  wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return
                t.SetSavePoint()
                t.EmptyUndoBuffer()
            finally:
                if f: f.close()
                
            self.notebookEditors.SetPageText(self.whichEditor, fname)

            # Update the tree to reflect the changes in the file
            #  by collapsing all the nodes associated with this path
            p = os.path.abspath(name)
            self.notebookEditorFileAbsPaths[self.whichEditor] = p
            if p in self.treeNodesByFileAbsPath:
                for n in self.treeNodesByFileAbsPath[p]:
                    self.treeCtrlFiles.Collapse(n)
                    # Find the new children of the updated node
                    configNode = self.treeCtrlFiles.GetItemPyData(n)
                    configNode.findChildren()
                    self.treeCtrlFiles.SetItemHasChildren(n,bool(configNode.children))
            mod = t.GetModify()
            self.frameMainStatusbar.SetStatusText("Mod" if mod else "",1)
            self.frameMainStatusbar.SetStatusText(p, 2)
        dlg.Destroy()        
    
    def onSaveAll(self,evt):
        # Iterate through files in editors and save any modified files
        for t,p in zip(self.notebookEditorTextCtrls,self.notebookEditorFileAbsPaths):
            mod = t.GetModify()
            if mod:
                f = None
                try:
                    f = open(p,"w")
                    f.write(t.GetText())
                    t.SetSavePoint()
                    t.EmptyUndoBuffer()
                finally:
                    if f: f.close()
                # Update the tree to reflect the changes in the file
                #  by collapsing all the nodes associated with this path
                for n in self.treeNodesByFileAbsPath[p]:
                    self.treeCtrlFiles.Collapse(n)
                    # Find the new children of the updated node
                    configNode = self.treeCtrlFiles.GetItemPyData(n)
                    configNode.findChildren()
                    self.treeCtrlFiles.SetItemHasChildren(n,bool(configNode.children))
        t = self.notebookEditorTextCtrls[self.whichEditor]
        mod = t.GetModify()
        self.frameMainStatusbar.SetStatusText("Mod" if mod else "",1)
    
    def onKeyPressed(self,evt):
        key = evt.GetKeyCode()
        if key == 70 and evt.ControlDown():
            self.onHelpFind(evt)
        if key == 72 and evt.ControlDown():
            self.onHelpReplace(evt)
        if key == 83 and evt.ControlDown():
            self.onSave(evt)
        else:    
            evt.Skip()
            
    def onExit(self,evt):
        # Iterate through files in editors and offer to save any modified files
        for w,(t,p) in enumerate(zip(self.notebookEditorTextCtrls,self.notebookEditorFileAbsPaths)):
            mod = t.GetModify()
            if mod:
                self.notebookEditors.SetSelection(w)
                dlg = wx.MessageDialog(self, '%s has not been modified. Save file?' % p,
                              'File Modified',
                              wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION)
                result = dlg.ShowModal()
                dlg.Destroy()
                if result == wx.ID_YES:
                    self.whichEditor = w
                    self.onSave(evt)
                elif result == wx.ID_CANCEL:
                    return
        self.Close()        
       
if __name__ == "__main__":
    appConfigManager = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frameMain = ConfigManager(None, -1, "")
    appConfigManager.SetTopWindow(frameMain)
    dlg = wx.FileDialog(None,"Select Supervisor Configuration File","C:/Picarro/G2000/AppConfig/Config/Supervisor","","*.ini",wx.OPEN)
    if dlg.ShowModal() == wx.ID_OK:
        fname = dlg.GetFilename()
        dname = dlg.GetDirectory()
        superConfig = os.path.join(dname,fname)
        # Use heuristic to determine directory of supervisor
        ini = ConfigObj(superConfig)
        npy, nexe = 0, 0
        for s in ini:
            try:
                if "Executable" in ini[s]:
                    n,e = os.path.splitext(ini[s]["Executable"])
                    if e.lower() == ".py": npy += 1
                    if e.lower() == ".exe": nexe += 1
            except:
                continue
        rootDir = os.path.join(dname,"../../..")        
        childBasePath = os.path.join(rootDir,"HostExe") if nexe>npy else os.path.join(rootDir,"Host/Supervisor")
        r = SupervisorConfigNode(os.path.join(dname,fname),childBasePath=childBasePath)
        frameMain.run(r)
        frameMain.Show()
        appConfigManager.MainLoop()
    dlg.Destroy()
    