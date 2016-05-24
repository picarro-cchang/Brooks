import wx
import os
import socket
import datetime
import shutil
import time
import serial
import math
import pylab
#import threading
#import sys
#import getopt
#import string
#import random

from datetime import date
from Host.MfgUtilities.Configuration.Graph1Gui import MyFrameGui
from Host.Common.GraphPanel import Series
from numpy import *
from pylab import *
from Host.Common.Listener import Listener
from Host.Common.TextListener import TextListener
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes, StringPickler, timestamp
from Host.Common.SharedTypes import ctypesToDict, RPC_PORT_DATALOGGER, RPC_PORT_FREQ_CONVERTER
from Host.MfgUtilities.Configuration.ConfigToolGUI import SandboxGUI
from Host.autogen import interface
from ctypes import addressof
from ctypes import c_char, c_byte, c_float, c_int, c_longlong
from ctypes import c_short, c_uint, c_ushort, sizeof, Structure
from random import randrange
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.autogen import usbdefs, interface
from Host.Common.analyzerUsbIf import AnalyzerUsb
from configobj import ConfigObj

fastMode = False
rdMode = True

#RPC_PORT_FREQ_CONVERTER = 50015
HOSTEXE_DIR = "C:\Picarro\G2000\HostExe"
INTEGRATION_DIR = "C:\Picarro\G2000\InstrConfig\Integration"
CAL_DIR = "C:\Picarro\G2000\InstrConfig\Calibration\InstrCal"
WARMBOX_CAL = "Beta2000_WarmBoxCal"
HOTBOX_CAL = "Beta2000_HotBoxCal"
LASER_TYPE_DICT = {"1603.2": "CO2", "1651.0": "CH4", "1599.6": "iCO2", "1392.0": "iH2O", "1567.9": "CO"}

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

NameString='Graph2'

FreqConverter = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,"ConfigTool", IsDontCareConnection = False)
DataLogger = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER, ClientName = "ConfigTool")

#############
# Config File accces
#############
def average(values):
    return sum(values, 0.0) / len(values)

def getConfig(fileName):
    return ConfigObj(fileName)

def Log(*a,**k):
    if a[0] not in ['Connection by Controller event log listener to port 40010 failed.',
                    'Connection by Controller event log listener to port 40010 broken.']:
        print "Log: %s, %s" % (a,k)

def startDataLog(userLogName):
    try:
        DataLogger.DATALOGGER_startLogRpc(userLogName)
        #LOGFUNC("Data log started\n")
    except:
        pass
        #LOGFUNC("Failed to start data log\n")

def stopDataLog(userLogName):
    try:
        DataLogger.DATALOGGER_stopLogRpc(userLogName)
        #LOGFUNC("Data log stopped\n")
    except:
        #LOGFUNC("Failed to stop data log\n")
        pass

def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        #print "_mkdir %s" % repr(newdir)
        if tail:
            os.mkdir(newdir)

