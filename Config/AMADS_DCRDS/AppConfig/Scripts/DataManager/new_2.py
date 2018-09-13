from Host.Common.CustomConfigObj import CustomConfigObj

def readConfig(fname):
    """Returns a ConfigParser object initialized with data from the specified
    file, located (by default) in the application directory"""
    # config = CustomConfigObj(prependAppDir(fname))
    config = CustomConfigObj(fname)
    return config

print readConfig("/home/picarro/I2000\AppConfig\Config\AlarmSystem\AlarmSystem_AMADS.ini")
