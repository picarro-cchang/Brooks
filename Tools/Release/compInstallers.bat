set version=1.3.6-2
for %%A in (4SpeciesFlight_CFKBDS, 4Species_CFKADS, AEDS, BFADS, CFADS, CFDDS, CFEDS, CFFDS, CFIDS, CFJDS, CHADS, CKADS, FCDS, Flux, HIDS, iCO2, iH2O, MADS, SuperFlux) do call runCompInstallers.bat %%A %version%

set version=1.3.7
for %%A in (FDDS) do call runCompInstallers.bat %%A %version%