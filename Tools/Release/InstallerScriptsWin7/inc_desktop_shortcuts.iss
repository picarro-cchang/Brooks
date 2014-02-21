; Desktop shortcuts, Start menu, and run at startup items that are common to all apps
;
; Notes:
;   1.  inc_icons.iss must be included before this file (defines icons used by this file)
;
;   2.  The following variables should be defined before this file is included (required
;       indicates they must be defined):
;
;           variable name                           description
;           =============                           ===========
;           quickGuiIni (optional)                  QuickGui.exe ini filename
;           dataRecalIni (optional)                 DataRecal.exe ini filename
;           supervisorLauncherIni (required)        SupervisorLauncher.exe ini filename
;           supervisorLauncherIntegIni (required)   Integration mode SupervisorLauncher ini filename
;           diagDataCollectorIni (required)         DiagDataCollecter.exe ini filename
;           setupToolIni (required)                 SetupTool.exe ini filename
;
;   3.  To support Flux instruments, which require unique shortcut names,
;       there are variables you can use to create shortcuts for QuickGui
;       and DataRecal (in which case don't define quickGuiIni or dataRecalIni). These
;       variables specify the shortcut title and the ini filename.
;
;           variable name                           description
;           =============                           ===========
;           quickGuiIni1 (optional)                 QuickGui.exe ini filename
;           quickGuiTitle1                          shortcut title (required if quickGuiIni1 is set)
;
;           quickGuiIni2, quickGuiTitle2            additional optional QuickGui shortcut ini filename/title
;           quickGuiIni3, quickGuiTitle3
;           quickGuiIni4, quickGuiTitle4
;
;           dataRecalIni1 (optional)                DataRecal.exe ini filename
;           dataRecalTitle1                         shortcut title (required if dataRecalIni1 is set)
;
;           dataRecalIni2, dataRecalTitle2          additonal optional shortcut ini filename/title
;
;   4.  The shortcut for ConfigTool.py is created in inc_configtool.iss (not here).


[Icons]

; Shortcuts on the desktop
Name: {userdesktop}\Start Instrument; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -a -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
Name: {userdesktop}\Picarro Mode Switcher; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
Name: {userdesktop}\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#controllerIcon}


; Diagnostics folder
; 

Name: {userdesktop}\Diagnostics\Stop Instrument; Filename: {app}\HostExe\StopSupervisor.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Cancel.ico

#ifdef quickGuiIni
Name: {userdesktop}\Diagnostics\User Interface; Filename: {app}\HostExe\QuickGui.exe; Parameters: -c ..\AppConfig\Config\QuickGui\{#quickGuiIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
#endif

#ifdef quickGuiIni1
Name: {userdesktop}\Diagnostics\{#quickGuiTitle1}; Filename: {app}\HostExe\QuickGui.exe; Parameters: -c ..\AppConfig\Config\QuickGui\{#quickGuiIni1}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
#endif

#ifdef quickGuiIni2
Name: {userdesktop}\Diagnostics\{#quickGuiTitle2}; Filename: {app}\HostExe\QuickGui.exe; Parameters: -c ..\AppConfig\Config\QuickGui\{#quickGuiIni2}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
#endif

#ifdef quickGuiIni3
Name: {userdesktop}\Diagnostics\{#quickGuiTitle3}; Filename: {app}\HostExe\QuickGui.exe; Parameters: -c ..\AppConfig\Config\QuickGui\{#quickGuiIni3}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
#endif

#ifdef quickGuiIni4
Name: {userdesktop}\Diagnostics\{#quickGuiTitle4}; Filename: {app}\HostExe\QuickGui.exe; Parameters: -c ..\AppConfig\Config\QuickGui\{#quickGuiIni4}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
#endif


Name: {userdesktop}\Diagnostics\Diag Data Collector; Filename: {app}\HostExe\DiagDataCollector.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#diagDataCollectorIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}


; Integration folder
;

Name: {userdesktop}\Integration\Integration Mode Switcher; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIntegIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}

; This references a specific INI file, but all installers
; use the same one so no define for it
Name: {userdesktop}\Integration\EEPROM Access; Filename: {app}\HostExe\InstrEEPROMAccess.exe; Parameters: -c ..\CommonConfig\Config\Utilities\InstrEEPROMAccess.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}


Name: {userdesktop}\Integration\Integration Tool; Filename: {app}\HostExe\IntegrationTool.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}


Name: {userdesktop}\Integration\Integration Backup; Filename: {app}\HostExe\IntegrationBackup.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}


; Picarro Utilities folder
;
; Note: dataRecalIni must be defined before this file is included

Name: {userdesktop}\Picarro Utilities\Setup Tool; Filename: {app}\HostExe\SetupTool.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#setupToolIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#utilitiesIcon}

#ifdef dataRecalIni
Name: {userdesktop}\Picarro Utilities\Data Recal; Filename: {app}\HostExe\DataRecal.exe; Parameters: -c ..\InstrConfig\Calibration\InstrCal\{#dataRecalIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#utilitiesIcon}
#endif

#ifdef dataRecalIni1
Name: {userdesktop}\Picarro Utilities\{#dataRecalTitle1}; Filename: {app}\HostExe\DataRecal.exe; Parameters: -c ..\InstrConfig\Calibration\InstrCal\{#dataRecalIni1}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#utilitiesIcon}
#endif

#ifdef dataRecalIni2
Name: {userdesktop}\Picarro Utilities\{#dataRecalTitle2}; Filename: {app}\HostExe\DataRecal.exe; Parameters: -c ..\InstrConfig\Calibration\InstrCal\{#dataRecalIni2}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#utilitiesIcon}
#endif

#ifdef dataRecalIni3
Name: {userdesktop}\Picarro Utilities\{#dataRecalTitle3}; Filename: {app}\HostExe\DataRecal.exe; Parameters: -c ..\InstrConfig\Calibration\InstrCal\{#dataRecalIni3}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#utilitiesIcon}
#endif

; Start menu

Name: {group}\Picarro Mode Switcher; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
Name: {group}\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#controllerIcon}
Name: {group}\Stop Instrument; Filename: {app}\HostExe\StopSupervisor.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Cancel.ico

; Startup
;
; Executed when system is started

Name: {userstartup}\Start Instrument; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -a -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}


; Workaround so apps with UI display an icon in the taskbar as the
; Win7 default icon looks tacky

Name: {app}\HostExe\ConfigManager; Filename: {app}\HostExe\ConfigManager.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

Name: {app}\HostExe\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

Name: {app}\HostExe\QuickGui; Filename: {app}\HostExe\QuickGui.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

; TODO: after ensuring the above works, add the following shortcuts:
;       (these are all apps with Windows UI, according to PicarroExeSetup.py)
;
; Coordinator, Controller,deltaCorrProcessor, dilutionCorrProcessor
; StopSupervisor, IPV, IPVLicense, DiagDataCollector, supervisorLauncher,
; HostStartup, CoordinatorLauncher, FluxScheduler, FluxSwitcherGui,
; ValveDisplay, InstrEEPROMAccess, DataRecal, SetupTool,PicarroKML,
; ReadGPSWS, PeriphModeSwitcher, RecipeEditor, AircraftValveSwitcher

