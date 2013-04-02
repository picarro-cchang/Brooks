
[Setup]
AppCopyright=Picarro Inc.
AppName=Picarro SSIM AddOn Installer
AppVerName=Version {#version}
Password=
DefaultDirName=C:\Picarro\G2000
DefaultGroupName=Picarro SSIM Software
OutputBaseFileName=setup_SSIM_{#version}
DirExistsWarning=no
OutputDir=.

[Components]
Name: "G2101i_CBDS"; Description: "Isotopic CO2"; Types: g2101i_cbds; Flags: fixed
Name: "G2101i_CFFDS"; Description: "Isotopic CO2 with CH4 correction"; Types: g2101i_cffds; Flags: fixed
Name: "G2132i"; Description: "Isotopic CH4"; Types: g2132i; Flags: fixed
Name: "G2201i"; Description: "Isotopic CO2 and isotopic CH4"; Types: g2201i; Flags: fixed
Name: "G2131i"; Description: "Isotopic CO2 with CH4 correction"; Types: g2131i; Flags: fixed

[Types]
Name: "g2101i_cbds"; Description: "G2101-i (Serial #: CBDS-2xxx)"
Name: "g2101i_cffds"; Description: "G2101-i (Serial #: CFFDS-2xxx)"
Name: "g2131i"; Description: "G2131-i"
Name: "g2132i"; Description: "G2132-i"
Name: "g2201i"; Description: "G2201-i"

[Files]
; CBDS
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_CBDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CBDS
Source: {#sandboxDir}\host\AddOns\SSIM\CoordinatorLauncher_SSIM_G2101-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CBDS

; CFFDS
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_CFFDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CFFDS
Source: {#sandboxDir}\host\AddOns\SSIM\CoordinatorLauncher_SSIM_G2101-i_CH4.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CFFDS

; CBDS + CFFDS
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_RT_G2101-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CBDS G2101i_CFFDS

; FCDS
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_FCDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2132i
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_RT_G2132-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2132i
Source: {#sandboxDir}\host\AddOns\SSIM\CoordinatorLauncher_SSIM_G2132-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2132i

; CFIDS
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_CFIDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2201i
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_RT_G2201-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2201i
Source: {#sandboxDir}\host\AddOns\SSIM\CoordinatorLauncher_SSIM_G2201-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2201i

; CFGDS
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_CFGDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2131i
Source: {#sandboxDir}\host\AddOns\SSIM\CoordinatorLauncher_SSIM_G2131-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2131i
Source: {#sandboxDir}\host\AddOns\SSIM\Coordinator_SSIM_RT_G2131-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2131i

Source: "{#sandboxDir}\host\AddOns\SSIM\Small_Sample_Isotope_Module_Manual Rev 1-22-13.pdf"; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion
Source: {#sandboxDir}\host\AddOns\SSIM\ReadExtSensor.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion
Source: {#sandboxDir}\host\AddOns\SSIM\ReferenceGases.ini; DestDir: {app}\AddOns\SSIM; Flags: confirmoverwrite

[Icons]
Name: "{userdesktop}\SSIM Coordinator Launcher"; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c {app}\AddOns\SSIM\CoordinatorLauncher_SSIM_G2101-i.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico; Components: G2101i_CBDS
Name: "{userdesktop}\SSIM Coordinator Launcher"; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c {app}\AddOns\SSIM\CoordinatorLauncher_SSIM_G2101-i_CH4.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico; Components: G2101i_CFFDS
Name: "{userdesktop}\SSIM Coordinator Launcher"; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c {app}\AddOns\SSIM\CoordinatorLauncher_SSIM_G2132-i.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico; Components: G2132i
Name: "{userdesktop}\SSIM Coordinator Launcher"; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c {app}\AddOns\SSIM\CoordinatorLauncher_SSIM_G2201-i.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico; Components: G2201i

Name: {userdesktop}\Read SSIM Pressure; Filename: {app}\HostExe\ReadExtSensor.exe; Parameters: -c {app}\AddOns\SSIM\ReadExtSensor.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico
