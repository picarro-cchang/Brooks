# Class for interfacing to Measurement Computing hardware

from ctypes import c_int, c_long, c_short, c_ulong, c_ushort, c_void_p, c_char_p, POINTER
from ctypes import byref, create_string_buffer, windll
import sys
import time

class MCC_Error(RuntimeError):
    pass

# Status values
IDLE          =   0
RUNNING       =   1

# Types of configuration information
GLOBALINFO    =     1
BOARDINFO     =     2
DIGITALINFO   =     3
COUNTERINFO   =     4
EXPANSIONINFO =     5
MISCINFO      =     6
EXPINFOARRAY  =     7
MEMINFO       =     8

AIFUNCTION    =  1 # Analog Input Function
AOFUNCTION    =  2 # Analog Output Function
DIFUNCTION    =  3 # Digital Input Function
DOFUNCTION    =  4 # Digital Output Function
CTRFUNCTION   =  5 # Counter Function
DAQIFUNCTION  =  6 # Daq Input Function
DAQOFUNCTION  =  7 # Daq Output Function

# Selectable A/D Ranges codes
BIP60VOLTS      = 20 # -60 to 60 Volts
BIP20VOLTS      = 15 # -20 to +20 Volts
BIP15VOLTS      = 21 # -15 to +15 Volts
BIP10VOLTS      = 1  # -10 to +10 Volts
BIP5VOLTS       = 0  # -5 to +5 Volts
BIP4VOLTS       = 16 # -4 to + 4 Volts
BIP2PT5VOLTS    = 2  # -2.5 to +2.5 Volts
BIP2VOLTS       = 14 # -2.0 to +2.0 Volts
BIP1PT25VOLTS   = 3  # -1.25 to +1.25 Volts
BIP1VOLTS       = 4  # -1 to +1 Volts
BIPPT625VOLTS   = 5  # -.625 to +.625 Volts
BIPPT5VOLTS     = 6  # -.5 to +.5 Volts
BIPPT25VOLTS    = 12 # -0.25 to +0.25 Volts
BIPPT2VOLTS     = 13 # -0.2 to +0.2 Volts
BIPPT1VOLTS     = 7  # -.1 to +.1 Volts
BIPPT05VOLTS    = 8  # -.05 to +.05 Volts
BIPPT01VOLTS    = 9  # -.01 to +.01 Volts
BIPPT005VOLTS   = 10 # -.005 to +.005 Volts
BIP1PT67VOLTS   = 11 # -1.67 to +1.67 Volts
BIPPT312VOLTS   = 17 # -0.312 to +0.312 Volts
BIPPT156VOLTS   = 18 # -0.156 to +0.156 Volts
BIPPT125VOLTS   = 22 # -0.125 to +0.125 Volts
BIPPT078VOLTS   = 19 # -0.078 to +0.078 Volts

# Option Flags
FOREGROUND    =   0x0000    # Run in foreground, don't return till done
BACKGROUND    =   0x0001    # Run in background, return immediately

SINGLEEXEC    =   0x0000    # One execution
CONTINUOUS    =   0x0002    # Run continuously until cbstop() called

TIMED         =   0x0000    # Time conversions with internal clock
EXTCLOCK      =   0x0004    # Time conversions with external clock

NOCONVERTDATA =   0x0000    # Return raw data
CONVERTDATA   =   0x0008    # Return converted A/D data

NODTCONNECT   =   0x0000    # Disable DT Connect
DTCONNECT     =   0x0010    # Enable DT Connect
SCALEDATA     =   0x0010    # Scale scan data to engineering units

DEFAULTIO     =   0x0000    # Use whatever makes sense for board
SINGLEIO      =   0x0020    # Interrupt per A/D conversion
DMAIO         =   0x0040    # DMA transfer
BLOCKIO       =   0x0060    # Interrupt per block of conversions
BURSTIO       =  0x10000    # Transfer upon scan completion
RETRIGMODE    =  0x20000    # Re-arm trigger upon acquiring trigger count samples
NONSTREAMEDIO = 0x040000    # Non-streamed D/A output
ADCCLOCKTRIG  = 0x080000    # Output operation is triggered on ADC clock
ADCCLOCK      = 0x100000    # Output operation is paced by ADC clock
HIGHRESRATE   = 0x200000    # Use high resolution rate
SHUNTCAL      =  0x400000   # Enable Shunt Calibration

BYTEXFER      =   0x0000    # Digital IN/OUT a byte at a time
WORDXFER      =   0x0100    # Digital IN/OUT a word at a time

INDIVIDUAL    =   0x0000    # Individual D/A output
SIMULTANEOUS  =   0x0200    # Simultaneous D/A output

FILTER        =   0x0000    # Filter thermocouple inputs
NOFILTER      =   0x0400    # Disable filtering for thermocouple

NORMMEMORY    =   0x0000    # Return data to data array
EXTMEMORY     =   0x0800    # Send data to memory board via DT-Connect

BURSTMODE     =   0x1000    # Enable burst mode

NOTODINTS     =   0x2000    # Disbale time-of-day interrupts

EXTTRIGGER    =   0x4000    # A/D is triggered externally

NOCALIBRATEDATA = 0x8000    # Return uncalibrated PCM data
CALIBRATEDATA =   0x0000    # Return calibrated PCM A/D data

CTR16BIT      = 0x0000      # Return 16-bit counter data
CTR32BIT      = 0x0100      # Return 32-bit counter data
CTR48BIT      = 0x0200      # Return 48-bit counter data

ENABLED       =   1
DISABLED      =   0

UPDATEIMMEDIATE = 0
UPDATEONCOMMAND = 1

BIBOARDTYPE   =       1
BIADRES       =     291
BIDACRES      =     292

# Types of digital I/O Ports

DIGITALOUT    =   1
DIGITALIN     =   2

AUXPORT       =   1
FIRSTPORTA    =   10
FIRSTPORTB    =   11
FIRSTPORTCL   =   12
FIRSTPORTC    =   12
FIRSTPORTCH   =   13
SECONDPORTA   =   14
SECONDPORTB   =   15
SECONDPORTCL  =   16
SECONDPORTCH  =   17
THIRDPORTA    =   18
THIRDPORTB    =   19
THIRDPORTCL   =   20
THIRDPORTCH   =   21
FOURTHPORTA   =   22
FOURTHPORTB   =   23
FOURTHPORTCL  =   24
FOURTHPORTCH  =   25
FIFTHPORTA    =   26
FIFTHPORTB    =   27
FIFTHPORTCL   =   28
FIFTHPORTCH   =   29
SIXTHPORTA    =   30
SIXTHPORTB    =   31
SIXTHPORTCL   =   32
SIXTHPORTCH   =   33
SEVENTHPORTA  =   34
SEVENTHPORTB  =   35
SEVENTHPORTCL =   36
SEVENTHPORTCH =   37
EIGHTHPORTA   =   38
EIGHTHPORTB   =   39
EIGHTHPORTCL  =   40
EIGHTHPORTCH  =   41

