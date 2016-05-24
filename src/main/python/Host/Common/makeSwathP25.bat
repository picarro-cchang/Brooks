if exist swathP.pyd del swathP.pyd
python c:\python25\scripts\f2py.py swathP.pyf swathP.c -c --compiler=mingw32
