; FCDS setup

; definitions referenced by inc_desktop_shortcuts.iss
#define quickGuiIni = "QuickGui.ini"

#define dataRecalIni = "UserCal.ini"

#define supervisorLauncherIni = "SupervisorLauncher.ini"
#define supervisorLauncherIntegIni = "SupervisorLauncher_Integration.ini"
#define diagDataCollectorIni = "DiagDataCollector.ini"
#define setupToolIni = "SetupTool.ini"

; create Coordinator Launcher shortcut as well as Integration Coordinator Launcher
; removed Coordinator Launcher (issue #721)
;#define coordinatorLauncherIni = "CoordinatorLauncher.ini"
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
