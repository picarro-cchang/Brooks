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
#include "inc_code_surveyor.iss"
#include "inc_usb.iss"
#include "inc_python.iss"
#include "inc_digio.iss"

; Notes: Files are installed in the order they are listed below.

; KillHostSoftware.py
Source: {#distDir}\HostExe\KillHostSoftware.py; DestDir: {app}\HostExe; Flags: recursesubdirs replacesameversion;
; installerSignature.txt
Source: {#configDir}\FEDS\installerSignature.txt; DestDir: {app}; Flags: ignoreversion; BeforeInstall: MyBeforeInstall; Check: CheckForFEDS
Source: {#configDir}\RFADS\installerSignature.txt; DestDir: {app}; Flags: ignoreversion; BeforeInstall: MyBeforeInstall; Check: CheckForRFADS
; InstrConfig
Source: {#configDir}\FEDS\InstrConfig\*; DestDir: {app}\InstrConfig; Flags: recursesubdirs replacesameversion; Check: CheckForFEDS
Source: {#configDir}\RFADS\InstrConfig\*; DestDir: {app}\InstrConfig; Flags: recursesubdirs replacesameversion; Check: CheckForRFADS
; AppConfig
Source: {#configDir}\FEDS\AppConfig\*; DestDir: {app}\AppConfig; Flags: recursesubdirs replacesameversion; Check: CheckForFEDS
Source: {#configDir}\RFADS\AppConfig\*; DestDir: {app}\AppConfig; Flags: recursesubdirs replacesameversion; Check: CheckForRFADS
; install the signature file a second time in order to call MyAfterInstall
Source: {#configDir}\FEDS\installerSignature.txt; DestDir: {app}; Flags: ignoreversion; AfterInstall: MyAfterInstall; Check: CheckForFEDS
Source: {#configDir}\RFADS\installerSignature.txt; DestDir: {app}; Flags: ignoreversion; AfterInstall: MyAfterInstall; Check: CheckForRFADS
; CommonConfig
Source: {#configDir}\CommonConfig\*; DestDir: {app}\CommonConfig; Flags: recursesubdirs replacesameversion
; HostExe executables (icons handled by inc_icons.iss)
Source: {#distDir}\HostExe\*; DestDir: {app}\HostExe; Flags: recursesubdirs replacesameversion
; Files needed for post-installation update
Source: {#distDir}\Tools\Scripts\UpdateHostSoftware.py; DestDir: {app}\HostExe; Flags: replacesameversion; Check: CheckForRFADS
Source: {#configDir}\RFADS\AppConfig\Config\Utilities\UpdateMasterIni.ini; DestDir: {app}\AppConfig\Config\Utilities; Flags: replacesameversion; Check: CheckForRFADS

#include "inc_datviewer.iss"
#include "inc_desktop_shortcuts.iss"
#include "inc_configtool.iss"
#include "inc_coordinator.iss"

; Setup items unique to FEDS Surveyor are below:

[Icons]
; Surveyor startup app is Picarro.Surveyor.Analyzer service
Name: {userstartup}\Start Analyzer Service; Filename: {app}\Picarro.Surveyor.Analyzer\Picarro.Surveyor.Analyzer.exe; WorkingDir: {app}\Picarro.Surveyor.Analyzer; IconFilename: {app}\HostExe\{#picarroIcon}
; Restart surveyor is used when the supervisor becomes unresponsive
Name: {userstartup}\Restart Surveyor; Filename: {app}\HostExe\RestartSurveyor.exe; Parameters: -c ..\AppConfig\Config\Utilities\RestartSurveyor.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

[Run]
Filename: C:\Python27\python.exe; Parameters: {app}\HostExe\UpdateHostSoftware.py; Check: CheckForRFADS

[InstallDelete]
Type: files; Name: "{userstartup}\Start Analyzer Service"
Type: files; Name: "{userstartup}\Restart Surveyor"
