import inspect
import os
import sys

# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname

rdict = _SYNC_OUT_("SYNC1")
for k in rdict:
    if k in newname:
        _REPORT_[newname[k]] = rdict[k]
    else:
        _REPORT_[k] = rdict[k]
