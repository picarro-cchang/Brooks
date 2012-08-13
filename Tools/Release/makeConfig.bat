rem Update and create version files for config files located at S:\CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller\%releaseBranch%
set releaseBranch=1.3

S:
cd \CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller\%releaseBranch%

cd CommonConfig
bzr pull
bzr version-info --custom --template="[Version]\nrevno = {revno}\ndate = {date}\nrevision_id = {revision_id}" > version.ini

C:
for %%A in (4SpeciesFlight_CFKBDS, 4Species_CFKADS, AEDS, BFADS, CFADS, CFDDS, CFEDS, CFFDS, CFIDS, CFJDS, CHADS, CKADS, FCDS, FDDS, Flux, HIDS, iCO2, iH2O, MADS, SuperFlux) do call runMakeConfig.bat %releaseBranch% %%A

