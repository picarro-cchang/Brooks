import time
from struct import unpack
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

client = ModbusClient(method='rtu', port='COM1', timeout=1)
client.connect()

while True:
    try:
        time.sleep(1)
        result = client.read_input_registers(0,24, unit=1)
        print unpack("<sfff", result.registers)
    except Exception, e:
        print "Error in reading Modbus: %s " % e

client.close()