set releaseBranch=1.3
set version=1.3.6

rem Part 1: Tag and branch in repository
S:

cd \CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Host
bzr tag --force %version%

cd ..\SrcCode
bzr tag --force %version%

cd ..\Config\CommonConfig
bzr tag --force %version%

cd ..\4SpeciesFlight_CFKBDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\4Species_CFKADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\AEDSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\BFADSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFADSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFDDSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFEDSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFFDSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFIDSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CHADSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CKADSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\FCDSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\FluxTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\HIDSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\iCO2Templates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\iH2OTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\MADSTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\SuperFluxTemplates\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%


cd \CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller\%releaseBranch%\CommonConfig
bzr tag --force %version%

cd ..\4SpeciesFlight_CFKBDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\4Species_CFKADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\AEDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\BFADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFDDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFEDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFFDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFIDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CHADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CKADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\FCDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\Flux\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\HIDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\iCO2\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\iH2O\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\MADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\SuperFlux\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

C:

cd ..\Host
bzr tag --force %version%

cd ..\SrcCode
bzr tag --force %version%

cd ..\CommonConfig
bzr tag --force %version%

cd ..\4SpeciesFlight_CFKBDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\4Species_CFKADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\AEDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\BFADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFDDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFEDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFFDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CFIDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CHADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\CKADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\FCDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\Flux\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\HIDS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\iCO2\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\iH2O\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\MADS\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\SuperFlux\AppConfig
bzr tag --force %version%
cd ..\InstrConfig
bzr tag --force %version%

cd ..\..\MakeTools