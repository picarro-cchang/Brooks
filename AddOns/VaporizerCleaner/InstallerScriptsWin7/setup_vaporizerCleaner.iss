; Main Win7 VaporizerCleaner installer script
;
; This could go in the VaporizerCleaner folder if there is only one (or two, one for win7 and another winxp)
;
;
; TODO:
;   1. Is there a way to add custom text to the Welcome page? It should instruct the user to disconnect the USB cable
;      before starting the installation.
;
;   2. May need a WinXP version. It probably needs to include MSVCRT71.DLL (though really is a system file not local).
;      Currently MSVCRT71.DLL is included in the DLL list in vaporizerCleanerSetup.py so don't need to include it below.


#define utilitiesIcon = "Utilities_icon.ico"
#define userManual = "Vaporizer Cleaning Procedure 2-17-10.pdf"

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro G2000 Vaporizer Cleaner
AppVerName=Picarro G2000 Win7 Vaporizer Cleaner {#vaporizerCleanerVersion}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro Vaporizer Cleaner
OutputBaseFileName=setup_{#vaporizerCleanerVersion}
DirExistsWarning=no

; Windows 7 SP 1 or higher is required
MinVersion=6.1.7601

[Files]

; Program
Source: {#sandboxDir}\host\AddOns\VaporizerCleaner\dist\*; DestDir: {app}\VaporizerCleanerExe; Flags: recursesubdirs replacesameversion

; User manual
Source: "{#sandboxDir}\host\AddOns\VaporizerCleaner\{#userManual}"; DestDir: {app}\AddOns\VaporizerCleanerExe; Flags: replacesameversion


; icon files
Source: {#sandboxDir}\host\Assets\icons\{#utilitiesIcon}; DestDir: {app}\VaporizerCleanerExe; Flags: replacesameversion


[Icons]

; Desktop shortcuts
Name: {userdesktop}\Picarro Utilities\VaporizerCleaner; Filename: {app}\VaporizerCleanerExe\VaporizerCleaner.exe; WorkingDir: {app}\VaporizerCleanerExe; IconFilename: {app}\VaporizerCleanerExe\{#utilitiesIcon}


; Start menu
Name: {group}\Vaporizer Cleaner; Filename: {app}\VaporizerCleanerExe\VaporizerCleaner.exe; WorkingDir: {app}\VaporizerCleanerExe; IconFilename: {app}\VaporizerCleanerExe\{#utilitiesIcon}

Name: {group}\Vaporizer Cleaning Procedure; Filename: {app}\VaporizerCleanerExe\{#userManual}; WorkingDir: {app}\VaporizerCleanerExe

; TODO
