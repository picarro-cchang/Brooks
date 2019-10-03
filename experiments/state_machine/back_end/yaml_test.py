import sys
from ruamel.yaml import YAML

yaml = YAML()
with open("pigss_config.yaml") as fp:
    object = yaml.load(fp.read())
print(object)
yaml.dump(object, sys.stdout)
