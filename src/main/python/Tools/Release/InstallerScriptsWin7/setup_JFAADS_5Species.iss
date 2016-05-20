; JFAADS setup (5Species= N2O_CH4_CO2_NH3_H2O)

; definitions referenced by inc_desktop_shortcuts.iss
#define quickGuiIni = "QuickGui.ini"

#define dataRecalIni = "UserCal.ini"

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

; Extras
[Icons]
Name: {userdesktop}\O2 Sensor Calibration; Filename: {app}\HostExe\StartO2SensorCal.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\O2cal.ico

; Coordinator
#include "inc_coordinator.iss"
