import sys
from Host.Utilities.ModbusServer.ErrorHandler import Errors

def format_timestamp(ts):
    """Format timestamp into string "YYMMDDhhmmss" """
    dt = MODBUS_TimestampToLocalDatetime(ts)
    return dt.strftime("%y%m%d%H%M%S")

def alarm_high_H2O2(x):
    return True if x > 0.0 else False
    
def get_system_time():
    """Write system time as timestamp in SyncTime register"""
    MODBUS_SetValue("SyncTime", MODBUS_GetSystemTime())
    return 1
    
def set_system_time():
    """Set system clock using timestamp in SyncTime register"""
    # Get timestamp of int-64 bit format
    sync_time = MODBUS_GetValue("SyncTime")
    if int(sync_time) < 1:
        print "Fail to read SyncTime from Modbus!"
        MODBUS_SetError(Errors.NO_SYNCTIME_SET)
        return 0
    # Set syncTime as the system current time    
    MODBUS_SetSystemTime(sync_time)
    # Set syncTime to 0 in Modbus
    MODBUS_SetValue("SyncTime", 0)
    return 1

def User_Login():
    #Get user name
    user_name=MODBUS_GetValue("UserName").lstrip()
    #Get user password
    user_password=MODBUS_GetValue("UserPassword").lstrip()

    #check if user name or user password is not empty
    if not user_name:
        print "Fail to read UserName from Modbus"
        MODBUS_SetError(Errors.NO_USERNAME_SET)
        return 0
    if not user_password:
        print "Fail to read UserPassword from Modbus"
        MODBUS_SetError(Errors.NO_PASSWORD_SET)
        return 0

    #update user password
    MODBUS_UserLogin(user_name, user_password)
    return 1

def Change_UserPassword():
    #Get user name
    user_name=MODBUS_GetValue("UserName").lstrip()
    #Get user password
    user_password=MODBUS_GetValue("UserPassword").lstrip()

    #check if user name or user password is not empty
    if not user_name:
        print "Fail to read UserName from Modbus"
        MODBUS_SetError(Errors.NO_USERNAME_SET)
        return 0
    if not user_password:
        print "Fail to read UserPassword from Modbus"
        MODBUS_SetError(Errors.NO_PASSWORD_SET)
        return 0

    #update user password
    MODBUS_ChangeUserPassword(user_name, user_password)

    return  1;
