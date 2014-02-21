; Coordinator configurations for analyzers that include this capability
;
; Note: coordinatorLauncherIni must be defined before this file is included


[Icons]

#ifdef coordinatorLauncherIni
Name: {userdesktop}\Coordinator Launcher; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#coordinatorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
#endif


; Integration

Name: {userdesktop}\Integration\Integration Coordinator Launcher; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#coordinatorLauncherIntegIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#integrationIcon}


; Start menu

Name: {group}\Coordinator Launcher; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c ..\AppConfig\Config\Utilities\{#coordinatorLauncherIni}; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\{#picarroIcon}
