# get default value for Sgdbr_Cal.ini, or set the max limit
from configobj import ConfigObj
import numpy as np
import os
import sys
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, "SGDBR_Scan", IsDontCareConnection=False)


def getParameterValue(config, laser_type, setting):
    if setting not in config['Parameters']:
        value = getDefaultValue(laser_type, setting)
    else:
        value = np.float(config['Parameters'][setting])
        if value < 0.0 or value > np.float(getMaxValue(laser_type, setting)):
            error_messgae = "Parameter " + setting + " value= " + str(value) + " is out of range"
            raise ValueError(error_messgae)
    config['Parameters'][setting] = value
    return value


def getDefaultValue(laser_type, setting):
    default_value = {
        'Tlaser': {
            'default': 20.0
        },
        'frontMirrorMax': {
            'UU': 100.0,
            'NN': 70.0,
            'LL': 90.0,
            'default': 100.0
        },
        'front_mirror_range_max': {
            'default': 95.0
        },
        'frontMirrorMin': {
            'default': 0.25
        },
        'front_mirror_range_min': {
            'default': 5.0
        },
        'backMirrorMax': {
            'default': 100.0
        },
        'back_mirror_range_max': {
            'default': 95.0
        },
        'backMirrorMin': {
            'default': 0.25
        },
        'back_mirror_range_min': {
            'default': 5.0
        },
        'phaseMin': {
            'default': 1.0
        },
        'phaseMax': {
            'default': 12.25
        },
        'soaSetting': {
            'UU': 150.0,
            'NN': 200.0,
            'default': 150.0
        },
        'gainSetting': {
            'UU': 150.0,
            'NN': 200.0,
            'default': 150.0
        },
        'wavenumber_width_allowed': {
            'default': 3.0
        },
        'rd_threshold': {
            'default': 9000.0
        },
        'relative_threshold': {
            'UU': 1.0,
            'NN': 5.0,
            'default': 1.0
        },
        'frac_misfit_threshold': {
            'default': 1e-2
        }
    }
    if laser_type in default_value[setting]:
        return default_value[setting][laser_type]
    else:
        return default_value[setting]['default']


def getMaxValue(laser_type, setting):
    max_value = {
        'Tlaser': {
            'default': 45.0
        },
        'frontMirrorMax': {
            'default': 375.0
        },
        'front_mirror_range_max': {
            'default': 100.0
        },
        'frontMirrorMin': {
            'default': 375.0
        },
        'front_mirror_range_min': {
            'default': 100.0
        },
        'backMirrorMax': {
            'default': 375.0
        },
        'back_mirror_range_max': {
            'default': 100.0
        },
        'backMirrorMin': {
            'default': 375.0
        },
        'back_mirror_range_min': {
            'default': 100.0
        },
        'phaseMin': {
            'default': 30.0
        },
        'phaseMax': {
            'default': 30.0
        },
        'soaSetting': {
            'default': 300.0
        },
        'gainSetting': {
            'default': 300.0
        },
        'wavenumber_width_allowed': {
            'default': 6.0
        },
        'rd_threshold': {
            'default': 30000.0
        },
        'relative_threshold': {
            'default': 10.0
        },
        'frac_misfit_threshold': {
            'default': 1e-1
        }
    }
    if laser_type in max_value[setting]:
        return max_value[setting][laser_type]
    else:
        return max_value[setting]['default']


# The common functions to set mirror. soa and gain


def setFront(prefix, front):
    frontDU = np.round(65535.0 * front / 301.2)
    if prefix is not None:
        Driver.wrDasReg(prefix + "_CNTRL_FRONT_MIRROR_REGISTER", frontDU)
    return frontDU


def setBack(prefix, back):
    backDU = np.round(65535.0 * back / 301.2)
    if prefix is not None:
        Driver.wrDasReg(prefix + "_CNTRL_BACK_MIRROR_REGISTER", backDU)
    return backDU


def setSoa(prefix, soa):
    soaDU = np.round(65535.0 * soa / 377.3)
    if prefix is not None:
        Driver.wrDasReg(prefix + "_CNTRL_SOA_REGISTER", soaDU)
    return soaDU


def setGain(prefix, gain):
    gainDU = np.round(65535.0 * gain / 377.3)
    if prefix is not None:
        Driver.wrDasReg(prefix + "_CNTRL_GAIN_REGISTER", gainDU)
    return gainDU


def setPhase(prefix, phase):
    phaseDU = np.round(65535.0 * phase / 30.12)
    if prefix is not None:
        Driver.wrDasReg(prefix + "_CNTRL_COARSE_PHASE_REGISTER", phaseDU)
        Driver.wrDasReg(prefix + "_CNTRL_FINE_PHASE_REGISTER", 0)
    return phaseDU


def config_check():
    config = ConfigObj(sys.argv[1] if len(sys.argv) > 1 else "sgdbr_cal.ini")
    laser_type = config['Parameters']['laser_type']
    base_name = config["Paths"]["base_name"]
    try:
        os.makedirs(base_name)
    except:
        pass
    name_settings = [
        'Tlaser', 'frontMirrorMax', 'front_mirror_range_max', 'frontMirrorMin', 'front_mirror_range_min', 'backMirrorMax',
        'back_mirror_range_max', 'backMirrorMin', 'back_mirror_range_min', 'phaseMin', 'phaseMax', 'soaSetting', 'gainSetting',
        'wavenumber_width_allowed', 'rd_threshold'
    ]

    frontMirrorMin = getParameterValue(config, laser_type, 'frontMirrorMin')
    frontMirrorMax = getParameterValue(config, laser_type, 'frontMirrorMax')
    backMirrorMin = getParameterValue(config, laser_type, 'backMirrorMin')
    backMirrorMax = getParameterValue(config, laser_type, 'backMirrorMax')
    phaseMin = getParameterValue(config, laser_type, 'phaseMin')
    phaseMax = getParameterValue(config, laser_type, 'phaseMax')
    front_mirror_range_min = getParameterValue(config, laser_type, 'front_mirror_range_min')
    front_mirror_range_max = getParameterValue(config, laser_type, 'front_mirror_range_max')
    back_mirror_range_min = getParameterValue(config, laser_type, 'back_mirror_range_min')
    back_mirror_range_max = getParameterValue(config, laser_type, 'back_mirror_range_max')

    if frontMirrorMin > frontMirrorMax: raise ValueError("frontMirrorMin must be smalller than frontMirrorMax")
    if backMirrorMin > backMirrorMax: raise ValueError("backMirrorMin must be smalller than backMirrorMax")
    if phaseMin > phaseMax: raise ValueError("phaseMin must be smalller than phaseMax")
    if front_mirror_range_min > front_mirror_range_max:
        raise ValueError("front_mirror_range_min must be smalller than front_mirror_range_max")
    if back_mirror_range_min > back_mirror_range_max:
        raise ValueError("back_mirror_range_min must be smalller than back_mirror_range_max")

    for settings in name_settings:
        print settings, "=", getParameterValue(config, laser_type, settings)

    config.filename = os.path.join(base_name, 'sgdbr_cal_save.ini')
    config.write()


if __name__ == "__main__":
    config_check()