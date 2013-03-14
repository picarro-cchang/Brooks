from Host.Common import CmdFIFO
RPC_PORT_DRIVER = 50010
import time

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, 
    'RDDGainSetter', IsDontCareConnection = False)

balance = int(raw_input("Balance (0-255)? "))
gain = int(raw_input("Gain (0-255)? "))
Driver.wrDasReg("RDD_BALANCE_REGISTER", balance)
Driver.wrDasReg("RDD_GAIN_REGISTER", gain)
time.sleep(1.0)
Driver.rddCommand(0x91)
time.sleep(1.0)
Driver.rddCommand(0x93)
