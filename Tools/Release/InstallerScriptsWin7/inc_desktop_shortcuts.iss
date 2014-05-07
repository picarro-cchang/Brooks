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
;           closeValves (optional)                  if set, -v option used for Mode Switcher (running
;                                                   SupervisorLauncher)
;
;           noStartInst (optional)                  if set, startup shortcut for Start Instrument is
;                                                   NOT created (only FDDS sets this def)
;
;           integToolIni (optional)                 IntegrationTool.exe ini filename (use -c option if
;                                                   defined, else option not used)
;
;           valveDisplayIni (optional)              ValveDisplay.exe ini filename
;
;   3.  To support Flux instruments, which require unique shortcut names,
;       there are variables you can use to create shortcuts for QuickGui and DataRecal
;       (then don't define quickGuiIni and dataRecalIni). These variables specify
;       the shortcut title and the ini filename.
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
;           dataRecalIni2, dataRecalTitle2          additional optional shortcut ini filename/title
;
;   4.  The shortcut for ConfigTool.py is created in inc_configtool.iss (not here).


#ifdef closeValves
#define closeValvesOpt = "-v"
#else
#define closeValvesOpt = ""
#endif


[Icons]

; Shortcuts on the desktop
Name: {userdesktop}\Start Instrument; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -a -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

Name: {userdesktop}\Picarro Mode Switcher; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: {#closeValvesOpt} -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

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

#ifdef valveDisplayIni
Name: {userdesktop}\Diagnostics\Valve Display; Filename: {app}\HostExe\ValveDisplay.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#valveDisplayIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
#endif

; Integration folder
;
; Integration shortcuts are installed under the desktop Diagnostics folder

Name: {userdesktop}\Diagnostics\Integration\Integration Mode Switcher; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIntegIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}



; All installers reference the same INI file
Name: {userdesktop}\Diagnostics\Integration\EEPROM Access; Filename: {app}\HostExe\InstrEEPROMAccess.exe; Parameters: -c ..\CommonConfig\Config\Utilities\InstrEEPROMAccess.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}


; Shortcut uses -c option if the integration tool ini filename is defined
#ifdef integToolIni
Name: {userdesktop}\Diagnostics\Integration\Integration Tool; Filename: {app}\HostExe\IntegrationTool.exe; Parameters: -c ..\CommonConfig\Config\Utilities\{#integToolIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}
#else
Name: {userdesktop}\Diagnostics\Integration\Integration Tool; Filename: {app}\HostExe\IntegrationTool.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}
#endif


Name: {userdesktop}\Diagnostics\Integration\Integration Backup; Filename: {app}\HostExe\IntegrationBackup.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}

; ConfigManager shortcuts for user launcher and integration launcher
Name: {userdesktop}\Diagnostics\Integration\ConfigManager; Filename: {app}\HostExe\ConfigManager.exe; Parameters: -l ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}

Name: {userdesktop}\Diagnostics\Integration\Integration ConfigManager; Filename: {app}\HostExe\ConfigManager.exe; Parameters: -l ..\AppConfig\Config\Utilities\{#supervisorLauncherIntegIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}


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

Name: {group}\Mode Switcher; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: {#closeValvesOpt} -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

Name: {group}\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#controllerIcon}

Name: {group}\Stop Instrument; Filename: {app}\HostExe\StopSupervisor.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Cancel.ico

; Startup
;
; Executed when system is started - only FDDS defines noStartInst so everything else includes this

#ifndef noStartInst
Name: {userstartup}\Start Instrument; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -a -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
#endif


; Workaround so apps with UI display an icon in the taskbar as the
; Win7 default icon looks tacky

Name: {app}\HostExe\ConfigManager; Filename: {app}\HostExe\ConfigManager.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

Name: {app}\HostExe\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

Name: {app}\HostExe\QuickGui; Filename: {app}\HostExe\QuickGui.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}

; TODO: after ensuring the above works, add the following shortcuts as needed for the apps:
;       (these are all apps with Windows UI, according to PicarroExeSetup.py)
;
; deltaCorrProcessor, dilutionCorrProcessor
; IPV, IPVLicense,
; HostStartup, CoordinatorLauncher, FluxScheduler, FluxSwitcherGui,
; PicarroKML,
; ReadGPSWS, PeriphModeSwitcher, RecipeEditor, AircraftValveSwitcher

