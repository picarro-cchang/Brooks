set releaseBranch=1.3
set version=1.3.6-2

S:
set root=CrdsRepositoryNew\Releases\G2000
cd \%root%\%releaseBranch%\Host
bzr tag --force %version%

cd ..\SrcCode
bzr tag --force %version%

cd ..\Config\CommonConfig
bzr tag --force %version%

C:
for %%A in (4SpeciesFlight_CFKBDS, 4Species_CFKADS, AEDSTemplates, BFADSTemplates, CFADSTemplates, CFDDSTemplates, CFEDSTemplates, CFFDSTemplates, CFIDSTemplates, CFJDSTemplates, CHADSTemplates, CKADSTemplates, FCDSTemplates, FDDSTemplates, FluxTemplates, HIDSTemplates, iCO2Templates, iH2OTemplates, MADSTemplates, SuperFluxTemplates) do call runTagOnlyS.bat \%root%\%releaseBranch%\Config %%A %version%

S:
set root=CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller
cd \%root%\%releaseBranch%\CommonConfig
bzr tag --force %version%

C:
for %%A in (4SpeciesFlight_CFKBDS, 4Species_CFKADS, AEDS, BFADS, CFADS, CFDDS, CFEDS, CFFDS, CFIDS, CFJDS, CHADS, CKADS, FCDS, FDDS, Flux, HIDS, iCO2, iH2O, MADS, SuperFlux) do call runTagOnlyS.bat \%root%\%releaseBranch% %%A %version%

cd ..\Host
bzr tag --force %version%

cd ..\SrcCode
bzr tag --force %version%

cd ..\CommonConfig
bzr tag --force %version%
cd ..\MakeTools

for %%A in (4SpeciesFlight_CFKBDS, 4Species_CFKADS, AEDS, BFADS, CFADS, CFDDS, CFEDS, CFFDS, CFIDS, CFJDS, CHADS, CKADS, FCDS, FDDS, Flux, HIDS, iCO2, iH2O, MADS, SuperFlux) do call runTagOnlyC.bat %%A %version%