class MFC:
    #MFC Ranges is hardcoded to 200sccm on chnl 2 and 1000 sccm on chnl 3
    """ser = serial.Serial(
        0,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )"""
    ser = serial.Serial(
        0,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    ser.open()
    #print ser.getSettingsDict()
    ser.isOpen()
    def __init__(self):
        self.setRanges()

    def ID(self):
        self.ser.write("id\r\n")
        time.sleep(0.25)
        id=self.ser.readline()
        print 'Connected to MFC with ID=%s'%id

    def Reset(self):
        self.ser.write("re\r\n")
        time.sleep(0.25)
        s=''#self.ser.readline()
        print 'Reset, response='+s

    def Range(self, chnl, rngCode):
        self.ser.write("ra %d %d\r\n"%(chnl,rngCode))
        time.sleep(0.25)
        s=''#self.ser.readline()
        print 'Range for chnl %d set to RngCode %d, response=%s'%(chnl,rngCode,s)

    def SetPoint(self, chnl,setPoint):
        self.ser.write("fs %d %d\r\n"%(chnl,setPoint))
        time.sleep(0.25)
        s=''#self.ser.readline()
        print 'Setpoint for chnl %d set to %d, response=%s'%(chnl,setPoint,s)

    def close(self):
        self.ser.close()

    def setRanges(self):
        self.Range(2,7)#Set Channel 2 to 200SCCM
        self.Range(3,9)#Set Channel 3 to 1000SCCM

    def setFlow(self, chnl, flow):
        if chnl==2:
            if flow>=220:
                self.SetPoint(2,1100)
            elif flow<0:
                self.SetPoint(2,0)
            else:
                sp=1000*flow/200
                self.SetPoint(2,sp)
        elif chnl==3:
            if flow>=1100:
                self.SetPoint(3,1100)
            elif flow<0:
                self.SetPoint(3,0)
                pass
            else:
                sp=1000*flow/1000
                self.SetPoint(3,sp)
        else:
            return

    def On(self, chnl):
        if chnl==2 or chnl==3:
            self.ser.write("on %d\r\n"%chnl)
            time.sleep(0.25)
            s=''#self.ser.readline()
            print 'Chnl %d set On'%chnl

    def Off(self, chnl):
        if chnl==2 or chnl==3:
            self.ser.write("of %d\r\n"%chnl)
            time.sleep(0.25)
            s=''#self.ser.readline()
            print 'Chnl %d set Off'%chnl

    def TurnOn(self):
        self.On(2)
        self.On(3)

    def TurnOff(self):
        self.Off(2)
        self.Off(3)

Data_analyse_iH2O_Keys=[
'AmbientPressure',
'CavityPressure',
'CavityTemp',
'DasTemp',
'Etalon1',
'Etalon2',
'EtalonTemp',
'HotBoxHeater',
'HotBoxHeatsinkTemp',
'HotBoxTec',
'InletValve',
'Laser1Current',
'Laser1Tec',
'Laser1Temp',
'Laser2Current',
'Laser2Tec',
'Laser2Temp',
'Laser3Current',
'Laser3Tec',
'Laser3Temp',
'Laser4Current',
'Laser4Tec',
'Laser4Temp',
'MPVPosition',
'OutletValve',
'Ratio1',
'Ratio2',
'Reference1',
'Reference2',
'SchemeID',
'SensorTime',
'SpectrumID',
'Time_s',
'ValveMask',
'WarmBoxHeatsinkTemp',
'WarmBoxTec',
'WarmBoxTemp',
'cal_enabled',
'cavity_pressure',
'cavity_temperature',
'delta_18_16',
'delta_18_16_2min',
'delta_18_16_30s',
'delta_18_16_5min',
'delta_D_H',
'delta_D_H_2min',
'delta_D_H_30s',
'delta_D_H_5min',
'galpeak77',
'galpeak77_offsetonly',
'galpeak79',
'galpeak82',
'galpeak82_offsetonly',
'h2o_adjust',
'h2o_conc',
'h2o_ppmv',
'h2o_shift',
'h2o_spline_amp',
'h2o_spline_max',
'h2o_squish_a',
'h2o_y_eff',
'h2o_y_eff_a',
'hms',
'interval',
'n2_flag',
'organic_77',
'organic_82',
'organic_MeOHampl',
'organic_base',
'organic_ch4conc',
'organic_res',
'organic_shift',
'organic_slope',
'organic_splinemax',
'organic_squish',
'organic_y',
'prefit_base',
'prefit_res',
'prefit_shift',
'prefit_slope',
'prefit_squish',
'pzt_ave',
'pzt_stdev',
'species',
'standard_base',
'standard_residuals',
'standard_slope',
'time',
'timestamp',
'wlm1_offset',
'ymd']

DataKeys=[
'MPVPosition',
'InletValve',
'Laser1Current',
'WarmBoxTemp',
'AmbientPressure',
'HotBoxHeater',
'Etalon2',
'CavityTemp',
'Etalon1',
'Reference2',
'Reference1',
'DasTemp',
'Laser1Tec',
'Laser1Temp',
'ValveMask',
'OutletValve',
'CavityPressure',
'HotBoxHeatsinkTemp',
'Ratio1',
'HotBoxTec',
'Ratio2',
'WarmBoxHeatsinkTemp',
'WarmBoxTec',
'EtalonTemp'
]

SensorStreamKeys=[
"Laser1Temp",
"Laser2Temp",
"Laser3Temp",
"Laser4Temp",
"EtalonTemp",
"WarmBoxTemp",
"WarmBoxHeatsinkTemp",
"CavityTemp",
"HotBoxHeatsinkTemp",
"DASTemp",
"Etalon1",
"Reference1",
"Etalon2",
"Reference2",
"Ratio1",
"Ratio2",
"Laser1Current",
"Laser2Current",
"Laser3Current",
"Laser4Current",
"CavityPressure",
"AmbientPressure",
"Laser1TEC",
"Laser2TEC",
"Laser3TEC",
"Laser4TEC",
"WarmBoxTec",
"HotBoxTec",
"HotBoxHeater",
"InletValve",
"OutletValve",
"ValveMask"]

DASRegisterList=[
'DAS_STATUS_REGISTER',
'SCHEDULER_CONTROL_REGISTER',
'RD_IRQ_COUNT_REGISTER',
'ACQ_DONE_COUNT_REGISTER',
'LASER1_TEMP_CNTRL_STATE_REGISTER',
'LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER',
'LASER1_TEMP_CNTRL_TOLERANCE_REGISTER',
'LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER',
'LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER',
'LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER',
'LASER1_TEMP_CNTRL_H_REGISTER',
'LASER1_TEMP_CNTRL_K_REGISTER',
'LASER1_TEMP_CNTRL_TI_REGISTER',
'LASER1_TEMP_CNTRL_TD_REGISTER',
'LASER1_TEMP_CNTRL_B_REGISTER',
'LASER1_TEMP_CNTRL_C_REGISTER',
'LASER1_TEMP_CNTRL_N_REGISTER',
'LASER1_TEMP_CNTRL_S_REGISTER',
'LASER1_TEMP_CNTRL_AMIN_REGISTER',
'LASER1_TEMP_CNTRL_AMAX_REGISTER',
'LASER1_TEMP_CNTRL_IMAX_REGISTER',
'LASER1_TEMP_CNTRL_FFWD_REGISTER',
'LASER1_TEC_PRBS_GENPOLY_REGISTER',
'LASER1_TEC_PRBS_AMPLITUDE_REGISTER',
'LASER1_TEC_PRBS_MEAN_REGISTER',
'LASER1_MANUAL_TEC_REGISTER',
'LASER1_CURRENT_CNTRL_STATE_REGISTER',
'LASER1_MANUAL_COARSE_CURRENT_REGISTER',
'LASER1_MANUAL_FINE_CURRENT_REGISTER',
'LASER1_CURRENT_SWEEP_MIN_REGISTER',
'LASER1_CURRENT_SWEEP_MAX_REGISTER',
'LASER1_CURRENT_SWEEP_INCR_REGISTER',
'LASER2_TEMP_CNTRL_STATE_REGISTER',
'LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER',
'LASER2_TEMP_CNTRL_TOLERANCE_REGISTER',
'LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER',
'LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER',
'LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER',
'LASER2_TEMP_CNTRL_H_REGISTER',
'LASER2_TEMP_CNTRL_K_REGISTER',
'LASER2_TEMP_CNTRL_TI_REGISTER',
'LASER2_TEMP_CNTRL_TD_REGISTER',
'LASER2_TEMP_CNTRL_B_REGISTER',
'LASER2_TEMP_CNTRL_C_REGISTER',
'LASER2_TEMP_CNTRL_N_REGISTER',
'LASER2_TEMP_CNTRL_S_REGISTER',
'LASER2_TEMP_CNTRL_AMIN_REGISTER',
'LASER2_TEMP_CNTRL_AMAX_REGISTER',
'LASER2_TEMP_CNTRL_IMAX_REGISTER',
'LASER2_TEMP_CNTRL_FFWD_REGISTER',
'LASER2_TEC_PRBS_GENPOLY_REGISTER',
'LASER2_TEC_PRBS_AMPLITUDE_REGISTER',
'LASER2_TEC_PRBS_MEAN_REGISTER',
'LASER2_MANUAL_TEC_REGISTER',
'LASER2_CURRENT_CNTRL_STATE_REGISTER',
'LASER2_MANUAL_COARSE_CURRENT_REGISTER',
'LASER2_MANUAL_FINE_CURRENT_REGISTER',
'LASER2_CURRENT_SWEEP_MIN_REGISTER',
'LASER2_CURRENT_SWEEP_MAX_REGISTER',
'LASER2_CURRENT_SWEEP_INCR_REGISTER',
'LASER3_TEMP_CNTRL_STATE_REGISTER',
'LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER',
'LASER3_TEMP_CNTRL_TOLERANCE_REGISTER',
'LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER',
'LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER',
'LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER',
'LASER3_TEMP_CNTRL_H_REGISTER',
'LASER3_TEMP_CNTRL_K_REGISTER',
'LASER3_TEMP_CNTRL_TI_REGISTER',
'LASER3_TEMP_CNTRL_TD_REGISTER',
'LASER3_TEMP_CNTRL_B_REGISTER',
'LASER3_TEMP_CNTRL_C_REGISTER',
'LASER3_TEMP_CNTRL_N_REGISTER',
'LASER3_TEMP_CNTRL_S_REGISTER',
'LASER3_TEMP_CNTRL_AMIN_REGISTER',
'LASER3_TEMP_CNTRL_AMAX_REGISTER',
'LASER3_TEMP_CNTRL_IMAX_REGISTER',
'LASER3_TEMP_CNTRL_FFWD_REGISTER',
'LASER3_TEC_PRBS_GENPOLY_REGISTER',
'LASER3_TEC_PRBS_AMPLITUDE_REGISTER',
'LASER3_TEC_PRBS_MEAN_REGISTER',
'LASER3_MANUAL_TEC_REGISTER',
'LASER3_CURRENT_CNTRL_STATE_REGISTER',
'LASER3_MANUAL_COARSE_CURRENT_REGISTER',
'LASER3_MANUAL_FINE_CURRENT_REGISTER',
'LASER3_CURRENT_SWEEP_MIN_REGISTER',
'LASER3_CURRENT_SWEEP_MAX_REGISTER',
'LASER3_CURRENT_SWEEP_INCR_REGISTER',
'LASER4_TEMP_CNTRL_STATE_REGISTER',
'LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER',
'LASER4_TEMP_CNTRL_TOLERANCE_REGISTER',
'LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER',
'LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER',
'LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER',
'LASER4_TEMP_CNTRL_H_REGISTER',
'LASER4_TEMP_CNTRL_K_REGISTER',
'LASER4_TEMP_CNTRL_TI_REGISTER',
'LASER4_TEMP_CNTRL_TD_REGISTER',
'LASER4_TEMP_CNTRL_B_REGISTER',
'LASER4_TEMP_CNTRL_C_REGISTER',
'LASER4_TEMP_CNTRL_N_REGISTER',
'LASER4_TEMP_CNTRL_S_REGISTER',
'LASER4_TEMP_CNTRL_AMIN_REGISTER',
'LASER4_TEMP_CNTRL_AMAX_REGISTER',
'LASER4_TEMP_CNTRL_IMAX_REGISTER',
'LASER4_TEMP_CNTRL_FFWD_REGISTER',
'LASER4_TEC_PRBS_GENPOLY_REGISTER',
'LASER4_TEC_PRBS_AMPLITUDE_REGISTER',
'LASER4_TEC_PRBS_MEAN_REGISTER',
'LASER4_MANUAL_TEC_REGISTER',
'LASER4_CURRENT_CNTRL_STATE_REGISTER',
'LASER4_MANUAL_COARSE_CURRENT_REGISTER',
'LASER4_MANUAL_FINE_CURRENT_REGISTER',
'LASER4_CURRENT_SWEEP_MIN_REGISTER',
'LASER4_CURRENT_SWEEP_MAX_REGISTER',
'LASER4_CURRENT_SWEEP_INCR_REGISTER',
'WARM_BOX_TEMP_CNTRL_STATE_REGISTER',
'TEC_CNTRL_REGISTER',
'WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER',
'WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER',
'WARM_BOX_TEMP_CNTRL_SWEEP_MAX_REGISTER',
'WARM_BOX_TEMP_CNTRL_SWEEP_MIN_REGISTER',
'WARM_BOX_TEMP_CNTRL_SWEEP_INCR_REGISTER',
'WARM_BOX_TEMP_CNTRL_H_REGISTER',
'WARM_BOX_TEMP_CNTRL_K_REGISTER',
'WARM_BOX_TEMP_CNTRL_TI_REGISTER',
'WARM_BOX_TEMP_CNTRL_TD_REGISTER',
'WARM_BOX_TEMP_CNTRL_B_REGISTER',
'WARM_BOX_TEMP_CNTRL_C_REGISTER',
'WARM_BOX_TEMP_CNTRL_N_REGISTER',
'WARM_BOX_TEMP_CNTRL_S_REGISTER',
'WARM_BOX_TEMP_CNTRL_AMIN_REGISTER',
'WARM_BOX_TEMP_CNTRL_AMAX_REGISTER',
'WARM_BOX_TEMP_CNTRL_IMAX_REGISTER',
'WARM_BOX_TEMP_CNTRL_FFWD_REGISTER',
'WARM_BOX_TEC_PRBS_GENPOLY_REGISTER',
'WARM_BOX_TEC_PRBS_AMPLITUDE_REGISTER',
'WARM_BOX_TEC_PRBS_MEAN_REGISTER',
'WARM_BOX_MANUAL_TEC_REGISTER',
'WARM_BOX_MAX_HEATSINK_TEMP_REGISTER',
'CAVITY_TEMP_CNTRL_STATE_REGISTER',
'TEC_CNTRL_REGISTER',
'CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER',
'CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER',
'CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER',
'CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER',
'CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER',
'CAVITY_TEMP_CNTRL_H_REGISTER',
'CAVITY_TEMP_CNTRL_K_REGISTER',
'CAVITY_TEMP_CNTRL_TI_REGISTER',
'CAVITY_TEMP_CNTRL_TD_REGISTER',
'CAVITY_TEMP_CNTRL_B_REGISTER',
'CAVITY_TEMP_CNTRL_C_REGISTER',
'CAVITY_TEMP_CNTRL_N_REGISTER',
'CAVITY_TEMP_CNTRL_S_REGISTER',
'CAVITY_TEMP_CNTRL_AMIN_REGISTER',
'CAVITY_TEMP_CNTRL_AMAX_REGISTER',
'CAVITY_TEMP_CNTRL_IMAX_REGISTER',
'CAVITY_TEMP_CNTRL_FFWD_REGISTER',
'CAVITY_TEC_PRBS_GENPOLY_REGISTER',
'CAVITY_TEC_PRBS_AMPLITUDE_REGISTER',
'CAVITY_TEC_PRBS_MEAN_REGISTER',
'CAVITY_MANUAL_TEC_REGISTER',
'CAVITY_MAX_HEATSINK_TEMP_REGISTER',
'HEATER_CNTRL_STATE_REGISTER',
'HEATER_CNTRL_GAIN_REGISTER',
'HEATER_CNTRL_QUANTIZE_REGISTER',
'HEATER_CNTRL_UBIAS_SLOPE_REGISTER',
'HEATER_CNTRL_UBIAS_OFFSET_REGISTER',
'HEATER_CNTRL_MARK_MIN_REGISTER',
'HEATER_CNTRL_MARK_MAX_REGISTER',
'HEATER_CNTRL_MANUAL_MARK_REGISTER',
'VALVE_CNTRL_STATE_REGISTER',
'VALVE_CNTRL_SOLENOID_VALVES_REGISTER',
'VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER',
'VALVE_CNTRL_USER_INLET_VALVE_REGISTER',
'VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER',
'VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER',
'VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER',
'VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER',
'VALVE_CNTRL_INLET_VALVE_MIN_REGISTER',
'VALVE_CNTRL_INLET_VALVE_MAX_REGISTER',
'VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER',
'VALVE_CNTRL_INLET_VALVE_DITHER_REGISTER',
'VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER',
'VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER',
'VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER',
'VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER',
'VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER',
'VALVE_CNTRL_OUTLET_VALVE_DITHER_REGISTER',
'VALVE_CNTRL_THRESHOLD_STATE_REGISTER',
'VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER',
'VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER',
'VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER',
'VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER',
'VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER',
'VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER',
'VALVE_CNTRL_SEQUENCE_STEP_REGISTER',
'ANALYZER_TUNING_MODE_REGISTER',
'TUNER_SWEEP_RAMP_HIGH_REGISTER',
'TUNER_SWEEP_RAMP_LOW_REGISTER',
'TUNER_WINDOW_RAMP_HIGH_REGISTER',
'TUNER_WINDOW_RAMP_LOW_REGISTER',
'TUNER_SWEEP_DITHER_HIGH_OFFSET_REGISTER',
'TUNER_SWEEP_DITHER_LOW_OFFSET_REGISTER',
'TUNER_WINDOW_DITHER_HIGH_OFFSET_REGISTER',
'TUNER_WINDOW_DITHER_LOW_OFFSET_REGISTER',
'PZT_OFFSET_VIRTUAL_LASER1',
'PZT_OFFSET_VIRTUAL_LASER2',
'PZT_OFFSET_VIRTUAL_LASER3',
'PZT_OFFSET_VIRTUAL_LASER4',
'PZT_OFFSET_VIRTUAL_LASER5',
'PZT_OFFSET_VIRTUAL_LASER6',
'PZT_OFFSET_VIRTUAL_LASER7',
'PZT_OFFSET_VIRTUAL_LASER8',
'VIRTUAL_LASER_REGISTER',
'SPECT_CNTRL_STATE_REGISTER',
'SPECT_CNTRL_MODE_REGISTER',
'SPECT_CNTRL_ACTIVE_SCHEME_REGISTER',
'SPECT_CNTRL_NEXT_SCHEME_REGISTER',
'SPECT_CNTRL_SCHEME_ITER_REGISTER',
'SPECT_CNTRL_SCHEME_ROW_REGISTER',
'SPECT_CNTRL_DWELL_COUNT_REGISTER',
'SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER',
'SPECT_CNTRL_DITHER_MODE_TIMEOUT_REGISTER',
'SPECT_CNTRL_RAMP_MODE_TIMEOUT_REGISTER',
'RDFITTER_MINLOSS_REGISTER',
'RDFITTER_MAXLOSS_REGISTER',
'RDFITTER_LATEST_LOSS_REGISTER',
'RDFITTER_IMPROVEMENT_STEPS_REGISTER',
'RDFITTER_START_SAMPLE_REGISTER',
'RDFITTER_FRACTIONAL_THRESHOLD_REGISTER',
'RDFITTER_ABSOLUTE_THRESHOLD_REGISTER',
'RDFITTER_NUMBER_OF_POINTS_REGISTER',
'RDFITTER_MAX_E_FOLDINGS_REGISTER',
'RDFITTER_META_BACKOFF_REGISTER',
'RDFITTER_META_SAMPLES_REGISTER',
'SENTRY_LOWER_LIMIT_TRIPPED_REGISTER',
'SENTRY_UPPER_LIMIT_TRIPPED_REGISTER',
'SENTRY_LASER1_TEMPERATURE_MIN_REGISTER',
'SENTRY_LASER1_TEMPERATURE_MAX_REGISTER',
'SENTRY_LASER2_TEMPERATURE_MIN_REGISTER',
'SENTRY_LASER2_TEMPERATURE_MAX_REGISTER',
'SENTRY_LASER3_TEMPERATURE_MIN_REGISTER',
'SENTRY_LASER3_TEMPERATURE_MAX_REGISTER',
'SENTRY_LASER4_TEMPERATURE_MIN_REGISTER',
'SENTRY_LASER4_TEMPERATURE_MAX_REGISTER',
'SENTRY_ETALON_TEMPERATURE_MIN_REGISTER',
'SENTRY_ETALON_TEMPERATURE_MAX_REGISTER',
'SENTRY_WARM_BOX_TEMPERATURE_MIN_REGISTER',
'SENTRY_WARM_BOX_TEMPERATURE_MAX_REGISTER',
'SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER',
'SENTRY_WARM_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER',
'SENTRY_CAVITY_TEMPERATURE_MIN_REGISTER',
'SENTRY_CAVITY_TEMPERATURE_MAX_REGISTER',
'SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MIN_REGISTER',
'SENTRY_HOT_BOX_HEATSINK_TEMPERATURE_MAX_REGISTER',
'SENTRY_DAS_TEMPERATURE_MIN_REGISTER',
'SENTRY_DAS_TEMPERATURE_MAX_REGISTER',
'SENTRY_LASER1_CURRENT_MIN_REGISTER',
'SENTRY_LASER1_CURRENT_MAX_REGISTER',
'SENTRY_LASER2_CURRENT_MIN_REGISTER',
'SENTRY_LASER2_CURRENT_MAX_REGISTER',
'SENTRY_LASER3_CURRENT_MIN_REGISTER',
'SENTRY_LASER3_CURRENT_MAX_REGISTER',
'SENTRY_LASER4_CURRENT_MIN_REGISTER',
'SENTRY_LASER4_CURRENT_MAX_REGISTER',
'SENTRY_CAVITY_PRESSURE_MIN_REGISTER',
'SENTRY_CAVITY_PRESSURE_MAX_REGISTER',
'SENTRY_AMBIENT_PRESSURE_MIN_REGISTER',
'SENTRY_AMBIENT_PRESSURE_MAX_REGISTER']

class RDFrequencyConverterProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr, SharedTypes.RPC_PORT_FREQ_CONVERTER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName=NameString)
            self.initialized = True

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr, SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName=NameString)
            self.initialized = True

class MeasurementSystemProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr, SharedTypes.RPC_PORT_MEAS_SYSTEM)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName=NameString)
            self.initialized = True

Driver = DriverProxy().rpc
MeasurementSystem = MeasurementSystemProxy().rpc
RDFrequencyConverter = RDFrequencyConverterProxy().rpc

class SandboxFrame(SandboxGUI):
    def __init__(self,*a,**k):
        SandboxGUI.__init__(self,*a,**k)
        self.waveform = Series(5000)
        self.waveformAnalysis1 = Series(5000)
        self.waveformAnalysis2 = Series(5000)
        self.waveformSensor1 = Series(5000)
        self.waveformSensor2 = Series(5000)
        self.testWaveform = Series(5000)
        self.waveformSensorStream1 = Series(5000)
        self.waveformSensorStream2 = Series(5000)
        self.graphPanel1.SetGraphProperties(xlabel='waveNumber',timeAxes=(False,False),ylabel='uncorrectedAbsorbance',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.graphPanel1.AddSeriesAsPoints(self.waveform,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        self.TestGraph1.SetGraphProperties(xlabel='X',timeAxes=(False,False),ylabel='Y',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.TestGraph1.AddSeriesAsPoints(self.testWaveform,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        self.keys=sorted(['ambientPressure','pztValue','uncorrectedAbsorbance','ratio1','laserTemperature','ratio2','etalonTemperature','schemeTable','tunerValue','timestamp','correctedAbsorbance','waveNumberSetpoint','ringdownThreshold','status','cavityPressure','subschemeId','lockerOffset','count','coarseLaserCurrent','waveNumber','laserUsed','sRDchemeRow','fineLaserCurrent','lockerError'])
        self.AnalyzeDataKeys = Data_analyse_iH2O_Keys
        self.SensorKeys = ['good','ver','source','mode','time','data']
        #self.SensorDataKeys = ['CavityPressure','CavityTemp','Laser2Temp','DasTemp']
        #self.SensorDataKeys = SensorStreamKeys
        self.SensorDataKeys = []
        self.update()
        self.eventCount=0
        self.keyY = 'uncorrectedAbsorbance'
        self.keyX = 'waveNumber'
        self.analyzeKey1 = 'CavityTemp'
        self.analyzeKey2 = 'CavityPressure'
        self.ListboxX.InsertItems(self.keys,0)
        self.ListboxY.InsertItems(self.keys,0)
        #self.Chart1LB.InsertItems(self.AnalyzeDataKeys,0)
        #self.Chart2LB.InsertItems(self.AnalyzeDataKeys,0)
        self.Chart1LB.SetStringSelection(self.analyzeKey1)
        self.Chart2LB.SetStringSelection(self.analyzeKey2)
        self.ListboxX.SetStringSelection(self.keyX)
        self.ListboxY.SetStringSelection(self.keyY)
        self.analyzeGraph1.SetGraphProperties(xlabel='',timeAxes=(True,False),ylabel='',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.analyzeGraph1.AddSeriesAsPoints(self.waveformAnalysis1,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        #self.analyzeGraph1.AddSeriesAsLine(self.waveformAnalysis1,colour='blue',width=2)
        self.analyzeGraph2.SetGraphProperties(xlabel='',timeAxes=(True,False),ylabel='',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.analyzeGraph2.AddSeriesAsPoints(self.waveformAnalysis2,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        #self.analyzeGraph2.AddSeriesAsLine(self.waveformAnalysis2,colour='blue',width=2)
        self.logListener = TextListener(None, port = SharedTypes.BROADCAST_PORT_EVENTLOG, retry = True, name = "Controller event log listener", streamFilter=self.logFilter, logFunc = Log)
        self.RDlistener = Listener(None,SharedTypes.BROADCAST_PORT_RD_RECALC,ProcessedRingdownEntryType,self.rdFilter,retry=True)
        self.dataListener = Listener(None, SharedTypes.BROADCAST_PORT_DATA_MANAGER,StringPickler.ArbitraryObject,self.dataFilter, retry = True)
        self.sensorListener = Listener(None, SharedTypes.BROADCAST_PORT_SENSORSTREAM, SensorEntryType, self.sensorFilter, retry = True)
        self.sensorKey1 = 'CavityTemp'
        self.sensorKey2 = 'CavityPressure'
        #self.SensorLB1.InsertItems(self.SensorDataKeys,0)
        #self.SensorLB2.InsertItems(self.SensorDataKeys,0)
        #self.SensorLB1.SetStringSelection(self.sensorKey1)
        #self.SensorLB2.SetStringSelection(self.sensorKey2)
        self.SensorChart1.SetGraphProperties(xlabel='',timeAxes=(True,False),ylabel='',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.SensorChart2.SetGraphProperties(xlabel='',timeAxes=(True,False),ylabel='',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.SensorChart1.AddSeriesAsPoints(self.waveformSensor1,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        self.SensorChart2.AddSeriesAsPoints(self.waveformSensor2,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        self.SensorStreamKey1 = 'Laser1Temp'
        self.SensorStreamKey2 = 'Laser2Temp'
        #self.SensorStreamListBox1.InsertItems(SensorStreamKeys,0)
        #self.SensorStreamListBox2.InsertItems(SensorStreamKeys,0)
        #self.SensorStreamListBox1.SetStringSelection(self.SensorStreamKey1)
        #self.SensorStreamListBox2.SetStringSelection(self.SensorStreamKey2)
        #self.SensorStreamGraph1.SetGraphProperties(xlabel='',timeAxes=(True,False),ylabel='',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        #self.SensorStreamGraph2.SetGraphProperties(xlabel='',timeAxes=(True,False),ylabel='',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        #self.SensorStreamGraph1.AddSeriesAsPoints(self.waveformSensorStream1,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        #self.SensorStreamGraph2.AddSeriesAsPoints(self.waveformSensorStream2,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        self.Timer = wx.Timer(self)
        self.Laser1Temp=0.0
        self.Laser4Temp=0.0
        self.Etalon1=0
        self.Reference1=0
        self.Etalon2=0
        self.Reference2=0
        self.EtalonTemp=0.0
        self.WarmBoxTemp=0.0
        self.WarmBoxHeatsink=0.0
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.Timer)
        self.DriverRegisterListBox.InsertItems(DASRegisterList,0)
        self.Timer.Start(1000)
        self.Buttoncolour = self.WLMPkScrnbutton.GetBackgroundColour()
        self.notebook_1.SetSelection(5)
        self.SensorDataList=[]
        self.analyze_iH20List=[]
        self.stateMachine=''
        self.state=''
        self.SMStatic=[]
        self.outputFName='tmp'
        self.outputToFile=False
        self.SMSuspend=False

    def update(self):
        pass

    def OnTimer(self, evt):
        self.graphPanel1.Update(delay=0)
        self.analyzeGraph1.Update(delay=0)
        self.analyzeGraph2.Update(delay=0)
        self.SensorChart1.Update(delay=0)
        self.SensorChart2.Update(delay=0)
        self.TestGraph1.Update(delay=0)
        #self.SensorStreamGraph1.Update(delay=0)
        #self.SensorStreamGraph2.Update(delay=0)

    def OnClear(self, event):
        self.waveform.Clear()
        self.update()

    def OnListBoxYSelected(self, event):
        self.keyY = self.ListboxY.GetStringSelection()
        self.waveform.Clear()
        self.update()
        xtime = self.keyX == 'timestamp'
        ytime = self.keyY == 'timestamp'
        self.graphPanel1.SetGraphProperties(xlabel=self.keyX,timeAxes=(xtime,ytime),ylabel=self.keyY,grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))

    def OnListBoxXSelected(self, event):
        self.keyX = self.ListboxX.GetStringSelection()
        self.waveform.Clear()
        self.update()
        xtime = self.keyX == 'timestamp'
        ytime = self.keyY == 'timestamp'
        self.graphPanel1.SetGraphProperties(xlabel=self.keyX,timeAxes=(xtime,ytime),ylabel=self.keyY,grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))

    def OnChart1LB(self, event):
        self.waveformAnalysis1.Clear()
        self.analyzeKey1 = self.Chart1LB.GetStringSelection()

    def OnChart2LB(self, event):
        self.waveformAnalysis2.Clear()
        self.analyzeKey2 = self.Chart2LB.GetStringSelection()

    def OnClearAnalzeButton(self, event):
        self.waveformAnalysis1.Clear()
        self.waveformAnalysis2.Clear()

    def OnSensorLB1(self, event):
        self.waveformSensor1.Clear()
        self.sensorKey1 = self.SensorLB1.GetStringSelection()

    def OnSensorLB2(self, event):
        self.waveformSensor2.Clear()
        self.sensorKey2 = self.SensorLB2.GetStringSelection()

    def OnSensorClearButton(self, event):
        self.waveformSensor1.Clear()
        self.waveformSensor2.Clear()

    def OnDriverAllVersionsButton(self, event):
        d = Driver.allVersions()
        s=''
        for k, v in d.items():
            s+="%s=%s\r\n" % (k, v)
        self.DriverTextCtrl.SetValue(s)

    def OnDriverDASGetTicksButton(self, event):
        v = Driver.dasGetTicks()
        self.DriverTextCtrl.SetValue(str(v))

    def OnDriverGetConfigFileButton(self, event):
        s = Driver.getConfigFile()
        self.DriverTextCtrl.SetValue(s)

    def OnDriverGetLockStatusButton(self, event):
        d = Driver.getLockStatus()
        s=''
        for k, v in d.items():
            s+="%s=%s\r\n" % (k, v)
        self.DriverTextCtrl.SetValue(s)

    def OnDriverGetPressureReadingButton(self, event):
        v = Driver.getPressureReading()
        self.DriverTextCtrl.SetValue(str(v))

    def OnDriverGetValveMaskButton(self, event):
        v = Driver.getValveMask()
        self.DriverTextCtrl.SetValue(str(v))

    def OnDriverGetHostTicksButton(self, event):
        v = Driver.hostGetTicks()
        self.DriverTextCtrl.SetValue(str(v))

    def OnDriverLoadINIFileButton(self, event):
        Driver.loadIniFile()
        self.DriverTextCtrl.Clear()

    def OnDriverReadSchemeSequenceButton(self, event):
        d = Driver.rdSchemeSequence()
        s=''
        for k, v in d.items():
            s+="%s=%s\r\n" % (k, v)
        self.DriverTextCtrl.SetValue(s)

    def OnDriverStopScanButton(self, event):
        Driver.stopScan()
        self.DriverTextCtrl.Clear()

    def OnDriverResynchDASButton(self, event):
        Driver.resyncDas()
        self.DriverTextCtrl.Clear()

    def OnStartEngineButton(self, event):
        Driver.startEngine()
        self.DriverTextCtrl.Clear()

    def OnDriverStartScan(self, event):
        Driver.startScan()
        self.DriverTextCtrl.Clear()

    def OnDriverRdDASRegButton(self, event):
        s = self.DriverRegisterTextCtrl.GetValue()
        v = Driver.rdDasReg(s)
        self.DriverTextCtrl.SetValue(str(v))

    def OnWrtDASRegButton(self, event):
        s = self.DriverRegisterTextCtrl.GetValue()
        v = self.DriverRegValueTextCtrl.GetValue()
        Driver.wrDasReg(s,v)

    def OnDriverRegisterListBox(self, event):
        s= self.DriverRegisterListBox.GetStringSelection()
        self.DriverRegisterTextCtrl.SetValue(s)

    def OnDriverHostReadyButton(self, event):
        v = self.DriverRegValueTextCtrl.GetValue()
        Driver.hostReady(v)

    def OnDriverRdSchemeButton(self, event):
        v = self.DriverRegValueTextCtrl.GetValue()
        d = Driver.rdScheme(int(v))
        s=''
        for k, v in d.items():
            s+="%s=%s\r\n" % (k, v)
        self.DriverTextCtrl.SetValue(s)

    def OnDriverRdValveSeqButton(self, event):
        l=Driver.rdValveSequence()
        s="%s" %l
        self.DriverTextCtrl.SetValue(s)

    def datetimeToTimestamp(self,t):
        ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
        td = t - ORIGIN
        return (td.days*86400 + td.seconds)*1000 + td.microseconds//1000

    def getTimestamp(self):
        return self.datetimeToTimestamp(datetime.datetime.utcnow())

    def OnSensorStreamListbox1(self, event):
        self.SensorStreamKey1 = self.SensorStreamListBox1.GetStringSelection()
        self.waveformSensorStream1.Clear()

    def OnSensorStreamListbox2(self, event):
        self.SensorStreamKey2 = self.SensorStreamListBox2.GetStringSelection()
        self.waveformSensorStream2.Clear()

    def OnHD5Viewerbutton(self, event):
        print "HD5Viewer..."
        os.system('R:\crd\SoftwareDevelopment\DataFileViewer\DatViewer4.py')
        self.TestResulttext_ctrl.AppendText("HD5 Viewer v4.0 Started...\r\n")
        event.Skip()

    def OnStartFlowbutton(self, event):
        self.TestResulttext_ctrl.Clear()
        print "StartFlow..."
        os.system('FlowController.exe')
        self.TestResulttext_ctrl.AppendText("Gas Flow Started...\r\n")
        event.Skip()

    def OnWLMPkScrnbutton(self, event):
        return
        if self.Commenttext_ctrl.Value == "Lsr1 Sweeping":
            self.TestResulttext_ctrl.Clear()
            s='LASER1_TEMP_CNTRL_STATE_REGISTER'
            v = 1
            Driver.wrDasReg(s,v)
            self.Commenttext_ctrl.Value = ""
            print "WLMPeakScrn, Laser1 Sweep stopped."
            self.WLMPkScrnbutton.SetBackgroundColour(self.Buttoncolour)
            self.TestResulttext_ctrl.AppendText("WLMPeakScrn, Laser1 Sweep stopped.")
        else:
            self.TestResulttext_ctrl.Clear()
            print "WLMPeakScrn, Laser1 Sweeping..."

            self.TestResulttext_ctrl.AppendText("WLM Peak Screen...\r\n\r\n")
            s="Look for flatness/saturation at the highest peaks in the WLM tab graph of Laser1 (corresponds with low temp in the sweep).  A rule of thumb is that the peaks s/b < ~55000 and the WLM Ratios > ~ 2.0, otherwise we may need to reduce the WLMEC resistors.\r\n"
            self.TestResulttext_ctrl.AppendText(s)
            s='\r\nThe WLMEC components are (R1 & R3: change to 2.2 kohms), (R5 & R7: change to 1.8 kohms)\r\n'
            self.TestResulttext_ctrl.AppendText(s)

            s = 'LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER'
            v=8.0
            Driver.wrDasReg(s,v)

            s='LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER'
            v = 30.0
            Driver.wrDasReg(s,v)

            s='LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER'
            v = 0.05
            Driver.wrDasReg(s,v)

            s='LASER1_TEMP_CNTRL_STATE_REGISTER'
            v = 3
            Driver.wrDasReg(s,v)
            self.WLMPkScrnbutton.SetBackgroundColour('Yellow')
            self.Commenttext_ctrl.Value = "Lsr1 Sweeping"
        event.Skip()

    def OnSchemeBuildbutton(self, event): # wxGlade: SandboxGUI.<event_handler>
        HBCfg=getConfig("C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini")
        FSR=float(HBCfg['AUTOCAL']['CAVITY_FSR'])
        self.schemeBuild(FSR)
        event.Skip()

    def getSystemNum(self):
        snum=2999
        try:
            snum=Driver.fetchObject("LOGIC_EEPROM")[0]["AnalyzerNum"]
        except:
            print 'getSystemNum failed\r\n'
        return snum

    def schemeBuild(self, FSR):
        num=int(self.MsgBox("Which one to Build?", "1=iH20, 2=CO2, 3=iCO2"))
        self.buildScheme(num,FSR)

    def buildScheme(self, num, FSR):
        fsrComment='#Using FSR=%f\r\n'%FSR
        systemNum=self.getSystemNum()
        #systemNum=2118#self.getSystemNum()
        self.Output("System Num=%s\r\n"%(systemNum))
        self.Output('Using FSR=%f\r\n'%FSR)
        trgtDir='C:\Picarro\G2000\InstrConfig\Integration\Schemes'
        trgtDir2='C:\Picarro\G2000\InstrConfig\Schemes'
        if num==1:
            self.Output('Writing Scheme for iH20\r\n\r\n')
            self.Output('Adjusting iH20 peaks\r\n')
            if not os.path.exists(trgtDir):
                os.mkdir(trgtDir)
            peak = 7183.9728
            template1 = r'C:\Picarro\G2000\InstrConfig\Schemes\HBDS213x_Nominal_wCal_Quad_Fast_v36.sch'
            refName1=trgtDir+'\HBDS%s_Nominal_wCal_Quad_Fast_v36_preAdjust.sch'%systemNum
            shutil.copy(template1,refName1)
            sp = file(refName1,"r")

            short_fname1='/HBDS%s_Nominal_wCal_Quad_Fast_v36.sch'%systemNum
            fname1 = trgtDir+'\\'+short_fname1
            fname2 = 'C:\Picarro\G2000\InstrConfig\Schemes\HBDS%s_Nominal_wCal_Quad_Fast_v36.sch'%systemNum

            modeFile = 'C:\Picarro\G2000\AppConfig\ModeInfo\iH2O_mode.mode'
            fpMode = file(modeFile,"r")

            self.Output('Installing new scheme name in %s\r\n'%modeFile)
            lst=fpMode.readlines()
            fpMode.close()
            nElem=len(lst)
            n=0
            while n<nElem:
                s=lst[n]
                word=s.rsplit(' ')
                if word[0]=='Scheme_2_Path':
                    s=word[0] + ' = ../../InstrConfig/Schemes' + short_fname1 + '\r\n'
                    self.Output(s+'\r\n')
                lst[n]=s
                n+=1
            fpModew = file(modeFile,"w")
            fpModew.writelines(lst)
            fpModew.close()

            lp = file(fname1,"w")
            print >>lp, int(sp.readline()) # nrepeat
            numEntries = int(sp.readline())
            print >>lp, numEntries
            first=True
            schemeTail=[]
            for i in range(numEntries):
                toks = sp.readline().split()
                toks += (6-len(toks)) * ["0"]
                waveNum = float(toks[0])
                waveNum = peak + FSR * round((waveNum - peak)/FSR)
                toks[0] = "%.5f" % (waveNum,)
                print >>lp, " ".join(toks)
                if first:
                    first=False
                else:
                    s= " ".join(toks)
                    schemeTail.append(s+'\n')
            print >>lp, fsrComment
            sp.close()
            lp.close()
            shutil.copy(fname1,fname2)
            self.Output('Writing FSR Adjusted Scheme to %s\r\n'%fname2)

        elif num==2:
            self.Output('Writing Schemes for CO2\r\n\r\n')
            self.Output('Adjusting CH4 peaks\r\n')
            self.Output('Adjusting CO2 peaks\r\n')
            self.Output('Adjusting H20 peaks\r\n\r\n')
            if not os.path.exists(trgtDir):
                os.mkdir(trgtDir)
            peakCH4 = 6057.09000
            peakCO2 = 6237.40800
            peakH2O = 6057.80000    #bug - it was 6257.80000

            template1 = r'R:\crd_G2000\CFxDS\CFADS_Config\Schemes\Beta_CFADS_nocal_v2.sch'
            template2 = r'R:\crd_G2000\CFxDS\CFADS_Config\Schemes\Beta_CFADS_cal_v2.sch'

            refName1=trgtDir+'\Beta_CFADS_nocal_v2.sch'
            refName2=trgtDir+'\Beta_CFADS_cal_v2.sch'

            shutil.copy(template1,refName1)
            shutil.copy(template2,refName2)

            sp = file(refName1,"r")
            sp2 = file(refName2,"r")

            short_fname1="CFADS%s_CFADS_nocal_v2.sch"%systemNum
            fname1 = trgtDir+'\\'+short_fname1
            short_fname2="CFADS%s_CFADS_cal_v2.sch"%systemNum
            fname2 = trgtDir+'\\'+short_fname2

            modeFile = 'C:\Picarro\G2000\AppConfig\ModeInfo\CFADS_mode.mode'
            fpMode = file(modeFile,"r")

            self.Output('Installing new scheme names in %s\r\n'%modeFile)
            lst=fpMode.readlines()
            fpMode.close()
            nElem=len(lst)
            n=0
            while n<nElem:
                s=lst[n]
                word=s.rsplit(' ')
                if word[0]=='Scheme_1_Path':
                    s=word[0] + ' = ../../InstrConfig/Schemes/' + short_fname1 + '\r\n'
                    self.Output(s+'\r\n')
                if word[0]=='Scheme_2_Path':
                    s=word[0] + ' = ../../InstrConfig/Schemes/' + short_fname2 + '\r\n'
                    self.Output(s+'\r\n')
                lst[n]=s
                n+=1
            fpModew = file("C:\Picarro\G2000\AppConfig\ModeInfo\CFADS_mode.mode","w")
            fpModew.writelines(lst)
            fpModew.close()

            lp1 = file(fname1,"w")
            lp2 = file(fname2,"w")

            print >>lp1, int(sp.readline()) # nrepeat
            numEntries = int(sp.readline())
            print >>lp1, numEntries
            for i in range(numEntries):
                toks = sp.readline().split()
                toks += (6-len(toks)) * ["0"]
                waveNum = float(toks[0])
                id = int(toks[2])
                if id in [8217,40985,25,4121,36889,16409]:
                    waveNum = peakCH4 + FSR * round((waveNum - peakCH4)/FSR)
                if id in [10,4106,36874,12,4108,36876,8202,40970,8204,40972]:
                    waveNum = peakCO2 + FSR * round((waveNum - peakCO2)/FSR)
                if id in [4107,36875,16410,40971,8203]:
                    waveNum = peakH2O + FSR * round((waveNum - peakH2O)/FSR)
                toks[0] = "%.5f" % (waveNum,)
                print >>lp1, " ".join(toks)
            sp.close()
            lp1.close()
            self.Output("Wrote file %s\r\n\r\n" % (fname1,))

            print >>lp2, int(sp2.readline()) # nrepeat
            numEntries = int(sp2.readline())
            print >>lp2, numEntries
            for i in range(numEntries):
                toks = sp2.readline().split()
                toks += (6-len(toks)) * ["0"]
                waveNum = float(toks[0])
                id = int(toks[2])
                if id in [8217,40985,25,4121,36889,16409]:
                    waveNum = peakCH4 + FSR * round((waveNum - peakCH4)/FSR)
                if id in [10,4106,36874,12,4108,36876,8202,40970,8204,40972]:
                    waveNum = peakCO2 + FSR * round((waveNum - peakCO2)/FSR)
                if id in [4107,36875,16410,40971,8203]:
                    waveNum = peakH2O + FSR * round((waveNum - peakH2O)/FSR)
                toks[0] = "%.5f" % (waveNum,)
                print >>lp2, " ".join(toks)
            sp.close()
            lp2.close()
            self.Output("Wrote file %s\r\n\r\n" % (fname2,))

            #Install Quad Peaks at 6237.40800
            fnum=1
            while fnum<3:
                fp = file(fname1,"r")
                if fnum==2:
                    self.Output('___________________________\r\n\r\n')
                    fp = file(fname2,"r")

                self.Output('Installing Quadpeaks in %s\r\n'%fname1)
                lst=fp.readlines()
                nElem=len(lst)
                n=0
                m=0
                k=0
                while n<nElem:
                    s=lst[n]
                    word=s.rsplit(' ')
                    if float(word[0])==peakCO2:
                        #on a peak
                        m+=1
                        s=''
                        mult=1.0
                        if k==1 or k==3:
                            mult=-1.0
                        if m==1:
                            word[0]="%0.5f"%(peakCO2-mult*0.00060)
                            s=' '.join(word)
                        elif m==2:
                            word[0]="%0.5f"%(peakCO2-mult*0.00030)
                            s=' '.join(word)
                        elif m==3:
                            s=lst[n]
                        elif m==4:
                            word[0]="%0.5f"%(peakCO2+mult*0.00030)
                            s=' '.join(word)
                        elif m==5:
                            word[0]="%0.5f"%(peakCO2+mult*0.00060)
                            s=' '.join(word)
                            m=0
                            k+=1
                        self.Output(s)
                    else:
                        #not on a peak
                        s=lst[n]
                        self.Output(s)
                    lst[n]=s
                    n+=1
                if fnum==1:
                    fp1 = file(fname1,"w")
                    fp1.writelines(lst)
                    fp1.write(fsrComment)
                    fp1.close()
                    fname2_1 = trgtDir2+'\\'+short_fname1
                    fp1 = file(fname2_1,"w")
                    fp1.writelines(lst)
                    fp1.write(fsrComment)
                    fp1.close()
                elif fnum==2:
                    fp2 = file(fname2,"w")
                    fp2.writelines(lst)
                    fp2.write(fsrComment)
                    fp2.close()
                    fname2_2 = trgtDir2+'\\'+short_fname2
                    fp2 = file(fname2_2,"w")
                    fp2.writelines(lst)
                    fp2.write(fsrComment)
                    fp2.close()
                fnum+=1
        elif num==3:
            #Todo - what is the correct # for the peakH20?????????????????????????????????????????????????????????????????????????????????????????
            self.Output('Writing Schemes for iCO2\r\n\r\n')

            self.Output('Adjusting CH4 peaks\r\n')
            self.Output('Adjusting CO2 peaks\r\n\r\n')
            if not os.path.exists(trgtDir):
                os.mkdir(trgtDir)

            peakCH4 = 6251.3145
            peakCO2 = 6251.758
            peakH2O = 6251.75800  #6251.75800  really?????  same as CO2????
            template1 = r'R:\crd_G2000\CxDS\CBDS_Config\Schemes\CBDSxx_v40_VL_C12_C13_Zippy_cal.sch'
            template2 = r'R:\crd_G2000\CxDS\CBDS_Config\Schemes\CBDSxx_v40_VL_C12_C13_Zippy_nocal.sch'

            refName1=trgtDir+'\CBDSxx_v40_VL_C12_C13_Zippy_cal.sch'
            refName2=trgtDir+'\CBDSxx_v40_VL_C12_C13_Zippy_nocal.sch'

            shutil.copy(template1,refName1)
            shutil.copy(template2,refName2)

            sp = file(refName1,"r")
            sp2 = file(refName2,"r")

            short_fname1="CBDS%s_v40_VL_C12_C13_Zippy_nocal.sch"%systemNum
            fname1IN = trgtDir+'\\'+short_fname1
            short_fname2="CBDS%s_v40_VL_C12_C13_Zippy_cal.sch"%systemNum
            fname2IN = trgtDir+'\\'+short_fname2

            sp = file(refName1,"r")
            sp2 = file(refName2,"r")

            fname1 = trgtDir+"\CBDS%s_v40_VL_C12_C13_Zippy_cal.sch"%systemNum
            fname2 = trgtDir+"\CBDS%s_v40_VL_C12_C13_Zippy_nocal.sch"%systemNum

            lp1 = file(fname1,"w")
            lp2 = file(fname2,"w")

            modeFile = 'C:\Picarro\G2000\AppConfig\ModeInfo\iCO2_mode.mode'
            fpMode = file(modeFile,"r")

            self.Output('Installing new scheme names in %s\r\n'%modeFile)
            lst=fpMode.readlines()
            fpMode.close()
            nElem=len(lst)
            n=0
            while n<nElem:
                s=lst[n]
                word=s.rsplit(' ')
                if word[0]=='Scheme_1_Path':
                    s=word[0] + ' = ../../InstrConfig/Schemes/' + short_fname1 + '\r\n'
                    self.Output(s+'\r\n')
                if word[0]=='Scheme_2_Path':
                    s=word[0] + ' = ../../InstrConfig/Schemes/' + short_fname2 + '\r\n'
                    self.Output(s+'\r\n')
                lst[n]=s
                n+=1
            fpModew = file(modeFile,"w")
            fpModew.writelines(lst)
            fpModew.close()

            print >>lp1, int(sp.readline())
            numEntries = int(sp.readline())
            print >>lp1, numEntries
            for i in range(numEntries):
                toks = sp.readline().split()
                toks += (6-len(toks)) * ["0"]
                waveNum = float(toks[0])
                id = int(toks[2])
                if id in [106,4202,36970,32874,1,156,4252,32924,8298,41066,8348,12444,41116]:
                    waveNum = peakCH4 + FSR * round((waveNum - peakCH4)/FSR)
                if id in [105,4201,36969,32873,4096,0,32768,32923,32873,155,32923,8347,12443,41115,8192,8297,12443,40960,41115,41065]:
                    waveNum = peakCO2 + FSR * round((waveNum - peakCO2)/FSR)
                if id in [4251,32923,4252,32877,8347,32923,8301,32877]:
                    waveNum = peakH2O + FSR * round((waveNum - peakH2O)/FSR)
                toks[0] = "%.5f" % (waveNum,)
                print >>lp1, " ".join(toks)
            sp.close()
            print >>lp1, fsrComment
            lp1.close()
            self.Output("Wrote file %s\r\n\r\n" % (fname1,))

            print >>lp2, int(sp2.readline()) # nrepeat
            numEntries = int(sp2.readline())
            print >>lp2, numEntries
            for i in range(numEntries):
                toks = sp2.readline().split()
                toks += (6-len(toks)) * ["0"]
                waveNum = float(toks[0])
                id = int(toks[2])
                if id in [106,4202,36970,32874,1,156,4252,32924,8298,41066,8348,12444,41116]:
                    waveNum = peakCH4 + FSR * round((waveNum - peakCH4)/FSR)
                if id in [105,4201,36969,32873,4096,0,32768,32923,32873,155,32923,8347,12443,41115,8192,8297,12443,40960,41115,41065]:
                    waveNum = peakCO2 + FSR * round((waveNum - peakCO2)/FSR)
                if id in [4251,32923,4252,32877,8347,32923,8301,32877]:
                    waveNum = peakH2O + FSR * round((waveNum - peakH2O)/FSR)
                toks[0] = "%.5f" % (waveNum,)
                print >>lp2, " ".join(toks)
            sp.close()
            print >>lp2, fsrComment
            lp2.close()
            self.Output("Wrote file %s\r\n" % (fname2,))

    def OnCalibrateSystemButton(self, event):
        self.TestResulttext_ctrl.Clear()
        self.Commenttext_ctrl.Value = ""

        os.chdir(INTEGRATION_DIR)
        wbCal=os.path.join(CAL_DIR, WARMBOX_CAL)+".ini"
        hbCal=os.path.join(CAL_DIR, HOTBOX_CAL)+".ini"
        FreqConverter.loadWarmBoxCal(wbCal)
        FreqConverter.loadHotBoxCal(hbCal)

        try:
            iniList = [ini for ini in os.listdir(".") if (ini.startswith("CalibrateSystem") and ini.endswith(".ini"))]
            for ini in iniList:
                cmd = "%s -c %s" % (os.path.join(HOSTEXE_DIR, "CalibrateSystem.exe"), ini)
                print cmd
                os.system(cmd)
            self.TestResulttext_ctrl.AppendText("Calibrate System finished.\n")
        except Exception, err:
            self.TestResulttext_ctrl.AppendText("%s\n" % err)
        event.Skip()

    def OnViewSystemCalButton(self, event):
        self.TestResulttext_ctrl.Clear()
        self.Commenttext_ctrl.Value = ""
        os.chdir(INTEGRATION_DIR)
        calList = [cal for cal in os.listdir(".") if (cal.startswith("CalibrateSystem") and cal.endswith(".txt"))]
        CalNum = 0
        for cal in calList:
            s=str(CalNum)+" = "+cal+"\r\n"
            print s
            self.TestResulttext_ctrl.AppendText(s)
            CalNum=CalNum+1

        num=self.MsgBox("Which one to View?", "Pick a CalibrateSystem file number...")
        self.TestResulttext_ctrl.Clear()
        fName=calList[int(num)]
        s="you picked "+fName+'\r\n'
        print s
        self.TestResulttext_ctrl.AppendText(s)
        fp=file(fName,"r")
        s=fp.read()
        self.TestResulttext_ctrl.AppendText(s)
        fp.seek(0)
        lst=fp.readlines()

        self.TestResulttext_ctrl.AppendText("============Summary=========\r\n")
        #Final SDev
        sDevs=[sd for sd in lst if (sd.startswith("Standard deviation:"))]
        finalSD=str(sDevs[len(sDevs)-1]).rstrip()
        s="Final " + finalSD + "                :   s/b below 250.0"+'\r\n'
        print s
        self.TestResulttext_ctrl.AppendText(s)

        #Cavity FSR
        fsr=[fsr for fsr in lst if (fsr.startswith("Cavity FSR  (WLM radians):"))]
        finalFsr=str(fsr[len(fsr)-1]).rstrip()
        s= finalFsr + "   :   s/b below .08 +/- .005"+'\r\n'
        print s
        self.TestResulttext_ctrl.AppendText(s)

        #Sensitivity
        sen=[sen for sen in lst if (sen.startswith("Sensitivity (digU/FSR):"))]
        finalSen=str(sen[len(sen)-1]).rstrip()
        s= finalSen + "                 :   s/b <= 35000"+'\r\n'
        print s
        self.TestResulttext_ctrl.AppendText(s)

        #Cavity free spectral range
        cfsr=[cfsr for cfsr in lst if (cfsr.startswith("Cavity free spectral range"))]
        finalcfsr=str(cfsr[len(cfsr)-1]).rstrip()
        alist =finalcfsr.split(' ')
        fcsr=alist[5]# wavenumbers
        s= "Cav FSR (Wave#): "+str(fcsr)+"                 :   s/b ~.0206 +/- .0005"+'\r\n'
        print s
        self.TestResulttext_ctrl.AppendText(s)

        event.Skip()

    def setMFC(self,chnl2,chnl3):
        self.Output('Set MFC Flows to Chnl2=%d Chnl3=%d\r\n'%(chnl2,chnl3))
        mfc = MFC()
        mfc.setFlow(2, chnl2)
        mfc.setFlow(3, chnl3)
        mfc.TurnOn()
        mfc.close()

    def set20K(self):
        MfcCfg=getConfig("R:\crd\TestSoftware\Configuration\MFC_iH2O_Conc20000.ini")
        ranges=MfcCfg['Range']
        flows=MfcCfg['Steps']['0']
        word=flows.rsplit(' ')
        flow1=word[1]
        flow2=word[2]
        self.setMFC(int(flow1),int(flow2))
        #self.setMFC(int(50),int(55))

    def OnSet20Kbutton(self, event):
        self.set20K()
        event.Skip()

    def OnSetFitParmsbutton(self, event):
        self.stateMachine='SetFit'
        self.state='Start'
        self.SMSetFit()
        event.Skip()

    def OnFSRSquishbutton(self, event):
        self.stateMachine='FSRSquish'
        self.state='Start'
        self.SMFSRSquish()
        event.Skip()

    def showSM(self):
        self.Commenttext_ctrl.Value = self.stateMachine + ':' + self.state

    def outSM(self):
        s = '\r\n--->' + self.stateMachine + ':' + self.state + '\r\n'
        self.Output(s)

    def changeState(self, newState):
        self.state = newState
        self.outSM()
    """
    def restartMode(self):
        RPC_PORT_MEAS_SYSTEM        = 50070
        RPC_PORT_DATA_MANAGER       = 50160
        APP_NAME = "ConfigTool"

        CRDS_MeasSys = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM, APP_NAME, IsDontCareConnection = False)
        CRDS_DataManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, APP_NAME, IsDontCareConnection = False)

        self.Output('Restarting Measurement System Mode and Data Manager\r\n')
        CRDS_MeasSys.Mode_Set(self.mode)
        time.sleep(5)
        CRDS_DataManager.Mode_Set(self.mode)
    """

    def SMFSRSquish(self):
        squishStabilizationGate=0.04
        minimumSquishReadingsPerPass=10#100
        numSquishReadingsToCalculateDeltaFrom=3#30
        trgtDir='C:\Picarro\G2000\InstrConfig\Integration\FSRSquish'
        self.Commenttext_ctrl.Value = self.state
        self.showSM()
        correctedFSR=0.0
        if(self.state=='Start'):
            systemNum=self.getSystemNum()
            print systemNum
            startTime=time.strftime('%m%d%y_%H%M%S')
            if not os.path.exists(trgtDir):
                os.mkdir(trgtDir)
            self.outputFName='C:\Picarro\G2000\InstrConfig\Integration\FSRSquish\SquishLogHBDS%s_%s.txt'%(systemNum,startTime)
            self.outputToFile=True
            self.clearOutputs()
            self.Output('Starting State Machine '+self.stateMachine+'\r\n')
            self.outSM()
            self.SMStatic = []
            startScheme='C:\Picarro\G2000\InstrConfig\Schemes\HBDS%s_Nominal_wCal_Quad_Fast_v36.sch'%systemNum
            savedSchemeName='C:\Picarro\G2000\InstrConfig\Integration\FSRSquish\HBDS%s_Nominal_wCal_Quad_Fast_v36.sch_saved_%s'%(systemNum,startTime)
            shutil.copy(startScheme,savedSchemeName)
            startDataLog('FSRSquish')
            self.changeState('WaitForMeasuring')
            return
        elif(self.state=='WaitForMeasuring'):
            #<<<< Wait for Measuring
            if self.analyze_iH20List==[]:
                self.Output(".")
                return
            else:
                self.Output("Measuring\r\n")
                self.changeState('SetFit2ISOBox')
                return
        elif(self.state=='SetFit2ISOBox'):
            #set up fitter for isobox
            FtrCfg=getConfig("C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini")
            self.Output("In file C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini:\r\n")
            FtrCfg['Autodetect_enable']=0
            self.Output("Setting Autodetect_enable = 0\r\n")
            FtrCfg['N2_flag']=1
            self.Output("Setting N2_flag = 1\r\n")
            FtrCfg.write()
            self.SetValveReg(4)     #isoBox is on Valve3
            self.fitterRestart()
            self.analyze_iH20List=[]
            self.set20K()
            self.changeState('Wait4Conc20000_N2')
            return
        elif(self.state=='Wait4Conc20000_N2'):
            #wait for h2O concentration of 20000 ppmv +/-2000
            h2o = self.analyze_iH20List['h2o_conc']
            s= 'h2o_conc = %f\r\n'%h2o
            self.Output(s)
            if h2o>=18000 and h2o<=22000:
                self.changeState('Wait4StableSquish')
                return
            else:
                self.Output(".")
                return
        elif(self.state=='Wait4StableSquish'):
            #wait for h2O_squish_a to stop varying
            h2O_squish_a=self.analyze_iH20List['h2o_squish_a']
            self.SMStatic.append(h2O_squish_a)
            start=len(self.SMStatic)-30
            tail=self.SMStatic[start:]
            maxSquish=max(tail)
            minSquish=min(tail)
            deltaSquish=maxSquish-minSquish
            s='Squish=%f delta=%f max=%f min=%f\r\n'%(h2O_squish_a, deltaSquish, maxSquish, minSquish)
            self.Output(s)
            if len(self.SMStatic)>minimumSquishReadingsPerPass and len(tail)>=numSquishReadingsToCalculateDeltaFrom and deltaSquish<=squishStabilizationGate:
                self.Output('h2O_squish_a squish stablized, last %d readings varied by %f, Gate is <=%f\r\n'%(numSquishReadingsToCalculateDeltaFrom, deltaSquish,squishStabilizationGate))
                self.changeState('AdjustFSR')
                return
            else:
                #self.Output(".")
                return
        elif(self.state=='AdjustFSR'):
            #read these 3 values from the GUI for isoBox
            h2O_squish_a=self.analyze_iH20List['h2o_squish_a']
            self.Output('h2O_squish_a = %.12f\r\n'%h2O_squish_a)
            HBCfg=getConfig("C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini")
            FSR=float(HBCfg['AUTOCAL']['CAVITY_FSR'])
            self.Output('FSR = %.12f\r\n'%FSR)
            correctedFSR=FSR*(1.0+(1.0/50.0)*math.atan(h2O_squish_a))
            HBCfg['AUTOCAL']['CAVITY_FSR']=correctedFSR
            HBCfg.write()
            self.Output('correctedFSR = %.12f\r\n'%correctedFSR)
            self.Output('Rebuilding Scheme to corrected FSR\r\n')
            self.buildScheme(1,FSR)
            endTime=time.strftime('%m%d%y_%H%M%S')
            systemNum=self.getSystemNum()
            startScheme='C:\Picarro\G2000\InstrConfig\Schemes\HBDS%s_Nominal_wCal_Quad_Fast_v36.sch'%systemNum
            savedSchemeName='C:\Picarro\G2000\InstrConfig\Integration\FSRSquish\HBDS%s_Nominal_wCal_Quad_Fast_v36.sch_calculated_%s'%(systemNum,endTime)
            shutil.copy(startScheme,savedSchemeName)
            self.changeState('RestartFitter')
            return
        elif(self.state=='RestartFitter'):
            self.fitterRestart()
            self.SMStatic=[]
            self.changeState('Wait4StableLowSquish')
            return
        elif(self.state=='Wait4StableLowSquish'):
            #wait for h2O_squish_a to stop varying
            h2O_squish_a=self.analyze_iH20List['h2o_squish_a']
            self.SMStatic.append(h2O_squish_a)
            start=len(self.SMStatic)-numSquishReadingsToCalculateDeltaFrom
            tail=self.SMStatic[start:]
            maxSquish=max(tail)
            minSquish=min(tail)
            deltaSquish=maxSquish-minSquish
            s='Squish=%f delta=%f max=%f min=%f\r\n'%(h2O_squish_a, deltaSquish, maxSquish, minSquish)
            self.Output(s)
            if len(self.SMStatic)>minimumSquishReadingsPerPass and len(tail)>=numSquishReadingsToCalculateDeltaFrom and deltaSquish<=squishStabilizationGate:
                systemNum=self.getSystemNum()
                self.Output('h2O_squish_a squish stablized, last %d readings varied by %f, Gate is <=%f\r\n'%(numSquishReadingsToCalculateDeltaFrom,deltaSquish,squishStabilizationGate))
                squish=average(tail)
                self.Output('Mean of last %d h2O_squish_a=%f\r\n'%(numSquishReadingsToCalculateDeltaFrom,squish))
                self.changeState('End')
                #self.TestGraph1.SetGraphProperties(xlabel='Measurement Count',timeAxes=(False,False),ylabel='h2O_squish_a',grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
                #self.TestGraph1Title.SetLabel("FSR Squish Optimization")
                #self.testWaveform=self.SMStatic
                pylab.cla()
                xList=[]
                indx=0
                for i in self.SMStatic:
                    indx+=1
                    xList.append(indx)
                pylab.scatter(xList,self.SMStatic)
                pylab.grid(True)
                pylab.xlabel('Measurement Count')
                pylab.ylabel('h2O_squish_a')
                title="FSR Squish Optimization"
                pylab.title(title)
                endTime=time.strftime('%m%d%y_%H%M%S')
                outGraphName='C:\Picarro\G2000\InstrConfig\Integration\FSRSquish\h2O_squish_aGraph_%s_%s.png'%(systemNum,endTime)
                pylab.savefig(outGraphName)
                return
            else:
                #self.Output(".")
                return
        elif(self.state=='End'):
            self.SMstatic = []
            self.outputToFile=False
            self.outputFNam='tmp'
            self.Commenttext_ctrl.Value =self.state =self.stateMachine=''
            stopDataLog('FSRSquish')
            return
        else:
            return

    def writeOutput(self, fName):
        s=self.TestResulttext_ctrl.Value
        fp = file(fName,"w")
        fp.write(s)
        fp.close()

    def SMSetFit(self):
        self.Commenttext_ctrl.Value = self.state
        self.showSM()
        if(self.state=='Start'):
            self.clearOutputs()
            self.Output('Starting State Machine '+self.stateMachine+'\r\n')
            self.outSM()
            self.SMStatic = []
            self.state ='WaitMeasuring'
            self.outSM()
            return
        elif(self.state=='WaitMeasuring'):
            #<<<< Wait for Measuring
            if self.analyze_iH20List==[]:
                self.Output(".")
                return
            else:
                self.state='SetFit2ISOBox'
                self.outSM()
                return
        elif(self.state=='SetFit2ISOBox'):
            #set up fitter for isobox
            FtrCfg=getConfig("C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini")
            self.Output("In file C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini:\r\n")
            FtrCfg['Autodetect_enable']=0
            self.Output("Setting Autodetect_enable = 0\r\n")
            FtrCfg['N2_flag']=1
            self.Output("Setting N2_flag = 1\r\n")
            FtrCfg.write()
            self.SetValveReg(4)     #isoBox is on Valve3
            self.fitterRestart()
            self.analyze_iH20List=[]
            self.state='Wait4Conc20000_N2'
            self.outSM()
            return
        elif(self.state=='Wait4Conc20000_N2'):
            #wait for h2O concentration of 20000 ppmv +/-2000
            h2o = self.analyze_iH20List['h2o_conc']
            s= 'h2o_conc = %f\r\n'%h2o
            self.Output(s)
            #if h2o>18000 and h2o<22000:
            if h2o>1800 and h2o<3200:
                self.state='RecordISOBoxFitValues'
                self.outSM()
                return
            else:
                self.Output(".")
                return
        elif(self.state=='RecordISOBoxFitValues'):
            #read these 3 values from the GUI for isoBox
            h2O_squish_a=self.analyze_iH20List['h2o_squish_a']  #????  Are these current????????????????????????
            h2O_y_eff_a=self.analyze_iH20List['h2o_y_eff']
            h2O_spline_max=self.analyze_iH20List['h2o_spline_max']
            self.Output('h2O_squish_a = %f\r\n'%h2O_squish_a)
            self.Output('h2O_y_eff_a = %f\r\n'%h2O_y_eff_a)
            self.Output('h2O_spline_max = %f\r\n'%h2O_spline_max)
            self.SMStatic.append({'ISOBoxh2O_squish_a':h2O_squish_a})
            self.SMStatic.append({'ISOBoxh2O_y_eff_a':h2O_y_eff_a})
            self.SMStatic.append({'ISOBoxh2O_spline_max':h2O_spline_max})
            self.state='SetZeroAir'
            self.outSM()
            return
        elif(self.state=='SetZeroAir'):
            #set up fitter for ZeroAir
            FtrCfg=getConfig("C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini")
            self.Output("In file C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini:\r\n")
            FtrCfg['Autodetect_enable']=0
            self.Output("Setting Autodetect_enable = 0\r\n")
            FtrCfg['N2_flag']=0
            self.Output("Setting N2_flag = 0\r\n")
            FtrCfg.write()
            self.SetValveReg(16)#zero Air is on Valve5
            self.fitterRestart()#restart the fitter<<
            self.state='Wait4Conc20000_ZA'
            self.outSM()
            return
        elif(self.state=='Wait4Conc20000_ZA'):
            #wait for h2O concentration of 20000 ppmv +/-2000
            h2o = self.analyze_iH20List['h2o_conc']
            s= 'h2o_conc = %f\r\n'%h2o
            self.Output(s)
            #if h2o>18000 and h2o<22000:
            if h2o>1800 and h2o<3200:
                self.state='RecordZAFitValues'
                self.outSM()
                return
            else:
                self.Output(".")
                return
        elif(self.state=='RecordZAFitValues'):
            #read these 3 values from the GUI for ZeroAir
            h2O_squish_a=self.analyze_iH20List['h2o_squish_a']
            h2O_y_eff_a=self.analyze_iH20List['h2o_y_eff']
            h2O_spline_max=self.analyze_iH20List['h2o_spline_max']
            self.Output('h2O_squish_a = %f\r\n'%h2O_squish_a)
            self.Output('h2O_y_eff_a = %f\r\n'%h2O_y_eff_a)
            self.Output('h2O_spline_max = %f\r\n'%h2O_spline_max)
            self.SMStatic.append({'ZABoxh2O_squish_a':h2O_squish_a})
            self.SMStatic.append({'ZABoxh2O_y_eff_a':h2O_y_eff_a})
            self.SMStatic.append({'ZABoxh2O_spline_max':h2O_spline_max})
            self.state='CalculateResults'
            self.outSM()
            return
        elif(self.state=='CalculateResults'):
            #Calculate these values before out Update the worksheet and calculate the values<<<<<<<<<<<<<<<<<<<<<<<<<<
            FtrCfg=getConfig("C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini")
            FtrCfg['Autodetect_enable']=0
            FtrCfg['N2_flag']=0.0
            FtrCfg['H2O_squish_ave']=0.0
            FtrCfg['H2O_y_trigger']=0.0
            FtrCfg['N2_intercept77']=0.0
            FtrCfg['N2_intercept82']=0.0
            FtrCfg['N2_y_at_zero']=0.0
            FtrCfg['AIR_intercept77']=0.0
            FtrCfg['AIR_intercept82']=0.0
            FtrCfg['AIR_y_at_zero']=0.0
            FtrCfg['Sine0_ampl']=0.0
            FtrCfg['Sine0_freq']=0.0
            FtrCfg['Sine0_period']=0.0
            FtrCfg['Sine0_phase']=0.0
            FtrCfg['Sine1_ampl']=0.0
            FtrCfg['Sine1_freq']=0.0
            FtrCfg['Sine1_period']=0.0
            FtrCfg['Sine1_phase']=0.0
            FtrCfg['Baseline_slope']=0.0
            self.Output("\r\nCalculating results...\r\n")
            #FtrCfg.write()<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            self.Output("\r\nUpdating Fitter Parameters in file:\r\nC:\Picarro\G2000\InstrConfig\Calibration\InstrCal\FitterConfig.ini\r\n")
            self.fitterRestart()#restart the fitter<<
            self.state='End'
            self.outSM()
            return
        elif(self.state=='End'):
            self.SMstatic = []
            self.Commenttext_ctrl.Value =self.state =self.stateMachine=''
            return
        else:
            return

    def fitterRestart(self):
        self.Output("Restarting the fitter\r\n")
        os.system("taskkill /im fitter.exe /f")

    def clearOutputs(self):
        self.TestResulttext_ctrl.Clear()
        self.Commenttext_ctrl.Value = ""

    def OnThresStatsbutton(self, event):
        self.TestResulttext_ctrl.Clear()
        s = Driver.stopScan()
        self.TestResulttext_ctrl.AppendText('Stopping Scans\r\n')
        dName=INTEGRATION_DIR+'\Threshold'
        _mkdir(dName)
        os.chdir(dName)
        shutil.copyfile('R:/crd/G2000/trunk/SrcCode/Utilities/ThresholdStats.py', dName+'/ThresholdStats.py')

        num=int(self.MsgBox("Which one to do ThresStats for?", "1=iH20, 2=CO2, 3=iCO2"))
        if num==1:
            s='S:\CRDS\SoftwareReleases\G2000Projects\AutoThresStats\AutoThresStats.exe'
            self.Output("Starting "+s+'\r\n')
            os.system(s)
            self.Output('\r\nCompleted Threshold Stats\r\n')
            event.Skip()
        elif num==2:
            shutil.copyfile('C:/Picarro/G2000/InstrConfig/Schemes/CO2_BL.sch', dName+'/CO2_BL.sch')
            shutil.copyfile('C:/Picarro/G2000/InstrConfig/Schemes/CH4_BL.sch', dName+'/CH4_BL.sch')
            shutil.copyfile('C:/Picarro/G2000/InstrConfig/Schemes/CO2_PK.sch', dName+'/CO2_PK.sch')
            shutil.copyfile('C:/Picarro/G2000/InstrConfig/Schemes/CH4_PK.sch', dName+'/CH4_PK.sch')
            time.sleep(0.9)
            self.TestResulttext_ctrl.AppendText('ThresholdStats.py 649CFADS2124 2000 16383 1000 CO2_BL.sch > CO2_BL.txt\r\n')
            os.system('ThresholdStats.py 649CFADS2124 2000 16383 1000 CO2_BL.sch > CO2_BL.txt')
            self.TestResulttext_ctrl.AppendText('ThresholdStats.py 649CFADS2124 2000 16383 1000 CH4_BL.sch > CH4_BL.txt\r\n')
            os.system('ThresholdStats.py 649CFADS2124 2000 16383 1000 CH4_BL.sch > CH4_BL.txt')
            self.TestResulttext_ctrl.AppendText('ThresholdStats.py 649CFADS2124 2000 16383 1000 CO2_PK.sch > CO2_PK.txt\r\n')
            os.system('ThresholdStats.py 649CFADS2124 2000 16383 1000 CO2_PK.sch > CO2_PK.txt')
            self.TestResulttext_ctrl.AppendText('ThresholdStats.py 649CFADS2124 2000 16383 1000 CH4_PK.sch > CH4_PK.txt\r\n')
            os.system('ThresholdStats.py 649CFADS2124 2000 16383 1000 CH4_PK.sch > CH4_PK.txt')
            self.TestResulttext_ctrl.AppendText('Threshold Stats Complete')
            pass
        elif num==3:
            shutil.copyfile('C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_Baseline.sch', dName+'/CBDSxx_Baseline.sch')
            shutil.copyfile('C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_C12Peak.sch', dName+'/CBDSxx_C12Peak.sch')
            shutil.copyfile('C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_C13Peak.sch', dName+'/CBDSxx_C13Peak.sch')
            os.system('ThresholdStats.py 642CBDS2093 2000 16000 500 C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_Baseline.sch > BL_TStats.txt')
            self.TestResulttext_ctrl.AppendText('ThresholdStats.py 642CBDS2093 2000 16000 500 C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_Baseline.sch > BL_TStats.txt\r\n')
            os.system('ThresholdStats.py 642CBDS2093 2000 16000 500 C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_C12Peak.sch > C12_TStats.txt')
            self.TestResulttext_ctrl.AppendText('ThresholdStats.py 642CBDS2093 2000 16000 500 C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_C12Peak.sch > C12_TStats.txt\r\n')
            os.system('ThresholdStats.py 642CBDS2093 2000 16000 500 C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_C13Peak.sch > C13_TStats.txt')
            self.TestResulttext_ctrl.AppendText('ThresholdStats.py 642CBDS2093 2000 16000 500 C:/Picarro/G2000/InstrConfig/Schemes/CBDSxx_C13Peak.sch > C13_TStats.txt\r\n')
            self.TestResulttext_ctrl.AppendText('Threshold Stats Complete')
            pass

    def OnViewTStatsbutton(self, event):
        print "In Event handler `OnViewTStatsbutton'..."
        self.TestResulttext_ctrl.Clear()
        s=r'R:\NewUtilities\ThresholdViewerExe\thresholdviewer.exe'
        self.Output("Starting "+s+'\r\n')
        os.system(s)
        self.Output('\r\nFinished Viewing Threshold Stats\r\n')
        event.Skip()

    def SetValveReg(self,v):
        s = "VALVE_CNTRL_SOLENOID_VALVES_REGISTER"
        Driver.wrDasReg(s,v)
        self.Output("Setting SOLENOID_VALVES_REGISTER to "+str(v)+'\r\n')

    def Output(self,s):
        print s
        self.TestResulttext_ctrl.AppendText(s)
        if self.outputToFile==True:
            self.writeOutput(self.outputFName)

    def MsgBox(self,msg,title):
        dlg=wx.TextEntryDialog(None,msg,title)
        rtnVal=""
        if dlg.ShowModal()==wx.ID_OK:
            rtnVal=dlg.GetValue()
        dlg.Destroy()
        return rtnVal

    def sensorFilter(self,obj):
        if fastMode:
            return
        time  = timestamp.unixTime(obj.timestamp)
        streamNum = obj.streamNum
        v= obj.value
        if streamNum == SensorStreamKeys.index(self.SensorStreamKey1):
            self.waveformSensorStream1.Add(time,v)
        if streamNum == SensorStreamKeys.index(self.SensorStreamKey2):
            self.waveformSensorStream2.Add(time,v)
        if streamNum == interface.STREAM_Laser1Temp:
            self.Laser1Temp = v
            #print "Laser1Temp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser2Temp:
            #print "Laser2Temp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser3Temp:
            #print "Laser3Temp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser4Temp:
            self.Laser4Temp = v
            #print "Laser4Temp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser1Tec:
            #print "Laser1Tec=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser2Tec:
            #print "Laser2Tec=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser3Tec:
            #print "Laser3Tec=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser4Tec:
            #print "Laser4Tec=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser1Current:
            #print "Laser1Current=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser2Current:
            #print "Laser2Current=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser3Current:
            #print "Laser3Current=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Laser4Current:
            #print "Laser4Current=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Etalon1:
            self.Etalon1=v
            #print "Etalon1=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Reference1:
            self.Reference1=v
            #print "Reference1=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Etalon2:
            self.Etalon2=v
            #print "Etalon2=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Reference2:
            self.Reference2=v
            #print "Reference2=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Ratio1:
            #print "Ratio1=%s" %(v)
            pass
        elif streamNum == interface.STREAM_Ratio2:
            #print "Ratio2=%s" %(v)
            pass
        elif streamNum == interface.STREAM_EtalonTemp:
            self.EtalonTemp=v
            #print "EtalonTemp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_WarmBoxTemp:
            self.WarmBoxTemp=v
            #print "WarmBoxTemp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_WarmBoxHeatsinkTemp:
            self.WarmBoxHeatsink=v
            #print "WarmBoxHeatsinkTemp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_WarmBoxTec:
            #print "WarmBoxTec=%s" %(v)
            pass
        elif streamNum == interface.STREAM_CavityTemp:
            #print "CavityTemp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_HotBoxHeatsinkTemp:
            #print "HotBoxHeatsinkTemp=%s" %(v)
            pass
        elif streamNum == interface.STREAM_HotBoxTec:
            #print "HotBoxTec=%s" %(v)
            pass
        elif streamNum == interface.STREAM_HotBoxHeater:
            #print "HotBoxHeater=%s" %(v)
            pass
        elif streamNum == interface.STREAM_AmbientPressure:
            #print "AmbientPressure=%s" %(v)
            pass
        elif streamNum == interface.STREAM_CavityPressure:
            #print "CavityPressure=%s" %(v)
            pass
        elif streamNum == interface.STREAM_InletValve:
            #print "InletValve=%s" %(v)
            pass
        elif streamNum == interface.STREAM_OutletValve:
            #print "OutletValve=%s" %(v)
            pass
        elif streamNum == interface.STREAM_ValveMask:
            #print "ValveMask=%s" %(v)
            pass
        pass

    def logFilter(self,text):
        if fastMode:
            return
        ignore="Running without Sample Manager - always returns stable status"
        tf = text.find(ignore)
        if tf<0:
            self.EventLog.AppendText(text+'\n')
            self.eventCount+=1
            if self.eventCount>100:
                self.EventLog.Clear()
                self.eventCount=0

    def rdFilter(self,data):
        if fastMode:
            return
        if not rdMode:
            return
        localDict =ctypesToDict(data)
        x=localDict[self.keyX]
        y=localDict[self.keyY]
        if self.keyY == 'ratio1' or self.keyY == 'ratio2':
            y=y/32768.0
        if self.keyX == 'ratio1' or self.keyX== 'ratio2':
            x=x/32768.0
        if self.keyY == 'timestamp':
            y=timestamp.unixTime(y)
        if self.keyX == 'timestamp':
            x=timestamp.unixTime(x)
        self.waveform.Add(x, y)
        self.update()

    def dataFilter(self,data):
        #if fastMode:
        #    return
        if data['source']=='analyze_iH2O':
            self.analyze_iH20List= d1 = data['data']
            v1=d1[self.analyzeKey1]
            v2=d1[self.analyzeKey2]
            time = data['time']
            self.waveformAnalysis1.Add(time,v1)
            self.waveformAnalysis2.Add(time,v2)
            self.Analyser1Label.SetLabel(str(v1))
            self.Analyser2Label.SetLabel(str(v2))
            self.AnalyzeDataKeys = Data_analyse_iH2O_Keys = sorted(d1.keys())
            if self.Chart1LB.GetItems()==[]:
                self.Chart1LB.SetItems(self.AnalyzeDataKeys)
                self.Chart2LB.SetItems(self.AnalyzeDataKeys)
                self.Chart1LB.Select(1)
                self.Chart2LB.Select(2)
            self.update()
        else:
            d1 = data['data']
            self.SensorDataList=d1
            v1=d1[self.sensorKey1]
            v2=d1[self.sensorKey2]
            time = data['time']
            self.waveformSensor1.Add(time,v1)
            self.waveformSensor2.Add(time,v2)
            self.SensorLabel1.SetLabel(str(v1))
            self.SensorLabel2.SetLabel(str(v2))
            if self.SensorLB1.GetItems()==[]:
                self.SensorLB1.SetItems(self.AnalyzeDataKeys)
                self.SensorLB2.SetItems(self.AnalyzeDataKeys)
                self.SensorLB1.Select(1)
                self.SensorLB2.Select(2)
            self.update()
        while True:
            savedState=self.state
            if self.stateMachine == 'SetFit':
                self.SMSetFit()
            elif self.stateMachine == 'FSRSquish':
                self.SMFSRSquish()
            if self.state == savedState:
                break

    def run(self):
        print Driver.allVersions()
        print "\nMeasurementSystem Sensor Data: %s" %MeasurementSystem.GetSensorData()
        print "\nRDFreqConverter HBCalFilePath: %s" %RDFrequencyConverter.getHotBoxCalFilePath()
        time.sleep(1)

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = SandboxFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    #frame_1.run()
    app.MainLoop()