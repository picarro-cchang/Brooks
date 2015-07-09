; setup_ChemCorrect.iss
;
; Main Win7 ChemCorrect installer script
;
;   1. May need a WinXP version. It probably needs to include MSVCRT71.DLL (though really
;      is a system file not local).
;
;      Currently MSVCRT71.DLL is included in the DLL list in chemcorrectSetup.py for WinXP
;      builds so don't need to include it below.


#define chemCorrectIcon = "ChemCorrect.ico"

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro PostProcess
AppVerName=Picarro G2000 Win7 ChemCorrect {#chemCorrectVersion}
Password=
DefaultDirName=C:\Picarro\PostProcess
DefaultGroupName=Picarro PostProcess
OutputBaseFileName=setup_postprocess_{#chemcorrectVersion}
DirExistsWarning=no
AppVersion={#productVersion}

; Windows 7 SP 1 or higher is required
MinVersion=6.1.7601

[Files]

; Program
Source:  {#distDir}\ChemCorrectExe\*; DestDir: {app}\ChemCorrectExe; Flags: recursesubdirs replacesameversion

; icon files
Source:  {#distDir}\Assets\icons\{#chemCorrectIcon}; DestDir: {app}\ChemCorrectExe; Flags: replacesameversion


[Icons]

; Desktop shortcuts
Name: {userdesktop}\PostProcess ChemCorrect; Filename: {app}\ChemCorrectExe\ChemCorrect.exe; WorkingDir: {app}\ChemCorrectExe; IconFilename: {app}\ChemCorrectExe\{#chemCorrectIcon}


; Start menu

Name: {group}\ChemCorrect; Filename: {app}\ChemCorrectExe\ChemCorrect.exe; WorkingDir: {app}\ChemCorrectExe; IconFilename: {app}\ChemCorrectExe\{#chemCorrectIcon}

