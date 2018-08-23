import os
import shutil
import sys

HELP_STRING = \
""" AnalyzerSwitcher.py [-a<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help.
-a                   Specify an analyzer type
"""

def HandleCommandSwitches():
    import getopt

    shortOpts = 'a:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)

    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
        
    #Start with option defaults...
    analyzer = ""
    if '-h' in options:
        PrintUsage()
        sys.exit()
    if "-a" in options:
        analyzer = options["-a"]
    return analyzer
    
if __name__ == "__main__":
    analyzer = HandleCommandSwitches()
    dest_dir = r"C:\Picarro\G2000"
    folders = ["AppConfig", "InstrConfig"]
    for subFolder in folders:
        dir = os.path.join(dest_dir, subFolder)
        if os.path.exists(dir):
            os.system('rd /s/q %s' % dir)
        src = os.path.join(dest_dir, "VA", "Config", analyzer, subFolder)
        if not os.path.isdir(src):
            raise Exception("Folder not found: %s" % src)
        shutil.copytree(src, dir)
    # copy warmbox calibration file
    wbFile = os.path.join(dest_dir, "VA", "WBCal", "Beta2000_WarmBoxCal_"+analyzer+".ini")
    dest = os.path.join(dest_dir, "InstrConfig", "Calibration", "InstrCal", "Beta2000_WarmBoxCal.ini")
    if not os.path.exists(wbFile):
        raise Exception("WarmBox Calibration file not found: %s" % wbFile)
    shutil.copy(wbFile, dest)
    # copy rdReprocessor.ini
    src = os.path.join(dest_dir, "VA", "rdReprocessor", "rdReprocessor_"+analyzer+".ini")
    dest = os.path.join(dest_dir, "rdReprocessor.ini")
    if not os.path.exists(wbFile):
        raise Exception("rdReprocessor.ini not found: %s" % src)
    shutil.copyfile(src, dest)