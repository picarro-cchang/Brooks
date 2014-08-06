"""
Copyright 2012-2013 Picarro Inc.
"""

import ctypes

from ctypes.wintypes import BOOL
from ctypes.wintypes import DWORD
from ctypes.wintypes import HANDLE


class Iphlpapi(object):
    """
    Wrappers for items defined in Iphlpapi.h.
    """

    MAX_ADAPTER_DESCRIPTION_LENGTH = 128
    MAX_ADAPTER_NAME_LENGTH = 256
    MAX_ADAPTER_ADDRESS_LENGTH = 8

    class IP_ADDR_STRING(ctypes.Structure):
        pass

    LP_IP_ADDR_STRING = ctypes.POINTER(IP_ADDR_STRING)
    IP_ADDR_STRING._fields_ = [
        ('next', LP_IP_ADDR_STRING),
        ('ipAddress', ctypes.c_char * 16),
        ('ipMask', ctypes.c_char * 16),
        ('context', ctypes.c_ulong)]

    class IP_ADAPTER_INFO(ctypes.Structure):
        pass

    LP_IP_ADAPTER_INFO = ctypes.POINTER(IP_ADAPTER_INFO)
    IP_ADAPTER_INFO._fields_ = [
        ('next', LP_IP_ADAPTER_INFO),
        ('comboIndex', ctypes.c_ulong),
        ('adapterName', ctypes.c_char * (MAX_ADAPTER_NAME_LENGTH + 4)),
        ('description', ctypes.c_char * (MAX_ADAPTER_DESCRIPTION_LENGTH + 4)),
        ('addressLength', ctypes.c_uint),
        ('address', ctypes.c_ubyte * MAX_ADAPTER_ADDRESS_LENGTH),
        ('index', ctypes.c_ulong),
        ('type', ctypes.c_uint),
        ('dhcpEnabled', ctypes.c_uint),
        ('currentIpAddress', LP_IP_ADDR_STRING),
        ('ipAddressList', IP_ADDR_STRING),
        ('gatewayList', IP_ADDR_STRING),
        ('dhcpServer', IP_ADDR_STRING),
        ('haveWins', ctypes.c_uint),
        ('primaryWinsServer', IP_ADDR_STRING),
        ('secondaryWinsServer', IP_ADDR_STRING),
        ('leaseObtained', ctypes.c_ulong),
        ('leaseExpires', ctypes.c_ulong)]


    @staticmethod
    def getAdaptersInfo():
        """
        Pythonic wrapper around GetAdaptersInfo().

        Returns:
            An array of IP_ADAPTER_INFO objects.
        """

        GetAdaptersInfo = ctypes.windll.iphlpapi.GetAdaptersInfo
        GetAdaptersInfo.restype = ctypes.c_ulong
        GetAdaptersInfo.argtypes = [Iphlpapi.LP_IP_ADAPTER_INFO,
                                    ctypes.POINTER(ctypes.c_ulong)]

        adapterList = (Iphlpapi.IP_ADAPTER_INFO * 10)()
        buflen = ctypes.c_ulong(ctypes.sizeof(adapterList))

        rc = GetAdaptersInfo(ctypes.byref(adapterList[0]), ctypes.byref(buflen))

        if rc == 0:
            return adapterList
        else:
            return None


class User32(object):
    """
    Wrappers for User32.dll routines/structs/etc.
    """

    @staticmethod
    def lockWorkStation():
        LockWorkstation = ctypes.windll.user32.LockWorkStation
        LockWorkstation.restype = BOOL

        return LockWorkstation()


class Kernel32(object):
    """
    Wrappers for Kernel32.dll routines/structs/etc.
    """

    WAIT_OBJECT_0 = 0x00000000L

    EVENT_MODIFY_STATE = 0x0002
    EVENT_ALL_ACCESS = 0x1F0003


    @staticmethod
    def exitProcess(retCode):
        return ctypes.windll.kernel32.ExitProcess(retCode)

    @staticmethod
    def createEvent(manualReset, name):
        CreateEvent = ctypes.windll.kernel32.CreateEventA
        CreateEvent.restype = HANDLE

        return CreateEvent(None, manualReset, 0, name)

    @staticmethod
    def setEvent(handle):
        SetEvent = ctypes.windll.kernel32.SetEvent
        SetEvent.restype = BOOL

        return SetEvent(handle)

    @staticmethod
    def openEvent(access, name):
        OpenEvent = ctypes.windll.kernel32.OpenEventA
        OpenEvent.restype = HANDLE

        return OpenEvent(access, 0, name)

    @staticmethod
    def waitForMultipleObjects(handles, waitAll, milliSeconds):
        WaitForMultipleObjects = ctypes.windll.kernel32.WaitForMultipleObjects
        WaitForMultipleObjects.restype = DWORD

        arrayType = ctypes.c_void_p * len(handles)
        arrayHandles = arrayType(*handles)

        return WaitForMultipleObjects(len(arrayHandles), arrayHandles, waitAll, DWORD(int(milliSeconds)))

    @staticmethod
    def waitForSingleObject(h, milliSeconds):
        WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
        WaitForSingleObject.restype = DWORD

        return WaitForSingleObject(h, DWORD(int(milliSeconds)))

    @staticmethod
    def getLastError():
        GetLastError = ctypes.windll.kernel32.GetLastError
        GetLastError.restype = DWORD

        return GetLastError()
