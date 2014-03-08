; Coordinator configurations for analyzers that include this capability
;
; Notes: 
;         1. Define coordinatorLauncherIni with the filename to create the Coordinator Launcher shortcut.
;
;         2. All apps currently get the Integration Coordinator Launcher shortcut, but it can be omitted
;            by not defining coordinatorLauncherIntegIni.


[Icons]

#ifdef coordinatorLauncherIni
Name: {userdesktop}\Coordinator Launcher; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#coordinatorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
#endif


; Integration

#ifdef coordinatorLauncherIntegIni
Name: {userdesktop}\Integration\Integration Coordinator Launcher; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#coordinatorLauncherIntegIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}
#endif


; Start menu

#ifdef coordinatorLauncherIni
Name: {group}\Coordinator Launcher; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#coordinatorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
#endif
