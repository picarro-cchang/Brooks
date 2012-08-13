"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_%1.iss

copy /y Output\setup_%1_%2.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\%1\Archive"
copy /y Output\setup_%1_%2.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\%1\Current\setup_%1.exe"
