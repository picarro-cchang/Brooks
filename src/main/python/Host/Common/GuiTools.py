import wx
import string
import re

def normalizeBoolean(s):
    s = s.lower()
    if s in ("1","yes","true","on"): return True
    if s in ("0","no","false","off"): return False
    raise ValueError("Invalid boolean value: %s" % (s,))

def setItemFont(obj,fontTuple):
    font,fg,bg = fontTuple
    obj.SetFont(font)
    obj.SetForegroundColour(fg)
    obj.SetBackgroundColour(bg)

def getInnerStr(str):
    """
    This function is used to get around the problem that ConfigObj can't read '#' in
    any value assignment. To assign a HTML color code we have to use quotes to enclose
    the color value like '#85B24A'. When ConfigObj parses configuration file it returns
    "'#85B24A'" (when list_values option is False), and we need to get the inner sring.
    This is not needed if list_values optin is True in ConfigObj. But to be consistent
    we always set list_values as False and use this function as special case.
    """
    if ("'" in str) or ('"' in str):
        try:
            innerStr = eval(str)
            if type(innerStr) == type(''):
                return innerStr
        except:
            pass
    return str

class DataXferValidator(wx.PyValidator):
    def __init__(self,data,key,validator):
        wx.PyValidator.__init__(self)
        self.data = data
        self.key = key
        self.validator = validator

    def Clone(self):
        return DataXferValidator(self.data,self.key,self.validator)

    def Validate(self,win):
        ctrl = self.GetWindow()
        if isinstance(ctrl,wx.TextCtrl):
            text = ctrl.GetValue()
            if len(text)==0:
                wx.MessageBox("This field should not be empty","Error")
                ctrl.SetBackgroundColour("pink")
                ctrl.SetFocus()
                ctrl.Refresh()
                return False
        if self.validator is not None:
            return self.validator(ctrl,win)
        else:
            return True

    def TransferToWindow(self):
        ctrl = self.GetWindow()
        if isinstance(ctrl,wx.StaticText):
            ctrl.SetLabel(self.data.get(self.key,""))
        else:
            ctrl.SetValue(self.data.get(self.key,""))
        return True

    def TransferFromWindow(self):
        ctrl = self.GetWindow()
        if not isinstance(ctrl,wx.StaticText):
            self.data[self.key] = ctrl.GetValue()
        return True

class ColorDatabase(object):
    # The color database allows the user to give names to colors. A named color may be use to define
    #  another color, up to the maximum depth specified by maxIter. It is implemented by looking up color
    #  names is a dictionary (self.dbase) and recursively looking up the result until it is not found.
    #  The unknown key is assumed to be a hexadecimal color specification (as a string of the
    #  form "#RRGGBB") or a string describing one of the standard wxPython colors.
    maxIter = 10
    def __init__(self,config,secname):
        self.dbase = {}
        self.config = config
        self.secname = secname
    # We get the color from the config file on an "as-needed" basis, resolving any back references which may
    #  be present. This is necessary because the order of the keys in an INI file is required to be undefined,
    #  and we cannot assume that dependencies occur before usage.
    def getColor(self,name):
        name = name.lower()
        if name not in self.dbase:
            if self.config.has_option(self.secname,name):
                self.dbase[name] = self.getColor(getInnerStr(self.config.get(self.secname,name)).lower())
            else:
                return name
        return self.dbase[name]
    def removeColor(self,name):
        del self.dbase[name]
    def clear(self):
        self.dbase.clear()
    def getColorFromIni(self, section, name):
        return self.getColor(getInnerStr(self.config.get(section, name)))

