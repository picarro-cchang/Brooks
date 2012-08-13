import os
instrList = ["4SpeciesFlight_CFKBDS", "4Species_CFKADS", "AEDS", "BFADS", "CFADS", "CFDDS", "CFEDS", "CFFDS", "CFIDS", "CFJDS", "CHADS", "CKADS", "FCDS", "FDDS", "Flux", "HIDS", "iCO2", "iH2O", "MADS", "SuperFlux"]
if __name__ == "__main__":
    outFile = file("currentVersions.txt", "w")
    for module in ["Host", "SrcCode", "CommonConfig"]:
        print module
        v = os.popen("bzr version-info --custom --template=\"revno = {revno}\" ..\%s" % module)
        outFile.write("%-35s, Version: %s\n" % (module, v.read()))
    for module in instrList:
        print module
        v = os.popen("bzr version-info --custom --template=\"revno = {revno}\" ..\%s\AppConfig" % module)
        outFile.write("\n%-35s, Version: %s\n" % (module+" - AppConfig", v.read()))
        v = os.popen("bzr version-info --custom --template=\"revno = {revno}\" ..\%s\InstrConfig" % module)
        outFile.write("%-35s, Version: %s\n" % (module+" - InstrConfig", v.read()))
    outFile.close()
