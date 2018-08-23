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

    #update user password
    MODBUS_UserLogin(user_name, user_password)
    return 1

def Change_UserPassword():
    #Get user name
    user_name=MODBUS_GetValue("UserName").lstrip()
    #Get user password
    user_password=MODBUS_GetValue("UserPassword").lstrip()

    #update user password
    MODBUS_ChangeUserPassword(user_name, user_password)

    return  1;

def Get_UserData_1():
    userdata_index = 1
    return Handle_Get_UserData(userdata_index)

def Set_UserData_1():
    userdata_index = 1
    return Handle_Set_UserData(userdata_index)

def Get_UserData_2():
    userdata_index = 2
    return Handle_Get_UserData(userdata_index)

def Set_UserData_2():
    userdata_index = 2
    return Handle_Set_UserData(userdata_index)

def Get_UserData_3():
    userdata_index = 3
    return Handle_Get_UserData(userdata_index)

def Set_UserData_3():
    userdata_index = 3
    return Handle_Set_UserData(userdata_index)

def Get_UserData_4():
    userdata_index = 4
    return Handle_Get_UserData(userdata_index)

def Set_UserData_4():
    userdata_index = 4
    return Handle_Set_UserData(userdata_index)

def Get_UserData_5():
    userdata_index = 5
    return Handle_Get_UserData(userdata_index)

def Set_UserData_5():
    userdata_index = 5
    return Handle_Set_UserData(userdata_index)

def Get_UserData_6():
    userdata_index = 6
    return Handle_Get_UserData(userdata_index)

def Set_UserData_6():
    userdata_index = 6
    return Handle_Set_UserData(userdata_index)

def Get_UserData_7():
    userdata_index = 7
    return Handle_Get_UserData(userdata_index)

def Set_UserData_7():
    userdata_index = 7
    return Handle_Set_UserData(userdata_index)

def Get_UserData_8():
    userdata_index = 8
    return Handle_Get_UserData(userdata_index)

def Set_UserData_8():
    userdata_index = 8
    return Handle_Set_UserData(userdata_index)

def Get_UserData_9():
    userdata_index = 9
    return Handle_Get_UserData(userdata_index)

def Set_UserData_9():
    userdata_index = 9
    return Handle_Set_UserData(userdata_index)

def Get_UserData_10():
    userdata_index = 10
    return Handle_Get_UserData(userdata_index)

def Set_UserData_10():
    userdata_index = 10
    return Handle_Set_UserData(userdata_index)

def Get_UserData_11():
    userdata_index = 11
    return Handle_Get_UserData(userdata_index)

def Set_UserData_11():
    userdata_index = 11
    return Handle_Set_UserData(userdata_index)

def Get_UserData_12():
    userdata_index = 12
    return Handle_Get_UserData(userdata_index)

def Set_UserData_12():
    userdata_index = 12
    return Handle_Set_UserData(userdata_index)

def Get_UserData_13():
    userdata_index = 13
    return Handle_Get_UserData(userdata_index)

def Set_UserData_13():
    userdata_index = 13
    return Handle_Set_UserData(userdata_index)

def Get_UserData_14():
    userdata_index = 14
    return Handle_Get_UserData(userdata_index)

def Set_UserData_14():
    userdata_index = 14
    return Handle_Set_UserData(userdata_index)

def Get_UserData_15():
    userdata_index = 15
    return Handle_Get_UserData(userdata_index)

def Set_UserData_15():
    userdata_index = 15
    return Handle_Set_UserData(userdata_index)

def Get_UserData_16():
    userdata_index = 16
    return Handle_Get_UserData(userdata_index)

def Set_UserData_16():
    userdata_index = 16
    return Handle_Set_UserData(userdata_index)

def Get_UserData_17():
    userdata_index = 17
    return Handle_Get_UserData(userdata_index)

def Set_UserData_17():
    userdata_index = 17
    return Handle_Set_UserData(userdata_index)

def Get_UserData_18():
    userdata_index = 18
    return Handle_Get_UserData(userdata_index)

def Set_UserData_18():
    userdata_index = 18
    return Handle_Set_UserData(userdata_index)

def Get_UserData_19():
    userdata_index = 19
    return Handle_Get_UserData(userdata_index)

def Set_UserData_19():
    userdata_index = 19
    return Handle_Set_UserData(userdata_index)

def Get_UserData_20():
    userdata_index = 20
    return Handle_Get_UserData(userdata_index)

def Set_UserData_20():
    userdata_index = 20
    return Handle_Set_UserData(userdata_index)


def Handle_Get_UserData(userdata_index):
    """Write User data"""
    userdata_key = "UserData_" + str(userdata_index)
    MODBUS_SetValue(userdata_key, MODBUS_GetUserData(userdata_key))
    return 1

def Handle_Set_UserData(userdata_index):
    """Write User data"""
    userdata_key = "UserData_" + str(userdata_index)

    #get new user data value for key from Holding register
    userdata_new_value = MODBUS_GetValue(userdata_key)

    MODBUS_SetUserData(userdata_key, userdata_new_value)
    return 1


