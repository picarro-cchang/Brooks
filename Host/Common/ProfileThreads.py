import profile
import tempfile

def profileThread(func):
    result = None
    p = profile.Profile()
    try:
        result = p.runcall(func)
    finally:
        if hasattr(func, 'func_name'):
            tmpfname = tempfile.mktemp() + func.func_name
        elif hasattr(func, 'im_func') and hasattr(func.im_func, '__name__'):
            tmpfname = tempfile.mktemp() + func.im_func.__name__
        else:
            tmpfname = tempfile.mktemp() + "unknownfuncname"

        print "thread finished %s\n" % (tmpfname,)
        p.dump_stats(tmpfname)
        p = None
        del p
    return result
