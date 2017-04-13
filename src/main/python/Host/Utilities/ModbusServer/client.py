import time
from struct import pack, unpack
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

com_setting = {"port": "COM7", "baudrate": 9600, "timeout": 1}
client = ModbusClient(method='rtu', **com_setting)
client.connect()

while True:
    try:
        time.sleep(1)
        result = client.read_input_registers(0,12, unit=1)
        values = pack(">12H", *result.registers)
        print unpack(">12sfff", values)
    except Exception, e:
        print "Error in reading Modbus: %s " % e

client.close()