import sys
import time
from struct import pack, unpack
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

com_setting = {"port": "COM2", "baudrate": 9600, "timeout": 3}
client = ModbusClient(method = 'rtu', **com_setting)
client.connect()
print("Connected to server.")

if "--debug" in sys.argv[1:]:
    import logging
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

reg_dict = {1: "Input Register", 2: "Discrete Register", 3: "Coil Register"}

def read_error(unit_number):
    result = client.read_input_registers(386, 1, unit=unit_number)
    values = pack(">h", *result.registers)
    return unpack(">h", values)[0]    
    
    
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
            res = client.read_input_registers(int(address), 2, unit = 1)
            try:
                values = pack(">2H", *res.registers)
                print "Value read: ", unpack(">f", values)[0]
            except:
                print "You entered invalid address... "
    elif registerID == 2:
        while True:
            address = raw_input("Enter Address of Discrete Register: ")
            if address == '<':
                break
            print "Address to read: ", address
            res = client.read_discrete_inputs(int(address), 1, unit = 1)
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
            client.write_coil(int(address), 1, unit=1)
            try:
                print "Status: ", read_error(1) 
            except:
                print "You entered invalid address... "
    else:
        print "*************Please enter a number of 1,2,3...********** "
#except:
#    print "Exit."
#finally:
#    client.close()
#    print "Closed"
    
    
    
    
    
    
    
