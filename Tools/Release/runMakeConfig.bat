S:
cd \CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller\%1\%2\AppConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini
cd ..\InstrConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

C:
