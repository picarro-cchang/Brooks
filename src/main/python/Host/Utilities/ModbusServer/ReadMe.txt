This module is developed by Yuan Ren in early 2017 for the SI2000 analyzers.

I design this module as a general-purpose platform for data transfer and remote control using Modbus.

The module is based on pyModbus. 

server.py: the Modbus server program running on analyzers.
client.py: example program of Modbus client. Used for testing.
ModbusServer.ini: configuration file of server.py
ModbusServer.py: python script of server.py. Define functions for remote control.


Document: http://confluence.picarro.int/display/SEM/Modbus+Programming