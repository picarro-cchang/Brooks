import unittest
from cStringIO import StringIO

# hexfile.py is useful for interpreting data from an Intel hexadecimal file

class Region(object):
    """Represents a region of memory, with data starting at a specified address"""
    def __init__(self,address):
        self.address = address
        self.data = []
    def nextAddress(self):
        return self.address + len(self.data)
    
class HexFile(object):
    def __init__(self,fp):
        """Construct a HexFile object associated with a file fp"""
        self.fp = fp
        self.segAddress = 0
        self.highAddress = 0
    def processLine(self,line):
        if line[0]!=":":
            raise ValueError,"Intel HEX record should start with :"
        sum = 0
        recLength = int(line[1:3],16); sum += recLength
        address = int(line[3:7],16); sum += address>>8; sum += address&0xFF
        recType = int(line[7:9],16); sum += recType
        data = []
        pos = 9
        for k in range(recLength):
            v = int(line[pos:pos+2],16); sum += v
            data.append(chr(v))
            pos += 2
        checksum = int(line[pos:pos+2],16)
        if checksum != (-sum)&0xFF:
            raise ValueError,"Checksum error in INTEL hex file at address %x" % (address,)
        return address,recType,data
    def process(self):
        """The data in the file is returned as a list of contiguous memory regions."""
        regions = []
        nextAddress = None
        for line in self.fp:
            line = line.strip()
            if line:
                address,type,data = self.processLine(line)
                if type not in [0,1]:
                    raise ValueError,"Unimplemented type code: %d" % (type,)
                if type == 0:
                    if address != nextAddress:
                        region = Region(address)
                        regions.append(region)
                        region.data = data
                    else:
                        region.data += data
                    nextAddress = region.nextAddress()
                elif type == 1:
                    # End of file
                    break
        return regions        
    
sampleHex1 = """
:03000000021400E7
:1014000075815F910780FC908000E091389090009A
:10141000E0913890A000E0913890B000E0913890D1
:101420008100E09138909100E0913890A100E09126
:101430003890B100E09138227A04D8FED9FCDAFA6B
:011440002289
:00000001FF
"""

class HexFileTests(unittest.TestCase):
    def setUp(self):
        self.fp = StringIO(sampleHex1)
        self.hexFile = HexFile(self.fp)
        pass
    def tearDown(self):
        self.fp.close()
        pass
    def testLineProcessing(self):
        addresses = []
        types = []
        lengths = []
        for line in self.fp:
            line = line.strip()
            if line:
                addresses.append(self.hexFile.processLine(line)[0])
                types.append(self.hexFile.processLine(line)[1])
                lengths.append(len(self.hexFile.processLine(line)[2]))
        self.assertEqual(lengths,[0x3,0x10,0x10,0x10,0x10,0x1,0x0])
        self.assertEqual(addresses,[0x0000,0x1400,0x1410,0x1420,0x1430,0x1440,0x0000])
        self.assertEqual(types,[0x00,0x00,0x00,0x00,0x00,0x00,0x01])
    def testFileProcessing(self):
        regions = self.hexFile.process()
        self.assertEqual(len(regions),2)
        self.assertEqual(regions[0].address,0x0)
        self.assertEqual(regions[1].address,0x1400)
        self.assertEqual(regions[0].data,['\x02','\x14','\x00'])
        
if __name__ == "__main__":
    unittest.main()
    