REM Create new release branches from trunk, using the local branches as media (pull from trunk, push to release)

set releaseBranch=1.3

s:
cd \CrdsRepositoryNew\Releases\G2000
mkdir %releaseBranch%
cd %releaseBranch%
mkdir Config
cd Config
mkdir 4SpeciesFlight_CFKBDS
mkdir 4Species_CFKADS
mkdir AEDSTemplates
mkdir BFADSTemplates
mkdir CFADSTemplates
mkdir CFDDSTemplates
mkdir CFEDSTemplates
mkdir CFFDSTemplates
mkdir CFIDSTemplates
mkdir CHADSTemplates
mkdir CKADSTemplates
mkdir FCDSTemplates
mkdir FluxTemplates
mkdir HIDSTemplates
mkdir iCO2Templates
mkdir iH2OTemplates
mkdir MADSTemplates
mkdir SuperFluxTemplates

c:

cd ..
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Host
cd Host
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Host
cd ..
bzr branch S:\CrdsRepositoryNew\trunk\G2000\SrcCode
cd SrcCode
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\SrcCode
cd ..
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CommonConfig
cd CommonConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CommonConfig
cd ..

mkdir 4SpeciesFlight_CFKBDS
cd 4SpeciesFlight_CFKBDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\4SpeciesFlight_CFKBDS\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\4SpeciesFlight_CFKBDS\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4SpeciesFlight_CFKBDS\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4SpeciesFlight_CFKBDS\InstrConfig
cd ..\..

mkdir 4Species_CFKADS
cd 4Species_CFKADS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\4Species_CFKADS\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\4Species_CFKADS\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4Species_CFKADS\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4Species_CFKADS\InstrConfig
cd ..\..

mkdir AEDS
cd AEDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\AEDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\AEDSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\AEDSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\AEDSTemplates\InstrConfig
cd ..\..

mkdir BFADS
cd BFADS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\BFADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\BFADSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\BFADSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\BFADSTemplates\InstrConfig
cd ..\..

mkdir CFADS
cd CFADS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFADSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFADSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFADSTemplates\InstrConfig
cd ..\..

mkdir CFDDS
cd CFDDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFDDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFDDSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFDDSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFDDSTemplates\InstrConfig
cd ..\..

mkdir CFEDS
cd CFEDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFEDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFEDSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFEDSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFEDSTemplates\InstrConfig
cd ..\..

mkdir CFFDS
cd CFFDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFFDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFFDSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFFDSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFFDSTemplates\InstrConfig
cd ..\..

mkdir CFIDS
cd CFIDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFIDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CFIDSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFIDSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFIDSTemplates\InstrConfig
cd ..\..

mkdir CHADS
cd CHADS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CHADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CHADSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CHADSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CHADSTemplates\InstrConfig
cd ..\..

mkdir CKADS
cd CKADS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CKADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\CKADSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CKADSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CKADSTemplates\InstrConfig
cd ..\..

mkdir FCDS
cd FCDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\FCDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\FCDSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FCDSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FCDSTemplates\InstrConfig
cd ..\..

mkdir Flux
cd Flux
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\FluxTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\FluxTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FluxTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FluxTemplates\InstrConfig
cd ..\..

mkdir HIDS
cd HIDS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\HIDSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\HIDSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\HIDSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\HIDSTemplates\InstrConfig
cd ..\..

mkdir iCO2
cd iCO2
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\iCO2Templates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\iCO2Templates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iCO2Templates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iCO2Templates\InstrConfig
cd ..\..

mkdir iH2O
cd iH2O
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\iH2OTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\iH2OTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iH2OTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iH2OTemplates\InstrConfig
cd ..\..

mkdir MADS
cd MADS
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\MADSTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\MADSTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\MADSTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\MADSTemplates\InstrConfig
cd ..\..

mkdir SuperFlux
cd SuperFlux
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\SuperFluxTemplates\AppConfig
bzr branch S:\CrdsRepositoryNew\trunk\G2000\Config\SuperFluxTemplates\InstrConfig
cd AppConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\SuperFluxTemplates\AppConfig
cd ..\InstrConfig
bzr push S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\SuperFluxTemplates\InstrConfig

cd ..\..\MakeTools