class MeasComp(object):
    def __init__(self):
        DLL_Path = ["cbw32.dll"]
        for p in DLL_Path:
            try:
                self.measCompDLL = windll.LoadLibrary(p)
                break
            except:
                continue
        else:
            raise ValueError("Cannot load Measurement Computing shared library")

        # This method is used to provide the error messages for those methods
        #  that return a status code
        self.cbGetErrMsg = self.measCompDLL.cbGetErrMsg
        self.cbGetErrMsg.argtypes = [c_int, c_char_p]
        self.cbGetErrMsg.restype = c_int

        # These methods do not return a status code, so they are not wrapped
        self.cbWinBufAlloc = self.measCompDLL.cbWinBufAlloc
        self.cbWinBufAlloc.argtypes = [c_long]
        self.cbWinBufAlloc.restype = c_void_p

        self.cbWinBufAlloc32 = self.measCompDLL.cbWinBufAlloc32
        self.cbWinBufAlloc32.argtypes = [c_long]
        self.cbWinBufAlloc32.restype = c_void_p

        self.cbWinBufAlloc64 = self.measCompDLL.cbWinBufAlloc64
        self.cbWinBufAlloc64.argtypes = [c_long]
        self.cbWinBufAlloc64.restype = c_void_p

        # These methods return a status code, so they are wrapped to throw an exception
        #  with a meaningful message if the status is non-zero
        self.cbAInScan = self._wrap(self.measCompDLL.cbAInScan)
        self.cbAInScan.argtypes = [c_int, c_int, c_int, c_long, POINTER(c_long),
                                   c_int, c_void_p, c_int]
        self.cbAInScan.restype = c_int

        self.cbALoadQueue = self._wrap(self.measCompDLL.cbALoadQueue)
        self.cbALoadQueue.argtypes = [c_int, POINTER(c_short), POINTER(c_short), c_int]
        self.cbALoadQueue.restype = c_int

        self.cbAOut = self._wrap(self.measCompDLL.cbAOut)
        self.cbAOut.argtypes = [c_int, c_int, c_int, c_short]
        self.cbAOut.restype = c_int

        self.cbAOutScan = self._wrap(self.measCompDLL.cbAOutScan)
        self.cbAOutScan.argtypes = [c_int, c_int, c_int, c_long, POINTER(c_long),
                                    c_int, c_void_p, c_int]
        self.cbAOutScan.restype = c_int

        self.cbDBitIn = self._wrap(self.measCompDLL.cbDBitIn)
        self.cbDBitIn.argtypes = [c_int, c_int, c_int, POINTER(c_ushort)]
        self.cbDBitIn.restype = c_int

        self.cbDBitOut = self._wrap(self.measCompDLL.cbDBitOut)
        self.cbDBitOut.argtypes = [c_int, c_int, c_int, c_ushort]
        self.cbDBitOut.restype = c_int

        self.cbDConfigPort = self._wrap(self.measCompDLL.cbDConfigPort)
        self.cbDConfigPort.argtypes = [c_int, c_int, c_int]
        self.cbDConfigPort.restype = c_int

        self.cbDConfigBit = self._wrap(self.measCompDLL.cbDConfigBit)
        self.cbDConfigBit.argtypes = [c_int, c_int, c_int, c_int]
        self.cbDConfigBit.restype = c_int

        self.cbDIn = self._wrap(self.measCompDLL.cbDIn)
        self.cbDIn.argtypes = [c_int, c_int, c_int, POINTER(c_ushort)]
        self.cbDIn.restype = c_int

        self.cbDInScan = self._wrap(self.measCompDLL.cbDInScan)
        self.cbDInScan.argtypes = [c_int, c_int, c_long, POINTER(c_long), c_void_p, c_int]
        self.cbDInScan.restype = c_int

        self.cbDOut = self._wrap(self.measCompDLL.cbDOut)
        self.cbDOut.argtypes = [c_int, c_int, c_int, c_ushort]
        self.cbDOut.restype = c_int

        self.cbDOutScan = self._wrap(self.measCompDLL.cbDOutScan)
        self.cbDOutScan.argtypes = [c_int, c_int, c_long, POINTER(c_long), c_void_p, c_int]
        self.cbDOutScan.restype = c_int

        self.cbErrHandling = self._wrap(self.measCompDLL.cbErrHandling)
        self.cbErrHandling.argtypes = [c_int, c_int]
        self.cbErrHandling.restype = c_int

        self.cbFlashLED = self._wrap(self.measCompDLL.cbFlashLED)
        self.cbFlashLED.argtypes = [c_int]
        self.cbFlashLED.restype = c_int

        self.cbGetConfig = self._wrap(self.measCompDLL.cbGetConfig)
        self.cbGetConfig.argtypes = [c_int, c_int, c_int, c_int, POINTER(c_int)]
        self.cbGetConfig.restype = c_int

        self.cbGetStatus = self._wrap(self.measCompDLL.cbGetIOStatus)
        self.cbGetStatus.argtypes = [c_int, POINTER(c_short), POINTER(c_ulong),
                                     POINTER(c_long), c_int]
        self.cbGetStatus.restype = c_int

        self.cbStopBackground = self._wrap(self.measCompDLL.cbStopIOBackground)
        self.cbStopBackground.argtypes = [c_int, c_int]
        self.cbStopBackground.restype = c_int

        self.cbWinBufFree = self._wrap(self.measCompDLL.cbWinBufFree)
        self.cbWinBufFree.argtypes = [c_void_p]
        self.cbWinBufFree.restype = c_int

    def _wrap(self,func):
        """Wraps a function so that it throws an exception rather
        than returning an error code. The keyword parameter wrap
        (True by default) controls whether this wrapping takes place."""
        def _func(*a,**k):
            wrap = k.get("wrap",True)
            if "wrap" in k: del k["wrap"]
            stat = func(*a,**k)
            if stat != 0 and wrap:
                msg = create_string_buffer('\000' * 132)
                self.cbGetErrMsg(stat,msg)
                raise MCC_Error(msg.value)
            return stat
        return _func