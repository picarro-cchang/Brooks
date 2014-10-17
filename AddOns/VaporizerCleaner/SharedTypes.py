# Embedded file name: SharedTypes.pyo
from ctypes import Structure, c_float, c_uint, c_ushort, c_int
import sys
if '../Common' not in sys.path:
    sys.path.append('../Common')
import ss_autogen as s
ACCESS_PUBLIC = 0
ACCESS_PICARRO_ONLY = 100
STREAM_SIZE = 32
RESULT_SIZE = 32
MAX_LASERS = 16
MAX_SCHEMES = 16
RDQ_VERSION = 106
RPC_PORT_LOGGER = 50000
RPC_PORT_DRIVER = 50010
RPC_PORT_FILER = 50020
RPC_PORT_SUPERVISOR = 50030
RPC_PORT_SUPERVISOR_BACKUP = 50031
RPC_PORT_INTERFACE = 50040
RPC_PORT_CONTROLLER = 50050
RPC_PORT_LIBRARIAN = 50060
RPC_PORT_MEAS_SYSTEM = 50070
RPC_PORT_SAMPLE_MGR = 50080
RPC_PORT_DATALOGGER = 50090
RPC_PORT_ALARM_SYSTEM = 50100
RPC_PORT_INSTR_MANAGER = 50110
RPC_PORT_COMMAND_HANDLER = 50120
RPC_PORT_EIF_HANDLER = 50130
RPC_PORT_PANEL_HANDLER = 50140
RPC_PORT_LOCAL_GUI = 50150
RPC_PORT_DATA_MANAGER = 50160
RPC_PORT_CAL_MANAGER = 50170
RPC_PORT_FILE_ERASER = 50190
RPC_PORT_VALVE_SEQUENCER = 50200
RPC_PORT_COORDINATOR = 50210
RPC_PORT_SER_CONNECTOR = 50220
TCP_PORT_INTERFACE = 51000
TCP_PORT_FITTER = 51010
TCP_PORT_SUPERVISOR = 23456
BROADCAST_PORT_EVENTLOG = 40010
BROADCAST_PORT_SENSORSTREAM = 40020
BROADCAST_PORT_RDRESULTS = 40030
BROADCAST_PORT_RCB = 40040
BROADCAST_PORT_MEAS_SYSTEM = 40050
BROADCAST_PORT_DATA_MANAGER = 40060
BROADCAST_PORT_PROCESSED_RESULTS = 40100
CALIBRATION_ID = 4096

class RDQ_record(Structure):
    _fields_ = [('time', c_float),
     ('wm1_ratio', c_float),
     ('wm2_ratio', c_float),
     ('loss_u', c_float),
     ('loss_c', c_float),
     ('pzt', c_float),
     ('waveno', c_uint),
     ('fitStatus', c_uint),
     ('schemeStatus', c_uint),
     ('schemeIdent', c_uint),
     ('schemeCounter', c_uint),
     ('schemeTableIndex', c_uint),
     ('schemeRow', c_uint),
     ('wavenoSetpoint', c_uint),
     ('etalonAndLaserSelect', c_uint),
     ('fineLaserCurrent', c_int)]


class RDX_record(Structure):
    _fields_ = [('time', c_float),
     ('Pcavity', c_float),
     ('Tcavity', c_float),
     ('Tlaser', c_float),
     ('Tetalon', c_float),
     ('Twarmbox', c_float),
     ('TEClaser', c_float),
     ('TECwarmbox', c_float),
     ('TEChotbox', c_float),
     ('Heater', c_float),
     ('Tenvironment', c_float),
     ('InletPropValve', c_float),
     ('OutletPropValve', c_float),
     ('SolenoidValves', c_float),
     ('Pambient', c_float)]


