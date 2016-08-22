from Host.Common import CmdFIFO
from Host.Common import SharedTypes
from Host.autogen import interface

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%s" % SharedTypes.RPC_PORT_DRIVER,
                                    'DriverRPCTests',
                                    IsDontCareConnection=False)
                                    
print Driver.rdDasReg("LASER1_TEMPERATURE_REGISTER")                                    
