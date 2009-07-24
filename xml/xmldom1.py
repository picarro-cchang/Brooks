
from xml.dom import minidom
import ctypes
import logging

logging.basicConfig(level = logging.WARNING)

# Store defined values, unions and structures in definitions
definitions = {}
definitions.update(ctypes.__dict__)

def printFp(fp,*a):
    if fp != None:
        print>>fp, "".join(a)

def closeFp(fp):
    if fp != None:
        fp.close()

typeToCtypeLookUp = {"long long":"c_longlong",
                     "uint32":"c_uint","int32":"c_int",
                     "uint16":"c_ushort","int16":"c_short",
                     "uint8":"c_ubyte","int8":"c_byte",
                     "float":"c_float","bool":"c_int"}

def typeToCtype(t):
    if t in typeToCtypeLookUp:
        return typeToCtypeLookUp[t]
    elif t == None:
        return None
    elif t[-1] == "]":
        s = t.find("[")
        return "(%s)*%s" % (typeToCtype(t[:s]),t[s+1:-1])
    else:
        return t

# The following tags are used to identify the automatically generated output files
outTags = []
outFps  = {}
outMods = {}

xmldoc = minidom.parse("Interface.xml")
# Render as XML
# wb.xmlout.b = xmldoc.toxml()
docEl = xmldoc.documentElement
#
assert(docEl.nodeName == 'Das_Interface')
files = docEl.getElementsByTagName('files')
for f in files:
    # The ident attributes of file elements are tags for the output files
    # The datum of the file element is the output file name
    for child in f.getElementsByTagName('file'):
        tag = child.attributes['ident'].value
        outTags.append(tag)
        outFps[tag] = file(child.firstChild.data,"w")
        # Get the boiler plate module associated with the output file, if it
        #  exists. These contain headers, trailers etc.
        try: outMods[tag] = __import__(tag + "bp")
        except: pass
# Write out file headers
for tag in outTags:
    if tag in outMods and "header" in outMods[tag].__dict__:
        print>>outFps[tag],outMods[tag].header

# Convenience variables for accessing file objects
usbPyFp = outFps.get("usbPy",None)
usbHFp = outFps.get("usbH",None)
usbA51Fp = outFps.get("usbA51",None)
intHFp = outFps.get("intH",None)
intPyFp = outFps.get("intPy",None)
dspCFp = outFps.get("dspC",None)
dspHFp = outFps.get("dspH",None)

printFp(usbPyFp,"IOC = 'Cypress port C'\nIOE = 'Cypress port E'")

for interface_version in docEl.getElementsByTagName('interface_version'):
    value = interface_version.firstChild.data
    printFp(intPyFp,'\n# Interface Version')
    printFp(intPyFp,'interface_version = %s\n' % value)
    printFp(intHFp,'\n/* Interface Version */')
    printFp(intHFp,'#define interface_version (%s)\n' % value)

usbConstants = docEl.getElementsByTagName('usb_constants')
for usbConstant in usbConstants:
    for child in usbConstant.getElementsByTagName('constant'):
        ident = child.attributes['ident'].value
        value = child.firstChild.data
        printFp(usbHFp, "#define %s (%s)" % (ident,value))
        printFp(usbPyFp, "%s = %s" % (ident,value))
        printFp(usbA51Fp, "%s EQU %s" % (ident,value))
        if ident in definitions:
            raise ValueError,"Redefinition of %s: Old value %s, New value %s" % (ident,definitions[ident],value)
        definitions[ident] = value

statusIdentList = []
statusMessageList = []
statusLists = docEl.getElementsByTagName('status_list')
for statusList in statusLists:
    for status in statusList.getElementsByTagName('status'):
        statusIdentList.append(status.attributes['ident'].value)
        statusMessageList.append(status.firstChild.data)

printFp(intPyFp,"error_messages = []")
for index,ident in enumerate(statusIdentList):
    printFp(intPyFp,'%s = %d' % (ident,-index))
    printFp(intHFp, "#define %s (%s)" % (ident,-index))
    printFp(intPyFp,'error_messages.append("%s")' % (statusMessageList[index]))
    if ident in definitions:
        raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (ident,definitions[ident],-index)
    definitions[ident] = -index

