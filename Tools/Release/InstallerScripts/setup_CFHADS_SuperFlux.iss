; CFHADS setup

; definitions referenced by inc_desktop_shortcuts.iss

; use -v option for launching Mode Switcher
#define closeValves = 1

#define quickGuiTitle1 = "User Interface (Flux)"
#define quickGuiIni1 = "QuickGui.ini"

#define quickGuiTitle2 = "User Interface (CFADS)"
#define quickGuiIni2 = "QuickGui_CFADS.ini"

#define dataRecalTitle1 = "Data Recal (Flux)"
#define dataRecalIni1 = "UserCal.ini"

#define dataRecalTitle2 = "Data Recal (High-Precision 3-Gas)"
#define dataRecalIni2 = "UserCal_CFADS.ini"

#define supervisorLauncherIni = "SupervisorLauncher.ini"
#define supervisorLauncherIntegIni = "SupervisorLauncher_Integration.ini"

#define diagDataCollectorIni = "DiagDataCollector.ini"
#define setupToolIni = "SetupTool.ini"

; only create the Integration Coordinator (coordinatorLauncherIni not defined)
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


[Icons]

; Create some additional custom shortcuts for Peripheral Mode Switcher

; Desktop
Name: {userdesktop}\Peripheral Mode Switcher; Filename: {app}\HostExe\PeriphModeSwitcher.exe; Parameters: -c ..\AppConfig\Config\Utilities\PeriphModeSwitcher.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}

; Start menu
Name: {group}\Peripheral Mode Switcher; Filename: {app}\HostExe\PeriphModeSwitcher.exe; Parameters: -c ..\AppConfig\Config\Utilities\PeriphModeSwitcher.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
