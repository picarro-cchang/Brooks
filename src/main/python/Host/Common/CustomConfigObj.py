#!/usr/bin/python
#
# File Name: CustomConfigObj.py
# Purpose: A customized ConfigObj to replace "SortedConfigParser".
# Notes:
#               1. Wrapper functions for ConfigParser compatibility are added on top of the methods and attributes from original ConfigObj.
#               2. When ignore_option_case is True, it should behave like ConfigParser
#
#               In CustomConfigObj some module options play important roles for 100% compatibility. For example, if single quote (') is used in the ini file,
#               the "list_values" option must be set as False, which means single line values are not quoted or unquoted when reading and writing.
#               Also the "ignore_option_case" must be set as True to force it behave like ConfigParser, where options are not case-sensitive.
#               However when an option needs case-conversion to retrieve the value a warning will be printed out in CustomConfigObj.
#
# File History:
# 08-09-16  Alex  Created file
#
# 25Sep2016 Ray   Restored % interpolation.
#
# configobj supported % interpolation with keys set in the [DEFAULT] section of an
# ini file like that below but this capability was not working in CustomConfigObj.
# I have restored this feature with a small change in the get() method to call
# configobj.get() when needed.
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# [DEFAULT]
# path = /home/rsf/git/host/src/main/python/Host
#
# [EventManager]
# Executable = %(path)s/EventManager/EventManager.py
# LaunchArgs = --viewer -c %(path)s/AppConfig/Config/EventManager/EventManager.ini
#
# [Driver]
# Executable = %(path)s/Driver/Driver.py
# LaunchArgs = -c %(path)s/AppConfig/Config/Driver/Driver_lct.ini
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#

"""Customized configuration file parser using ConfigObj.

Based on the enhanced configuration parser ConfigObj, which supports
a many features missing from the original ConfigParser, this module
adds most of the useful ConfigParser-compatible wrapper functions.
It takes the advantage of both ConfigObj and ConfigParser.


class:

CustomConfigObj -- responsible for parsing a list of
                   configuration files, and managing the parsed database.

    Options:
    ========
    ignore_option_case
        If True, this module will treat options as non-case-sensitive,
        and returns options as all lower-case.
        This is not a preferred mode, but it supported the
        backward compatibility with the original ConfigParser.

    print_case_convert
        If True, a warning message will be printed whenever a
        case conversion is needed to match an option name with
        the configuration dictionary (i.e., an option can still match
        even it has different case than the key defined in dictionary).
        It takes effect only when ignore_option_case is True.

    Methods that support ConfigParser compatibility:
    ================================================
    get(section, option, default=None)
        return a string value for the named option. If the default
        is not given and (section, option) can't be found in the
        configuration file, a KeyError will be raised. Otherwise
        the default value will be returned, and also added to
        the internal configuration dictionary.
        Note % interpolations are not supported.

    getint(section, option, default=None)
        like get(), but convert value to an integer

    getfloat(section, option, default=None)
        like get(), but convert value to a float

    getboolean(section, options)
        like get(), but convert value to a boolean (currently case
        insensitively defined as 0, false, no, off for False, and 1, true,
        yes, on for True).  Returns False or True.

    set(section, option, value)
        set the given option

    has_section(section)
        return whether the given section exists

    list_sections()
        return all the configuration section names.
        This used to be the sections() function in ConfigParser.

    add_section(section)
        add a new section. Raise DuplicateSectionError if a
        section by the specified name already exists.

    remove_section(section)
        remove the given file section and all its options. If an
        existing section is removed, it returns True. If trying
        to remove a non-existing section, it returns False.

    has_option(section, option)
        return whether the given option exists in the given section

    list_options(section)
        return list of configuration options for the named section.
        This used to be the options() function in ConfigParser.

    remove_option(section, option)
        remove the given option from the given section. If an
        existing option is removed, it returns True. If trying
        to remove a non-existing option, it returns False.

    list_items(section, raw=False, vars=None)
        return a list of tuples with (name, value) for each option
        in the section. This used to be the items() function in ConfigParser.

    Additional methods:
    ignore_option_case_on (or off)
        Turn on/off the ignore_option_case flag.

"""
import Host.Common.configobj as configobj
import types

class Error(Exception):
    """Base class for ConfigParser exceptions."""

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message
    __str__ = __repr__

class DuplicateSectionError(Error):
    """Raised when a section is multiply-created."""
    def __init__(self, section):
        Error.__init__(self, "Section %r already exists" % section)

class DuplicateOptionError(Error):
    """Raised when an option is present in several cases, and ignore_option_case_on is in effect."""
    def __init__(self, option):
        Error.__init__(self, "Option %r already exists" % option)

