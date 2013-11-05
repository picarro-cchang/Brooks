# DatViewerPrefs.py
#
# This is a useful class for managing user preferences, based on the Python
# configobj class.
#
# Provide a config spec file that is set up with settings for
# defaults and it handles the rest. At a minimum, the config spec
# needs the following entries:
#
# Note: Put the following defs for version and resetPrefsOnNextRestart
#       at the top of the file, not within a section. Set the
#       default for version to a new value whenever prefs are changed so
#       they are no longer compatible with previous user prefs settings that
#       may have been persisted. This should be a fairly rare occurrence,
#       typically only if a setting type is changed or some other
#       incompatibility is introduced.
#
#
#    # this should never be True by default else settings will never be remembered
#    resetPrefsOnNextRestart = boolean(default=False)
#
#    # set the default version number to whatever the prefs version is,
#    # bumping it by 1 whenever
#    version = integer(default=1)

from __future__ import with_statement

#import wx  # for wx.Size, wx.Point
import os
import sys
from configobj import ConfigObj, flatten_errors
from validate import Validator

#from validate import Validator, VdtParamError, VdtTypeError, \
#    VdtValueTooLongError, VdtValueTooShortError, \
#    VdtValueTooSmallError, VdtValueTooBigError

# AppPrefsSpec.ini should be in the configobj configspec format
_DEFAULT_PREFS_SPEC_FILENAME = "AppPrefsSpec.ini"
_DEFAULT_USER_PREFS_FILENAME_WIN = "UserPrefs.ini"
_DEFAULT_USER_PREFS_FILENAME_OSX = ".UserPrefs"
_DEFAULT_USER_PREFS_FILENAME_UNIX = ".UserPrefs"


"""
# I couldn't get this working the way I want. Still need to
# do a conversion back to a list for wx.Size (also wx.Point)
# for writing out the prefs. So let the app handle the translation.
# A custom validators for wx.Size (wx_size_list). Will be similar for
# wx.Point (wx_point_list)
def wx_size_list(value, length):
    # Check that the supplied value is a list integers,
    # 'length' entries must be exactly 2.
    #length = 2
    # the Python Validator must have turned off stdout
    # because I never see any print stmt output...
    fp = open("debug_dump.txt", 'at')
    print>> fp, ""
    print>> fp, "length=", length
    print>> fp, "value=", value

    # length is supplied as a string
    # we need to convert it to an integer
    try:
        length = int(length)
    except ValueError:
        raise VdtParamError('length', length)

    # Check the supplied value is a list
    if not isinstance(value, list):
        raise VdtTypeError(value)

    #if length != 2:
    #    raise VdtParamError('length', length)

    # check the length of the list is correct
    if len(value) > length:
        raise VdtValueTooLongError(value)
    elif len(value) < length:
        raise VdtValueTooShortError(value)

    # Next, check every member in the list
    # converting strings as necessary
    out = []
    for entry in value:
        if not isinstance(entry, (str, unicode, int)):
            # a value in the list
            # is neither an integer nor a string
            raise VdtTypeError(value)
        elif isinstance(entry, (str, unicode)):
            if not entry.isdigit():
                raise VdtTypeError(value)
            else:
                entry = int(entry)

        ## we don't need to check whether the values are too large or small
        #if entry < 0:
        #    raise VdtValueTooSmallError(value)
        #elif entry > 99:
        #    raise VdtValueTooBigError(value)
        out.append(entry)
    #
    # if we got this far, all is well
    # convert the list to a wx.Size object
    return wx.Size(out[0], out[1])


fdict = {
    'wx_size': wx_size_list
    #'wx_position': wx_position_list,
}
"""


