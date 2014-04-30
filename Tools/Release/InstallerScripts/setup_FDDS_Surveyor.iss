; FDDS Surveyor setup

; don't create a user Startup shortcut to Start Instrument in inc_desktop_shortcuts.iss
; gets created below (uses RestartSupervisor instead)
#define noStartInst = 1


; definitions referenced by inc_desktop_shortcuts.iss
#define quickGuiIni = "QuickGui.ini"

#define dataRecalIni = "UserCal.ini"

#define supervisorLauncherIni = "SupervisorLauncher.ini"
#define supervisorLauncherIntegIni = "SupervisorLauncher_Integration.ini"
#define diagDataCollectorIni = "DiagDataCollector.ini"
#define setupToolIni = "SetupTool.ini"

; provide an ini file for the Integration Tool
#define integToolIni = "IntegrationTool.ini"

; create Coordinator Launcher shortcut as well as Integration Coordinator Launcher
#define coordinatorLauncherIni = "CoordinatorLauncher.ini"
#define coordinatorLauncherIntegIni = "CoordinatorLauncher_Integration.ini"


; Note: Order of items in [Files] sections (which spans these
;       files) is the install order. Be careful about changing
;       the ordering of the include files below.
;
#include "inc_icons.iss"
#include "inc_setup.iss"
#include "inc_code.iss"
#include "inc_usb.iss"
#include "inc_python.iss"
#include "inc_digio.iss"
#include "inc_ms.iss"
#include "inc_exe_configs.iss"
#include "inc_datviewer.iss"
#include "inc_desktop_shortcuts.iss"
#include "inc_configtool.iss"

#include "inc_coordinator.iss"


; Setup items unique to FDDS Surveyor are below:


[Icons]

; Surveyor startup app is RestartSupervisor
Name: {userstartup}\Start Instrument; Filename: {app}\HostExe\RestartSupervisor.exe; Parameters: -c ..\AppConfig\Config\Utilities\RestartSupervisor.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}


; Remove any previous startup items that referenced Supervisor.exe since we use
; the RestartSupervisor now.
[InstallDelete]
Type: files; Name: "{userstartup}\Start Instrument"
