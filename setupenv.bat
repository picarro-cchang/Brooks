call mkvirtualenv --system-site-packages host_build
call cdvirtualenv
copy c:\python27\scripts\f2py.py scripts\f2py.py
call cd-
pip install pybuilder
pip install coverage
pip install doit
pip install flake8
setprojectdir .
add2virtualenv .

