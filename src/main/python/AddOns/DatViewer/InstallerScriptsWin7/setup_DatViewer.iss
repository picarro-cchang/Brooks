; DatViewer installer
;
; Currently this is distributed as source code so works for either WinXP or Win7

; TODO: use MinVersion or OnlyBelowVersion for the shortcut since depends on Python version installed


;  5.0.2195    Windows 2000
;  5.1.2600    Windows XP or Windows XP 64-Bit Edition Version 2002 (Itanium)
;  5.2.3790    Windows Server 2003 or Windows XP x64 Edition (AMD64/EM64T) or Windows XP 64-Bit Edition Version 2003 (Itanium)
;  6.0.6000    Windows Vista
;  6.0.6001    Windows Vista with Service Pack 1 or Windows Server 2008
;  6.1.7600    Windows 7 or Windows Server 2008 R2
;  6.1.7601    Windows 7 with Service Pack 1 or Windows Server 2008 R2 with Service Pack 1
;  6.2.9200    Windows 8 or Windows Server 2012
;  6.3.9200    Windows 8.1 or Windows Server 2012 R2

; What matters more here what is the Python version installed, need Pascal code to detect this
; Used to create shortcut

#define diagnosticsIcon = "Diagnostics_icon.ico"

; Common [Setup] section stuff

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro DatViewer
AppVerName=Picarro DatViewer {#datViewerVersion}
Password=
DefaultDirName=C:\Picarro\G2000
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
; Program
Source: {#sandboxDir}\AddOns\DatViewer\DatViewer.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\DatViewerLib.pyd; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\DateRangeSelectorFrame.pyd; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\Analysis.pyd; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\FileOperations.pyd; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\timestamp.pyd; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\CustomConfigObj.pyd; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
; Manual
Source: {#sandboxDir}\AddOns\DatViewer\Manual\*; DestDir: {app}\DatViewer\Manual; Flags: recursesubdirs replacesameversion
; tzlocal
Source: {#sandboxDir}\AddOns\DatViewer\tzlocal\*; DestDir: C:\Python27\Lib\site-packages\tzlocal; Flags: recursesubdirs replacesameversion
; Resources
Source: {#sandboxDir}\AddOns\DatViewer\Scripts\*; DestDir: {app}\DatViewer\Scripts; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\datViewer.ini; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Assets\icons\{#diagnosticsIcon}; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion

[Icons]

Name: {userdesktop}\Picarro Utilities\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: {app}\DatViewer\DatViewer.pyc; WorkingDir: {app}\DatViewer; IconFilename: {app}\DatViewer\{#diagnosticsIcon}
Name: {userdesktop}\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: {app}\DatViewer\DatViewer.pyc; WorkingDir: {app}\DatViewer; IconFilename: {app}\DatViewer\{#diagnosticsIcon}