printFp(intPyFp,'\n# Constant definitions')
printFp(intHFp,'\n/* Constant definitions */')
constantLists = docEl.getElementsByTagName('constant_list')
for constantList in constantLists:
    for constant in constantList.getElementsByTagName('constant'):
        ident = constant.attributes['ident'].value
        value = constant.firstChild.data
        try:
            description = constant.attributes['description'].value
            printFp(intPyFp,'# %s' % (description))
            printFp(intPyFp,'%s = %s' % (ident,value))
            printFp(intHFp,'// %s' % (description))
            printFp(intHFp, "#define %s (%s)" % (ident,value))
        except:
            printFp(intPyFp,'%s = %s' % (ident,value))
            printFp(intHFp, "#define %s (%s)" % (ident,value))
        if ident in definitions:
            raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (ident,definitions[ident],value)
        definitions[ident] = value

unionLists = docEl.getElementsByTagName('union_list')
for unionList in unionLists:
    for union in unionList.getElementsByTagName('union'):
        unionName = union.attributes['type'].value
        declC = []
        declPy = []
        fieldList = []
        for field in union.getElementsByTagName('field'):
            typeName = field.attributes['type'].value
            ident = field.attributes['ident'].value
            declC.append("    %s %s;" % (typeName,ident))
            fieldList.append((ident,definitions[typeToCtype(typeName)]))
            declPy.append('    ("%s",%s)' % (ident,typeToCtype(typeName)))
        printFp(intHFp, "\ntypedef union {\n%s\n} %s;" % ("\n".join(declC),unionName,))
        printFp(intPyFp, "\nclass %s(Union):\n    _fields_ = [\n%s\n    ]" % (unionName,",\n".join(declPy)))
        definitions[unionName] = type(str(unionName),(ctypes.Union,),
                                        dict(_fields_=fieldList))

structLists = docEl.getElementsByTagName('struct_list')
for structList in structLists:
    for struct in structList.getElementsByTagName('struct'):
        structName = struct.attributes['type'].value
        declC = []
        declPy = []
        fieldList = []
        for field in struct.getElementsByTagName('field'):
            typeName = field.attributes['type'].value
            ident = field.attributes['ident'].value
            try:
                size = int(field.attributes['size'].value)
                declC.append("    %s %s[%s];" % (typeName,ident,size))
                fieldList.append((ident,definitions[typeToCtype(typeName)]*size))
                declPy.append('    ("%s",%s*%s)' % (ident,typeToCtype(typeName),size))
            except:
                size = None
                declC.append("    %s %s;" % (typeName,ident))
                fieldList.append((ident,definitions[typeToCtype(typeName)]))
                declPy.append('    ("%s",%s)' % (ident,typeToCtype(typeName)))

        printFp(intHFp, "\ntypedef struct {\n%s\n} %s;" % ("\n".join(declC),structName,))
        printFp(intPyFp, "\nclass %s(Structure):\n    _fields_ = [\n%s\n    ]" % (structName,",\n".join(declPy)))
        definitions[structName] = type(str(structName),(ctypes.Structure,),
                                        dict(_fields_=fieldList))

enumLists = docEl.getElementsByTagName('enum_list')
enumLookup = {}
for enumList in enumLists:
    for enum in enumList.getElementsByTagName('enum'):
        enumType = enum.attributes['type'].value
        declC = ["typedef enum {"]
        decl1Py = ["# Enumerated definitions for %s" % enumType]
        decl1Py.append("%s = c_uint" % enumType)
        decl2Py = ["# Dictionary for enumerated constants in %s" % enumType]
        dictName = "%sDict" % enumType
        decl2Py.append("%s = {}" % dictName)
        enumLookup[enumType] = []
        value = -1
        for i,v in enumerate(enum.getElementsByTagName('enum_value')):
            if i>0: declC.append("    %s = %s, // %s" % (ident,value,caption))
            ident = v.attributes["ident"].value
            try: value = int(v.attributes["value"].value)
            except: value += 1
            try: caption = v.attributes["caption"].value
            except: caption = ""
            enumLookup[enumType].append((ident,value,caption))
            decl1Py.append("%s = %s # %s" % (ident,value,caption))
            decl2Py.append("%s[%s] = '%s' # %s" % (dictName,value,ident,caption))
            if ident in definitions:
                raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (ident,definitions[ident],value)
            definitions[ident] = value
        declC.append("    %s = %s // %s" % (ident,value,caption))
        declC.append("} %s;" % (enumType,))
        printFp(intHFp, "\n%s" % ("\n".join(declC),))
        printFp(intPyFp, "\n%s" % ("\n".join(decl1Py),))
        printFp(intPyFp, "\n%s" % ("\n".join(decl2Py),))