class Monitor(Structure):
    _fields_ = [('etal1', c_ushort),
     ('ref1', c_ushort),
     ('etal2', c_ushort),
     ('ref2', c_ushort),
     ('ratio', c_ushort),
     ('setpoint_error', c_ushort),
     ('scaled_error', c_ushort),
     ('tuner_value', c_ushort),
     ('il_monitor', c_ushort),
     ('etalon_temp', c_ushort),
     ('dummy1', c_ushort),
     ('status', c_ushort),
     ('dummy2', c_ushort),
     ('dummy3', c_ushort),
     ('dummy4', c_ushort),
     ('dummy5', c_ushort)]


class OscilloscopeBuff(Structure):
    _fields_ = [('descriptor', c_ushort),
     ('dummy', c_ushort * 7),
     ('monData', Monitor * 512),
     ('waveform', c_ushort * 8192)]


class CaptureBuff(Structure):
    _fields_ = [('descriptor', c_ushort),
     ('dummy', c_ushort * 7),
     ('monData', Monitor * 512),
     ('ringdown', c_ushort * 8192)]


class TunerBuff(Structure):
    _fields_ = [('descriptor', c_ushort), ('dummy', c_ushort * 7), ('monData', Monitor * 512)]


def getSchemeClass(version, numEntries):
    if version < 1:

        class RDDATA_RdSchemeEntry(Structure):
            _fields_ = [('setpoint', c_int), ('dwellCount', c_int)]

        RDDATA_RDSCHEME_MAX_NUM_ENTRIES = 4096
    elif version < 2:

        class RDDATA_RdSchemeEntry(Structure):
            _fields_ = [('setpoint', c_int), ('dwellCount', c_ushort), ('subSchemeIdAndIncrFlag', c_ushort)]

        RDDATA_RDSCHEME_MAX_NUM_ENTRIES = 8192
    elif version < 3:

        class RDDATA_RdSchemeEntry(Structure):
            _fields_ = [('setpoint', c_int),
             ('dwellCount', c_ushort),
             ('subSchemeIdAndIncrFlag', c_ushort),
             ('laserSelectAndUseThreshold', c_ushort),
             ('threshold', c_ushort)]

        RDDATA_RDSCHEME_MAX_NUM_ENTRIES = 8192
    else:

        class RDDATA_RdSchemeEntry(Structure):
            _fields_ = [('setpoint', s.DataType),
             ('dwellCount', c_ushort),
             ('subSchemeIdAndIncrFlag', c_ushort),
             ('laserSelectAndUseThreshold', c_ushort),
             ('threshold', c_ushort),
             ('laserTemp', c_float)]

        RDDATA_RDSCHEME_MAX_NUM_ENTRIES = 8192
    if numEntries <= 0:
        raise DasException, 'Number of entries in scheme cannot be negative'
    if numEntries > RDDATA_RDSCHEME_MAX_NUM_ENTRIES:
        raise DasException, 'Scheme file has too many entries %d (max: %d)' % (numEntries, RDDATA_RDSCHEME_MAX_NUM_ENTRIES)
    SCHEME_ENTRY_ARRAY = RDDATA_RdSchemeEntry * numEntries

    class RDDATA_RdScheme(Structure):
        _fields_ = [('nrepeat', c_int), ('numEntries', c_int), ('schemeEntry', SCHEME_ENTRY_ARRAY)]

    return RDDATA_RdScheme


def getRdResultClass(version):
    if version < 1:
        return s.RD_ResultsEntryType_V0dotX
    elif version < 2:
        return s.RD_ResultsEntryType_V1dotX
    elif version < 3:
        return s.RD_ResultsEntryType_V2dotX
    elif version < 4:
        return s.RD_ResultsEntryType_V3dotX
    else:
        return s.RD_ResultsEntryType


def getCalLsrBasedTableType(version):
    if version < 5:
        return s.CAL_LsrBasedTableType_upTo4
    else:
        return s.CAL_LsrBasedTableType


def fmtVer(ver):
    """Write version number as a formatted string in such a way that string comparisons work reliably"""
    return '%06.2f' % float(ver)


def regAvailableInVersion(registerIndex, interfaceVersion):
    """Returns True if register of the specified index is available in the specified interface version"""
    return fmtVer(interfaceVersion) >= fmtVer(s.register_info[registerIndex].firstVersion)


