if exist peakF.pyd del peakF.pyd
python c:\python25\scripts\f2py.py peakF.pyf peakF.c -c --compiler=mingw32
