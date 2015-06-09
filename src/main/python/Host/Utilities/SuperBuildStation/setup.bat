if exist fastLomb.pyd del fastLomb.pyd
python setup.py build_src build_ext --inplace -c mingw32
