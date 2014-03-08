; Common [Setup] section stuff

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro G2000 {#installerType} Host
AppVerName=Picarro G2000 Win7 {#installerType} Host {#hostVersion}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro Analyzer Software
OutputBaseFileName=setup_{#installerType}_{#commonName}_{#hostVersion}
DirExistsWarning=no

; We could limit installs to WinXP but since earlier installers never had
; any restrictions leaving this out.
;
; WinXP is 5.1.2600
; OnlyBelowVersion=5.2
