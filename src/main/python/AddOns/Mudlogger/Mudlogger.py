import wx
import sys
import os
sys.path.append(os.getcwd())
from MainFrame import MainFrame

HELP_STRING = \
"""\
Mudlogger.py [-h] [--data<FILENAME>] [--test]

Where the options can be a combination of the following:
-h              Print this help.
--data          Program reads data file for testing 
--test          Program generates fake data for testing
--test_peak_detection 
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt
    alarmConfigFile = None
    shortOpts = 'h'
    longOpts = ["help", "test", "data=", "test_peak_detection"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    executeTest = False
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()
    else:
        if "--test" in options:
            executeTest = True

    if "--data" in options:
        dataFile = options["--data"]
        executeTest = False
    else:
        dataFile = None
        
    if "--test_peak_detection" in options:
        test_peak_detection = True
    else:
        test_peak_detection = False

    return (executeTest, dataFile, test_peak_detection)

def main():
    #Get and handle the command line options...
    test, dataFile, test_peak_detection = HandleCommandSwitches()
    app = wx.App()
    MainFrame(None, generate_fake_data=test, read_data_file=dataFile, test_peak_detection=test_peak_detection)
    app.MainLoop()
    
if __name__ == '__main__':
    main()
