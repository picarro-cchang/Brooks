# Program large serial EEPROM for Cypress FX2 from a 0xC2 mode file

from ctypes import byref, c_ubyte, create_string_buffer
from usb import LibUSB
from hexfile import HexFile
from time import sleep
from cStringIO import StringIO
from array import array
from sys import stdout

myVendAx = """
:0A0DBD00000102020303040405050F
:1005C000E4F52CF52BF52AF529C203C200C202C2BC
:1005D00001120D797E087F6F8E0A8F0B75120875D8
:1005E000138175080875098B7510087511AB7514A2
:1005F000087515CBEE54E0700302070C752D0075DD
:100600002E808E2F8F30C374F59FFF74089ECF24E9
:1006100002CF3400FEE48F288E27F526F525F52439
:10062000F523F522F521AF28AE27AD26AC25AB2466
:10063000AA23A922A821C3120A07502AE52E25249D
:10064000F582E52D3523F58374CDF0E4FAF9F8E56C
:10065000242401F524EA3523F523E93522F522E89F
:100660003521F52180C0E4F524F523F522F521AFED
:1006700028AE27AD26AC25AB24AA23A922A821C3E6
:10068000120A075035AE23AF24E5302FF582E52F4F
:100690003EF583E0FDE52E2FF582E52D3EF583ED59
:1006A000F0E4FAF9F8EF2401F524EA3EF523E93500
:1006B00022F522E83521F52180B5852D0A852E0BFE
:1006C000746F2480FF740834FFFEC3E5139FF51395
:1006D000E5129EF512C3E50D9FF50DE50C9EF50C98
:1006E000C3E50F9FF50FE50E9EF50EC3E5099FF5D7
:1006F00009E5089EF508C3E5119FF511E5109EF583
:1007000010C3E5159FF515E5149EF514D2E843D8FE
:100710002090E668E04409F090E65CE0443DF0D2C9
:10072000AF90E680E054F7F0538EF8C20330010535
:10073000120327C201300329120DDB5024C2031219
:100740000CB920001690E682E030E704E020E1EFEB
:1007500090E682E030E604E020E0E4120C61120D45
:06076000DD1208FF80C756
:010766002270
:1003270090E6B9E070030204021470030204AB24E0
:10033700FE700302054024FB70030203FC147003E4
:100347000203F61470030203EA1470030203F02495
:100357000560030205AC120DDF40030205B890E605
:10036700BBE024FE602C14604724FD601614603146
:1003770024067065E50A90E6B3F0E50B90E6B4F065
:100387000205B8E51290E6B3F0E51390E6B4F00283
:1003970005B8E50C90E6B3F0E50D90E6B4F002057C
:1003A700B8E50E90E6B3F0E50F90E6B4F00205B8B5
:1003B70090E6BAE0FF120C8DAA06A9077B01EA496D
:1003C700600DEE90E6B3F0EF90E6B4F00205B8905A
:1003D700E6A0E04401F00205B890E6A0E04401F091
:1003E7000205B8120D9F0205B8120DC70205B81213
:1003F70008F70205B8120D8D0205B8120DE140038A
:100407000205B890E6B8E0247F602B14603C240214
:1004170060030204A1A200E433FF25E0FFA202E487
:10042700334F90E740F0E4A3F090E68AF090E68B34
:100437007402F00205B8E490E740F0A3F090E68A72
:10044700F090E68B7402F00205B890E6BCE0547EAB
:10045700FF7E00E0D3948040067C007D0180047C11
:10046700007D00EC4EFEED4F24BDF582740D3EF588
:1004770083E493FF3395E0FEEF24A1FFEE34E68F8C
:1004870082F583E0540190E740F0E4A3F090E68A18
:10049700F090E68B7402F00205B890E6A0E0440104
:1004A700F00205B8120DE340030205B890E6B8E084
:1004B70024FE601D240260030205B890E6BAE0B48A
:1004C7000105C2000205B890E6A0E04401F002056C
:1004D700B890E6BAE0705990E6BCE0547EFF7E0023
:1004E700E0D3948040067C007D0180047C007D0081
:1004F700EC4EFEED4F24BDF582740D3EF583E4937B
:10050700FF3395E0FEEF24A1FFEE34E68F82F583FB
:10051700E054FEF090E6BCE05480FF131313541F21
:10052700FFE0540F2F90E683F0E04420F00205B877
:1005370090E6A0E04401F08078120DE5507390E654
:10054700B8E024FE60202402706790E6BAE0B401A8
:1005570004D200805C90E6BAE06402605490E6A0A2
:10056700E04401F0804B90E6BCE0547EFF7E00E063
:10057700D3948040067C007D0180047C007D00ECE4
:100587004EFEED4F24BDF582740D3EF583E493FFD7
:100597003395E0FEEF24A1FFEE34E68F82F583E08A
:1005A7004401F0800C120080500790E6A0E044015F
:0805B700F090E6A0E04480F0A2
:0105BF002219
:03003300020DD7E4
:040DD70053D8EF32CC
:100D7900D200120DCF90E678E05410FFC4540F440E
:040D890050F51D22E2
:0108FF0022D6
:020DDB00D32221
:020DDD00D3221F
:020DDF00D3221D
:0808F70090E6BAE0F51ED322E1
:100D8D0090E740E51EF0E490E68AF090E68B04F0E3
:020D9D00D3225F
:080DC70090E6BAE0F51CD3220E
:100D9F0090E740E51CF0E490E68AF090E68B04F0D3
:020DAF00D3224D
:020DE100D3221B
:020DE300D32219
:020DE500D32217
:10008000E51D13E433F51F90E6B9E0245EB40B00E0
:1000900040030203259000A375F003A4C58325F057
:1000A000C5837302019D02019D0201180200C40272
:1000B00000DE0200FE020147020197020121020157
:1000C0003402016D90E740E51FF0E490E68AF0907D
:1000D000E68B04F090E6A0E04480F002032590E671
:1000E00000E0FFC4540F90E740F0E490E68AF090FF
:1000F000E68B04F090E6A0E04480F002032590E750
:1001000040740FF0E490E68AF090E68B04F090E6FD
:10011000A0E04480F002032590E6BAE0F51D02035A
:100120002590E67AE054FEF0E490E68AF090E68BC3
:10013000F002032590E67AE04401F0E490E68AF0CC
:1001400090E68BF002032590E7407407F0E490E618
:100150008AF090E68B04F090E6A0E04480F07FE81F
:100160007E03120AADD204120C3202032590E6B5CA
:10017000E054FEF090E6BFE090E68AF090E6BEE044
:1001800090E68BF090E6BBE090E6B3F090E6BAE044
:1001900090E6B4F0020325751F01431D0190E6BAF5
:1001A000E0753100F532A3E0FEE4EE423190E6BEA8
:1001B000E0753300F534A3E0FEE4EE423390E6B898
:1001C000E064C0600302028DE5344533700302032E
:1001D0002590E6A0E020E1F9C3E5349440E53394AE
:1001E0000050088533358534368006753500753600
:1001F0004090E6B9E0B4A335E4F537F538C3E53807
:100200009536E53795355060E5322538F582E5318C
:100210003537F583E0FF74402538F582E434E7F59F
:1002200083EFF00538E5387002053780D0E4F53704
:10023000F538C3E5389536E53795355018744025BF
:1002400038F582E434E7F58374CDF00538E538708D
:1002500002053780DDAD367AE779407EE77F40AB37
:1002600007AF32AE31120A18E490E68AF090E68BBE
:10027000E536F02532F532E5353531F531C3E53473
:100280009536F534E5339535F5330201C890E6B877
:10029000E064406003020325E53445337003020344
:1002A00025E490E68AF090E68BF090E6A0E020E16D
:1002B000F990E68BE0753500F53690E6B9E0B4A329
:1002C00035E4F537F538C3E5389536E537953550DB
:1002D0003874402538F582E434E7F583E0FFE532F1
:1002E0002538F582E5313537F583EFF00538E53807
:1002F0007002053780D0AD367AE779407EE77F40DF
:10030000AB07AF32AE31120B97E5362532F532E549
:10031000353531F531C3E5349536F534E53395356A
:06032000F533020298C350
:0103260022B4
:100CDE00C0E0C083C08290E6B5E04401F0D201537B
:0F0CEE0091EF90E65D7401F0D082D083D0E032B8
:100D4D00C0E0C083C0825391EF90E65D7404F0D093
:060D5D0082D083D0E032D9
:100D6300C0E0C083C0825391EF90E65D7402F0D07F
:060D730082D083D0E032C3
:100AF300C0E0C083C08290E680E030E70E85080C3A
:100B030085090D85100E85110F800C85100C85113C
:100B13000D85080E85090F5391EF90E65D7410F073
:070B2300D082D083D0E03244
:100D3500C0E0C083C082D2035391EF90E65D740892
:080D4500F0D082D083D0E0322F
:100B2A00C0E0C083C08290E680E030E70E85080C02
:100B3A0085090D85100E85110F800C85100C851105
:100B4A000D85080E85090F5391EF90E65D7420F02C
:070B5A00D082D083D0E0320D
:010DE70032D9
:010DE80032D8
:010DE90032D7
:010DEA0032D6
:010DEB0032D5
:010DEC0032D4
:010DED0032D3
:010DEE0032D2
:010DEF0032D1
:010DF00032D0
:010DF10032CF
:010DF20032CE
:010DF30032CD
:010DF40032CC
:010DF50032CB
:010DF60032CA
:010DF70032C9
:010DF80032C8
:010DF90032C7
:010DFA0032C6
:010DFB0032C5
:010DFC0032C4
:010DFD0032C3
:010DFE0032C2
:010DFF0032C1
:010E000032BF
:010E010032BE
:010E020032BD
:010E030032BC
:010E040032BB
:010E050032BA
:010E060032B9
:010E070032B8
:010E080032B7
:010E090032B6
:010E0A0032B5
:060A6300AB07AA06AC057A
:100A6900E4FDE51F6010EA7E000DEE2400F582E446
:100A79003410F583EAF0EBAE050D74002EF582E42F
:100A89003410F583EBF0AF050D74002FF582E434D3
:100A990010F583ECF07A107B00AF1D120D19AF1D14
:030AA900120B61CC
:010AAC002227
:0A0B97008E398F3A8D3B8A3C8B3D6E
:100BA100E4F53EE53EC3953B5020053AE53AAE39C2
:100BB1007002053914FFE53D253EF582E4353CF52B
:0A0BC10083E0FD120A63053E80D9AF
:010BCB002207
:0A0A18008E398F3A8D3B8A3C8B3DEE
:100A2200E4FDF53EE51F6012E539FF7E000DEE2480
:100A320000F582E43410F583EFF0E53AAE050D746B
:100A4200002EF582E43410F583E53AF07A107B004B
:100A5200AF1D120D19AB3DAA3CAD3BAF1D120CFDF3
:010A62002271
:10086F0012010002000000404705021000000102C3
:10087F0000010A06000200000040010009022000EA
:10088F00010100A0320904000002FF00000007056B
:10089F000202000200070586020002000902200082
:1008AF00010100A0320904000002FF00000007054B
:1008BF000102400000070581024000000403090403
:1008CF00100343007900700072006500730073001D
:1008DF00160345005A002D0055005300420020001A
:0808EF00460058003200000031
:100C610090E682E030E004E020E60B90E682E0309E
:100C7100E119E030E71590E680E04401F07F147E51
:0C0C810000120AAD90E680E054FEF02264
:100CB90090E682E044C0F090E681F04387010000AD
:040CC9000000002205
:100C320030040990E680E0440AF0800790E680E004
:100C42004408F07FDC7E05120AAD90E65D74FFF089
:0F0C520090E65FF05391EF90E680E054F7F022C8
:100AAD008E398F3A90E600E054187012E53A240121
:100ABD00FFE43539C313F539EF13F53A801590E698
:100ACD0000E05418FFBF100BE53A25E0F53AE53983
:100ADD0033F539E53A153AAE39700215394E6005E0
:060AED00120CCD80EE2288
:080DCF00E4F51BD2E9D2AF22CA
:100B610090E678E020E6F9C2E990E678E04480F08A
:100B7100EF25E090E679F090E678E030E0F990E654
:100B810078E04440F090E678E020E6F990E678E0FD
:060B910030E1D6D2E9229A
:100C0000A90790E678E020E6F9E51B702390E678E6
:100C1000E04480F0E925E090E679F08D16AF03A975
:100C2000077517018A188919E4F51A751B01D32273
:020C3000C322DD
:100BCC00A90790E678E020E6F9E51B702590E67819
:100BDC00E04480F0E925E0440190E679F08D16AF11
:100BEC0003A9077517018A188919E4F51A751B03EF
:040BFC00D322C3221B
:03004B0002076742
:10076700C0E0C083C082C085C084C086758600C0D3
:10077700D075D000C000C001C002C003C006C007CA
:1007870090E678E030E206751B0602085190E6789D
:10079700E020E10CE51B64026006751B07020851A7
:1007A700E51B24FE605F14603624FE7003020842D6
:1007B70024FC700302084E24086003020851AB179B
:1007C700AA18A919AF1A051A8F827583001209B8DA
:1007D70090E679F0E51A65167070751B05806B90C9
:1007E700E679E0AB17AA18A919AE1A8E82758300AD
:1007F7001209E5751B02E5166401704E90E678E074
:100807004420F08045E51624FEB51A0790E678E007
:100817004420F0E51614B51A0A90E678E04440F053
:10082700751B0090E679E0AB17AA18A919AE1A8EC6
:10083700827583001209E5051A800F90E678E04477
:1008470040F0751B008003751B005391DFD007D064
:1008570006D003D002D001D000D0D0D086D084D02B
:0808670085D082D083D0E0327D
:020C8D00A907B5
:100C8F00AE14AF158F828E83A3E064037017AD018E
:100C9F0019ED7001228F828E83E07C002FFDEC3ED8
:090CAF00FEAF0580DF7E007F002E
:010CB8002219
:100CFD00120BCCE51B24FA600E146006240770F36A
:0C0D0D00D322E4F51BD322E4F51BD32213
:100D1900120C00E51B24FA600E146006240770F318
:0C0D2900D322E4F51BD322E4F51BD322F7
:100CCD007400F58690FDA57C05A3E582458370F93A
:010CDD0022F4
:03004300020900AF
:030053000209009F
:10090000020CDE00020D6300020D4D00020D3500E9
:10091000020AF300020B2A00020DE700020DE800B4
:10092000020DE900020DEA00020DEB00020DEC00E1
:10093000020DED00020DEE00020DEF00020DF000C1
:10094000020DF100020DE800020DF200020DF300AD
:10095000020DF400020DF500020DF600020DF70085
:10096000020DF800020DE800020DE800020DE8009B
:10097000020DF900020DFA00020DFB00020DFC0051
:10098000020DFD00020DFE00020DFF00020E000030
:10099000020E0100020E0200020E0300020E04000D
:1009A000020E0500020E0600020E0700020E0800ED
:0809B000020E0900020E0A000C
:03000000020DB13D
:0C0DB100787FE4F6D8FD75813E0205C095
:1009B800BB010CE58229F582E5833AF583E02250F4
:1009C80006E92582F8E622BBFE06E92582F8E2223E
:0D09D800E58229F582E5833AF583E4932258
:1009E500F8BB010DE58229F582E5833AF583E8F048
:1009F500225006E92582C8F622BBFE05E92582C8F4
:020A0500F222DB
:100A0700EB9FF5F0EA9E42F0E99D42F0E89C45F045
:010A170022BC
:00000001FF
"""

