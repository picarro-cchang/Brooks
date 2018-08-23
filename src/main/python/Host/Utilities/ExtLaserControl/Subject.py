#!/usr/bin/python
"""
File Name: Subject.py
Purpose: Base class for notification system that observers can subscribe to

File History:
    19-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
class Subject(object):
    """Something to which listeners can subscribe for updates.
    """
    def __init__(self, *a, **kwds):
        if "name" in kwds:
            self.name = kwds["name"]
        else:
            self.name = "unknown"

        self.listeners = {}
        self.nextListenerIndex = 0
        self.changed = ""

    def addListener(self, listenerFunc):
        """Adds a function to the list of listeners for subject.

        Args:
            listenerFunc: A function to be called when the subject is updated. It is called passing
               the subject as the only parameter.

        Returns:
            An integer index which is useful for removing the listener.
        """
        self.listeners[self.nextListenerIndex] = listenerFunc
        retVal = self.nextListenerIndex

        self.nextListenerIndex += 1
        return retVal

    def removeListener(self, listenerIndex):
        """Removes a listener from the list.

        Args:
            listenerIndex: The index that was returned when the listener was added
        """
        del self.listeners[listenerIndex]

    def update(self, changed=None):
        """Calls all the active listeners.
        """
        if changed is not None:
            self.changed = changed
        for listener in self.listeners:
            self.listeners[listener](self)

    def set(self, var, value, force=False):
        """Set a variable and call listeners.

        Args:
            var: Name of variable, which must be an attribute of the model
            value: Value to set the varible to
            force: Call update whether or not variable has changed
        """
        oldValue = getattr(self, var)
        if force or (oldValue != value):
            setattr(self, var, value)
            self.update(var)
