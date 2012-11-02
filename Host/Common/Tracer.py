"""
Copyright 2012 Picarro Inc.
"""


def traceCalls(frame, event, arg):
    """
    Adapted from http://www.doughellmann.com/PyMOTW/sys/tracing.html
    Use this with sys.settrace() to quickly track what is happening in
    an application.
    """

    if event != 'call':
        return

    code = frame.f_code
    funcName = code.co_name

    if funcName == 'write':
        return

    funcLineNum = frame.f_lineno
    funcFileName = code.co_filename
    caller = frame.f_back
    callerLineNum = caller.f_lineno
    callerFileName = caller.f_code.co_filename

    print 'Call to %s on line %s of %s from line %s of %s' % (funcName,
                                                              funcLineNum,
                                                              funcFileName,
                                                              callerLineNum,
                                                              callerFileName)
    return