class FontDatabase(object):
    default = {'font':'arial','pointsize':10,
               'italic':False,'bold':False,
               'foregroundcolor':'black','backgroundcolor':'white'}
    def __init__(self,config,secname,colorDatabase):
        self.dbase = {}
        self.config = config
        self.secname = secname
        self.colorDatabase = colorDatabase

    def parseDescr(self,descr):
        """Parse a font description in the INI file, returning a dictionary of the parameters"""
        try:
            d = dict([map(string.strip,map(string.lower,item.split(":"))) for item in descr.split(",")])
        except ValueError:
            raise ValueError,"Invalid font parameters (check punctuation):\n%s" % (descr,)

        # Check keynames and handle Booleans
        for k in d:
            if k not in self.default:
                raise KeyError("Unknown font description key: %s",k)
            # Booleans are special, "1","yes","true" and "on" are True
            #                       "0","no","false" and "off" are False
            if isinstance(self.default[k],bool):
                d[k] = normalizeBoolean(d[k])
            else:
                d[k] = type(self.default[k])(d[k])
        return d

    def getFont(self,name):
        """Returns a dictionary containing the parameters of the named font"""
        name = name.lower()
        if name not in self.dbase:
            if self.config.has_option(self.secname,name):
                descr = getInnerStr(self.config.get(self.secname,name)).lower()
                d = self.parseDescr(descr)
                self.dbase[name] = self.getFont(d["font"]).copy()
                del d["font"]
                self.dbase[name].update(d)
            else:
                self.dbase[name] = self.default.copy()
                self.dbase[name]["font"] = name
        return self.dbase[name]

    def getDefault(self):
        return self.default.copy()

    def getFontFromIni(self,section,optionName="font"):
        """Reads font and color information from the requested section in a configuration file"""
        fontNames={'times':wx.ROMAN,'arial':wx.SWISS,'script':wx.SCRIPT,'courier':wx.TELETYPE,'fixed':wx.MODERN}
        def getValue(key,getter):
            if self.config.has_option(section,key): return getter(section,key)
            else: return fontDict[key]
        if self.config.has_option(section,optionName):
            fontDict = self.getFont(getInnerStr(self.config.get(section,optionName)))
        else:
            fontDict = self.getDefault()
        # Allow font parameters to be overridden within the section, if desired
        size = getValue("pointsize",self.config.getint)
        italicFlag = getValue("italic",self.config.getboolean)
        boldFlag = getValue("bold",self.config.getboolean)
        foregroundColour = self.colorDatabase.getColor(getValue("foregroundcolor", self.colorDatabase.getColorFromIni))
        backgroundColour = self.colorDatabase.getColor(getValue("backgroundcolor", self.colorDatabase.getColorFromIni))
        if italicFlag: style = wx.ITALIC
        else: style = wx.NORMAL
        if boldFlag: weight = wx.BOLD
        else: weight = wx.NORMAL
        faceName=fontDict["font"]
        if faceName in fontNames:
            font = wx.Font(size,fontNames[faceName],style,weight)
        else:
            font = wx.Font(size,wx.DEFAULT,style,weight,faceName=faceName)
        return font, foregroundColour, backgroundColour
#end of class FontDatabase

class SubstDatabase(object):
    # The substitution database is used to store collections of compiled regular expressions for matching
    #  against an input string together with substitutions that may be applied to the input string
    #  to transform it for various purposes. The substitution may be a string, a list of strings or a
    #  dictionary of strings. The function applySubstitution returns a string, a list of strings or a
    #  dictionary of strings resulting from applying the most recent matching substitution to the input
    #  string.
    # If there is no matching entry in the substitution database, the returned value is None

    @staticmethod
    def fromIni(config,secname,keyPrefix="string",substPrefixList=[],defaultSubst=None):
        """Creates and returns a substitution database from a ConfigParser object."""
        db = SubstDatabase()
        if defaultSubst is None: defaultSubst = len(substPrefixList)*[r"\g<0>"]
        if not config.has_section(secname): return
        else:
            for opt in config.list_options(secname):
                if opt.startswith(keyPrefix.lower()):
                    index = int(opt[len(keyPrefix):])
                    str  = getInnerStr(config.get(secname,opt).strip())
                    # If the regular expression does not start with ^ or end with a $, append these
                    if not str.startswith("^"): str = "^" + str
                    if not str.endswith("$"): str = str + "$"
                    repl = []
                    for sp,default in zip(substPrefixList,defaultSubst):
                        try:
                            repl.append(getInnerStr(config.get(secname,"%s%d" % (sp.lower(),index,))))
                        except KeyError:
                            repl.append(default)
                    db.setSubstitution(index,str,repl)
        return db
    def __init__(self):
        self.dbase = {}
        self.sortedIndices = None
    def setSubstitution(self,index,regExp,subst,flags=re.IGNORECASE):
        self.dbase[index] = ((re.compile(regExp,flags),subst))
        self.sortedIndices = None
    def applySubstitution(self,input):
        # Finds the substitution with the largest index whose regex matches the input string
        if self.sortedIndices is None:
            self.sortedIndices = sorted(self.dbase.keys())
        for index in reversed(self.sortedIndices):
            regEx,subst = self.dbase[index]
            if re.match(regEx,input) is not None:
                if isinstance(subst,list):
                    return [re.sub(regEx,s,input) for s in subst]
                elif isinstance(subst,dict):
                    result = {}
                    for k in subst:
                        result[k] = re.sub(regEx,subst[k],input)
                    return result
                else:
                    return re.sub(regEx,subst,input)
        else:
            return None
    def match(self,input):
        # Returns match index if some regExp matches the input, -1 if no match
        if self.sortedIndices is None:
            self.sortedIndices = sorted(self.dbase.keys())
        for index in reversed(self.sortedIndices):
            regEx,subst = self.dbase[index]
            if re.match(regEx,input) is not None:
                return index
        else:
            return -1

class StringDict(object):
    # Class which manages a dictionary of strings specified within a section of an INI file using keys with the same
    #  prefix
    @staticmethod
    def fromIni(config,secname,keyPrefix="string"):
        sl = StringDict()
        for opt in config.list_options(secname):
            if opt.startswith(keyPrefix.lower()):
                index = int(opt[len(keyPrefix):])
                sl.strings[index] = getInnerStr(config.get(secname,opt).strip())
        return sl
    def __init__(self):
        self.strings = {}
    def getString(self,index):
        return self.strings[index]
    def getStrings(self):
        return self.strings
    def addString(self, newStr):
        if newStr not in self.strings.values():
            newIdx = max(self.strings.keys())+1
            self.strings[newIdx] = newStr