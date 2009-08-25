from ctypes import *

class DataType(Union):
    _fields_ = [
        ("asFloat",c_float),
        ("asUint",c_uint),
        ("asInt",c_int)
    ]

class DIAG_EventLogStruct(Structure):
    _fields_ = [
        ("time",c_uint),
        ("cause",c_uint),
        ("etalonPd1Current",c_uint),
        ("refPd1Current",c_uint),
        ("etalonPd2Current",c_uint),
        ("refPd2Current",c_uint),
        ("etalonTemp",c_uint),
        ("cavityTemp",c_uint),
        ("warmChamberTemp",c_uint),
        ("hotChamberTecHeatsinkTemp",c_uint),
        ("warmChamberTecHeatsinkTemp",c_uint),
        ("laser1Temp",c_uint),
        ("laser2Temp",c_uint),
        ("laserCurrent",c_uint),
        ("cavityPressure",c_uint),
        ("inletPressure",c_uint),
        ("outletPressure",c_uint),
        ("customDataArray",c_ushort*16)
    ]

class RD_ResultsEntryType(Structure):
    _fields_ = [
        ("lockValue",DataType),
        ("ratio1",c_float),
        ("ratio2",c_float),
        ("correctedAbsorbance",c_float),
        ("uncorrectedAbsorbance",c_float),
        ("tunerValue",c_ushort),
        ("pztValue",c_ushort),
        ("etalonAndLaserSelectAndFitStatus",c_ushort),
        ("schemeStatusAndSchemeTableIndex",c_ushort),
        ("msTicks",c_uint),
        ("count",c_ushort),
        ("subSchemeId",c_ushort),
        ("schemeIndex",c_ushort),
        ("fineLaserCurrent",c_ushort),
        ("name",c_char*10),
        ("lockSetpoint",DataType*3),
        ("values",c_uint*16)
    ]

class PidControllerEnvType(Structure):
    _fields_ = [
        ("swpDir",c_int),
        ("lockCount",c_int),
        ("unlockCount",c_int),
        ("firstIteration",c_int),
        ("a",c_float),
        ("u",c_float),
        ("perr",c_float),
        ("derr1",c_float),
        ("derr2",c_float),
        ("Dincr",c_float)
    ]

def ctypesToDict(s):
    """Create a dictionary from a ctypes structure where the keys are the field names"""
    if isinstance(s,(float,int,long,str)):
        return s
    else:
        r = {}
        for f in s._fields_:
            a = getattr(s,f[0])
            if hasattr(a,'_length_'):
                l = []
                for e in a:
                    l.append(ctypesToDict(e))
                r[f[0]] = l
            else:
                r[f[0]] = ctypesToDict(a)
        return r

def dictToCtypes(d,c):
    """Fill the ctypes object c with data from the dictionary d"""
    for k in d:
        if isinstance(d[k],dict):
            dictToCtypes(d[k],getattr(c,k))
        elif isinstance(d[k],list):
            for i,e in enumerate(d[k]):
                if not isinstance(e,dict):
                    getattr(c,k)[i] = e
                else:
                    dictToCtypes(e,getattr(c,k)[i])
        else:
            if hasattr(c,k):
                setattr(c,k,d[k])
            else:
                raise ValueError,"Unknown structure field name %s" % k
    
if __name__ == "__main__":
    p = RD_ResultsEntryType()
    p.ratio1 = 1.2
    p.name = "Hello"
    p.lockSetpoint[0].asInt = 1
    p.lockSetpoint[1].asInt = 2
    p.lockSetpoint[2].asInt = 3
    p.lockValue.asFloat = 1.234
    p.values[0] = 10
    p.values[1] = 20
    p.values[2] = 30
    
    r = ctypesToDict(p)
    print r
    q = RD_ResultsEntryType()
    # r.update(dict(foo='bar'))
    dictToCtypes(r,q)
    print ctypesToDict(q)

    