
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
Name: "G2101i_CBDS"; Description: "Isotopic CO2"; Types: g2101i; Flags: fixed
Name: "G2101i_CFFDS"; Description: "Isotopic CO2 with CH4 correction"; Types: g2101i; Flags: fixed
Name: "G2132i"; Description: "Isotopic CH4"; Types: g2132i; Flags: fixed
Name: "G2201i"; Description: "Isotopic CO2 and isotopic CH4"; Types: g2201i; Flags: fixed

[Types]
Name: "g2101i"; Description: "G2101-i"
Name: "g2132i"; Description: "G2132-i"
Name: "g2201i"; Description: "G2201-i"

[Files]
Source: {#sandboxDir}\trunk\AddOns\SSIM\Coordinator_SSIM_CBDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CBDS
Source: {#sandboxDir}\trunk\AddOns\SSIM\Coordinator_SSIM_CFFDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CFFDS
Source: {#sandboxDir}\trunk\AddOns\SSIM\Coordinator_SSIM_RT_G2101-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CBDS G2101i_CFFDS
Source: {#sandboxDir}\trunk\AddOns\SSIM\CoordinatorLauncher_SSIM_G2101-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2101i_CBDS G2101i_CFFDS

Source: {#sandboxDir}\trunk\AddOns\SSIM\Coordinator_SSIM_FCDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2132i
Source: {#sandboxDir}\trunk\AddOns\SSIM\Coordinator_SSIM_RT_G2132-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2132i
Source: {#sandboxDir}\trunk\AddOns\SSIM\CoordinatorLauncher_SSIM_G2132-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2132i


Source: {#sandboxDir}\trunk\AddOns\SSIM\Coordinator_SSIM_CFIDS.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2201i
Source: {#sandboxDir}\trunk\AddOns\SSIM\Coordinator_SSIM_RT_G2201-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2201i
Source: {#sandboxDir}\trunk\AddOns\SSIM\CoordinatorLauncher_SSIM_G2201-i.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion; Components: G2201i

Source: "{#sandboxDir}\trunk\AddOns\SSIM\Small_Sample_Isotope_Module_Manual Rev 7-30-12_Draft.pdf"; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion
Source: {#sandboxDir}\trunk\AddOns\SSIM\ReadExtSensor.ini; DestDir: {app}\AddOns\SSIM; Flags: replacesameversion

[Icons]
Name: "{userdesktop}\G2101-i Coordinator Launcher"; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c {app}\AddOns\SSIM\CoordinatorLauncher_SSIM_G2101-i.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico; Components: G2101i_CBDS G2101i_CFFDS
Name: "{userdesktop}\G2132-i Coordinator Launcher"; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c {app}\AddOns\SSIM\CoordinatorLauncher_SSIM_G2132-i.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico; Components: G2132i
Name: "{userdesktop}\G2201-i Coordinator Launcher"; Filename: {app}\HostExe\CoordinatorLauncher.exe; Parameters: -c {app}\AddOns\SSIM\CoordinatorLauncher_SSIM_G2201-i.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico; Components: G2201i
Name: {userdesktop}\Read Ext Sensor; Filename: {app}\HostExe\ReadExtSensor.exe; Parameters: -c {app}\AddOns\SSIM\ReadExtSensor.ini; WorkingDir: {app}\HostExe; IconFilename: {app}\HostExe\Diagnostics_icon.ico