bitsLists = docEl.getElementsByTagName('bits_list')
for bitsList in bitsLists:
    for bits in bitsList.getElementsByTagName('bits'):
        bitsName = bits.attributes['ident'].value
        declC = ["/* Definitions for %s */" % bitsName]
        declPy = ["# Definitions for %s" % bitsName]
        for mask in bits.getElementsByTagName('mask'):
            maskName = mask.attributes['ident'].value
            value = mask.firstChild.data
            declC.append("#define %s (%s)" % (maskName,value))
            declPy.append("%s = %s" % (maskName,value))
            if maskName in definitions:
                raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (maskName,definitions[maskName],value)
            definitions[maskName] = value

        for shift in bits.getElementsByTagName('shift'):
            shiftName = shift.attributes['ident'].value
            value = shift.firstChild.data
            declC.append("#define %s (%s)" % (shiftName,value))
            declPy.append("%s = %s" % (shiftName,value))
            if shiftName in definitions:
                raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (shiftName,definitions[shiftName],value)
            definitions[shiftName] = value

        printFp(intHFp, "\n%s" % ("\n".join(declC),))
        printFp(intPyFp, "\n%s" % ("\n".join(declPy),))


registerLists = docEl.getElementsByTagName('register_list')
registerNames = []
registerMinVer = []
registerAccess = []
registerDisplay = {}
types = []
initialValues = []
registerPersistence = []

for registerList in registerLists:
    for i,register in enumerate(registerList.getElementsByTagName('register')):
        registerName = register.attributes['ident'].value
        registerNames.append(registerName)
        registerMinVer.append(register.attributes['minver'].value)
        registerAccess.append(register.attributes['access'].value)
        types.append(register.attributes['type'].value)
        initialValue = None
        persistence = 0
        for initialElement in register.getElementsByTagName('initial'):
            initialValue = initialElement.firstChild.data
        for saveElement in register.getElementsByTagName('save'):
            persistence = 1
        initialValues.append(initialValue)
        registerPersistence.append(persistence)
        for display in register.getElementsByTagName('display'):
            try:
                format = display.attributes['format'].value
            except:
                format = ""
            try:
                units = display.attributes['units'].value
            except:
                units = ""
            label = display.firstChild.data
            registerDisplay[i] = (label,units,format)

printFp(intHFp,  "\n/* Register definitions */")
printFp(intHFp, "#define INTERFACE_NUMBER_OF_REGISTERS (%d)\n" % (len(registerNames),))
printFp(intPyFp, "\n# Register definitions" )
printFp(intPyFp, "INTERFACE_NUMBER_OF_REGISTERS = %d\n" % (len(registerNames),))

for i,registerName in enumerate(registerNames):
    printFp(intHFp, "#define %s (%d)" % (registerName,i))
    printFp(intPyFp, "%s = %d" % (registerName,i))
    if registerName in definitions:
        raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (registerName,definitions[registerName],i)
    definitions[registerName] = i

printFp(intPyFp, "\n# Dictionary for accessing registers by name and list of register information" )
printFp(intPyFp, "registerByName = {}\nregisterInfo = []" )

printFp(dspCFp,'extern int writeRegister(unsigned int regNum,DataType data);')
printFp(dspCFp,'void initRegisters() \n{\n    DataType d;')
printFp(dspHFp,'void initRegisters(void);')

