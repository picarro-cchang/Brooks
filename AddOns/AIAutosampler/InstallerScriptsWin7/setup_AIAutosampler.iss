; Main Win7 Autosampler installer script
;
; This could go in the AIAutosampler folder if there is only one (or two, one for win7 and another winxp)
;
;
; TODO:
;   1. Is there a way to add custom text to the Welcome page? It should instruct the user to disconnect the USB cable
;      before starting the installation.
;
;   2. May need a WinXP version. It probably needs to include MSVCRT71.DLL (though really is a system file not local).
;      Currently MSVCRT71.DLL is included in the DLL list in autosamplerSetup.py so don't need to include it below.


#define utilitiesIcon = "Utilities_icon.ico"

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro G2000 Autosampler
AppVerName=Picarro G2000 Win7 Autosampler {#autosamplerVersion}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro Autosampler
OutputBaseFileName=setup_{#autosamplerVersion}
DirExistsWarning=no

;[Types]
;Name: "full"; Description: "Full installation"
;Name: "custom"; Description: "Custom installation"; Flags: iscustom

;[Components]
;Name: "program"; Description: "Program Files"; Types: full custom; Flags: fixed
;Name: "coord"; Description: "Coordinator Files"; Types: full
;Name: "coord\HIDS"; Description: "HIDS Coordinator Files"; Flags: exclusive
;Name: "coord\HBDS"; Description: "HBDS Coordinator Files"; Flags: exclusive

[Files]

; add this back to the modules below to support component installs: Components: program;
; Program
Source: {#sandboxDir}\host\AddOns\AIAutosampler\dist\*; DestDir: {app}\AutosamplerExe; Flags: recursesubdirs replacesameversion

; Training module
Source: {#sandboxDir}\host\Vendor\Applied Instruments\ALS-G\x86\Picarro_Training_Utility.exe; DestDir: {app}\AutosamplerExe; Flags: replacesameversion

; USB-COM Port Driver installer
Source: {#sandboxDir}\host\Vendor\Applied Instruments\ALS-G\x86\CDM20824_Setup.exe; DestDir: {app}\AutosamplerExe; Flags: replacesameversion

; icon files
Source: {#sandboxDir}\host\Assets\icons\{#utilitiesIcon}; DestDir: {app}\AutosamplerExe; Flags: replacesameversion


[Icons]

; Desktop shortcuts
Name: {userdesktop}\Autosampler Control; Filename: {app}\AutosamplerExe\Autosampler.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\{#utilitiesIcon}

Name: {userdesktop}\Autosampler Training; Filename: {app}\AutosamplerExe\Picarro_Training_Utility.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\Picarro_Training_Utility.exe

; Start menu

Name: {group}\Autosampler Control; Filename: {app}\AutosamplerExe\Autosampler.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\{#utilitiesIcon}

Name: {group}\Autosampler Training; Filename: {app}\AutosamplerExe\Picarro_Training_Utility.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\Picarro_Training_Utility.exe

