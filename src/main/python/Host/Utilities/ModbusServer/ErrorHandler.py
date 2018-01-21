from struct import pack, unpack
from enum import Enum

class Errors(Enum):
    NO_ERROR = 0
    ERROR_HANDLER_ERROR = 1
    ERROR = 2
    NO_SUDO_USER_PRIVILEGE = 3
    NO_SYNCTIME_SET = 4
    NO_USER_EXIST = 7
    USERNAME_PASSWORD_INCORRECT = 9
    USER_DISABLED = 10
    ADMIN_RIGHT_REQUIRES = 11
    PASSWORD_LENGTH_ERROR = 12
    PASSWORD_FORMAT_ERROR = 13
    PASSWORD_REUSE_ERROR = 14


class ErrorHandler(object):

    def __init__(self, server, errorkey):
        self.server = server
        self.errorkey=errorkey
        self.variableParam = server.variable_params[errorkey]
        self.MAX_ERROR_VALUE = 2**self.variableParam['bit'] - 1


    def set_error(self, error):
        try:
            #lets make sure that passed value is int number
            if isinstance(error, Errors):
                #Error is x bits register, so lets make sure we are not writing bigger value than
                #what x bits register can handle
                if error.value < self.MAX_ERROR_VALUE:
                    self.__Pack_Write_Error(error.value)
                    return 1
            self.__Pack_Write_Error(Errors.ERROR_HANDLER_ERROR.value)
            return 0
        except:
            self.__Pack_Write_Error(Errors.ERROR_HANDLER_ERROR.value)
            return 0

    def __Pack_Write_Error(self, value):
        str = pack(self.variableParam['format'], value)
        value_to_write = list(unpack('%s%dH' % (self.server.endian, self.variableParam['size']), str))
        self.server.context[self.server.slaveid].setValues(self.variableParam['register'],
                                                           self.variableParam['address'], value_to_write)