for i,registerName in enumerate(registerNames):
    printFp(intPyFp, 'registerByName["%s"] = %s' % (registerName,registerName))
    printFp(intPyFp, 'registerInfo.append(RegInfo("%s",%s,%d,%s,"%s"))' % \
     (registerName,typeToCtype(types[i]),registerPersistence[i],registerMinVer[i],registerAccess[i]))
    iv = initialValues[i]
    if iv != None:
        if types[i] == "float":
            printFp(dspCFp,'    d.asFloat = %s;\n    writeRegister(%s,d);' % (iv,registerName))
        elif types[i] == "uint32":
            printFp(dspCFp,'    d.asUint = %s;\n    writeRegister(%s,d);' % (iv,registerName))
        elif types[i] == "int32":
            printFp(dspCFp,'    d.asInt = %s;\n    writeRegister(%s,d);' % (iv,registerName))
        else:
            # Unknown types are assumed to be enumerations
            printFp(dspCFp,'    d.asUint = %s;\n    writeRegister(%s,d);' % (iv,registerName))
printFp(dspCFp,'}')

fpgaBlockLists = docEl.getElementsByTagName('fpga_block_list')
fpgaRegisterDescriptor = {}
numRegistersByBlock = {}
fpgaSaveRegByBlock = {}

declC = ["/* FPGA block definitions */"]
declPy = ["# FPGA block definitions"]
for fpgaBlockList in fpgaBlockLists:
    for fpgaBlock in fpgaBlockList.getElementsByTagName('fpga_block'):
        blockName = fpgaBlock.attributes['ident'].value
        fpgaRegisterDescriptor[blockName] = {}
        try:
            blockDescription = fpgaBlock.attributes['description'].value
        except:
            blockDescription = ""
        declC.append("\n/* Block %s %s */" % (blockName,blockDescription))
        declPy.append("\n# Block %s %s" % (blockName,blockDescription))
        numRegisters = 0
        for reg in fpgaBlock.getElementsByTagName('reg'):
            regName = reg.attributes['ident'].value
            try:
                regDescription = reg.attributes['description'].value
            except:
                regDescription = ""

            try:
                regType = reg.attributes['type'].value
            except:
                regType = ""
            try:
                regAccess = reg.attributes['access'].value
            except:
                regAccess = u"rw"

            label, units, format = u"", u"", u""
            for display in reg.getElementsByTagName('display'):
                try:
                    format = display.attributes['format'].value
                except:
                    pass
                try:
                    units= display.attributes['units'].value
                except:
                    pass
                label = display.firstChild.data
            for save in reg.getElementsByTagName('save'):
                if blockName not in fpgaSaveRegByBlock:
                    fpgaSaveRegByBlock[blockName] = []
                fpgaSaveRegByBlock[blockName].append(regName)
                
            name = "_".join([blockName,regName])
            value = numRegisters
            descr = regDescription
            declC.append("#define %s (%d) // %s" % (name,value,descr))
            declPy.append("%s = %d # %s" % (name,value,descr))
            if name in definitions:
                raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (name,definitions[name],value)
            definitions[name] = value
            nBitfields = 0
            bitfields = []
            for bitfield in reg.getElementsByTagName('bitfield'):
                bitfieldName = bitfield.attributes['ident'].value
                try:
                    bitfieldDescription = bitfield.attributes['description'].value
                except:
                    bitfieldDescription = ""
                bitfieldLsb = int(bitfield.attributes['lsb'].value)
                try:
                    bitfieldWidth = int(bitfield.attributes['width'].value)
                except:
                    bitfieldWidth = 1
                name = "_".join([blockName,regName,bitfieldName,"B"])
                value = bitfieldLsb
                descr = bitfieldDescription + " bit position"
                declC.append("#define %s (%d) // %s" % (name,value,descr))
                declPy.append("%s = %d # %s" % (name,value,descr))
                if name in definitions:
                    raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (name,definitions[name],value)
                definitions[name] = value
                name = "_".join([blockName,regName,bitfieldName,"W"])
                value = bitfieldWidth
                descr = bitfieldDescription + " bit width"
                declC.append("#define %s (%d) // %s" % (name,value,descr))
                declPy.append("%s = %d # %s" % (name,value,descr))
                if name in definitions:
                    raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (name,definitions[name],value)
                definitions[name] = value
                nBitfields += 1
                # Generate the field_list from the fielddef elements
                field_list = []
                for field in bitfield.getElementsByTagName('fielddef'):
                    value = int(field.attributes['value'].value)<<bitfieldLsb
                    descr = field.firstChild.data
                    field_list.append((value,descr))
                mask = ((1<<bitfieldWidth)-1)<<bitfieldLsb
                bitfields.append((mask,bitfieldDescription,field_list))
            if nBitfields > 0:
                declC.append("")
                declPy.append("")
            numRegisters += 1
            fpgaRegisterDescriptor[blockName][regName] = (regType,regAccess,format,units,label,bitfields)
        numRegistersByBlock[blockName] = numRegisters
    printFp(intHFp, "\n%s" % ("\n".join(declC),))
    printFp(intPyFp, "\n%s" % ("\n".join(declPy),))
    
