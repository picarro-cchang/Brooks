import sys
import time
from struct import pack, unpack
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.client.sync import ModbusTcpClient

#RTU = False
#IP_ADDRESS = '10.100.2.103'
TCP_PORT = 50500

struct_type_map = {
    "int_16"  :  "h",
    "int_32"  :  "i",
    "int_64"  :  "q",
    "float_32":  "f",
    "float_64":  "d"
}

if "--debug" in sys.argv[1:]:
    import logging
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

reg_dict = {1: "Input Register", 2: "Discrete Register", 3: "Coil Register", 4: "Holding Register"}

def read_error(unit_number):
    result = client.read_input_registers(386, 1, unit=unit_number)
    values = pack(">h", *result.registers)
    return unpack(">h", values)[0]    
    
    
def get_variable_type(bit, type):
    if type == "string":
        return "%ds" % (bit/8)
    else:
        return struct_type_map["%s_%s" % (type.strip().lower(), bit)]
    
    
    
   
print "\n ***Picarro Modbus Test Client.***"

while True:
    print "Slave ID: \n an integer"
    slaveID = int(raw_input("Enter slaveID (defaul is 1): "))
    
    print "Protocol: \n1, RTU \n2, TCP/IP"
    protocol =  int(raw_input("Enter the protocol number: "))   
    if protocol == 1:
        RTU = True
        break
    elif protocol == 2:
        RTU = False
        break
    else:
        print "Invalid input. Must inpput 1 or 2."

        
        
if RTU:
    while True:
        print "Enter your com port number: an integer between \n0-99."
        comport = int(raw_input("Enter the comport number: "))
        if comport >=0 and comport < 100:
            port = "COM" + str(comport)
            com_setting = {"port": port, "baudrate": 19200, "timeout": 3}
        else:
            print "Invalid comport number.."
            continue
        client = ModbusSerialClient(method = 'rtu', **com_setting)
        if client.connect():
            print("Connected to server via RTU.")
            break
        else:
            print "Connection Failed."
else:
    while True:
        IP_ADDRESS = raw_input("Enter the IP address of the Slave: ")
        client = ModbusTcpClient(IP_ADDRESS, port=TCP_PORT)
        if client.connect():
            print("Connected to server via TCP/IP.")
            break
        else:
            print "Failed to connect to the server at the specified IP address."
    
    
#try:
while True:
    print "Register ID: register"
    for i in reg_dict:
        print i, ":", reg_dict[i]    
    registerID = int(raw_input("Enter the register ID number: "))
    if registerID == 1: 
        while True:
            address = raw_input("Enter Address of Input Register: ")
            if address == '<':
                break
            print "Address to read: ", address
            
            size = int(raw_input("Enter size -- number of registers: "))
            print "data types: \n 1, int \n 2, float \n 3, string"
            data_type = int(raw_input("Enter data type (1,2 or 3): "))
            res = client.read_input_registers(int(address), size, unit = slaveID)
            
            
            if data_type == 2: 
                try:
                    values = pack("%s%dH" % ('>', size), *res.registers)
                    print "Value read: ", unpack(">f", values)[0]
                except:
                    print "You entered invalid address... "
            elif data_type == 1:
                try:
                    values = pack("%s%dH" % ('>', size), *res.registers)
                    print "Value read: ", unpack(">H", values)[0]
                except:
                    print "You entered invalid address... "
            elif data_type == 3:
                try:
                    values = pack("%s%dH" % ('>', size), *res.registers)
                    print "Value read: ", values #unpack(">s", values)
                except:
                    print "You entered invalid address... "
            else:
                print "Wrong data_type."
                continue
    elif registerID == 2:
        while True:
            address = raw_input("Enter Address of Discrete Register: ")
            if address == '<':
                break
            print "Address to read: ", address
            res = client.read_discrete_inputs(int(address), 1, unit = slaveID)
            try:
                print "Value read: ", res.bits[0]
            except:
                print "You entered invalid address... "
    elif registerID == 3:
        while True:
            address = raw_input("Enter Address of Coil Register: ")
            if address == '<':
                break
            print "Address to read: ", address
            client.write_coil(int(address), 1, unit=slaveID)
            try:
                print "Status: ", read_error(1) 
            except:
                print "You entered invalid address... "
    elif registerID == 4:
        while True:
            address = raw_input("Enter Address of holding Register: ")
            if address == '<':
                break
            print "Address to read: ", address
            
            ops = int(raw_input("Enter you want to read or write  (1 or 2): "))
            if ops == 1:
                size = int(raw_input("Enter size -- number of registers: "))
                res = client.read_holding_registers(int(address), size, unit=slaveID)
                print res
                try:
                    value_str = pack("%s%dH" % ('>', size), *res.registers)
                    ret = unpack("%s%s" % ('>', get_variable_type(16*size, 'int')), value_str)
                    print "Value read: ", ret[0]
                except Exception, e:
                    print "Error in reading: %s" %e 
                    print "You entered invalid parameters... "
            elif ops == 2:
                size = int(raw_input("Enter size -- number of registers: "))
                print "data types: \n 1, int \n 2, string"
                data_type = int(raw_input("Enter data type (1 or 2): "))
                if data_type == 1:
                    input_value = int(raw_input("Enter integer value: "))
                    value_str = pack("%s%s" % ('>', get_variable_type(16*size, 'int')), input_value)
                    wr_2_value = list( unpack('%s%dH' % ('>', size), value_str) )
                    client.write_registers(int(address), wr_2_value, unit=slaveID)
                elif data_type == 2:
                    input_value = raw_input("Enter string value: ")
                    char_cnt = str(size * 2)
                    user_name_fixsize=("{:>" + char_cnt + "}").format(input_value)
                    
                    value_to_write = list(unpack('%s%dH' % ('>', size), user_name_fixsize) )
                    client.write_registers(int(address), value_to_write, unit=slaveID)
                    
                else:
                    print "Please enter a number of 1 or 2. "
                    break
                    
            else:
                print "Please enter a number of 1 or 2. "
                break
    else:
        print "*************Please enter a number of 1,2,3...********** "
#except:
#    print "Exit."
#finally:
#    client.close()
#    print "Closed"
    
    
    
    
    
    
    
