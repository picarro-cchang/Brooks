import sys
import time
from struct import pack, unpack
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.client.sync import ModbusTcpClient

RTU = False
IP_ADDRESS = '10.100.3.86'
TCP_PORT = 50500

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

try:
    com_setting = {"port": "COM3", "baudrate": 19200, "timeout": 3}
    if RTU:
        client = ModbusSerialClient(method='rtu', **com_setting)
    else:
        client = ModbusTcpClient(IP_ADDRESS, port=TCP_PORT)
    client.connect()
    print("Connected to server")
except Exception, e:
    print "Error in Modbus Client: %s " % e

if "--debug" in sys.argv[1:]:
    import logging
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)


def read_error(unit_number):
    result = client.read_input_registers(386, 1, unit=unit_number)
    values = pack(">h", *result.registers)
    return unpack(">h", values)[0]


def read_current_time(unit_number):
    client.write_coil(150, 1, unit=1)
    print read_error(unit_number)
    result = client.read_holding_registers(0, 4, unit=unit_number)
    value_str = pack("%s%dH" % ('>', 4), *result.registers)
    ret = unpack("%s%s" % ('>', get_variable_type(64, 'int')), value_str)
    print (ret[0])


def read_measurement(unit_number):
    result = client.read_input_registers(1, 16, unit=unit_number)
    values = pack(">16H", *result.registers)
    print("Analyzer" +str(unit_number)+ ":(Timestamp , H2O2 , H2O , Cavity Pressure, Cavity Temp, WarmBoxTemp)")
    print unpack(">12sfffff", values)

def read_First_Three_Gas_measurement(unit_number):
    result = client.read_input_registers(0, 48, unit=unit_number)
    values = pack(">48H", *result.registers)
    print("Analyzer" +str(unit_number)+ ":(Timestamp , H2O2 , H2O2_ID , H2O2_30S, H2O2_2min, H2O2_5min, H2O2_Maximum, H2O2_Minimum, H2O , H2O_ID , H2O_30S, H2O_2min, H2O_5min, H2O_Maximum, H2O_Minimum, CH4 , CH4_ID , CH4_30S, CH4_2min, CH4_5min, CH4_Maximum, Ch4_Minimum)")
    print unpack(">12sfiffffffiffffffifffff", values)

def read_Sesor_Data(unit_number):
    result = client.read_input_registers(200, 36, unit=unit_number)
    values = pack(">36H", *result.registers)
    print("Analyzer" +str(unit_number)+ ":(CavityPressure, CavityTemp, DasTemp, EtalonTemp, WarmBoxTemp, OutletValve, H202 Inst Offfset, H2O2 Inst slope, H2O2 user Slope, H2O2 user offset, H20 Inst Offfset, H2O Inst slope, H2O user Slope, H2O user offset, CH4 Inst Offfset, CH4 Inst slope, CH4 user Slope, CH4 user offset)")
    print unpack(">ffffffffffffffffff", values)

def read_Private_Data(unit_number):
    result = client.read_input_registers(300, 12, unit=unit_number)
    values = pack(">12H", *result.registers)
    print("Analyzer" +str(unit_number)+ ":(Etalon1, Etalon2, Ratio1, Ratio2, Reference1, Reference2)")
    print unpack(">ffffff", values)


def set_clock(unit_number, clock):
    value_str = pack("%s%s" % ('>', get_variable_type(64, 'int')), clock)
    value_to_write = list( unpack('%s%dH' % ('>', 4), value_str) )
    client.write_registers(0, value_to_write, unit=unit_number)
    client.write_coil(151, 1, unit=unit_number)


def shutdown(unit_number):
    client.write_coil(115, 1, unit=unit_number)
    print read_error(unit_number)


def logout(unit_number):
    client.write_coil(155, 1, unit=unit_number)
    time.sleep(1)
    print read_error(unit_number)


def set_username(user_name, unit_number):
    user_name_fixsize = "{:>8}".format(user_name)
    value_to_write = list(unpack('%s%dH' % ('>', 4), user_name_fixsize))
    client.write_registers(4, value_to_write, unit=unit_number)


def set_password(user_password, unit_number):
    user_password_fixsize = "{:>8}".format(user_password)
    value_to_write = list(unpack('%s%dH' % ('>', 4), user_password_fixsize))
    client.write_registers(8, value_to_write, unit=unit_number)


def login(unit_number):
    client.write_coil(153, 1, unit=unit_number)
    time.sleep(1)
    print read_error(unit_number)


def login_with_userInfo(user_name, user_password, unit_number):
    set_username(user_name, unit_number)
    set_password(user_password, unit_number)
    login(unit_number)

def update_password(unit_number):
    # update password
    client.write_coil(154, 1, unit=unit_number)
    time.sleep(1)
    print read_error(unit_number)

def update_password_with_userinfo(user_name, user_password, unit_number):
    set_username(user_name, unit_number)
    set_password(user_password, unit_number)
    update_password(unit_number)


def read_float_register(register_address, unit_number):
    result = client.read_input_registers(register_address, 2, unit=unit_number)
    values = pack(">2H", *result.registers)
    print unpack(">f", values)[0]


def read_status_register(register_Address, unit_number):
    result = client.read_discrete_inputs(register_Address, 1, unit=unit_number)
    print result.bits[0]

# #Check error case when username and password is not set
# login(1);

# #Check error case when only username is set
# set_username('admin', 1)
# login(1)

# #login with admin
# user_name='admin'
# user_password='admin'
# login_with_userInfo(user_name, user_password, 1)
#
# #update user password
# user_name='tech'
# user_password='picarro'
# update_password_with_userinfo(user_name, user_password, 1)
#
# #Logout from admin
# logout(1)
# logout(2)


# # Try to change password without administration login
# user_name='tech'
# user_password='picarro'
# login_with_userInfo(user_name, user_password, 1)
#
# #update user password
# user_name='admin'
# user_password='picarro1'
# update_password_with_userinfo(user_name, user_password, 1)
#
# #logout from tech user
# logout(1)


# #update user password with shorter password length
# #login with admin
# user_name='admin'
# user_password='admin'
# login_with_userInfo(user_name, user_password, 1)
#
# #update user password
# user_name='tech'
# user_password='tech'
# update_password_with_userinfo(user_name, user_password, 1)
#
# #Passowrd reuse error
# #update user password
# user_name='tech'
# user_password='picarro1'
# update_password_with_userinfo(user_name, user_password, 1)
#
# #update user password
# user_name='tech'
# user_password='picarro'
# update_password_with_userinfo(user_name, user_password, 1)
#
#
# #Logout from admin
# logout(1)

# #lock user error
# user_name='tech'
# user_password='picarro'
# login_with_userInfo(user_name, user_password, 1)
# login_with_userInfo(user_name, user_password, 1)
# login_with_userInfo(user_name, user_password, 1)
# login_with_userInfo(user_name, user_password, 1)

# #shut down
# shutdown(1)
# shutdown(2)

#read current time
#milliseconds from 1AD January 1st to now
# read_current_time(1)
#read_current_time(2)

#set clock
# value = 63645754135000
# set_clock(1, value)
# print read_error(1)

#read h2o2 max value
sys.stdout.write('H2O2 Max value: ')
read_float_register(16,1)

#read h2o2 min value
sys.stdout.write('H2O2 Min value: ')
read_float_register(18,1)

#read inst cal h2o2 slope
sys.stdout.write('H2O2 instr cal slope: ')
read_float_register(214,1)

#read inst cal h2o2 offset
sys.stdout.write('H2O2 instr cal offset: ')
read_float_register(212,1)

#read user cal h2o2 slope
sys.stdout.write('H2O2 user cal slope: ')
read_float_register(216,1)

#read user cal h2o2 offset
sys.stdout.write('H2O2 user cal offset: ')
read_float_register(218,1)

#read h2o max value
sys.stdout.write('H2O Max value: ')
read_float_register(30,1)

#read h2o min value
sys.stdout.write('H2O Min value: ')
read_float_register(32,1)

#read inst cal h2o slope
sys.stdout.write('H2O instr cal slope: ')
read_float_register(222,1)

#read inst cal h2o offset
sys.stdout.write('H2O instr cal offset: ')
read_float_register(220,1)

#read user cal h2o slope
sys.stdout.write('H2O user cal slope: ')
read_float_register(224,1)

#read user cal h2o offset
sys.stdout.write('H2O user cal slope: ')
read_float_register(226,1)

while True:
    try:
        time.sleep(2)
        read_First_Three_Gas_measurement(1)

        read_Sesor_Data(1)
        read_Private_Data(1)

        #time.sleep(2)
        #read_H2O2_measurement(2)

        #read status of cavity pressure
        sys.stdout.write("Cavity Pressure Status: ")
        read_status_register(5, 1)

        sys.stdout.write("Cavity Temp Status: ")
        #read status of cavity temp
        read_status_register(6, 1)

        #read status of warm box temp
        sys.stdout.write("Wamr Box Temp Status: ")
        read_status_register(7, 1)
        print("-------------------------------------------------------------------------------")
    except Exception, e:
        print "Error in reading Modbus: %s " % e
        print("-------------------------------------------------------------------------------")

client.close()
