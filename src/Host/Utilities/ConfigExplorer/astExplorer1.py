import ast
import symtable
import tokenize

def walk(root):
    # Perform a depth first traversal of a Python AST
    print root.__class__
    print root.__dict__


fname = 'c:/Picarro/G2000/AppConfig/scripts/fitter/fitScriptCO2.py'
fname = 'c:/Picarro/G2000/Host/Fitter/FitterCoreWithFortran.py'
fp = None
fp = open(fname,"r")
try:
    st = fp.read().replace("\r\n","\n")
    code = compile(st,fname,'exec',ast.PyCF_ONLY_AST)
    sym = symtable.symtable(st,fname,'exec')
finally:
    fp.close()

fp = None
fp = open(fname,"r")
try:
    for typ,st,(srow,scol),(erow,ecol),line in tokenize.generate_tokens(fp.readline):
        if typ == tokenize.STRING:
            print st

finally:
    fp.close()