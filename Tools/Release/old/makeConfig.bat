rem Update and create version files for config files located at S:\CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller\%releaseBranch%
set releaseBranch=1.3

S:
cd \CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller\%releaseBranch%

cd CommonConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\4SpeciesFlight_CFKBDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\4Species_CFKADS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\AEDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\BFADS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CFADS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CFDDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CFEDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CFFDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CFIDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CFJDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CHADS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\CKADS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\FCDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\FDDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\Flux\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\HIDS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\iCO2\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\iH2O\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\MADS\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

cd ..\..\SuperFlux\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

C:
