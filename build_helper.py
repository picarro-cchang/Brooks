import json
from Queue import Queue, Empty
import shlex
from subprocess import PIPE, Popen, STDOUT
import os
import sys
import getopt
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'wx'
from traits.api import *
from traitsui.api import *
from threading  import Thread
import wx

ON_POSIX = 'posix' in sys.builtin_module_names

class TextDisplayHandler(Handler):
    def object_string_changed(self, info):
        ui = info.ui
        for ed in ui._editors:
            if ed.name == 'string':
                ed.control.SetInsertionPointEnd()
                return

class TextDisplay(HasTraits):
    string = String()
    view = View( Item('string', show_label=False, springy=True, style='custom'),
                 handler = TextDisplayHandler)

class BuildHelper(HasTraits):
    build = Button(label="Start Build")
    build_e = Bool(True)
    check_working_tree = Bool(False, desc="Ensure that working tree is consistent with repository", label="Check working tree")
    check_configs = Bool(False, desc="Check configuration directory versions are up-to-date", label="Check configurations")
    check_configs_e = Property(depends_on = ['product'])
    incr_version = Enum("major", "minor", "revision", "build", desc="Version field to increment", label="Increment Version",
                        visible_when="version=='Increment'")
    incr_version_e = Property(depends_on = ['version'])
    official = Bool(False, label="Official", desc="Produce an official release")
    push = Bool(False, desc="Push repository back to GitHub", label="Push repository")
    copy = Bool(False, desc="Copy installers to folders", label="Copy installers")
    changeDir = Button
    product = Enum("si2000",
                   "mobile",
                   "ai_autosampler",
                   "chem_correct",
                   "sdm",
                   "ssim",
                   "vaporizer_cleaner",
                   "datviewer",
                   desc="the product to build software for",
                   label="Product")
    set_version = String("0.0.0.0", desc="Version number (dotted quad of integers)", label="Set Version")
    set_version_e = Property(depends_on = ['version'])
    version = Enum("Do not change", "Increment", "Set", desc="Version of installer", label="Version")
    tag = Bool(False, desc="Tag local repository", label="Tag repository")
    task = Enum("make_installers", "run_unit_tests", "clean", "check_config_hashes", "update_config_hashes", desc="Task to perform", label="Task")

    text_display = Instance(TextDisplay)
    si2000_types_available = List(Str)
    si2000_types = List(editor = CheckListEditor(name = 'si2000_types_available', cols=4, format_func=lambda x: x))
    si2000_types_e = Property(depends_on = ['product'])
    mobile_types_available = List(Str)
    mobile_types = List(editor = CheckListEditor(name = 'mobile_types_available', cols=4, format_func=lambda x: x))
    mobile_types_e = Property(depends_on = ['product'])
    types_toggle_button_label = Str('Set all SI2000 types')
    types_toggle = Button(editor = ButtonEditor(label_value = 'types_toggle_button_label'))
    view = View(
        HGroup(
            Group(
                Item(name="task"),
                Item(name="product"),
                Item(name="official"),
                Item(name="check_working_tree"),
                Group(
                    Item(name="si2000_types", style = "custom", show_label=False),
                    Item(name="types_toggle", show_label=False),
                    enabled_when="si2000_types_e", show_border=True, label='SI2000'
                ),
                Group(
                    Item(name="mobile_types", style = "custom", show_label=False),
                    enabled_when="mobile_types_e", show_border=True, label='Mobile'
                ),
                Item(name="check_configs", enabled_when="check_configs_e"),
                Item(name="version"),
                Item(name="incr_version", enabled_when="incr_version_e"),
                Item(name="set_version", enabled_when="set_version_e"),
                Item(name="tag"),
                Item(name="push"),
                HGroup(
                    Item(name="copy"),
                    Item(name="changeDir", enabled_when="copy")
                ),
                Group(
                    Item(name="build", show_label=False, enabled_when="build_e")
                )
            ),
            Group(
                Item(name="text_display", style="custom", show_label=False)
            )
        ), resizable=True, width=0.5
    )

    def __init__(self):
        self.si2000_types_available = self.load_types_from_file("si2000")
        self.mobile_types_available = self.load_types_from_file("mobile")
        self.text_display = TextDisplay()
        self.copyDir = ""
        
    def load_types_from_file(self, product):
        with open("versions/%s_types.json" % product, "r") as inp:
            config_info = json.load(inp)
        return sorted(config_info['buildTypes'].keys())
    
    def _get_check_configs_e(self):
        return self.product=='si2000' or self.product=='mobile'

    def _get_si2000_types_e(self):
        return self.product=='si2000'
        
    def _get_mobile_types_e(self):
        return self.product=='mobile'

    def _get_incr_version_e(self):
        return self.version=='Increment'

    def _get_set_version_e(self):
        return self.version=='Set'

    def _types_toggle_fired(self):
        if self.types_toggle_button_label == 'Set all SI2000 types':
            self.types_toggle_button_label = 'Clear all SI2000 types'
            self.si2000_types = self.si2000_types_available
        else:
            self.types_toggle_button_label = 'Set all SI2000 types'
            self.si2000_types = []

    def _official_changed(self):
        self.push = self.official
        self.tag = self.official
        
    def _copy_changed(self):
        if self.copy:
            if self.copyDir == "":
                defaultPath = r'S:\CRDS\CRD Engineering\Software\SI2000'
            else:
                defaultPath = self.copyDir
            d = wx.DirDialog(None, r"Select root directory and installers will be copied into subfolders named with analyzer species",
                             defaultPath=defaultPath,
                             style=wx.DD_DIR_MUST_EXIST | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
            if d.ShowModal() == wx.ID_OK:
                self.copyDir = d.GetPath()
            d.Destroy()

    def make_option(self, attr, formatter=None):
        if formatter is None:
            formatter = lambda x : x
        if attr == "types":
            pybuilder_attr = "types"
            attr = self.product + "_types"
        else:
            pybuilder_attr = attr
        if hasattr(self, attr + "_e") and not getattr(self, attr + "_e"):
            return []
        else:
            return ["-P%s=%s" % (pybuilder_attr, formatter(getattr(self, attr)))]

    def list_formatter(self, lis):
        return ",".join(lis)
        
    def process_output(self, out):
        for line in iter(out.readline, ''):
            #wx.CallAfter(self.add_to_display, line)
            self.text_display.string += line
        out.close()
        #wx.CallAfter(self.restore_build_button)
        self.build_e = True

    def add_to_display(self, line):
        self.text_display.string += line

    def restore_build_button(self):
        self.build_e = True
    
    def _changeDir_fired(self):
        d = wx.DirDialog(None, r"Select root directory and installers will be copied into subfolders named with analyzer species",
                         defaultPath=self.copyDir,
                         style=wx.DD_DIR_MUST_EXIST | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        if d.ShowModal() == wx.ID_OK:
            self.copyDir = d.GetPath()
        d.Destroy()
    
    def _build_fired(self):
        command = ["python -u build.py"]
        command.extend(self.make_option("product"))
        command.extend(self.make_option("check_working_tree"))
        if self.task != "update_config_hashes":
            command.extend(self.make_option("check_configs"))
        command.extend(self.make_option("types", self.list_formatter))
        if self.task == "make_installers":
            command.extend(self.make_option("official"))
            command.extend(self.make_option("incr_version"))
            command.extend(self.make_option("set_version"))
            command.extend(self.make_option("push"))
            command.extend(self.make_option("tag"))
            if self.copy:
                command.extend(self.make_option("copyDir"))
        command.append(self.task)
        self.text_display.string += " ".join(command) + "\n"
        args = shlex.split(" ".join(command), posix=False)
        self.build_e = False
        p = Popen(args, stdout=PIPE, stderr=STDOUT, bufsize=1, close_fds=ON_POSIX)
        t = Thread(target=self.process_output, args=(p.stdout,))
        t.daemon = True
        t.start()

def process_build_config_file(configFile):
    if not os.path.exists(configFile):
        raise("Configuration file not found: %s" % configFile)
    else:
        from configobj import ConfigObj
        config = ConfigObj(configFile)
        if "git_path" in config["Setup"]:
            git_path = config["Setup"]["git_path"]
        else:
            git_path = None
        for section in config:
            if section.startswith("Build"):
                if bool(config[section]["enable"]):
                    product = config[section]["product"]
                    types = config[section]["types"]
                    official = config[section]["official_release"]
                    tag = config[section]["tag_github"]
                    push = config[section]["push_github"]
                    upload = config[section]["upload_artifactory"]
                    version_inc = config[section]["version_increase"]
                    other_options = "-Pcheck_working_tree=False -Pcheck_configs=False"
                    command = "python -u build.py -Pproduct=%s -Ptypes=%s -Pofficial=%s -Ppush=%s -Ptag=%s -Pupload_artifactory=%s %s" % \
                        (product, types, official, push, tag, upload, other_options)
                    if git_path:
                        command += (" -Pgit=%s" % git_path)
                    command += " make_installers"
                    print command
                    args = shlex.split(command, posix=False)
                    p = Popen(args, stdout=PIPE, stderr=STDOUT, bufsize=1, close_fds=ON_POSIX)
                    while True:
                        line = p.stdout.readline()
                        if len(line) == 0:
                            break
                        else:
                            print line
        
HELP_STRING = """\
build_helper.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a build configuration file. Specified build process will be run automatically
"""
def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]
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

    # Start with option defaults...
    configFile = ""

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile
        
if __name__ == "__main__":
    configFile = handleCommandSwitches()
    if len(configFile) > 0:
        process_build_config_file(configFile)
    else:
        build_helper = BuildHelper()
        build_helper.configure_traits()