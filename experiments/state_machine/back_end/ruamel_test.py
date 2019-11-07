import sys
from pathlib import Path

import yaml as py_yaml

from ruamel.yaml import YAML, version_info, RoundTripRepresenter
import json

yaml = YAML()
yaml.default_flow_style = False


class MyRepresenter(RoundTripRepresenter):
    def ignore_aliases(self, _data):
        return True


def my_compose_document(self):
    self.parser.get_event()
    node = self.compose_node(None, None)
    self.parser.get_event()
    # self.anchors = {}    # <<<< commented out
    return node


yaml.Composer.compose_document = my_compose_document


# adapted from http://code.activestate.com/recipes/577613-yaml-include-support/
def yaml_include(loader, node):
    y = loader.loader
    yaml = YAML(typ=y.typ, pure=y.pure)  # same values as including YAML
    yaml.composer.anchors = loader.composer.anchors
    return yaml.load(Path(node.value))


yaml.Constructor.add_constructor("!include", yaml_include)
yaml.Representer = MyRepresenter

with open("pigss_config.yaml") as fp:
    object = yaml.load(fp.read())
print(object)

# object["Configuration"]["Simulation"] = False
yaml.dump(object, sys.stdout)

print(py_yaml.dump(py_yaml.safe_load(json.dumps(object)), default_flow_style=False))
