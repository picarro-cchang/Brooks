REM Change the parent repository

set releaseBranch=1.3

cd ..\Host
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Host
cd ..\SrcCode
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\SrcCode
cd ..\CommonConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CommonConfig

cd ..\4SpeciesFlight_CFKBDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4SpeciesFlight_CFKBDS\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4SpeciesFlight_CFKBDS\InstrConfig
cd ..\..

cd 4Species_CFKADS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4Species_CFKADS\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\4Species_CFKADS\InstrConfig
cd ..\..

cd AEDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\AEDSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\AEDSTemplates\InstrConfig
cd ..\..

cd BFADS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\BFADSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\BFADSTemplates\InstrConfig
cd ..\..

cd CFADS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFADSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFADSTemplates\InstrConfig
cd ..\..

cd CFDDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFDDSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFDDSTemplates\InstrConfig
cd ..\..

cd CFEDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFEDSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFEDSTemplates\InstrConfig
cd ..\..

cd CFFDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFFDSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFFDSTemplates\InstrConfig
cd ..\..

cd CFIDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFIDSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CFIDSTemplates\InstrConfig
cd ..\..

cd CHADS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CHADSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CHADSTemplates\InstrConfig
cd ..\..

cd CKADS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CKADSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\CKADSTemplates\InstrConfig
cd ..\..

cd FCDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FCDSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FCDSTemplates\InstrConfig
cd ..\..

cd Flux
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FluxTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\FluxTemplates\InstrConfig
cd ..\..

cd HIDS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\HIDSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\HIDSTemplates\InstrConfig
cd ..\..

cd iCO2
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iCO2Templates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iCO2Templates\InstrConfig
cd ..\..

cd iH2O
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iH2OTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\iH2OTemplates\InstrConfig
cd ..\..

cd MADS
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\MADSTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\MADSTemplates\InstrConfig
cd ..\..

cd SuperFlux
cd AppConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\SuperFluxTemplates\AppConfig
cd ..\InstrConfig
bzr pull --remember S:\CrdsRepositoryNew\Releases\G2000\%releaseBranch%\Config\SuperFluxTemplates\InstrConfig

cd ..\..\MakeTools

