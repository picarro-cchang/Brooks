from configobj import ConfigObj
from optparse import OptionParser

def merge(a, b, path=None):
    "merges b into a"
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

usage = "usage: %prog inFilename changeFilename outFilename"
parser = OptionParser(usage=usage)
options, args = parser.parse_args()
if len(args) != 3:
    args = []
    args.append(raw_input('Name of input file? '))
    args.append(raw_input('Name of file specifying changes? '))
    args.append(raw_input('Name of output file? '))

master = ConfigObj(args[0])
changes = ConfigObj(args[1])
op = file(args[2], "wb")
merge(master, changes)
master.write(op)
op.close()