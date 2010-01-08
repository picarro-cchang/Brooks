# File Name: ExecTask.py
# Purpose: Class for task to be run by executive.
#
# File History:
# 06-09-11 ytsai   Created file
import os
import sys
import wx
import wx.wizard as wiz
import wx.lib.masked as masked

from wizardhelper import WizardTitledLogoPage

class ExecTask(object):
    def __init__(self, parent=None, title=None, description=None, globals=None, pArgs=None, nArgs=None ):
        self._results = 'None'
        self._status  = True
        if title != None:
            self._title = title
        if description != None:
            self._description = description
        self._error = 'None'
        self._filelist = []
        self._dellist=[]
        self._execute = False
        self.printMsg = None
        self.globals = globals
        self.parent = parent

    def logMsg(self, **args):
        """ Logs messages """
        if printMsg != None:
            self.printMsg(args)
        else:
            print(args)
    def Run(self, *pArgs, **nArgs ):
        return True

class ExecPage( WizardTitledLogoPage, ExecTask ):
    def __init__(self, parent, title=None, description=None, globals=None, pArgs=None, nArgs=None ):
        ExecTask.__init__(self, title, description, globals, pArgs, nArgs )
        WizardTitledLogoPage.__init__(self, parent, globals['title'] )
        self.parent = parent
        self.globals = globals
        self.Running = False
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self._OnPageChanged)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self._OnPageChanging)
        self.Bind(wiz.EVT_WIZARD_CANCEL, self._OnPageCancel)

    def OnPageChanged(self, evt):
        pass

    def OnPageChanging(self, evt):
        pass

    def OnPageCancel(self, evt):
        pass

    def _OnPageChanged(self, evt):
        self._error = 'Okay'
        self.OnPageChanged(evt)

        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
            return;

        if self.Running == True:
            return
        self.Running = True
        try:
            self.status = self.Run()
        except:
            error ="\nTask %s: Archive %s %s\n" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
            self._status = False
            self._error  = error
        self.Running = False

    def _OnPageChanging(self, evt):
        self.OnPageChanging(evt)

        if evt.GetDirection():
            dir = "forward"
            self._ArchiveFiles( self._filelist )
            self._DeleteFiles( self._dellist )
        else:
            dir = "backward"
        if self.Running == True:
            evt.Veto()

    def _OnPageCancel(self, evt):
        self.OnPageCancel(evt)

        if self.Running == True:
            evt.Veto()

    def _ArchiveFiles(self, filelist):
        """ Archive files """
        # zip results file
        try:
            if self.globals['archiveFp']!= None and len(filelist):
                self.printMsg("Please wait, archiving results")
                filecount = 0
                for file in filelist:
                    if os.path.exists( file ):
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
                        self.printMsg("Unable to find %s.\n" % file)
                self.printMsg("\nArchived %d files (%d).\n" % (filecount, len(filelist)) )
        except:
            error ="\nTask %s: Archive %s %s\n" % (self._title, sys.exc_info()[0], sys.exc_info()[1])
            self._status = False
            self._error  = error
            self.printMsg ( error )

    def _DeleteFiles( self, filelist ):
        """ Delete files """
        if eval( self.globals['deletefiles'] ) == True:
            for file in filelist:
                os.remove(file)
