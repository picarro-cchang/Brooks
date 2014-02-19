; CFBDS Flux setup

; definitions referenced by inc_desktop_shortcuts.iss
#define quickGuiTitle1 = "User Interface (CO2_CH4)"
#define quickGuiIni1 = "QuickGui.ini"

#define quickGuiTitle2 = "User Interface (CO2_H2O))"
#define quickGuiIni2 = "QuickGui_CO2_H2O.ini"

#define quickGuiTitle3 = "User Interface (H2O_CH4)"
#define quickGuiIni3 = "QuickGui_H2O_CH4.ini"

#define quickGuiTitle4 = "User Interface (CFADS)"
#define quickGuiIni4 = "QuickGui_CFADS.ini"

#define dataRecalTitle1 = "Data Recal (Flux)"
#define dataRecalIni1 = "UserCal.ini"

#define dataRecalTitle2 = "Data Recal (High-Precision 3-Gas)"
#define dataRecalIni2 = "UserCal_CFADS.ini"

#define supervisorLauncherIni = "SupervisorLauncher.ini"
#define supervisorLauncherIntegIni = "SupervisorLauncher_Integration.ini"

#define diagDataCollectorIni = "DiagDataCollector.ini"
#define setupToolIni = "SetupTool.ini"


; definitions referenced by inc_coordinator.iss
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


; Extras
;

; Not including Coordinator, only an integration shortcut gets installed
;#include "inc_coordinator.iss"


[Icons]

; Additional Flux shortcuts

; Flux Mode Scheduler (desktop and Start menu)

Name: {userdesktop}\Flux Mode Scheduler; Filename: {app}\HostExe\FluxScheduler.exe; Parameters: -c ..\AppConfig\Config\Utilities\FluxSwitcher.ini -s ..\AppConfig\Config\Utilities\SupervisorLauncher.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

Name: {group}\Flux Mode Scheduler; Filename: {app}\HostExe\FluxScheduler.exe; Parameters: -c ..\AppConfig\Config\Utilities\FluxSwitcher.ini -s ..\AppConfig\Config\Utilities\SupervisorLauncher.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}


; TODO: This is the only Coordinator shortcut, is this correct? No other Coordinator stuff?
Name: {userdesktop}\Integration\Integration Coordinator Launcher; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\CoordinatorLauncher_Integration.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}

