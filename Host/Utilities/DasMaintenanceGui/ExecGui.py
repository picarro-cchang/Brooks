# File Name  : ExecGui.py
# Description: Simple task execution GUI
#
# File History:
# 06-09-12 ytsai   Created file
# 08-09-18  alex  Replaced ConfigParser with CustomConfigObj

import os, sys
import wx
import wx.wizard as wiz
import wx.lib.masked as masked
import time
import getopt
from CustomConfigObj import CustomConfigObj
import zipfile
import DiagTasks

from wizardhelper import WizardTitledLogoPage
from ExecTask import ExecTask, ExecPage

# Task field names in ini-file.
INIFILE_TASK_SECTION            = 'task'
INIFILE_TASK_TITLE_FIELD        = '_title'
INIFILE_TASK_DESCRIPTION_FIELD  = '_description'
INIFILE_TASK_MODULE_FIELD       = '_module'
INIFILE_TASK_CLASS_FIELD        = '_class'
INIFILE_TASK_EXECUTE_FLAG_FIELD = '_execute'
INIFILE_TASK_VISIBLE_FLAG_FIELD = '_visible'
INIFILE_TASK_ARG_FIELD          = 'arg'

# Return result fields from task execution
TASK_STATUS_FIELD               = '_status'
TASK_RESULTS_FIELD              = '_results'
TASK_FILES_FIELD                = '_files'
TASK_ERROR_FIELD                = '_error'

INPUT_BACKGROUND_COLOR          = 'WHITE'
TEXT_BACKGROUND_COLOR           = 'TURQUOISE'
LISTBOX_BACKGROUND_COLOR        = 'TURQUOISE'

DEFAULT_INI                     = 'Diag.ini'

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

if os.path.split(AppPath)[0] not in sys.path: sys.path.append(os.path.split(AppPath)[0])

# For saving status logs
globalLog   = ''
globalLogFp = None

def LogMsg(args):
    """ Log message and print to file"""
    print(args)
    global globalLog
    globalLog = globalLog + str(args)
    if globalLogFp <> None and globalLogFp >= 0 :
        globalLogFp.write(args)
    try:
        wx.Yield()
    except:
        pass

class ExecStartPage( WizardTitledLogoPage ):
    """ Task Start Page """
    def __init__(self, parent, title, taskList, globals, pages ):
        WizardTitledLogoPage.__init__(self, parent, title)

        self.parent = parent
        self.taskList = taskList
        self.globals = globals
        self.pages = pages

        self.sizer.Add( (1,8) )
        prompt = self.globals['tasklistprompt']
        text = wx.StaticText( self, -1, prompt )
        self.sizer.Add( text )
        self.sizer.Add( (1,1) )

        self.listbox = wx.CheckListBox( self, -1, size=(100, 80) )
        self.listbox.SetBackgroundColour(wx.NamedColour(LISTBOX_BACKGROUND_COLOR))
        self.sizer.Add( self.listbox, 1, wx.EXPAND|wx.ALL, 3)
        selected = 0
        visible  = 0

        # fill listbox
        for i in range( len(self.taskList) ):
            try:
                self.listbox.Append( "%d.  %s" % (i+1,self.taskList[i]._title) )
                self.listbox.Check( i, self.taskList[i]._execute )
                visible += 1
                if self.taskList[i]._execute:
                    selected+=1
            except:
                LogMsg ("Task missing parameters? %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
                self.taskList[i]._execute = False

        self.tasksText = wx.StaticText( self, -1, "Total tasks: %d (%d)   " % (selected,visible) )
        self.sizer.Add( (1,5) )
        self.sizer.Add( self.tasksText, 0, wx.ALIGN_RIGHT )
        self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, self.listbox )

        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnWizPageChanging)
        self.Bind(wiz.EVT_WIZARD_CANCEL, self.OnWizCancel)

    def OnWizPageChanging(self, evt):
        if evt.GetDirection():
            pass

    def EvtCheckListBox(self, event):

        # update execute list
        selected = 0
        for i in range( len(self.taskList) ):
            self.taskList[i]._execute=self.listbox.IsChecked(i)
            if self.listbox.IsChecked(i):
                selected += 1
        self.tasksText.SetLabel("Total tasks: %d (%d)   " % (selected,len(self.taskList)))

        # update page links
        prevPage = None
        for page in self.pages:
            if hasattr(page,'_execute')==False:
                linkPage = True
            elif page._execute:
                linkPage = True
            else:
                linkPage = False

            if linkPage:
                if ( prevPage != None ):
                    page.SetPrev( prevPage )
                    prevPage.SetNext( page )
                prevPage = page

    def OnWizCancel(self, evt):
        LogMsg("Cancelled.")
        if globalLogFp <> None:
            globalLogFp.close()


class ExecPage( WizardTitledLogoPage ):
    """ Page for executing tasks. """
    def __init__(self, parent, title, taskList, globals ):
        WizardTitledLogoPage.__init__(self, parent, title )

        self.Running = False
        self.taskList = taskList
        self.runList = []
        self.globals = globals

        self.taskText = wx.StaticText( self, -1, "")
        self.sizer.Add( self.taskText )
        self.sizer.Add( (1,5) )

        self.status = wx.TextCtrl(self, -1, "", (100,200),style=wx.TE_MULTILINE|wx.TE_READONLY )
        self.status.SetBackgroundColour(wx.NamedColour(TEXT_BACKGROUND_COLOR))
        self.sizer.Add( self.status, 1, wx.EXPAND | wx.ALL | wx.ALIGN_TOP , border=1 )
        self.sizer.Add( (1,5) )

        self.tgauge = wx.Gauge(self, -1, 20, (1, 1), (300, 18), wx.GA_HORIZONTAL) # wx.GA_SMOOTH
        self.sizer.Add( self.tgauge, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, 0 )

        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnWizPageChanged)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnWizPageChanging)
        self.Bind(wiz.EVT_WIZARD_CANCEL, self.OnWizCancel)

    def PrintMsg(self,newText):
        last = self.status.GetLastPosition()
        self.status.SetInsertionPoint(last)
        self.status.WriteText(newText)
        LogMsg(newText)

    def OnWizPageChanged(self, evt):
        if evt.GetDirection() == False:
            if self.Running==True:
                evt.Veto()
            return
        self.Running = True
        self.Show()
        self.OnRun(evt)
        self.Running = False

    def OnRun(self,evt):
        count = len(self.taskList)

        # Execute tasks
        for taskIndex in self.runList:
            task = self.taskList[taskIndex]

            # TODO: redirect stdout
            task.printMsg = self.PrintMsg

            if task._execute:

                self.status.Clear()
                # Run task
                try:
                    self.taskText.SetLabel("Please wait. Running - %s. " % ( task._title ))
                    self.PrintMsg("\n%d. %s\n" % ( taskIndex+1, task._title ))
                    task._error = 'Okay'
                    gaugeRange = 10
                    self.tgauge.SetRange( gaugeRange )
                    self.tgauge.SetValue( 0 )
                    task._status = task.Run( globals=self.globals, gauge=self.tgauge, *task._pargs, **task._nargs )
                    self.tgauge.SetValue( gaugeRange )
                    if task._status == True:
                        self.PrintMsg ("Done.\n")
                    else:
                        self.PrintMsg("\n%s: Failed\n" % task._title )

                except:
                    error ="\nTask %s: Execution %s %s\n" % (task._title, sys.exc_info()[0], sys.exc_info()[1])
                    task._status = False
                    task._error  = error
                    self.PrintMsg ( error )

                # zip results file
                try:
                    if self.globals['archiveFp']!= None and len(task._filelist):
                        self.PrintMsg("Please wait, archiving results")
                        filecount = 0
                        self.tgauge.SetRange( len(task._filelist) )
                        for file in task._filelist:
                            if os.path.exists( file ):
                                # check zip file size, if size exceeds max, add files in new zipfile.
                                possibleSize = os.path.getsize( self.globals['archiveFilename'] )+os.path.getsize(file)
                                if self.globals['archiveSplit'] and possibleSize > self.globals['archiveSplitSize']:
                                    self.globals['archiveFp'].close()
                                    prefix = self.globals['archiveFilename'][0:-4].split('-')
                                    self.globals['archiveIndex'] +=1
                                    self.globals['archiveFilename'] = prefix[0] + '-' + str(self.globals['archiveIndex']) + '.zip'
                                    self.globals['archiveFp'] = zipfile.ZipFile( self.globals['archiveFilename'], "w", zipfile.ZIP_DEFLATED)
                                self.globals['archiveFp'].write(file)
                                filecount+=1
                            else:
                                self.PrintMsg("Unable to find %s.\n" % file)
                            self.tgauge.SetValue( filecount )
                        self.PrintMsg("\nArchived %d files (%d).\n" % (filecount, len(task._filelist)) )
                        if eval( self.globals['deletefiles'] ) == True:
                            for file in task._dellist:
                                os.remove(file)
                except:
                    error ="\nTask %s: Archive %s %s\n" % (task._title, sys.exc_info()[0], sys.exc_info()[1])
                    task._status = False
                    task._error  = error
                    self.PrintMsg ( error )

                if eval(self.globals['abortonerror']) == True and ret == False:
                    break

            if self.Running==False:
                break

        self.PrintMsg ("\nTasks Done.\n" )
        self.taskText.SetLabel("Tasks Completed!")

    def OnWizCancel(self, evt):
        LogMsg("Cancelled.")
        if self.Running == True:
            self.Running = False
            evt.Veto()

    def OnWizPageChanging(self, evt):
        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
        page = evt.GetPage()
        if self.Running == True:
            evt.Veto()

    def AddTaskList ( self, list ):
        self.runList = list

class ExecEndPage(WizardTitledLogoPage):
    def __init__(self, parent, title, taskList, globals ):
        WizardTitledLogoPage.__init__(self, parent, title)

        self.taskList = taskList

        text = wx.StaticText( self, -1, "Tasks completed.")
        self.sizer.Add( text )
        self.sizer.Add( (1,5) )

        self.listbox = ExecListCtrl( self, taskList )
        self.listbox.SetBackgroundColour(wx.NamedColour(LISTBOX_BACKGROUND_COLOR))
        self.sizer.Add( self.listbox, 1, wx.EXPAND|wx.ALL| wx.ALIGN_TOP, border=1 )
        dict = { 'title' : ['#','Name','Result'], 'columnSize' : [40,170,200] }
        self.listbox.Setup( dict )

        self.status = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY, size=(100,50) )
        self.status.SetBackgroundColour(wx.NamedColour(TEXT_BACKGROUND_COLOR))
        self.sizer.Add( self.status, 0, wx.EXPAND | wx.ALL, 1 )

        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnWizPageChanged)

    def OnWizPageChanged(self, evt):
        if evt.GetDirection() == False:
            return

        self.listbox.UpdateTable(self.taskList)

        self.status.WriteText(globalLog)
        self.status.ShowPosition(self.status.GetLastPosition ())

class ExecListCtrl( wx.ListCtrl ):
    def __init__( self, parent, table ):
        wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.table = table

        self.ilEventIcons = wx.ImageList(16, 16)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)

        self.IconIndex_Error = myIL.Add(wx.Bitmap('Cancel.ico', wx.BITMAP_TYPE_ICO))
        self.IconIndex_Check = myIL.Add(wx.Bitmap('Check.ico', wx.BITMAP_TYPE_ICO))
        self.IconIndex_Question = -1 #myIL.Add(wx.Bitmap('MSGBOX02.ICO', wx.BITMAP_TYPE_ICO))

    def Setup( self, dict ):
        """ Input: Dictionary with keys (Title, Width,...), contain list of values. """

        key = 'title'
        if dict.has_key( key ) == False:
            logMsg ("ExecListCtrl: missing dict parameter - %r\n" % key)
            return
        count =  len(dict[key])

        for i in range(count):
            self.InsertColumn( i, dict['title'][i] )

            if dict.has_key( 'columnSize' ) == True:
                self.SetColumnWidth(i, dict['columnSize'][i] )

        self.SetItemCount(len(self.table))
        self.Refresh()

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex

    def GetColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnGetItemText(self, item, col):
        if item > len(self.table):
            return ""
        try:
            if col == 0: return item+1
            elif col == 1:
                text = self.table[item]._title
                text = text.strip('\n')
            elif col == 2:
                text = self.table[item]._error
                text = text.strip('\n')
        except:
            return ""
        return text

    def OnGetItemImage(self, item):
        if self.table[item]._execute == False:
            return -1
        elif self.table[item]._status == True:
            return self.IconIndex_Check
        elif self.table[item]._status == False:
            return self.IconIndex_Error

    def OnGetItemAttr(self, item):
        return None

    def UpdateTable(self,table):
        self.table=table

