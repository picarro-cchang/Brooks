REM Create the branches that will be used for installer creation

set releaseBranch=1.3

S:
cd \CRDS\SoftwareReleases\G2000Projects\G2000_PrepareInstaller
mkdir %releaseBranch%
cd %releaseBranch%
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Host
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\SrcCode
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CommonConfig

mkdir 4SpeciesFlight_CFKBDS
cd 4SpeciesFlight_CFKBDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4SpeciesFlight_CFKBDS\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4SpeciesFlight_CFKBDS\InstrConfig
cd ..

mkdir 4Species_CFKADS
cd 4Species_CFKADS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4Species_CFKADS\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4Species_CFKADS\InstrConfig
cd ..

mkdir AEDS
cd AEDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\AEDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\AEDSTemplates\InstrConfig
cd ..

mkdir BFADS
cd BFADS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\BFADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\BFADSTemplates\InstrConfig
cd ..

mkdir CFADS
cd CFADS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFADSTemplates\InstrConfig
cd ..

mkdir CFDDS
cd CFDDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFDDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFDDSTemplates\InstrConfig
cd ..

mkdir CFEDS
cd CFEDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFEDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFEDSTemplates\InstrConfig
cd ..

mkdir CFFDS
cd CFFDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFFDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFFDSTemplates\InstrConfig
cd ..

mkdir CFIDS
cd CFIDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFIDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFIDSTemplates\InstrConfig
cd ..

mkdir CHADS
cd CHADS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CHADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CHADSTemplates\InstrConfig
cd ..

mkdir CKADS
cd CKADS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CKADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CKADSTemplates\InstrConfig
cd ..

mkdir FCDS
cd FCDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FCDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FCDSTemplates\InstrConfig
cd ..

mkdir Flux
cd Flux
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FluxTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FluxTemplates\InstrConfig
cd ..

mkdir HIDS
cd HIDS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\HIDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\HIDSTemplates\InstrConfig
cd ..

mkdir iCO2
cd iCO2
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iCO2Templates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iCO2Templates\InstrConfig
cd ..

mkdir iH2O
cd iH2O
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iH2OTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iH2OTemplates\InstrConfig
cd ..

mkdir MADS
cd MADS
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\MADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\MADSTemplates\InstrConfig
cd ..

mkdir SuperFlux
cd SuperFlux
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\SuperFluxTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\SuperFluxTemplates\InstrConfig

C: