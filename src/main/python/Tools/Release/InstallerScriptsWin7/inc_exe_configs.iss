; Common code to populate files into the configs and HostExe folders


[Files]

; Notes: Files are installed in the order they are listed below.
;
;        Backup and restore of InstrConfig backup and restore is piggybacked
;        onto installing the installerSignature.txt file. We can't call
;        MyBeforeInstall for the InstrConfig folder install because it gets
;        called for *every* file installed.

; StopSupervisor.exe
Source: {#sandboxDir}\Host\dist\StopSupervisor.exe; DestDir: {app}\HostExe; Flags: recursesubdirs replacesameversion; BeforeInstall: BeforeInstallStopSupervisor

; installerSignature.txt
Source: {#configDir}\{#installerType}\installerSignature.txt; DestDir: {app}; Flags: ignoreversion; BeforeInstall: MyBeforeInstall

; InstrConfig
Source: {#configDir}\{#installerType}\InstrConfig\*; DestDir: {app}\InstrConfig; Flags: recursesubdirs replacesameversion

; AppConfig
Source: {#configDir}\{#installerType}\AppConfig\*; DestDir: {app}\AppConfig; Flags: recursesubdirs replacesameversion

; install the signature file a second time in order to call MyAfterInstall
Source: {#configDir}\{#installerType}\installerSignature.txt; DestDir: {app}; Flags: ignoreversion; AfterInstall: MyAfterInstall

; CommonConfig
Source: {#configDir}\CommonConfig\*; DestDir: {app}\CommonConfig; Flags: recursesubdirs replacesameversion

; HostExe executables (icons handled by inc_icons.iss)
Source: {#distDir}\HostExe\*; DestDir: {app}\HostExe; Flags: recursesubdirs replacesameversion