fpgaMapLists = docEl.getElementsByTagName('fpga_map_list')
fpgaMapNames = []
fpgaMapIndexByName = {}
fpgaMapDescriptionsByName = {}
fpgaBlockByMapName = {}
fpgaSaveRegList = []

for fpgaMapList in fpgaMapLists:
    index = -1
    for fpgaMap in fpgaMapList.getElementsByTagName('fpga_map'):
        name = fpgaMap.attributes['ident'].value
        fpgaMapNames.append(name)
        try: index = int(fpgaMap.attributes['index'].value)
        except: index += 1
        try:
            blockName = fpgaMap.attributes['block'].value
        except:
            blockName = ""

        if blockName:
                num = int(numRegistersByBlock[blockName])
        else:
            num = 1

        fpgaBlockByMapName[name] = blockName
        if blockName in fpgaSaveRegByBlock:
            fpgaSaveRegList.append((name,[blockName + "_" + regName for regName in fpgaSaveRegByBlock[blockName]]))
        
        for descriptionElement in fpgaMap.getElementsByTagName('description'):
            fpgaMapDescriptionsByName[name] = descriptionElement.firstChild.data
        fpgaMapIndexByName[name] = index
        index += num-1
    declC = ["/* FPGA map indices */\n"]
    declPy = ["# FPGA map indices"]
    for name in fpgaMapNames:
        index = fpgaMapIndexByName[name]
        descr = fpgaMapDescriptionsByName[name]
        declC.append("#define %s (%d) // %s" % (name,index,descr))
        declPy.append("%s = %d # %s" % (name,index,descr))
        if name in definitions:
            raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (name,definitions[name],index)
        definitions[name] = index

    printFp(intHFp, "\n%s" % ("\n".join(declC),))
    printFp(intPyFp, "\n%s" % ("\n".join(declPy),))

# Figure out which FPGA registers are to be saved
declPy = ["# FPGA registers to load and save\n"]
declPy = ["persistent_fpga_registers = []"]
for f in fpgaSaveRegList:
    declPy.append("persistent_fpga_registers.append(%r)" % (f,))
printFp(intPyFp, "\n%s" % ("\n".join(declPy),))
    
# Process environment definitions, which are associated with a specific
#  structure and an index. These are used to store the states of actions
#  for more complex activities such as controllers, etc.


declC = ["/* Environment addresses */\n"]
declPy = ["# Environment addresses"]
envAddress = 0
envNameList = []
envType = {}
enironmentLists = docEl.getElementsByTagName('environment_list')
for environmentList in enironmentLists:
    for env in environmentList.getElementsByTagName('env'):
        envName = env.attributes['ident'].value
        envNameList.append(envName)
        envType[envName] = definitions[env.attributes['type'].value]
        declC.append("#define %s (%d)" % (envName,envAddress))
        declPy.append("%s = %d" % (envName,envAddress))
        envAddress += (ctypes.sizeof(envType[envName])+3)//4
    printFp(intHFp, "\n%s" % ("\n".join(declC),))
    printFp(intPyFp, "\n%s" % ("\n".join(declPy),))

printFp(intPyFp, "\n# Dictionary for accessing environments by name" )
printFp(intPyFp, "envByName = {}" )

for envName in envNameList:
    printFp(intPyFp, "envByName['%s'] = (%s,%s)" % \
        (envName,envName,envType[envName].__name__))

