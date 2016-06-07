; FEDS Surveyor setup

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

#include "inc_scripts.iss"

; Setup items unique to FEDS Surveyor are below:

[Icons]
; Surveyor startup app is Picarro.Surveyor.Analyzer service
Name: {userstartup}\Start Analyzer Service; Filename: {app}\Picarro.Surveyor.Analyzer\Picarro.Surveyor.Analyzer.exe; WorkingDir: {app}\Picarro.Surveyor.Analyzer; IconFilename: {app}\HostExe\{#picarroIcon}
; Restart surveyor is used when the supervisor becomes unresponsive
Name: {userstartup}\Restart Surveyor; Filename: {app}\HostExe\RestartSurveyor.exe; Parameters: -c ..\AppConfig\Config\Utilities\RestartSurveyor.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

[Run]
Filename: {app}\HostExe\setvalvemasks.cmd

[InstallDelete]
Type: files; Name: "{userstartup}\Start Analyzer Service"
Type: files; Name: "{userstartup}\Restart Surveyor"
