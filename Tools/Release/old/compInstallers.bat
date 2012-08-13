set version=1.3.6-2

"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_4Species_CFKADS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_4SpeciesFlight_CFKBDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_AEDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_BFADS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CFADS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CFDDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CFEDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CFFDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CFIDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CFJDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CHADS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_CKADS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_FCDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_Flux.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_HIDS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_iCO2.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_iH2O.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_MADS.iss
"C:\Program Files\Inno Setup 5\Compil32.exe" /cc setup_SuperFlux.iss

cd Output

copy /y setup_4Species_CFKADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\4Species_CFKADS\Archive"
copy /y setup_4Species_CFKADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\4Species_CFKADS\Current\setup_4Species_CFKADS.exe"

copy /y setup_4SpeciesFlight_CFKBDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\4SpeciesFlight_CFKBDS\Archive"
copy /y setup_4SpeciesFlight_CFKBDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\4SpeciesFlight_CFKBDS\Current\setup_4SpeciesFlight_CFKBDS.exe"

copy /y setup_CFADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFADS\Archive"
copy /y setup_CFADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFADS\Current\setup_CFADS.exe"

copy /y setup_CKADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CKADS\Archive"
copy /y setup_CKADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CKADS\Current\setup_CKADS.exe"

copy /y setup_Flux_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\Flux\Archive"
copy /y setup_Flux_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\Flux\Current\setup_Flux.exe"

copy /y setup_SuperFlux_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\SuperFlux\Archive"
copy /y setup_SuperFlux_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\SuperFlux\Current\setup_SuperFlux.exe"

copy /y setup_iH2O_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\iH2O\Archive"
copy /y setup_iH2O_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\iH2O\Current\setup_iH2O.exe"

copy /y setup_iCO2_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\iCO2\Archive"
copy /y setup_iCO2_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\iCO2\Current\setup_iCO2.exe"

copy /y setup_CFDDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFDDS\Archive"
copy /y setup_CFDDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFDDS\Current\setup_CFDDS.exe"

copy /y setup_CFEDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFEDS\Archive"
copy /y setup_CFEDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFEDS\Current\setup_CFEDS.exe"

copy /y setup_CFFDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFFDS\Archive"
copy /y setup_CFFDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFFDS\Current\setup_CFFDS.exe"

copy /y setup_AEDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\AEDS\Archive"
copy /y setup_AEDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\AEDS\Current\setup_AEDS.exe"

copy /y setup_MADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\MADS\Archive"
copy /y setup_MADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\MADS\Current\setup_MADS.exe"

copy /y setup_CFIDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFIDS\Archive"
copy /y setup_CFIDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFIDS\Current\setup_CFIDS.exe"

copy /y setup_CFJDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFJDS\Archive"
copy /y setup_CFJDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CFJDS\Current\setup_CFJDS.exe"

copy /y setup_CHADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CHADS\Archive"
copy /y setup_CHADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\CHADS\Current\setup_CHADS.exe"

copy /y setup_HIDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\HIDS\Archive"
copy /y setup_HIDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\HIDS\Current\setup_HIDS.exe"

copy /y setup_FCDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\FCDS\Archive"
copy /y setup_FCDS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\FCDS\Current\setup_FCDS.exe"

copy /y setup_BFADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\BFADS\Archive"
copy /y setup_BFADS_%version%.exe "s:\Crds\CRD Engineering\Software\G2000\Installer\BFADS\Current\setup_BFADS.exe"