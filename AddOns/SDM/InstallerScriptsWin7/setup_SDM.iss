; setup_SDM.iss
;
; Main Win7 SDM installer script


#define sdmIcon = "EnviroSense.ico"

[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro SDM
AppVerName=Picarro G2000 Win7 SDM {#sdmVersion}
Password=
DefaultDirName=C:\Picarro
DefaultGroupName=Picarro SDM
OutputBaseFileName=setup_{#sdmVersion}
DirExistsWarning=no

VersionInfoCompany=Picarro Inc.
VersionInfoVersion={#installerVersion}
VersionInfoProductName=Picarro G2000 SDM
VersionInfoProductTextVersion={#productVersion}
VersionInfoCopyright=Copyright (C) 2009-2014 Picarro Inc.

; Windows 7 SP 1 or higher is required
MinVersion=6.1.7601

[Files]

; Program
Source: {#sandboxDir}\host\AddOns\SDM\DataProcessor\dist\*; DestDir: {app}\SyringePump\DataProcessor; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\SDM\Priming\dist\*; DestDir: {app}\SyringePump\Priming; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\SDM\Sequencer\dist\*; DestDir: {app}\SyringePump\Sequencer; Flags: recursesubdirs replacesameversion

; icon files
Source: {#sandboxDir}\host\Assets\icons\{#sdmIcon}; DestDir: {app}\SyringePump\DataProcessor; Flags: replacesameversion
Source: {#sandboxDir}\host\Assets\icons\{#sdmIcon}; DestDir: {app}\SyringePump\Priming; Flags: replacesameversion
Source: {#sandboxDir}\host\Assets\icons\{#sdmIcon}; DestDir: {app}\SyringePump\Sequence; Flags: replacesameversion

; Coordinator launcher, does not replace existing (TODO: update existing)
Source: {#sandboxDir}\host\AddOns\SDM\CoordinatorLauncher.ini; DestDir: {app}\G2000\AppConfig\Config\Utilities; Flags: onlyifdoesntexist


[Icons]

; Desktop shortcuts
Name: {userdesktop}\SDM Data Processor; Filename: {app}\SyringePump\DataProcessor\PumpDataProcessor.exe; WorkingDir: {app}\SyringePump\DataProcessor; IconFilename: {app}\SyringePump\DataProcessor\{#sdmIcon}

Name: {userdesktop}\SDM Priming; Filename: {app}\SyringePump\Priming\CentrisPumpPriming.exe; WorkingDir: {app}\SyringePump\Priming; IconFilename: {app}\SyringePump\Priming\{#sdmIcon}

Name: {userdesktop}\SDM Pump Sequencer; Filename: {app}\SyringePump\Sequencer\PumpSequencer.exe; WorkingDir: {app}\SyringePump\Sequencer; IconFilename: {app}\SyringePump\Sequencer\{#sdmIcon}


; Start menu

Name: {group}\Data Processor; Filename: {app}\SyringePump\DataProcessor\PumpDataProcessor.exe; WorkingDir: {app}\SyringePump\DataProcessor; IconFilename: {app}\SyringePump\DataProcessor\{#sdmIcon}

Name: {group}\Priming; Filename: {app}\SyringePump\Priming\CentrisPumpPriming.exe; WorkingDir: {app}\SyringePump\Priming; IconFilename: {app}\SyringePump\Priming\{#sdmIcon}

Name: {group}\Pump Sequencer; Filename: {app}\SyringePump\Sequencer\PumpSequencer.exe; WorkingDir: {app}\SyringePump\Sequencer; IconFilename: {app}\SyringePump\Sequencer\{#sdmIcon}

