if exist cluster_analyzer.pyd del cluster_analyzer.pyd
if exist fitutils.pyd del fitutils.pyd
python c:\python27\scripts\f2py.py -c -m fitutils fitutils.f --compiler=mingw32
python setup.py build_src build_ext --inplace -c mingw32
