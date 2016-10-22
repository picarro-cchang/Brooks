import os

def write_desktop_icon_file(fileName, iconName, command, iconPath, Terminal=False):
    context = "#!usr/bin/env xdg-open\n" + \
        "[Desktop Entry]\n" + \
        "Type=Application\n" + \
        "Name=%s\n" % iconName + \
        "Icon=%s\n" % iconPath + \
        "Exec=%s\n" % command + \
        "Terminal=%s" % ("true" if Terminal else "false")
    with open("/root/Desktop/%s.desktop" % fileName, "w") as f:
        f.write(context)
 
if not os.path.exists("/root/Desktop"):
    os.mkdir("/root/Desktop")
    
write_desktop_icon_file("modeSwitcher", "Picarro Mode Switcher", 
                        "bash -c 'cd /Picarro/G2000/Host/Utilities/SupervisorLauncher;python -O SupervisorLauncher.py -v -k -c ../../../AppConfig/Config/Utilities/SupervisorLauncher.ini'",
                        "/Picarro/G2000/Assets/icons/Picarro_icon.ico")
write_desktop_icon_file("startInstrument", "Start Instrument", 
                        "bash -c 'cd /Picarro/G2000/Host/Utilities/SupervisorLauncher;python -O SupervisorLauncher.py -a -c ../../../AppConfig/Config/Utilities/SupervisorLauncher.ini'",
                        "/Picarro/G2000/Assets/icons/Picarro_icon.ico")
write_desktop_icon_file("stopInstrument", "Stop Instrument", 
                        "bash -c 'python /Picarro/G2000/Host/Common/StopSupervisor.py'",
                        "/Picarro/G2000/Assets/icons/Cancel.ico")
write_desktop_icon_file("integrationTool", "Integration Tool", 
                        "bash -c 'cd /Picarro/G2000/Host/Utilities/IntegrationTool;python -O IntegrationTool.py -c ../../../CommonConfig/Config/Utilities/IntegrationTool.ini'",
                        "/Picarro/G2000/Assets/icons/Integration_icon.ico", True)
write_desktop_icon_file("controller", "Controller", 
                        "bash -c 'python -O /Picarro/G2000/Host/Controller/Controller.py'",
                        "/Picarro/G2000/Assets/icons/Controller_icon.ico")