class ExecApp(wx.PySimpleApp):
    """ Main App for ExecGui """

    def OnInit(self):
        self.globals = {}
        return True

    def LoadConfig(self,filename):
        """ Load main config file """        
        try:
            self.config = CustomConfigObj(filename)
        except:
            LogMsg ("Unable to open config. %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
            return False
        return True

    def Run(self, filename):

        if self.LoadConfig( filename ) == False:
            wx.MessageBox("Unable to load config", filename )
            return False

        # Open global log file for writing status
        global globalLogFp
        try:
            LogFlag   = eval(self.config.get('Main','LogFlag'))
            LogPath   = self.config.get('Main','LogPath')
            LogPrefix = self.config.get('Main','LogPrefix')
            if LogFlag == True:
                logFilename = time.strftime( LogPath + LogPrefix + "%s%Y%m%d_%H%M%S.log", time.localtime())
                globalLogFp = file( logFilename, 'w')
        except:
            globalLogFp = None
            LogMsg ("Unable op open file: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))

        # create zipfile
        try:
            archiveFlag     = eval(self.config.get('Main','ArchiveFlag'))
            archivePath     = self.config.get('Main','ArchivePath')
            archivePrefix   = self.config.get('Main','ArchivePrefix')
            archiveSplit    = eval(self.config.get('Main','ArchiveSplit'))
            archiveSplitSize= eval(self.config.get('Main','ArchiveSplitSize')) * 1024*1024
            if archiveSplit:
                archiveFilename = time.strftime( archivePath + archivePrefix + "%s%Y%m%d_%H%M%S-1.zip", time.localtime())
            else:
                archiveFilename = time.strftime( archivePath + archivePrefix + "%s%Y%m%d_%H%M%S.zip", time.localtime())
            if archiveFlag == True:
                archiveFp = zipfile.ZipFile( archiveFilename, "w", zipfile.ZIP_DEFLATED)
        except:
            archiveFp = None
            LogMsg ("Unable to open file: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))

        title = self.config.get('Main','Title')
        frame  = wx.Frame(None)

        self.wizard = wiz.Wizard( frame, -1, title   )

        # Set app icon
        iconFile = "P_RGB_BLACKBCKGRND.bmp"
        ic = wx.Icon(iconFile, wx.BITMAP_TYPE_ICO)
        frame.SetIcon( ic )
        self.wizard.SetIcon( ic )

        # Create global dictionary
        optionList = self.config.list_items('Main')
        self.globals = {}
        for k,v in optionList:
            self.globals[k] = v

        # Add some global entries
        self.globals['archiveFilename']= archiveFilename
        self.globals['archiveFp']= archiveFp
        self.globals['archiveSplit']= archiveSplit
        self.globals['archiveSplitSize']= archiveSplitSize
        self.globals['archiveIndex']= 1

        # Read task configs
        self.taskList = self.ReadTaskList( self.wizard, self.config, self.globals )

        # Create pages
        self.pages    = []
        self.mainPage = ExecStartPage( self.wizard, title, self.taskList, self.globals, self.pages )
        self.lastPage = ExecEndPage( self.wizard, title, self.taskList, self.globals )
        runList       = []
        execPage      = None

        # Create task pages
        self.pages.append( self.mainPage )
        for taskIndex in range( len(self.taskList) ):
            if isinstance( self.taskList[taskIndex], wiz.PyWizardPage ):
                if execPage != None:
                    execPage.AddTaskList( runList )
                    self.pages.append( execPage )
                    execPage = None
                    runList  = []
                self.pages.append( self.taskList[taskIndex] )
                self.taskList[taskIndex].globals = self.globals
            elif isinstance( self.taskList[taskIndex], ExecTask ):
                if execPage == None:
                    execPage = ExecPage( self.wizard, title, self.taskList, self.globals )
                runList.append(taskIndex)
            else:
                LogMsg ("Invalid task type: %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        if execPage != None:
            execPage.AddTaskList( runList )
            self.pages.append( execPage )
        self.pages.append ( self.lastPage )

        # Link pages
        prevPage = None
        for page in self.pages:
            if hasattr(page,'_execute')==False:
                linkPage = True
            elif page._execute:
                linkPage = True
            else:
                linkPage = False

            if linkPage:
                if ( prevPage != None ):
                    page.SetPrev( prevPage )
                    prevPage.SetNext( page )
                prevPage = page

        # Start wizard
        self.displayTasks = eval( self.globals['displaytasks'] )
        if self.displayTasks:
            page = self.mainPage
        else:
            page = self.mainPage.GetNext()
        self.wizard.FitToPage( page  )
        self.wizard.RunWizard( page )

        # cleanup
        if globalLogFp != None:
            globalLogFp.close()
            globalLogFp=None

        if self.globals['archiveFp'] != None:
            if len(self.globals['archiveFp'].infolist())==0:
                self.globals['archiveFp'].close()
                os.remove( logFilename )
                os.remove( self.globals['archiveFilename'] )
            else:
                self.globals['archiveFp'].write( logFilename )
                self.globals['archiveFp'].close()
                if self.globals['archiveSplit']:
                    prefix = self.globals['archiveFilename'][0:-4].split('-')
                    msg = "Results saved to directory %s.\n%d zip files with prefix %s-*." % (os.getcwd(), self.globals['archiveIndex'], prefix[0])
                else:
                    msg = "Results saved to %s." % self.globals['archiveFilename']
                LogMsg(msg)
                dlg = wx.MessageDialog(self.wizard, msg, title, wx.OK | wx.ICON_INFORMATION )
                dlg.ShowModal()
                dlg.Destroy()
                os.remove( logFilename )

    def ReadTaskList(self, wiz, config, globals ):
        """ Read Task ini files and read sections with prefix 'task'. """

        # Go through task sections and create tasks
        taskList = []
        sections = [ s for s in config.list_sections() if s.startswith('Task') and len(s)>4 ]
        sections.sort( cmp=lambda x,y: cmp(eval(x[4:]), eval(y[4:])) )
        for section in sections:

            if type(section) <> type(''):
                continue

            if section.lower().startswith(INIFILE_TASK_SECTION) == False:
                continue

            # create dict for task config
            taskConfig = {}
            for item in config.list_items(section):
                taskConfig[item[0]] = item[1]
            taskKeys   = taskConfig.keys()
            taskKeys.sort()
            pargs = []
            nargs = {}
            for key in taskKeys:
                if key.startswith('_') == False:
                    if key.startswith(INIFILE_TASK_ARG_FIELD) == True:
                        pargs.append( taskConfig[key] )
                    else:
                        nargs[key] = taskConfig[key]

            # create task and assign attributes
            try:

                # create task
                moduleName    = taskConfig[INIFILE_TASK_MODULE_FIELD]
                className     = taskConfig[INIFILE_TASK_CLASS_FIELD]
                taskmod       = __import__(moduleName)
                taskclass     = getattr(taskmod, className)
                task          = taskclass( wiz,
                                   taskConfig[INIFILE_TASK_TITLE_FIELD],
                                   taskConfig[INIFILE_TASK_DESCRIPTION_FIELD],
                                   globals,
                                   pargs, nargs )
                task._execute = eval(taskConfig[INIFILE_TASK_EXECUTE_FLAG_FIELD])
                task._nargs   = nargs
                task._pargs   = pargs
                task.printMsg = LogMsg

            except:
                error ="\nTask %s: %s %s\n" % (taskConfig[INIFILE_TASK_TITLE_FIELD], sys.exc_info()[0], sys.exc_info()[1])
                LogMsg ( error )

            taskList.append( task )
        return taskList

# Main
def Main():
    try:
        options, args = getopt.getopt(sys.argv[1:], "he:", ["help", "execfile="])
    except getopt.GetoptError:
        # print help information and exit:
        print "-h\tDisplay help.\n-e\texecution list filename.\n"
        sys.exit(2)

    filename = DEFAULT_INI

    for opt, arg in options:
        if opt in ("-h", "--help"):
            Usage()
            sys.exit()
        if opt in ("-e", "--execfile"):
            filename = arg

    app = ExecApp()
    app.Run( filename )

if __name__ == "__main__" :
    Main()
