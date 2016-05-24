"""
Set Master.ini values to desired values. Need this since
the installer won't change InstrConfig files and we need to ensure
Master.ini are reset new values

Leaves behind a snapshot of Master.ini in case something goes wrong
"""

import os
import sys
import time
from configobj import ConfigObj
from shutil import copyfile

current_location = os.path.split(os.path.realpath(__file__))[0]
current_date = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time()))
master = os.path.join(current_location, r"..\InstrConfig\Calibration\InstrCal\Master.ini")
master_copy = os.path.join(current_location, r"..\InstrConfig\Calibration\InstrCal\Master_"+current_date+".ini")
update = os.path.join(current_location, r"..\AppConfig\Config\Utilities\UpdateMasterIni.ini")
if not os.path.exists(master):
    print "Master file not found: %s" % master
    sys.exit(0)
elif not os.path.exists(update):
    print "Master update file not found: %s" % update
    sys.exit(0)
copyfile(master, master_copy)
config = ConfigObj(master)
new_config = ConfigObj(update)

for section in new_config:
    config[section].update(new_config[section])
config.write()