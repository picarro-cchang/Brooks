; Desktop shortcuts, Start menu, and run at startup items that are common to all apps
;
; Notes:
;   1.  inc_icons.iss must be included before this file (defines icons used by this file)
;   2.  the following must be defined before this file is included:
;           quickGuiIni
;           dataRecalIni
;           supervisorLauncherIni
;           supervisorLauncherIntegIni
;           diagDataCollectorIni
;           setupToolIni
;
;   3.  Shortcut for ConfigTool.py is created in inc_configtool.iss (not here).


[Icons]

; Shortcuts on the desktop
Name: {userdesktop}\Start Instrument; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -a -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
Name: {userdesktop}\Picarro Mode Switcher; Filename: {app}\HostExe\SupervisorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#supervisorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
Name: {userdesktop}\Controller; Filename: {app}\HostExe\Controller.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#controllerIcon}


; Diagnostics folder
; 
; Note: quickGuiIni must be defined before this file is included

Name: {userdesktop}\Diagnostics\Stop Instrument; Filename: {app}\HostExe\StopSupervisor.exe; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Cancel.ico
Name: {userdesktop}\Diagnostics\User Interface; Filename: {app}\HostExe\QuickGui.exe; Parameters: -c ..\AppConfig\Config\QuickGui\{#quickGuiIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#diagnosticsIcon}
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
Name: {userdesktop}\Picarro Utilities\Data Recal; Filename: {app}\HostExe\DataRecal.exe; Parameters: -c ..\InstrConfig\Calibration\InstrCal\{#dataRecalIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#utilitiesIcon}


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
;
; Coordinator, Controller,deltaCorrProcessor, dilutionCorrProcessor
; StopSupervisor, IPV, IPVLicense, DiagDataCollector, supervisorLauncher,
; HostStartup, CoordinatorLauncher, FluxScheduler,FluxSwitcherGui,
; ValveDisplay, InstrEEPROMAccess, DataRecal, SetupTool,PicarroKML,
; ReadGPSWS, PeriphModeSwitcher, RecipeEdito, AircraftValveSwitcher