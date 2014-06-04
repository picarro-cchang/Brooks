; DatViewer installer
;
; Currently this is distributed as source code so works for either WinXP or Win7

#define utilitiesIcon = "Utilities_icon.ico"

; Common [Setup] section stuff

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro DatViewer
AppVerName=Picarro DatViewer {#datViewerVersion}
Password=
DefaultDirName=C:\Picarro\Utilities
DefaultGroupName=Picarro Utilities
OutputBaseFileName=setup_DatViewer_{#datViewerVersion}
DirExistsWarning=no
VersionInfoCompany=Picarro Inc.
VersionInfoVersion={#datViewerVersion}
VersionInfoProductName=Picarro DatViewer
VersionInfoProductTextVersion={#datViewerVersion}
VersionInfoCopyright=Copyright (C) {#productYear} Picarro Inc.

; NO MIN VERSION REQUIREMENT
; Windows 7 SP 1 or higher is required
;MinVersion=6.1.7601


[Files]

Source: {#sandboxDir}\Host\DatViewer\DatViewer.py; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Host\DatViewer\datViewer.ini; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Assets\icons\{#utilitiesIcon}; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion


[Icons]

Name: {userdesktop}\Picarro Utilities\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: {app}\DatViewer\DatViewer.py -c DatViewer.ini; WorkingDir: {app}\DatViewer; IconFilename: {app}\DatViewer\{#utilitiesIcon}
