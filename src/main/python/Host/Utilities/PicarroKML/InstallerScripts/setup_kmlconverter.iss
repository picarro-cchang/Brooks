; KMLConverter installer
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

#define utilitiesIcon = "Utilities_icon.ico"

; Common [Setup] section stuff

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro KML Converter
AppVerName=Picarro KML Converter {#kmlConverterVersion}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro Utilities
OutputBaseFileName=setup_KMLConverter_{#kmlConverterVersion}
DirExistsWarning=no
VersionInfoCompany=Picarro Inc.
VersionInfoVersion={#kmlConverterVersion}
VersionInfoProductName=Picarro KML Converter
VersionInfoProductTextVersion={#kmlConverterVersion}
VersionInfoCopyright=Copyright (C) {#productYear} Picarro Inc.

; NO MIN VERSION REQUIREMENT
; Windows 7 SP 1 or higher is required
;MinVersion=6.1.7601


[Files]
; Program
Source: {#sandboxDir}\Host\Utilities\PicarroKML\KMLConverter.pyc; DestDir: {app}\KMLConverter; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Host\Utilities\PicarroKML\KMLConverterFrame.pyc; DestDir: {app}\KMLConverter; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Host\Utilities\PicarroKML\CustomConfigObj.pyc; DestDir: {app}\KMLConverter; Flags: recursesubdirs replacesameversion

; Resources
Source: {#sandboxDir}\Host\Utilities\PicarroKML\KMLConverter.ini; DestDir: {app}\KMLConverter; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Assets\icons\{#utilitiesIcon}; DestDir: {app}\KMLConverter; Flags: recursesubdirs replacesameversion

[Icons]
Name: {userdesktop}\KML Converter; Filename: C:\Python27\python.exe; Parameters: {app}\KMLConverter\KMLConverter.pyc; WorkingDir: {app}\KMLConverter; IconFilename: {app}\KMLConverter\{#utilitiesIcon}