if __name__ == "__main__":
    # Ids are for bare Cypress FX2 kit and for the Silverstone FX2 EEPROM
    validIds = [(0x4B4,0x8613),(0x4B4,0x1002)]
    imageString = ["Unprogrammed FX2 device","Picarro Silverstone image"]
    usb = LibUSB()
    usb.usbInit()
    #print "usbFindBusses returns %d"  % usb.usbFindBusses()
    #print "usbFindDevices returns %d" % usb.usbFindDevices()
    handle = None
    while handle == None:
        for bus in usb.usbBusses():
            #print bus.dirname
            for pDev in usb.usbDevices(bus):
                dev = pDev.contents
                #print "%s,%x,%x" % (dev.filename, dev.descriptor.idVendor, dev.descriptor.idProduct)
                (vid,pid) = (dev.descriptor.idVendor,dev.descriptor.idProduct)
                try:
                    idIndex = validIds.index((vid,pid))
                    handle = usb.usbOpen(pDev)
                    break
                except:
                    pass
            if handle != None: break
        else:
            raw_input("Unrecognized FX2 firmware.\nDisconnect EEPROM from FX2, reset and press <Enter> after enumeration")
                    
    raw_input("%s recognized.\nCheck EEPROM is connected, and press <Enter> to continue" % imageString[idIndex])
    if usb.usbSetConfiguration(handle,1) < 0:
        usb.usbClose(handle)
        raise ValueError("Setting config 1 failed")
    if usb.usbClaimInterface(handle,0) < 0:
        usb.usbClose(handle)
        raise ValueError("Claiming interface 0 failed")

    try:
        # Reset the 8051 by sending it a vendor command
        usb.usbControlMsg(handle,0x40,0xA0,0xE600,0x00,byref(c_ubyte(0x1)),1,5000)
        block = 128 # Maximum length for download
        # Use the same vendor command to load in the hexadecimal data
        fp = StringIO(myVendAx)
        hexFile = HexFile(fp)
        regions = hexFile.process()
        for r in regions:
            n = len(r.data)
            addr = r.address
            start = 0
            while n > block:
                usb.usbControlMsg(handle,0x40,0xA0,addr+start,0x00,
                create_string_buffer("".join(r.data[start:start+block]),block),block,5000)
                n -= block
                start += block
            if n>0:
                usb.usbControlMsg(handle,0x40,0xA0,addr+start,0x00,
                create_string_buffer("".join(r.data[start:start+n]),n),n,5000)
        # Restart the 8051 by sending it a vendor command
        usb.usbControlMsg(handle,0x40,0xA0,0xE600,0x00,byref(c_ubyte(0x0)),1,5000)
        # Send command to configure for EEPROM with dual byte address
        usb.usbControlMsg(handle,0x40,0xA4,0x051,0x00,byref(c_ubyte(0x1)),0,5000)
        # Confirm EEPROM type
        typeCode = c_ubyte(0)
        usb.usbControlMsg(handle,0xC0,0xA5,0x00,0x00,byref(typeCode),1,5000)
        if typeCode.value != 1:
            raise ValueError("EEPROM type has not been set correctly")
        while True:
            fname = raw_input("Name of EEPROM image file? ")
            fp = file(fname,"rb")
            image = fp.read()
            if ord(image[0]) == 0xC2: break
            print "First byte of Cypress FX2 image file must be 0xC2"
        # Set first byte to zero, so that we can interrupt programming
        image = '\0' + image[1:]
        print "Programming EEPROM, please wait..."
        # Note that we must break up large images into blocks before sending them to the USB FIFO. If we do not,
        #  only the first portion of the EEPROM is written correctly, and subsequent calls to read back the EEPROM
        #  for verification fail
        n = len(image)
        addr = 0
        while n > block:
            usb.usbControlMsg(handle,0x40,0xA2,addr,0x00,
            create_string_buffer(image[addr:addr+block],block),block,60000)
            stdout.write(".")
            n -= block
            addr += block
        if n>0:
            usb.usbControlMsg(handle,0x40,0xA2,addr,0x00,
            create_string_buffer(image[addr:addr+n],n),n,60000)
            stdout.write(".\n")
        print "Programming complete, starting verification"
        goodImage = True
        n = len(image)
        addr = 0
        while n > block:
            buffer = create_string_buffer('\000',block)
            usb.usbControlMsg(handle,0xC0,0xA2,addr,0x00,buffer,block,60000)
            for i in range(block):
                if image[addr+i] != buffer[i]:
                    print "Mismatch at %04x, wrote %02x, read %02x" % (addr+i,ord(image[addr+i]),ord(buffer[i]))
                    goodImage = False
            n -= block
            addr += block
        if n>0:
            buffer = create_string_buffer('\000',n)
            usb.usbControlMsg(handle,0xC0,0xA2,addr,0x00,buffer,n,60000)
            for i in range(n):
                if image[addr+i] != buffer[i]:
                    print "Mismatch at %04x, wrote %02x, read %02x" % (addr+i,ord(image[addr+i]),ord(buffer[i]))
                    goodImage = False
        # Finally write and verify the 0xC2
        addr = 0
        usb.usbControlMsg(handle,0x40,0xA2,addr,0x00,byref(c_ubyte(0xC2)),1,5000)
        check = c_ubyte(0x0)
        usb.usbControlMsg(handle,0xC0,0xA2,addr,0x00,byref(check),1,5000)
        if check.value != 0xC2: 
            print "Mismatch reading EEPROM type byte"
            goodImage = False
        if goodImage: print "Verification complete"
        else: print "Verification failed"
    finally:
        usb.usbReleaseInterface(handle,0)
        usb.usbClose(handle)
    print "Cycle power to start using EEPROM contents."
