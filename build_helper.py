import json
from Queue import Queue, Empty
import shlex
from subprocess import PIPE, Popen, STDOUT
import sys
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
    check_working_tree = Bool(True, desc="Ensure that working tree is consistent with repository", label="Check working tree")
    check_configs = Bool(True, desc="Check configuration directory versions are up-to-date", label="Check configurations")
    check_configs_e = Property(depends_on = ['product'])
    incr_version = Enum("major", "minor", "revision", "build", desc="Version field to increment", label="Increment Version",
                        visible_when="version=='Increment'")
    incr_version_e = Property(depends_on = ['version'])
    official = Bool(False, label="Official", desc="Produce an official release")
    push = Bool(False, desc="Push repository back to GitHub", label="Push repository")
    product = Enum("g2000",
                   "ai_autosampler",
                   "chem_correct",
                   "sdm",
                   "ssim",
                   "vaporizer_cleaner",
                   desc="the product to build software for",
                   label="Product")
    set_version = String("0.0.0.0", desc="Version number (dotted quad of integers)", label="Set Version")
    set_version_e = Property(depends_on = ['version'])
    version = Enum("Do not change", "Increment", "Set", desc="Version of installer", label="Version")
    tag = Bool(False, desc="Tag local repository", label="Tag repository")
    task = Enum("make_installers", "clean", "check_config_hashes", "update_config_hashes", desc="Task to perform", label="Task")

    text_display = Instance(TextDisplay)
    types_available = List(Str)
    types = List(editor = CheckListEditor(name = 'types_available', cols=4, format_func=lambda x: x))
    types_e = Property(depends_on = ['product'])
    types_toggle_button_label = Str('Set all types')
    types_toggle = Button(editor = ButtonEditor(label_value = 'types_toggle_button_label'))
    view = View(
        HGroup(
            Group(
                Item(name="task"),
                Item(name="product"),
                Item(name="official"),
                Item(name="check_working_tree"),
                Group(
                    Item(name="types", style = "custom", show_label=False),
                    Item(name="types_toggle", show_label=False),
                    enabled_when="types_e"
                ),
                Item(name="check_configs", enabled_when="check_configs_e"),
                Item(name="version"),
                Item(name="incr_version", enabled_when="incr_version_e"),
                Item(name="set_version", enabled_when="set_version_e"),
                Item(name="tag"),
                Item(name="push"),
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
        with open("versions/g2000_types.json","r") as inp:
            config_info = json.load(inp)
        self.types_available = sorted(config_info['buildTypes'].keys())
        self.text_display = TextDisplay()

    def _get_check_configs_e(self):
        return self.product=='g2000'

    def _get_types_e(self):
        return self.product=='g2000'

    def _get_incr_version_e(self):
        return self.version=='Increment'

    def _get_set_version_e(self):
        return self.version=='Set'

    def _types_toggle_fired(self):
        if self.types_toggle_button_label == 'Set all types':
            self.types_toggle_button_label = 'Clear all types'
            self.types = self.types_available
        else:
            self.types_toggle_button_label = 'Set all types'
            self.types = []

    def _official_changed(self):
        self.push = self.official
        self.tag = self.official

    def make_option(self, attr, formatter=None):
        if formatter is None:
            formatter = lambda x : x
        if hasattr(self, attr + "_e") and not getattr(self, attr + "_e"):
            return []
        else:
            return ["-P%s=%s" % (attr, formatter(getattr(self, attr)))]

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

    def _build_fired(self):
        command = ["python -u build.py"]
        command.extend(self.make_option("product"))
        command.extend(self.make_option("official"))
        command.extend(self.make_option("check_working_tree"))
        command.extend(self.make_option("check_configs"))
        command.extend(self.make_option("incr_version"))
        command.extend(self.make_option("set_version"))
        command.extend(self.make_option("tag"))
        command.extend(self.make_option("push"))
        command.extend(self.make_option("types", self.list_formatter))
        command.append(self.task)
        self.text_display.string += " ".join(command) + "\n"
        args = shlex.split(" ".join(command), posix=False)
        self.build_e = False
        p = Popen(args, stdout=PIPE, stderr=STDOUT, bufsize=1, close_fds=ON_POSIX)
        t = Thread(target=self.process_output, args=(p.stdout,))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    build_helper = BuildHelper()
    build_helper.configure_traits()
