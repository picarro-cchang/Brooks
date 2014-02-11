; Common code to populate files into the configs and HostExe folders


[Files]
Source: {#sandboxDir}\{#installerType}\*; DestDir: {app}; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\CommonConfig\*; DestDir: {app}\CommonConfig; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\Host\dist\*; DestDir: {app}\HostExe; Flags: recursesubdirs replacesameversion
Source: {#resourceDir}\*.ico; DestDir: {app}\HostExe; Flags: replacesameversion
Source: {#resourceDir}\{#installerType}\installerSignature.txt; DestDir: {app}; Flags: recursesubdirs replacesameversion

