# DatViewerPrefs.py
#
#
# TODO: Need a class to handle prefs load/save/get/set that is
#       initialized with a prefs dictionary containing the following info:
#          pref name
#          pref description
#          section name
#          pref type (float, int, string, etc.)
#          pref default
#          bit flag (?) for pref (system or user), only user persisted
#
#       Implement class methods to load/save, get/set, reset, etc.
#
# For now I'll just hard-code things for the app.

from __future__ import with_statement

import wx
import os
from Host.Common.CustomConfigObj import CustomConfigObj

_DEFAULT_CONFIG_NAME = "DatViewer.ini"
_DEFAULT_PREFS_FILENAME = "DatViewerPrefs.ini"
_DEFAULT_USER_PREFS_FILENAME = "DatViewerUserPrefs.ini"


class DatViewerPrefs(object):
    def __init__(self, appname, appversion, defaultConfigPath=None, fPrefsReset=False):
        self.defaultConfigPath = defaultConfigPath

        # default to DatViewerPrefs.ini in script folder if not set
        if self.defaultConfigPath is None:
            self.defaultConfigPath = os.path.join(os.getcwd(), _DEFAULT_PREFS_FILENAME)

        # construct a path for user's private prefs
        # TODO: fix so path is not Windows-specific
        appdataDir = os.path.join(os.environ['LOCALAPPDATA'], appname, appversion)
        self.userPrefsPath = os.path.join(appdataDir, _DEFAULT_USER_PREFS_FILENAME)

        # save off the prefs reset flag and initialize them
        self.fPrefsReset = fPrefsReset
        self.InitPrefs()

    def InitPrefs(self):
        # These are the initial built-in prefs settings
        #
        # [FileManagement]
        self.lastH5OpenDir = ""

        self.lastZipOpenDir = ""
        self.lastZipOpenSaveH5Dir = ""

        # [UILayout]
        self.viewerFrameSize = wx.Size(500, 300)
        self.viewerFramePos = wx.Point(-1, -1)
        self.plotWindowToolbar = True

        # [Config]
        self.tz = 'US/Pacific'

    def LoadPrefs(self):
        # get defaults from DatViewerPrefs.ini in the app's folder
        if os.path.isfile(self.defaultConfigPath):
            self._LoadConfigFile(self.defaultConfigPath)

        # user settings override defaults unless resetting the prefs
        if self.fPrefsReset is False:
            if os.path.isfile(self.userPrefsPath):
                self._LoadConfigFile(self.userPrefsPath)

    def ResetPrefs(self):
        # for manually resetting prefs
        self.InitPrefs()

        # pull in app defaults from app's INI
        if os.path.isfile(self.defaultConfigPath):
            self._LoadConfigFile(self.defaultConfigPath)

    def SavePrefs(self):
        self._SaveConfigFile(self.userPrefsPath)

    def _LoadConfigFile(self, filepath):
        #print "_LoadConfigFile: filepath=", filepath

        # not sure if ignore_option_case should be False, default is True
        co = CustomConfigObj(filepath)

        # sections are categories for user preferences
        # [FileManagement]
        section = 'FileManagement'

        #   lastH5OpenDir
        try:
            self.lastH5OpenDir = co.get(section, 'lastH5OpenDir', self.lastH5OpenDir)
            if not os.path.isdir(self.lastH5OpenDir):
                self.lastH5OpenDir = ""
        except:
            pass

        #   lastZipOpenDir - folder for opening ZIP to create H5 file
        try:
            self.lastZipOpenDir = co.get(section, 'lastZipOpenDir', self.lastZipOpenDir)
            if not os.path.isdir(self.lastZipOpenDir):
                self.lastZipOpenDir = ""
        except:
            pass

        #   lastZipOpenSaveH5Dir - folder for H5 file created from ZIP archive
        try:
            self.lastZipOpenSaveH5Dir = co.get(section, 'lastZipOpenSaveH5Dir', self.lastZipOpenSaveH5Dir)
            if not os.path.isdir(self.lastZipOpenSaveH5Dir):
                self.lastZipOpenSaveH5Dir = ""
        except:
            pass

        # [UILayout]
        section = "UILayout"

        #   viewerFrameSize
        try:
            width = co.get(section, 'DatViewerFrameWidth', self.viewerFrameSize.x)
            height = co.get(section, 'DatViewerFrameHeight', self.viewerFrameSize.y)
            self.viewerFrameSize = wx.Size(int(width), int(height))
        except:
            pass

        #   viewerFramePos
        try:
            x = co.get(section, 'DatViewerFrameX', self.viewerFramePos.x)
            y = co.get(section, 'DatViewerFrameY', self.viewerFramePos.y)
            self.viewerFramePos = wx.Point(int(x), int(y))
        except:
            pass

        #   plotWindowToolbar - whether plot windows have a toolbar
        self.plotWindowToolbar = co.getboolean(section,
                                               'plotWindowToolbar',
                                               self.plotWindowToolbar)

        #   DatViewerResizable

        # [Config]
        section = "Config"

        #   tz (timezone)
        try:
            self.tz = co.get(section, 'tz', self.tz)
        except:
            pass

    def _SaveConfigFile(self, configPath):
        co = CustomConfigObj()

        section = 'FileManagement'
        if not co.has_section(section):
            co.add_section(section)

        co.set(section, 'lastH5OpenDir', self.lastH5OpenDir)
        co.set(section, 'lastZipOpenDir', self.lastZipOpenDir)
        co.set(section, 'lastZipOpenSaveH5Dir', self.lastZipOpenDir)

        section = "UILayout"
        if not co.has_section(section):
            co.add_section(section)
        co.set(section, 'DatViewerFrameWidth', self.viewerFrameSize.width)
        co.set(section, 'DatViewerFrameHeight', self.viewerFrameSize.height)

        co.set(section, 'DatViewerFrameX', self.viewerFramePos.x)
        co.set(section, 'DatViewerFrameY', self.viewerFramePos.y)

        section = "Config"
        if not co.has_section(section):
            co.add_section(section)

        # something like timezone information should be system not user-specific
        #co.set(section, 'tz', self.tz)

        # create folder to hold user prefs file if it doesn't exist
        # call os.makedirs() all intermediate folders are created as well
        folder = os.path.split(configPath)[0]
        if not os.path.exists(folder):
            print "create folder '%s'" % folder
            os.makedirs(folder)

        with open(configPath, 'w') as f:
            co.write(f)
