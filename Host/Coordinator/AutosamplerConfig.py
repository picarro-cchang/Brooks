#@+leo-ver=4-thin
#@+node:stan.20080530002206.2:@thin AutosamplerConfig.py
import wx
import Host.Coordinator.AutosamplerParameterDialog as AutosamplerParameterDialog
from string import maketrans

transtab = maketrans('\x91\x9b\x9d','\xba\xb1\xb5')

class Choices(object):
    def __init__(self,limit,choices):
        self.limit = limit
        self.choices = choices
    def __str__(self):
        return "limit: %d\nchoices: %s" % (self.limit,self.choices)

class Lists(object):
    def __init__(self,fp):
        self.data = []
        if fp.readline().strip() != '[LISTS]':
            raise ValueError,"Must start with '[LISTS]'"
        i = 0
        for line in fp:
            if not line.strip():
                break
            line = line.translate(transtab)
            l = line.strip().split(";")
            if int(l[0]) != i:
                raise ValueError,"LISTS entry is out of sequence"
            i += 1
            self.data.append(Choices(int(l[1]),l[2:]))

class Objects(object):
    def __init__(self,fp):
        self.objects = {}
        if fp.readline().strip() != '[OBJECTS]':
            raise ValueError,"Must start with '[OBJECTS]'"
        for line in fp:
            if not line.strip():
                break
            line = line.translate(transtab)
            l = line.strip().split(";")
            if l[0] not in self.objects:
                self.objects[l[0]] = []
            self.objects[l[0]].append((l[1],l[2:]))
    def labelProperties(self,classes,lists):
        """Associate a parameter name with each parameter"""
        self.objectsByClass = {}
        for className in self.objects:
            classParams = classes.classes[className]
            objectDict = {}
            for oName,params in self.objects[className]:
                paramDict = {}
                for i,p in enumerate(params):
                    paramName = classParams[i][0]
                    if paramName[0] == "#":
                        paramName = paramName[1:]
                        listType = classParams[i][1][-1]
                        p = lists.data[int(listType)].choices[int(p)]
                    elif paramName[0] != "&":
                        units = classParams[i][1][-1]
                        if units not in classes.classes:
                            if units == 'E': units = ''
                            p = " ".join([p,units])
                        else:
                            p = (p,units)
                    paramDict[paramName] = p
                objectDict[oName] = paramDict
            self.objectsByClass[className] = objectDict
    def makeTreeDef(self):
        """Construct a list for passing to the tree drawing GUI"""
        self.treeList = []
        hyperLinks = []
        hyperTargets = {}
        for className in sorted(self.objectsByClass.keys()):
            objectsDict = self.objectsByClass[className]
            if objectsDict:
                objectList = []
                for o in sorted(objectsDict.keys()):
                    paramsDict = objectsDict[o]
                    if paramsDict:
                        paramsList = []
                        for p in sorted(paramsDict.keys()):
                            if isinstance(paramsDict[p],str):
                                paramsList.append(p+": "+paramsDict[p])
                            else:
                                item = paramsDict[p][0]
                                if item == "None":
                                    paramsList.append(p+": "+item)
                                else:
                                    link = [p+": "+item]
                                    hyperLinks.append((item,link))
                                    paramsList.append(link)
                        objectList.append([o,paramsList])
                        hyperTargets[o] = paramsList
                    else:
                        objectList.append(o)
                self.treeList.append([className,objectList])
            else:
                self.treeList.append(className)
        for h in hyperLinks:
            o = h[0]  # Recover object
            l = h[1]    # Recover link
            l.append(hyperTargets[o])

class Classes(object):
    def __init__(self,fp):
        self.classes = {}
        current = []
        if fp.readline().strip() != '[CLASSES]':
            raise ValueError,"Must start with '[CLASSES]'"
        for line in fp:
            if not line.strip():
                break
            line = line.translate(transtab)
            if line[0] == '!':
                current = []
                self.classes[line[1:].strip()] = current
            else:
                l = line.strip().split(";")
                current.append((l[0],l[1:]))

class Atoms(object):
    def __init__(self,fp):
        self.atoms = {}
        current = []
        if fp.readline().strip() != '[ATOMS]':
            raise ValueError,"Must start with '[ATOMS]'"
        for line in fp:
            if not line.strip():
                break
            line = line.translate(transtab)
            if line[0] == '!':
                current = []
                self.atoms[line[1:].strip()] = current
            else:
                l = line.strip().split(";")
                current.append((l[0],l[1:]))

    def setupChoices(self,objects,classes,lists):
        self.atomParamDict = {}
        for a in self.atoms:
            params = self.atoms[a]
            paramList = []
            for pname,pDescr in params:
                minVal = ""
                maxVal = ""
                defVal = ""
                units = ""
                format = []
                optional = (pname[0] == "?")
                if optional:
                    pname = pname[1:]
                if pname[0] == "#":
                    pname = pname[1:]
                    listType = int(pDescr[-1])
                    format = lists.data[int(listType)].choices
                    type = 'choices'
                else:
                    classChoice = True
                    for p in pDescr:
                        if p not in classes.classes:
                            classChoice = False
                        if p in objects.objectsByClass:
                            format.extend(objects.objectsByClass[p].keys())
                    if classChoice:
                        type = 'choices'
                    else:
                        type = 'int'
                        format = "%d"
                        minVal = pDescr[0]
                        maxVal = pDescr[1]
                        defVal = pDescr[2]
                        incr = pDescr[3]
                        units = pDescr[4]
                        if units == 'E': units = ''
                label = pname
                paramList.append([type,label,format,units,optional,minVal,maxVal,defVal])
            self.atomParamDict[a] = paramList

def getAutosamplerConfig():
    objects = Objects(file('objects.txt','r'))
    classes = Classes(file('classes.txt','r'))
    lists = Lists(file('lists.txt','r'))
    atoms = Atoms(file('atoms.txt','r'))
    objects.labelProperties(classes,lists)
    objects.makeTreeDef()
    atoms.setupChoices(objects,classes,lists)
    return objects,classes,lists,atoms

if __name__ == "__main__":
    objects,classes,lists,atoms = getAutosamplerConfig()
    # app = wx.PySimpleApp(0)
    # wx.InitAllImageHandlers()

    # parameter_forms = []
    # for a in atoms.atomParamDict:
        # __p = atoms.atomParamDict[a]
        # parameter_forms.append((a,__p))

    # frame_1 = AutosamplerParameterDialog.ParameterDialogBase(None, -1, descr=parameter_forms[35])
    # #frame_1.ReadFromDas()

    # app.SetTopWindow(frame_1)
    # frame_1.Show()
    # app.MainLoop()
#@-node:stan.20080530002206.2:@thin AutosamplerConfig.py
#@-leo