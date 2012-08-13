rem Update and create version files for local config files
cd ..\CommonConfig
bzr pull
cd ..\MakeTools

for %%A in (4SpeciesFlight_CFKBDS, 4Species_CFKADS, AEDS, BFADS, CFADS, CFDDS, CFEDS, CFFDS, CFIDS, CFJDS, CHADS, CKADS, FCDS, FDDS, Flux, HIDS, iCO2, iH2O, MADS, SuperFlux) do call runPullConfig.bat %%A