printFp(dspCFp,"""
int doAction(unsigned int command,unsigned int numInt,void *params,void *env)
{
    switch (command) {""")
printFp(dspHFp,'int doAction(unsigned int command,unsigned int numInt,void *params,void *env);')

actionLists = docEl.getElementsByTagName('action_list')
actionNames = []
functionNames = []

for actionList in actionLists:
    for action in actionList.getElementsByTagName('action'):
        actionName = action.attributes['ident'].value
        actionNames.append(actionName)
        function = action.firstChild.data
        printFp(dspHFp,"int %s(unsigned int numInt,void *params,void *env);" % (function,));
        printFp(dspCFp,"        case %s:\n            return %s(numInt,params,env);" % (actionName,function))
printFp(dspCFp,"""        default:
            return ERROR_BAD_COMMAND;
    }
}
""")

printFp(intHFp,  "\n/* Action codes */")
printFp(intPyFp, "\n# Action codes" )
for i,a in enumerate(actionNames):
    printFp(intHFp,  "#define %s (%d)" % (a,i+1))
    printFp(intPyFp, "%s = %d" % (a,i+1))
    if a in definitions:
        raise ValueError, "Redefinition of %s: Old value %s, New value %s" % (a,definitions[a],i+1)
    definitions[a] = i+1

# Process the parameter pages XML file which defines the appearance of
#  parameters on the controller GUI

xmldoc = minidom.parse("ParameterPages.xml")
docEl = xmldoc.documentElement
#
assert(docEl.nodeName == 'Controller_gui')

printFp(intPyFp, """

# Parameter form definitions

parameter_forms = []""")

paramTypes = dict(int32='int32',uint32='uint32',int16='int16',uint16='uint16',float='float')
for guiPages in docEl.getElementsByTagName('gui_pages'):
    for guiPage in guiPages.getElementsByTagName('gui_page'):
        for node in guiPage.childNodes:
            if node.localName == 'title':
                titleStr = node.firstChild.data
                printFp(intPyFp, "\n# Form: %s\n\n__p = []\n" % titleStr)
            elif node.localName == 'fpga_register':
                offset = node.attributes['offset'].value
                block = fpgaBlockByMapName[offset]
                regName = node.firstChild.data
                t,access,format,units,label,bitfields = fpgaRegisterDescriptor[block][regName]
                if t in paramTypes:
                    printFp(intPyFp, "__p.append(('fpga','%s',%s+%s_%s,'%s','%s','%s',%d,%d))" %
                        (paramTypes[t],
                         offset, block, regName,
                         label,units,format,
                         'r' in access,
                         'w' in access,
                         )
                    )
                elif t == 'mask':
                    printFp(intPyFp, "__p.append(('fpga','mask',%s+%s_%s,%r,None,None,%d,%d))" %
                        (offset, block, regName,
                         bitfields,
                         'r' in access,
                         'w' in access,
                         )
                    )
                
            elif node.localName == 'register':
                registerStr = node.firstChild.data
                reg_index = definitions[registerStr]
                label,units,format = registerDisplay[reg_index]
                t = types[reg_index]
                if t in paramTypes:
                    printFp(intPyFp, "__p.append(('dsp','%s',%s,'%s','%s','%s',%d,%d))" %
                        (paramTypes[t],
                         registerNames[reg_index],
                         label,units,format,
                         'r' in registerAccess[reg_index],
                         'w' in registerAccess[reg_index],
                         )
                    )
                else:
                    format = "["
                    for ident,value,caption in enumLookup[t]:
                        format += '(%s,"%s"),' % (ident,caption)
                    format += "]"
                    printFp(intPyFp, "__p.append(('dsp','%s',%s,'%s','%s',%s,%d,%d))" %
                        ("choices",
                         registerNames[reg_index],
                         label,units,format,
                         'r' in registerAccess[reg_index],
                         'w' in registerAccess[reg_index],
                         )
                    )

        printFp(intPyFp,"parameter_forms.append(('%s',__p))" % titleStr)

# Write out file trailers and close files
for tag in outTags:
    if tag in outMods and "trailer" in outMods[tag].__dict__:
        print>>outFps[tag],outMods[tag].trailer
    outFps[tag].close()