class CustomConfigObj(configobj.ConfigObj):
    def __init__(self, infile=None, options=None, ignore_option_case=True, print_case_convert=False, **kwargs):
        if not kwargs.has_key('file_error'):
            kwargs['file_error'] = True
        if not kwargs.has_key('list_values'):
            kwargs['list_values'] = False
        configobj.ConfigObj.__init__(self, infile, options, **kwargs)
        self.ignoreOptionCase = ignore_option_case
        self.print_case_convert = print_case_convert
        if ignore_option_case:
            self.shadow = self._lowerCaseOpts(self)
        else:
            self.shadow = None

    def _lowerCaseOpts(self,subDict):
        """Recursive routine which takes a nested dictionary and lower-cases
        the keys of the leaf nodes"""
        newDict = {}
        for k in subDict:
            v = subDict[k]
            if isinstance(v,dict):
                newDict[k] = self._lowerCaseOpts(v)
            else:
                if k.lower() in newDict:
                    raise DuplicateOptionError(k)
                else:
                    newDict[k.lower()] = (v,k)
        return newDict

    # This get() overrides the configobj.get().  However, to use the 
    # DEFAULT section we make a direct call to configobj.get() with
    # the super method.  Without this, configobj interpolation causes
    # a fatal exception.  See the notes above.
    #
    def get(self, section, option='', default=None):
        if not option:
            return super(CustomConfigObj, self).get(section)
        if default is None:
            if not self.ignoreOptionCase:
                return self[section][option]
            else:
                v,origKey = self.shadow[section][option.lower()]
                return v
        else:
            default = str(default)
            try:
                if not self.ignoreOptionCase:
                    return self[section][option]
                else:
                    v,origKey = self.shadow[section][option.lower()]
                    return v
            except KeyError:
                self._add_value(section, option, default)
                return default


    def getint(self, section, option, default=None):
        try:
            return int(self.get(section, option, default))
        except ValueError:
            return int(float(self.get(section, option, default)))

    def getfloat(self, section, option, default=None):
        return float(self.get(section, option, default))

    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def getboolean(self, section, option, default=None):
        v = self.get(section, option, default)
        if v.lower() not in self._boolean_states:
            raise ValueError, 'Not a boolean: %s' % v
        return self._boolean_states[v.lower()]

    def set(self, section, option, value, format=None):
        if format != None:
            value = format%value

        if not self.ignoreOptionCase:
            self[section].update({option: str(value)})
        else:
            optionLc = option.lower()
            if optionLc in self.shadow[section]:
                v, k = self.shadow[section][optionLc]
                self[section].update({k: str(value)})
                self.shadow[section].update({optionLc: (str(value),option)})
            else:
                self[section].update({option: str(value)})
                self.shadow[section].update({optionLc: (str(value),option)})

    def has_section(self, section):
        return self.has_key(section)

    def list_sections(self):
        """ Equivalent to sections() function in ConfigParser
        """
        return self.keys()

    def add_section(self, section):
        if not self.has_key(section):
            self[section] = {}
            if self.ignoreOptionCase:
                self.shadow[section] = {}
        else:
            raise DuplicateSectionError(section)

    def remove_section(self, section):
        existed = self.has_key(section)
        if existed:
            del self[section]
            if self.ignoreOptionCase:
                del self.shadow[section]
        return existed

    def has_option(self, section, option):
        if self.has_key(section):
            if not self.ignoreOptionCase:
                return option in self[section]
            else:
                return option.lower() in self.shadow[section]
        else:
            return False

    def list_options(self, section):
        """ Equivalent to options() function in ConfigParser
        """
        if not self.ignoreOptionCase:
            return self[section].keys()
        else:
            return self.shadow[section].keys()

    def remove_option(self, section, option):
        if self.has_key(section):
            if not self.ignoreOptionCase:
                try:
                    del self[section][option]
                    return True
                except KeyError:
                    return False
            else:
                try:
                    v,k = self.shadow[section][option.lower()]
                    del self[section][k]
                    del self.shadow[section][option.lower()]
                    return True
                except KeyError:
                    return False
        else:
            return False

    def list_items(self, section):
        """ Equivalent to items() function in ConfigParser
        """
        if not self.ignoreOptionCase:
            return self[section].items()
        else:
            return [(k.lower(),self[section][k]) for k in self[section]]

    def ignore_option_case_on(self):
        """ The class treats options as case non-sensitive
        """
        self.ignoreOptionCase = True
        self.shadow = self._lowerCaseOpts(self)

    def ignore_option_case_off(self):
        """ The class treats options as case sensitive
        """
        self.ignoreOptionCase = False
        self.shadow = None

    def _add_value(self, section, option, value):
        if self.has_key(section):
            self.set(section, option, value)
        else:
            self.update({section: {option: value}})