def regByVersion(mcuVersion):
    """Returns for each mcuVersion the index of the highest register available"""
    info = [(fmtVer(1), s.DASCNTRL_RESET_COUNT_REGISTER),
     (fmtVer(2.0), s.RD_SCHEME_TABLE_INDEX_REGISTER),
     (fmtVer(2.1), s.DISPLAY_RESERVED_REGISTER3),
     (fmtVer(2.3), s.RDCNTRL_WL_LOCK_TIMEOUT_DURATION_REGISTER),
     (fmtVer(2.4), s.RD_START_SAMPLE_REGISTER),
     (fmtVer(2.5), s.FPGA_CARD_PRESENT_REGISTER),
     (fmtVer(3.0), s.DIAG_ENABLE_REGISTER),
     (fmtVer(3.02), s.RDCNTRL_PZT_CUTOFF_FREQ_REGISTER),
     (fmtVer(4.0), s.RD_UPPER_TO_LOWER_THRESHOLD_OFFSET),
     (fmtVer(5.6), s.I2C_BUS0_MCU_BYPASS_REGISTER)]
    mcuVersion = fmtVer(float(mcuVersion))
    for v, i in info[::-1]:
        if mcuVersion >= v:
            return i

    return s.TEST_STATUS_REGISTER


def intStreamByVersion(mcuVersion):
    """Returns for each mcuVersion the index of the highest integer data stream available"""
    mcuVersion = fmtVer(float(mcuVersion))
    info = [(fmtVer(2.0), s.STREAM_HeaterTapeVMonAdc)]
    mcuVersion = fmtVer(float(mcuVersion))
    for v, i in info[::-1]:
        if mcuVersion >= v:
            return i

    return s.STREAM_SpectWlStd


def floatStreamByVersion(mcuVersion):
    """Returns for each mcuVersion the index of the highest floating point data stream available"""
    mcuVersion = fmtVer(float(mcuVersion))
    info = [(fmtVer(2.0), s.STREAM_OutletDacValue), (fmtVer(3.0), s.STREAM_EtalonTempAvg), (fmtVer(9.0), s.STREAM_SolenoidValveStatus)]
    mcuVersion = fmtVer(float(mcuVersion))
    for v, i in info[::-1]:
        if mcuVersion >= v:
            return i

    return s.STREAM_DasTemp


class CrdsException(Exception):
    """Base class for all CRDS exceptions."""
    pass


class DasException(CrdsException):
    """Base class for all DAS layer exceptions."""
    pass


class DasTransportLayerException(DasException):
    pass


class UsbUnavailable(CrdsException):
    """The USB layer has failed, but should be restarted soon."""
    pass


class InterfaceError(CrdsException):
    pass


class DasVersionError(DasException):
    """There is a problem with the firmware versions on the DAS."""
    pass


DriverRpcServerPort = RPC_PORT_DRIVER
InterfaceServerPort = TCP_PORT_INTERFACE
InterfaceRpcServerPort = RPC_PORT_INTERFACE
ControllerCallbackPort = RPC_PORT_CONTROLLER
FilerRpcServerPort = RPC_PORT_FILER
LoggerRpcServerPort = RPC_PORT_LOGGER
MasterRpcServerPort = RPC_PORT_SUPERVISOR
LoggerBroadcastPort = BROADCAST_PORT_EVENTLOG
DriverStreamPort = BROADCAST_PORT_SENSORSTREAM
DriverRdResultsPort = BROADCAST_PORT_RDRESULTS
DriverRcbPort = BROADCAST_PORT_RCB
if __name__ == '__main__':
    mcuVer = raw_input('MCU version number? ')
    print 'Last register: %d [%s]' % (regByVersion(mcuVer), s.register_info[regByVersion(mcuVer)].name)
    print 'Last float Stream: %d' % (floatStreamByVersion(mcuVer),)
    print 'Last integer Stream: %d' % (intStreamByVersion(mcuVer),)