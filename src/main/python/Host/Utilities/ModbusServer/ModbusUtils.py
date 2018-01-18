import sys
import time
import datetime
import requests
import struct
import subprocess
import shlex

from Host.Common import CmdFIFO, SharedTypes
from Host.Utilities.ModbusServer.ErrorHandler import Errors
from Host.autogen import interface


DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"        
ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
OFFSET = datetime.datetime.now() - datetime.datetime.utcnow()

struct_type_map = {
    "int_16"  :  "h",
    "int_32"  :  "i",
    "int_64"  :  "q",
    "float_32":  "f",
    "float_64":  "d"
}

def get_variable_type(bit, type):
    if type == "string":
        return "%ds" % (bit/8)
    else:
        return struct_type_map["%s_%s" % (type.strip().lower(), bit)]

class ModbusScriptEnv(object):
    def __init__(self, server):
        self.server = server
        self.host_session = requests.Session()
        self.current_user = None
        self._driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
            ClientName = "ModbusServer")
        self._instrument_manager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_INSTR_MANAGER, 
            ClientName = "ModbusServer")
        self._valve_sequencer = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_VALVE_SEQUENCER, 
            ClientName = "ModbusServer")
        self.sampleMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_SAMPLE_MGR,
            ClientName="ModbusServer")
        self.cavityPressureS = None
        self.cavityPressureT = None
        try:
            self.cavityPressureS = self.sampleMgrRpc.ReadOperatePressureSetpoint()
            self.cavityPressureTPer = self.sampleMgrRpc.ReadPressureTolerancePer()
        except:
            self.cavityPressureS = 140.0
            self.cavityPressureTPer = 0.05
        self.cavityPressureT = self.cavityPressureTPer * self.cavityPressureS
        self._clockStatus = {}
        proc = subprocess.Popen('timedatectl', stdout=subprocess.PIPE)
        for line in proc.stdout.readlines():
            (key, val) = line.split(':', 1)
            self._clockStatus[key.lstrip().rstrip(' \n')] = val.lstrip().rstrip(' \n')
        
    def create_script_env(self):
        script_env = {}
        class_dir = dir(self)
        for s in class_dir:
            attr = getattr(self, s)
            if callable(attr) and s.startswith("MODBUS_"):
                script_env[s] = attr
        return script_env
                
    def _send_request(self, action, api, payload):
        """
        action: 'get' or 'post'
        """
        if self.current_user and "token" in self.current_user:
            header = {'Authentication': self.current_user["token"]}
        else:
            header = {}
        action_func = getattr(self.host_session, action)
        try:
            response = action_func(DB_SERVER_URL + api, data=payload, headers=header)
            json = response.json()
            return response, json
        except Exception, err:
            return response, {"error": str(err)}
                
    ########## Functions for accessing Modbus memory #####################################
        
    def MODBUS_GetValue(self, name):
        if name in self.server.variable_params:
            d = self.server.variable_params[name]
            reg = d["register"]
            addr = d["address"]
            if reg < 2:
                return self.server.context[self.server.slaveid].getValues(reg, addr, 1)[0]
            else:
                bit = d["bit"]
                type = d["type"]
                count = bit/16
                values = self.server.context[self.server.slaveid].getValues(reg, addr, count)
                value_str = struct.pack("%s%dH" % (self.server.endian, count), *values)
                ret = struct.unpack("%s%s" % (self.server.endian, get_variable_type(bit, type)), value_str)
                return ret[0]
                
    def MODBUS_SetValue(self, name, value):
        if name in self.server.variable_params:
            d = self.server.variable_params[name]
            reg = d["register"]
            addr = d["address"]
            if reg < 2:
                self.server.context[self.server.slaveid].setValues(reg, addr, value)
            else:
                bit = d["bit"]
                type = d["type"]
                count = bit/16
                value_str = struct.pack("%s%s" % (self.server.endian, get_variable_type(bit, type)), value)
                value_to_write = list( struct.unpack('%s%dH' % (self.server.endian, count), value_str) )
                self.server.context[self.server.slaveid].setValues(reg, addr, value_to_write)

    def MODBUS_SetError(self, error):
        self.server.errorhandler.set_error(error)

    ########## Time related functions #####################################
                
    def MODBUS_TimestampToLocalDatetime(self, timestamp):
        """Converts 64-bit millisecond resolution timestamp to local datetime"""
        return datetime.timedelta(microseconds=1000*timestamp) + ORIGIN + OFFSET
        
    def MODBUS_GetSystemTime(self):
        """Get 64-bit millisecond resolution timestamp"""
        currenttime = time.time()*1000+62135596800000
        self.server.errorhandler.set_error(Errors.NO_ERROR)
        return currenttime
        
    def MODBUS_SetSystemTime(self, timestamp):
        """Set system clock using 64-bit millisecond resolution timestamp"""
        dt = self.MODBUS_TimestampToLocalDatetime(timestamp)
        if sys.platform == 'win32':
            import win32api
            win32api.SetSystemTime(
                dt.year,
                dt.month,
                0,  # day of week
                dt.day,
                dt.hour,
                dt.minute,
                dt.second,
                dt.microsecond / 1000
            )
        elif sys.platform == 'linux2':
            try:
                datetimeStr = dt.strftime("%Y-%m-%d %H:%M:%S")
                if self.isTimeSyncEnabled():
                    self.disableTimeSync()
                subprocess.check_call(shlex.split("timedatectl set-time '%s'" % datetimeStr))
                subprocess.check_call(shlex.split("sudo hwclock -w"))
            except Exception as e:
                self.MODBUS_SetError(Errors.NO_SUDO_USER_PRIVILEGE)
                print(str(e))
                return 0

        self.MODBUS_SetError(Errors.NO_ERROR)
        return 1

    def isTimeSyncEnabled(self):
        """
        Ubunut 16.04 uses Systemd's simple NTP service: timesyncd.
        Other/older systems will use the standard NTPd.
        If either is enabled return True.
        :return:
        """
        timeSyncEnabled = False
        if self._clockStatus:
            if self._clockStatus["Network time on"].lower() == "yes":
                timeSyncEnabled = True
            if self._clockStatus["NTP synchronized"].lower() == "yes":
                timeSynchEnabled = True
        return timeSyncEnabled

    def disableTimeSync(self):
        """
        Disable timesyncd and ntp.
        :return:
        """
        # Need error/exception handling here.  check_call blocks until we get a return code
        # from timedatectl.  It should be instantaneous.
        subprocess.check_call(shlex.split("timedatectl set-ntp false"))
        return

    ########## Instrument Manager functions #####################################
    
    def MODBUS_EnableMeasurement(self):
        self._instrument_manager.INSTMGR_StartMeasureRpc()

    def MODBUS_DisableMeasurement(self):
        self._instrument_manager.INSTMGR_StopMeasureRpc()
        
    def MODBUS_ParkInstrument(self):
        self._instrument_manager.INSTMGR_ShutdownRpc(0)
        self.MODBUS_SetError(Errors.NO_ERROR)
        return 1

    def MODBUS_ShutdownInstrument(self):
        self._instrument_manager.INSTMGR_ShutdownRpc(1)
        self.MODBUS_SetError(Errors.NO_ERROR)
        return 1
    
    ########## Valve Sequencer functions #####################################
    
    def MODBUS_StartValveSequence(self):
        self._valve_sequencer.startValveSeq()

    def MODBUS_StopValveSequence(self):
        self._valve_sequencer.stopValveSeq()

    def MODBUS_GetValveState(self):
        return self._valve_sequencer.getValveSeqStatus()

    def MODBUS_SetValveState(self, valveMask):
        self._valve_sequencer.stopValveSeq()
        self._valve_sequencer.setValves(int(valveMask))
        
    ########## User Database functions #####################################
    
    def MODBUS_UserLogin(self, username, password):
        payload = {'command': "log_in_user",
                   'requester': "Modbus",
                   'username': username, 
                   'password': password}
        response, return_dict = self._send_request("post", "account", payload)
        if "error" not in return_dict and response.status_code == 200:
            self.current_user = return_dict
            self.MODBUS_SetError(Errors.NO_ERROR)
            return 1
        else:
            error_code = Errors.NO_ERROR
            if response.status_code == 401:
                error_code = Errors.USERNAME_PASSWORD_INCORRECT
            elif response.status_code == 400:
                error_code = Errors.NO_USER_EXIST
            elif response.status_code == 403:
                error_code = Errors.ADMIN_RIGHT_REQUIRES
            elif response.status_code == 423:
                error_code = Errors.USER_DISABLED
            else:
                error_code = Errors.ERROR
            self.MODBUS_SetError(error_code)
            return 0
        
    def MODBUS_UserLogoff(self):
        response, return_dict = self._send_request("post", "account", {"command":"log_out_user", 'requester': "Modbus"})
        if "error" not in return_dict and response.status_code == 200:
            self.current_user = None
            self.MODBUS_SetError(Errors.NO_ERROR)
            return 1
        else:
            self.MODBUS_SetError(Errors.ERROR)
            return 0
            
    def MODBUS_ChangeUserPassword(self, username, new_password):
        payload = dict(command="update_user", username=username, password=new_password)
        response, return_dict = self._send_request("post", "users", payload)
        if "error" not in return_dict and response.status_code == 200:
            self.MODBUS_SetError(Errors.NO_ERROR)
            return 1
        else:
            error_code = Errors.NO_ERROR
            if response.status_code == 403:
                error_code = Errors.ADMIN_RIGHT_REQUIRES
            elif response.status_code == 404:
                error_code = Errors.NO_USER_EXIST
            elif response.status_code == 409:
                error_code = Errors.PASSWORD_REUSE_ERROR
            elif response.status_code == 411:
                error_code = Errors.PASSWORD_LENGTH_ERROR
            elif response.status_code == 422:
                error_code = Errors.PASSWORD_FORMAT_ERROR
            elif response.status_code == 423:
                error_code = Errors.USER_DISABLED
            else:
                error_code = Errors.ERROR
            self.MODBUS_SetError(error_code)
            return 0

    ########## Instrument status functions #####################################

    def MODBUS_Get_Cavity_Temp_Status(self, cavity_temp):
        '''
        Method use to check status of Cavity temp. If temp is above/below allowed range it will return
        True otherwise false
        :param cavity_temp:
        :return:
        '''
        try:
            lockStatus = self._driver.rdDasReg("DAS_STATUS_REGISTER")
            return ((lockStatus >> interface.DAS_STATUS_CavityTempCntrlLockedBit) & 1)
        except:
            pass

    def MODBUS_Get_Warm_Box_Temp_Status(self, warm_box_temp):
        '''
        Method use to check status of Warm box temp. If temp is above/below allowed range it will return
        True otherwise false
        :param warm_box_temp:
        :return:
        '''
        try:
            lockStatus = self._driver.rdDasReg("DAS_STATUS_REGISTER")
            return ((lockStatus >> interface.DAS_STATUS_WarmBoxTempCntrlLockedBit ) & 1)
        except:
            pass

    def MODBUS_Get_Cavity_Pressure_Status(self, cavity_pressure):
        '''
        Method use to check status of Cavity pressure. If pressure is above/below allowed range it will return
        True otherwise false
        :param cavity_pressure:
        :return:
        '''
        try:
            if cavity_pressure != 0.0:
                #check if pressure is in range
                if self.cavityPressureS != None and self.cavityPressureT != None:
                    cavityPressureDev = cavity_pressure - self.cavityPressureS
                    if abs(cavityPressureDev) > self.cavityPressureT:
                        return 0
                    else:
                        return 1
        except:
            pass
