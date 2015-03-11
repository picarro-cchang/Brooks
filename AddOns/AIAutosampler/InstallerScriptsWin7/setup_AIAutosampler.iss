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
; #define autosamplerVersion = "3.0"
; #define sandboxDir = "C:\Picarro\G2000"

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro G2000 Autosampler
AppVerName=Picarro G2000 Win7 Autosampler {#autosamplerVersion}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro Autosampler
OutputBaseFileName=setup_{#autosamplerVersion}
DirExistsWarning=no

; Windows 7 SP 1 or higher is required
MinVersion=6.1.7601

[Files]

; Program
Source: {#sandboxDir}\AddOns\AIAutosampler\dist\*; DestDir: {app}\AutosamplerExe; Flags: recursesubdirs replacesameversion

; Training module
Source: {#sandboxDir}\Vendor\Applied Instruments\ALS-G\x86\Picarro_Training.exe; DestDir: {app}\AutosamplerExe; Flags: replacesameversion

; USB-COM to Serial Port Driver installer
Source: {#sandboxDir}\Vendor\FTDI\CDM 2.08.30 WHQL Certified\CDM v2.08.30 WHQL Certified.exe; DestDir: {app}\AutosamplerExe; Flags: replacesameversion

; icon files
Source: {#sandboxDir}\Assets\icons\{#utilitiesIcon}; DestDir: {app}\AutosamplerExe; Flags: replacesameversion

[Icons]

; Desktop shortcuts
Name: {userdesktop}\Autosampler Control; Filename: {app}\AutosamplerExe\Autosampler.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\{#utilitiesIcon}

Name: {userdesktop}\Autosampler Training; Filename: {app}\AutosamplerExe\Picarro_Training.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\Picarro_Training.exe

; Start menu

Name: {group}\Autosampler Control; Filename: {app}\AutosamplerExe\Autosampler.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\{#utilitiesIcon}

Name: {group}\Autosampler Training; Filename: {app}\AutosamplerExe\Picarro_Training.exe; WorkingDir: {app}\AutosamplerExe; IconFilename: {app}\AutosamplerExe\Picarro_Training.exe

