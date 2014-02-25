; FDDS Surveyor setup

; don't create a user Startup shortcut to Start Instrument
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




#define picarroIcon = "Picarro_icon.ico"
#define controllerIcon = "Controller_icon.ico"
#define diagnosticsIcon = "Diagnostics_icon.ico"
#define integrationIcon = "Integration_icon.ico"
#define utilitiesIcon = "Utilities_icon.ico"

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro G2000 {#installerType} Host
AppVerName=Picarro G2000 {#installerType} Host {#hostVersion}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro Analyzer Software
OutputBaseFileName=setup_{#installerType}_{#commonName}_{#hostVersion}
DirExistsWarning=no

[Code]
var
    savedInstrConfig : String;
    instrConfig : String;

procedure MyBeforeInstall();
var
    dateTime : String;
    app : String;
    ResultCode : Integer;
begin
    dateTime := GetDateTimeString('_yyyymmdd_hhnnss',#0,#0);
    app := ExpandConstant('{app}');
    savedInstrConfig := app+'\InstrConfig'+dateTime;
    instrConfig := app+'\InstrConfig';
    Exec(ExpandConstant('{sys}\xcopy.exe'), '/E /Y /I '+instrConfig+' '+savedInstrConfig, '', SW_SHOW,
    ewWaitUntilTerminated, ResultCode);
    {Don't use RenameFile because it will fail if the instrConfig is open in Windows Explorer when installer is running}
    {MsgBox('Renaming:' + instrConfig + ' to ' + savedInstrConfig, mbInformation, MB_OK);}
    {RenameFile(instrConfig,savedInstrConfig);}
    {MsgBox('Renaming Done', mbInformation, MB_OK);}
end;

procedure MyAfterInstall();
var
    ResultCode : Integer;
begin
    {MsgBox('Running xcopy:', mbInformation, MB_OK);}
    Exec(ExpandConstant('{sys}\xcopy.exe'), '/E /Y /I '+savedInstrConfig+' '+instrConfig, '', SW_SHOW,
    ewWaitUntilTerminated, ResultCode);
    {MsgBox('xcopy Done', mbInformation, MB_OK);}
end;

[Files]
Source: {#resourceDir}\Picarro.pth; DestDir: C:\Python25\Lib\site-packages; Flags: replacesameversion
Source: {#resourceDir}\libusb0.dll; DestDir: {sys}; Tasks: LibUSB; Flags: replacesameversion
Source: {#resourceDir}\libusb0.sys; DestDir: {sys}\Drivers; Tasks: LibUSB; Flags: replacesameversion
Source: {#resourceDir}\PicarroUninitialized.inf; DestDir: {win}\inf; Flags: replacesameversion; BeforeInstall: MyBeforeInstall
Source: {#resourceDir}\PicarroUSB.inf; DestDir: {win}\inf; Flags: replacesameversion
Source: {#resourceDir}\Cypress.inf; DestDir: {win}\inf; Flags: replacesameversion
Source: {#resourceDir}\IB_WDT.dll; DestDir: {sys}; Flags: replacesameversion
Source: {#resourceDir}\IBEM_WD.sys; DestDir: {sys}\Drivers; Flags: replacesameversion
Source: {#sandboxDir}\{#installerType}\*; DestDir: {app}; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\CommonConfig\*; DestDir: {app}\CommonConfig; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\Host\dist\*; DestDir: {app}\HostExe; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\MobileKit\dist\*; DestDir: {app}\AnalyzerServerExe; Flags: recursesubdirs replacesameversion
Source: {#resourceDir}\*.ico; DestDir: {app}\HostExe; Flags: replacesameversion
Source: {#resourceDir}\MSVCP71.DLL; DestDir: {sys}; Flags: replacesameversion; AfterInstall: MyAfterInstall
Source: {#resourceDir}\{#installerType}\installerSignature.txt; DestDir: {app}; Flags: recursesubdirs replacesameversion
Source: {#resourceDir}\DatViewer\*; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion

[Tasks]
Name: LibUSB; Description: Install USB driver

[Icons]


Name: {userdesktop}\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#controllerIcon}
Name: {userdesktop}\Diagnostics\Stop Instrument; Filename: {app}\HostExe\StopSupervisor.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Cancel.ico



Name: {userdesktop}\Integration\EEPROM Access; Filename: {app}\HostExe\InstrEEPROMAccess.exe; Parameters: -c ..\CommonConfig\Config\Utilities\InstrEEPROMAccess.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}

Name: {userdesktop}\Integration\Integration Backup; Filename: {app}\HostExe\IntegrationBackup.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}
Name: {userdesktop}\Integration\Configuration Tool; Filename: R:\crd\TestSoftware\Configuration\ConfigTool.py; WorkingDir: R:\crd\TestSoftware\Configuration; IconFilename: {app}\HostExe\{#integrationIcon}

Name: {userdesktop}\Picarro Utilities\Data File Viewer; Filename: C:\Python25\python.exe; Parameters: DatViewer.py -c DatViewer.ini; WorkingDir: {app}\DatViewer; IconFilename: {app}\HostExe\{#utilitiesIcon}

Name: {group}\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#controllerIcon}
Name: {group}\Stop Instrument; Filename: {app}\HostExe\StopSupervisor.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Cancel.ico
Name: {userstartup}\Start Instrument; Filename: {app}\HostExe\RestartSupervisor.exe; Parameters: -c ..\AppConfig\Config\Utilities\RestartSupervisor.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

; Remove any previous startup items that referenced Supervisor.exe since we use
; the RestartSupervisor now.
[InstallDelete]
Type: files; Name: "{userstartup}\Start Instrument"