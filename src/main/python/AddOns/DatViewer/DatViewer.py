import gettext
import getopt
import sys
from DatViewerLib import ViewNotebook

APPVERSION = "3.0.3"
_DEFAULT_CONFIG_NAME = "DatViewer.ini"

HELP_STRING = """\
DatViewer.py [-h] [-c<FILENAME>] [-v]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file. Default = "datViewer.ini"
-v  Print version number.

View/analyze data in an HDF5 file.
"""

def printUsage():
    print HELP_STRING

def printVersion():
    print "DatViewer %s" % APPVERSION

def handleCommandSwitches():
    shortOpts = 'hc:p:v'
    longOpts = ["help", "prefs", "version"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    # assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    # support /? and /h for help
    if "/?" in args or "/h" in args:
        options["-h"] = ""

    #executeTest = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit(0)

    if "-v" in options or "--version" in options:
        printVersion()
        sys.exit(0)

    # Start with option defaults...
    configFile = _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile

if __name__ == "__main__":
    gettext.install("app")
    configFile = handleCommandSwitches()

    #config = CustomConfigObj(configFile)
    viewNotebook = ViewNotebook(version=APPVERSION)   #config=config)
    viewNotebook.configure_traits(view=viewNotebook.traits_view)
