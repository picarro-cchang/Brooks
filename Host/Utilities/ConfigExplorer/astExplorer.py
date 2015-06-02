import _ast
import symtable
import tokenize

def depthFirst(code,parentType=None):
    if isinstance(code,list):
        for e in code:
            depthFirst(e)
    elif isinstance (code,_ast.AST):
        children = code._fields
        for c in children:
            n = getattr(code,c)
            depthFirst(n,code.__class__)
    else:
        if parentType.__name__ == "Str":
        #if isinstance(code,str) and code.endswith('.ini'):
            print "%s: %s" % (parentType,code)

#fname = 'c:/Picarro/G2000/AppConfig/scripts/fitter/fitScriptCO2.py'
fname = 'c:/Picarro/G2000/Host/Fitter/FitterCoreWithFortran.py'
fp = None
fp = open(fname,"r")
try:
    st = fp.read().replace("\r\n","\n")
    code = compile(st,fname,'exec',_ast.PyCF_ONLY_AST)
finally:
    fp.close()

depthFirst(code)