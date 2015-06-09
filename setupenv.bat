call mkvirtualenv --system-site-packages host_build
pip install pybuilder
pip install coverage
pip install doit
pip install flake8
setprojectdir .
add2virtualenv .
