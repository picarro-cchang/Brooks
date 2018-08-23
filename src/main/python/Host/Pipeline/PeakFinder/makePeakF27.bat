if exist peakF.pyd del peakF.pyd
f2py peakF.pyf peakF.c -c --compiler=mingw32
