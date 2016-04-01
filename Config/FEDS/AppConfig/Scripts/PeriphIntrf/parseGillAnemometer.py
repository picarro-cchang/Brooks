
import struct

from Host.PeriphIntrf.PeripheralStatus import PeripheralStatus


GILL_MSG_LEN = 27
GILL_MSG_FORMAT = 'B' * GILL_MSG_LEN


def parseGillAnemometer(rawStr):
    status = 0

    rawStr = rawStr.strip()

    if len(rawStr) != GILL_MSG_LEN:
        status |= PeripheralStatus.MALFORMED_DATA_STRING
        return [0.0, 0.0, status]

    rawBytes = struct.unpack(GILL_MSG_FORMAT, rawStr)

    # Sample message from Gill in UV, Continuous mode:
    # ☻Q,+000.05,+000.00,M,00,♥35. The checksum is XOR of all bytes
    # between \x02 and \x03 tags.
    checksum = 0
    for b in rawBytes[1:-3]:
        checksum ^= b

    msgChecksum = int(chr(rawBytes[-2])+chr(rawBytes[-1]), 16)

    if checksum != msgChecksum:
        status |= PeripheralStatus.WIND_MESSAGE_CHECKSUM_ERROR
        return [0.0, 0.0, status]

    atoms = rawStr.split(",")

    if atoms[3] != 'M':
        status |= PeripheralStatus.WIND_BAD_UNITS

    # Check anemometer status messages
    if atoms[4] == '01':
        status |= PeripheralStatus.WIND_AXIS1_FAILED
    elif atoms[4] == '02':
        status |= PeripheralStatus.WIND_AXIS2_FAILED
    elif atoms[4] == '04':
        status |= (PeripheralStatus.WIND_AXIS1_FAILED | PeripheralStatus.WIND_AXIS2_FAILED)
    elif atoms[4] == '08':
        status |= PeripheralStatus.WIND_NONVOLATILE_CHECKSUM_ERROR
    elif atoms[4] == '09':
        status |= PeripheralStatus.WIND_ROM_CHECKSUM_ERROR

    windLon, windLat = -float(atoms[1]), float(atoms[2])

    return [windLon, windLat, status]



