from sys import argv
from time import strftime
from configobj import ConfigObj

def splitIntoLines(text,lineLen,delim=" "):
    lines = []
    while True:
        if len(text) <= lineLen:
            lines.append(text)
            break
        else:
            delimPos = text.rfind(delim,0,lineLen)
            if delimPos >= 0:
                lines.append(text[:delimPos+1])
                text = text[delimPos+1:]
            else:
                delimPos = text.find(delim)
                if delimPos >= 0:
                    lines.append(text[:delimPos+1])
                    text = text[delimPos+1:]
                else:
                    lines.append(text)
                    break
    return lines

header = """#!/usr/bin/python
#
# FILE:
#   %s
#
# DESCRIPTION:
#
# SEE ALSO:
#
# HISTORY:
#   %s  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#"""

benchUtils = """    PERIOD = 20  # 50MHz clock
    @always(delay(PERIOD//2))
    def clockGen():
        clk.next = not clk

    def writeFPGA(regNum,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readFPGA(regNum,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = (1<<(EMIF_ADDR_WIDTH-1)) + regNum
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def writeRdmem(wordAddr,data):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 1
        dsp_data_out.next = data
        yield clk.posedge
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.negedge

    def readRdmem(wordAddr,result):
        yield clk.negedge
        yield clk.posedge
        dsp_addr.next = wordAddr
        dsp_wr.next = 0
        yield clk.posedge
        yield clk.posedge
        result.next = dsp_data_in
        yield clk.negedge

    def assertReset():
        yield clk.negedge
        yield clk.posedge
        reset.next = 1
        dsp_wr.next = 0
        yield clk.posedge
        reset.next = 0
        yield clk.negedge
"""

if __name__ == "__main__":
    try:
        blockName = argv[1]
    except:
        blockName = raw_input("Block name (no extension)? ")
    config = ConfigObj(file(blockName+".ini","r"))
    op = file(blockName+"_template.py","w")
    tp = file("test_"+blockName+"_template.py","w")
    xp = file(blockName+"_template.xml","w")
    try:
        print>>op, header%(blockName+".py",strftime("%d-%b-%Y"))
        print>>tp, header%("test_"+blockName+".py",strftime("%d-%b-%Y"))
        importList = ["from myhdl import *","from Host.autogen import interface"]
        for option in config.get("IMPORTS",[]):
            s = config["IMPORTS"][option]
            importList.append(s)
        impString = "from Host.autogen.interface import"
        splitLen = 72-len(impString)
        regs = [" %s_%s" % (blockName.upper(),reg.upper()) for reg in config["REGISTERS"]]
        lines = splitIntoLines(",".join(regs),splitLen,",")

        importList.append("%s EMIF_ADDR_WIDTH, EMIF_DATA_WIDTH" % impString)
        importList.append("%s FPGA_REG_WIDTH, FPGA_REG_MASK, FPGA_%s" % (impString,blockName.upper()))
        importList.append("")
        for line in lines:
            importList.append("%s%s" % (impString,line.rstrip(",")))

        #for reg in config["REGISTERS"]:
        #    importList.append("from intf import %s_%s" % (blockName.upper(),reg.upper()))
        importList.append("")
        for section in config:
            if section not in ["IMPORTS","PORTS","REGISTERS"]:
                for field in config[section]:
                    name = "%s_%s_%s" % (blockName.upper(),section.upper(),field.upper())
                    importList.append("%s %s_B, %s_W" % (impString,name,name))
        importList.append("")
        print>>op, "\n".join(importList)
        print>>tp, "\n".join(importList)
        print>>tp, "from MyHDL.Common.%s import %s" % (blockName,blockName)

        print>>op, "\nLOW, HIGH = bool(0), bool(1)"
        print>>tp, "\nLOW, HIGH = bool(0), bool(1)"

        portSignalList = []
        for port in config["PORTS"]:
            value = config["PORTS"][port].strip()
            if value == "1":
                portSignalList.append("%s = Signal(LOW)" % (port,))
            elif not value.startswith("$"):
                portSignalList.append("%s = Signal(intbv(0)[%s:])" % (port,value))
            else:
                portSignalList.append("%s = FPGA_%s" % (port,blockName.upper()))

        print>>tp, "\n".join(portSignalList)

        decl = "def %s(" % blockName
        leadSpace = len(decl)* " "
        splitLen = 72-len(decl)
        ports = config["PORTS"].keys()
        lines = splitIntoLines(",".join(ports),splitLen,",")
        if len(lines) >= 1:
            for i,line in enumerate(lines):
                print>>op, "%s%s%s" % (decl if i==0 else leadSpace,lines[i],"):" if i==len(lines)-1 else "")
        else:
            print>>op, "%s%s" % (decl,"):")
        # Write out comments for describing block
        print>>op,'    """'
        print>>op,"    Parameters:"
        for p in ports:
            print>>op,"    %s" % p
        print>>op,"\n    Registers:"
        for r in regs:
            print>>op,"   %s" % r
        for section in config:
            if section not in ["IMPORTS","PORTS","REGISTERS"]:
                print>>op,"\n    Fields in %s_%s:" % (blockName.upper(),section.upper())
                for field in config[section]:
                    name = "%s_%s_%s" % (blockName.upper(),section.upper(),field.upper())
                    print>>op,"    %s" % (name,)
        print>>op,'    """'
        for r in regs:
            print>>op,"   %s_addr = map_base +%s" % (r.lower(),r.upper())

        for reg in config["REGISTERS"]:
            regSize = config["REGISTERS"][reg][0]
            print>>op,"    %s = Signal(intbv(0)[%s:])" % (reg,regSize)

        print>>op,"    @instance"
        print>>op,"    def logic():"
        print>>op,"        while True:"
        print>>op,"            yield clk.posedge, reset.posedge"
        print>>op,"            if reset:"
        for reg in config["REGISTERS"]:
            print>>op,"                %s.next = 0" % (reg,)
        print>>op,"            else:"
        print>>op,"                if dsp_addr[EMIF_ADDR_WIDTH-1] == FPGA_REG_MASK:"
        print>>op,"                    if False: pass"
        for reg in config["REGISTERS"]:
            regSize,access = config["REGISTERS"][reg]
            print>>op,"                    elif dsp_addr[EMIF_ADDR_WIDTH-1:] == %s_%s_addr: # %s" % (blockName.lower(),reg.lower(),access)
            if "w" in access:
                print>>op,"                        if dsp_wr: %s.next = dsp_data_out" % (reg,)
            if "r" in access:
                print>>op,"                        dsp_data_in.next = %s" % (reg,)
        print>>op,"                    else:"
        print>>op,"                        dsp_data_in.next = 0"
        print>>op,"                else:"
        print>>op,"                    dsp_data_in.next = 0"

        print>>op,"    return instances()"

        print>>op
        print>>op,'if __name__ == "__main__":'
        print>>op,"    " + ("\n    ".join(portSignalList))
        print>>op
        leadStr = "    toVHDL(%s," % blockName
        leadSpace = len(leadStr)*" "
        ports = config["PORTS"].keys()
        splitLen = 72-len(leadStr)
        lines = splitIntoLines(",".join([" %s=%s" % (p,p) for p in ports]),splitLen,",")
        if len(lines) >= 1:
            for i,line in enumerate(lines):
                print>>op, "%s%s%s" % (leadStr if i==0 else leadSpace,lines[i],")" if i==len(lines)-1 else "")
        else:
            print>>op, "%s%s" % (decl,")")

        print>>tp
        print>>tp, "def bench():"
        print>>tp, benchUtils
        print>>tp, "    # N.B. If there are several blocks configured, ensure that dsp_data_in is "
        print>>tp, "    #  derived as the OR of the data buses from the individual blocks."
        leadStr = "    %s = %s(" % (blockName.lower(),blockName)
        leadSpace = len(leadStr)*" "
        ports = config["PORTS"].keys()
        splitLen = 72-len(leadStr)
        lines = splitIntoLines(",".join([" %s=%s" % (p,p) for p in ports]),splitLen,",")
        if len(lines) >= 1:
            for i,line in enumerate(lines):
                print>>tp, "%s%s%s" % (leadStr if i==0 else leadSpace,lines[i]," )" if i==len(lines)-1 else "")
        else:
            print>>tp, "%s%s" % (decl," )")

        print>>tp,"    @instance"
        print>>tp,"    def stimulus():"
        print>>tp,"        yield delay(10*PERIOD)"
        print>>tp,"        raise StopSimulation"

        print>>tp,"    return instances()"
        print>>tp
        print>>tp,"def test_%s():" % blockName
        print>>tp,"    s = Simulation(traceSignals(bench))"
        print>>tp,"    s.run(quiet=1)"
        print>>tp
        print>>tp,'if __name__ == "__main__":'
        print>>tp,"    test_%s()" % blockName

        print>>xp, '<fpga_block ident="%s" description="">' % blockName.upper()
        for reg in config["REGISTERS"]:
            if reg in config:
                print>>xp, '    <reg ident="%s" description="">' % reg.upper()
                lsb = 0
                for field in config[reg]:
                    width = int(config[reg][field])
                    print>>xp, '        <bitfield ident="%s" description="" lsb="%d" width="%d" />' % (field.upper(),lsb,width)
                    lsb += width
                print>>xp, '    </reg>'
            else:
                print>>xp, '    <reg ident="%s" description="" />' % reg.upper()
        print>>xp, '</fpga_block>'
    finally:
        op.close()
        tp.close()
