; Main Win7 Autosampler installer script
;
; This could go in the AIAutosampler folder if there is only one (or two, one for win7 and another winxp)
;
; TODO:
;   1. Is there a way to add custom text to the Welcome page? It should instruct the user to disconnect the USB cable
;      before starting the installation.
;
;   2. May need a WinXP version. It probably needs to include MSVCRT71.DLL (though really is a system file not local).
;      Currently MSVCRT71.DLL is included in the DLL list in autosamplerSetup.py


#define utilitiesIcon = "Utilities_icon.ico"

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro G2000 Autosampler
AppVerName=Picarro G2000 Win7 Autosampler {#autosamplerVersion}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro Autosampler Software
OutputBaseFileName=setup_{#autosamplerVersion}
DirExistsWarning=no

[Types]
Name: "full"; Description: "Full installation"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "program"; Description: "Program Files"; Types: full custom; Flags: fixed
Name: "coord"; Description: "Coordinator Files"; Types: full
Name: "coord\HIDS"; Description: "HIDS Coordinator Files"; Flags: exclusive
Name: "coord\HBDS"; Description: "HBDS Coordinator Files"; Flags: exclusive
[Files]

; Program
Source: {#sandboxDir}\host\AddOns\AIAutosampler\dist\*; DestDir: {app}\AutosamplerExe; Components: program; Flags: recursesubdirs replacesameversion

; Training module
Source: {#sandboxDir}\host\Vendor\Applied Instruments\ALS-G\x86\Picarro_Training_Utility.exe; DestDir: {app}\AutosamplerExe; Components: program; Flags: replacesameversion

; USB-COM Port Driver installer
Source: {#sandboxDir}\host\Vendor\Applied Instruments\ALS-G\x86\CDM20824_Setup.exe; DestDir: {app}\AutosamplerExe; Components: program; Flags: replacesameversion

; icon files
Source: {#sandboxDir}\host\Assets\icons\{#utilitiesIcon}; DestDir: {app}\AutosamplerExe; Flags: replacesameversion

; HBDS Coordinators and launcher
Source: {#sandboxDir}\host\AddOns\AIAutosampler\HBDS\Coordinator\*; DestDir: {app}\AppConfig\Config\Coordinator; Components: coord\HBDS; Flags: replacesameversion
Source: {#sandboxDir}\host\AddOns\AIAutosampler\HBDS\CoordinatorLauncher.ini; DestDir: {app}\AppConfig\Config\Utilities; Components: coord\HBDS; Flags: replacesameversion

; HIDS Coordinators and launcher
Source: {#sandboxDir}\host\AddOns\AIAutosampler\HIDS\Coordinator\*; DestDir: {app}\AppConfig\Config\Coordinator; Components: coord\HIDS; Flags: replacesameversion
Source: {#sandboxDir}\host\AddOns\AIAutosampler\HIDS\CoordinatorLauncher.ini; DestDir: {app}\AppConfig\Config\Utilities; Components: coord\HIDS; Flags: replacesameversion


[Icons]

; Desktop shortcuts
Name: {userdesktop}\Autosampler Control; Filename: {app}\AutosamplerExe\Autosampler.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\{#utilitiesIcon}

Name: {userdesktop}\Autosampler Training; Filename: {app}\AutosamplerExe\Picarro_Training_Utility.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\Picarro_Training_Utility.exe