class DatViewerPrefs(object):
    """
    Constructor has the following arguments:

    appname (required)        Application name

    appversion (required)     Application version string. Used with appname to
                              construct a path in the user's local appdata dir
                              to persist user preferences

    defaultConfigSpec         Input configspec file (default is None which uses
                              "AppPrefsSpec.ini" which you probably don't want)

    defaultUserPrefsFilename  Filename to persist user preferences to, under the
                              user's local appdata dir (default is None, which
                              uses "UserPrefs.ini" which you probably don't want)

    fPrefsReset               Set this to True to reset preferences to the defaults
                              in the defaultConfigSpec file. User preferences are
                              ignored.
    """
    def __init__(self, appname, appversion,
                 defaultConfigSpec=None,
                 defaultUserPrefsFilename=None,
                 fPrefsReset=False):
        self.defaultConfigSpec = defaultConfigSpec

        # look for the config spec file in the executing app's folder
        # if not passed in by caller
        if self.defaultConfigSpec is None:
            self.defaultConfigSpec = os.path.join(os.getcwd(), _DEFAULT_PREFS_SPEC_FILENAME)
        else:
            self.defaultConfigSpec = os.path.join(os.getcwd(), defaultConfigSpec)

        print "configspec=", self.defaultConfigSpec

        # construct a path for persisting the user's private prefs
        if os.sys.platform == 'darwin':
            from AppKit import NSSearchPathForDirectoriesInDomains
            # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
            # NSApplicationSupportDirectory = 14
            # NSUserDomainMask = 1
            # True for expanding the tilde into a fully qualified path
            appdataDir = os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], appname, appversion)
            prefsFilename = _DEFAULT_USER_PREFS_FILENAME_OSX

        elif sys.platform == 'win32':
            # This will always be win32 for Windows regardless of the bitness of
            # the platform, for backwards compatibility.
            #
            # See: http://stackoverflow.com/questions/2144748/is-it-safe-to-use-sys-platform-win32-check-on-64-bit-python
            appdataDir = os.path.join(os.environ['LOCALAPPDATA'], appname, appversion)
            prefsFilename = _DEFAULT_USER_PREFS_FILENAME_WIN

        else:
            # OS is probably Linux (could use startswith() to look for it)
            #
            # save prefs under a .<appname> directory
            appnameDir = "".join([".", appname])
            appdataDir = os.path.join(os.path.expanduser('~'), appnameDir, appversion)
            prefsFilename = _DEFAULT_USER_PREFS_FILENAME_UNIX

        if defaultUserPrefsFilename is None:
            self.userPrefsPath = os.path.join(appdataDir, prefsFilename)
        else:
            self.userPrefsPath = os.path.join(appdataDir, defaultUserPrefsFilename)

        print "userPrefsPath=", self.userPrefsPath

        self.config = None

        # save off the prefs reset flag -- if reset then we won't load
        # user-specific prefs
        self.fPrefsReset = fPrefsReset

        #self.LoadPrefs()

    def LoadPrefs(self):
        fLoaded = False

        if self.fPrefsReset is False:
            if os.path.isfile(self.userPrefsPath):
                self._LoadConfigFile(self.userPrefsPath,
                                     configspec=self.defaultConfigSpec,
                                     fCopy=True)
                fLoaded = True

                # check whether prefs reset on next app start is set in
                # user file
                if self.config["resetPrefsOnNextRestart"] is True:
                    self.fPrefsReset = True
                    print "resetPrefsOnNextRestart triggered a prefs reset"

                # get last saved version, if differs from spec then
                # need to reset them
                ver = self.config["version"]
                lastVer = ver

                try:
                    lastVer = int(self.config["lastSavedVersion"])
                except:
                    pass

                if lastVer != ver:
                    self.fPrefsReset = True
                    print "version mismatch, resetting prefs"

                # set the last saved version to the current so it
                # is written with persisted user prefs
                self.config["lastSavedVersion"] = ver

                # we must remove the version so it isn't persisted
                del self.config["version"]

            else:
                # user prefs file doesn't exist so force a reset
                self.fPrefsReset = True

        if self.fPrefsReset is True:
            # resetting prefs - we won't specify an output file so user
            # prefs aren't loaded
            print "resetting user prefs"

            # be sure to clear prefs if they've already been read in
            if self.config is not None:
                self.config.clear()

            # now load prefs with only the config spec
            self._LoadConfigFile(None, configspec=self.defaultConfigSpec,
                                 fCopy=True)

            # last saved version is the current, remove version so it
            # isn't persisted
            self.config["lastSavedVersion"] = self.config["version"]
            del self.config["version"]

        if fLoaded is False:
            print "Using system defaults, user prefs don't exist or prefs were reset."

        #print "User file = '%s'" % self.userPrefsPath
        #print "Config spec = '%s'" % self.defaultConfigSpec

    def _LoadConfigFile(self, filepath, configspec=None, fCopy=False):
        # fCopy=True  validator will make a copy of the settings so
        #             defaults are persisted; otherwise they won't be
        #             written back out
        #print "_LoadConfigFile: filepath=", filepath

        # we always want to catch errors where the config file is missing
        self.config = ConfigObj(filepath, configspec=configspec, file_error=True)

        # validate the settings
        #validator = Validator(fdict)  # includes our own custom checking functions
        validator = Validator()
        results = self.config.validate(validator, copy=fCopy)

        # report validation errors
        if results is not True:
            for (section_list, key, _) in flatten_errors(self.config, results):
                if key is not None:
                    print 'The "%s" key in the section "%s" failed validation' % (key, ', '.join(section_list))
                else:
                    print 'The following section was missing:%s ' % ', '.join(section_list)

    def SavePrefs(self):
        self._SaveConfigFile(self.userPrefsPath)

    def _SaveConfigFile(self, configPath):
        # create folder to hold user prefs file if it doesn't exist
        # os.makedirs() creates all intermediate folders as well
        folder = os.path.split(configPath)[0]
        if not os.path.exists(folder):
            print "create folder '%s'" % folder
            os.makedirs(folder)

        self.config.filename = configPath
        self.config.write()

"""
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
"""
