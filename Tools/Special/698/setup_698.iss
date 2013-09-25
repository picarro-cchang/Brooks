[Setup]
AppContact = support@picarro.com
AppName = Picarro Patch Installer
AppPublisher = Picarro Inc.
AppPublisherURL = http://www.picarro.com
AppVersion = 698
AppCopyright = Copyright 2012-2013 Picarro Inc.
DefaultDirName = c:\Picarro\G2000
OutputBaseFilename = setup_698

[Types]
Name: "L2120i"; Description: "L2120-i"
Name: "L2130i"; Description: "L2130-i"

[Components]
Name: "L2120i_Coord"; Description: "L2120-i Isotopic Water Coordinators"; Types: L2120i; Flags: fixed
Name: "L2130i_Coord"; Description: "L2130-i Isotopic Water Coordinators"; Types: L2130i; Flags: fixed

[Files]
Source: "patch_698.py"; DestDir: "{tmp}"
Source: "Path.py"; DestDir: "{tmp}"
Source: "HBDS\AppConfig\Config\Coordinator\*"; DestDir: "{tmp}\HBDS\AppConfig\Config\Coordinator"; Components: L2120i_Coord; Flags: recursesubdirs
Source: "HIDS\AppConfig\Config\Coordinator\*"; DestDir: "{tmp}\HIDS\AppConfig\Config\Coordinator"; Components: L2130i_Coord; Flags: recursesubdirs

[Run]
Filename: "python.exe"; Parameters: "{tmp}\patch_698.py -n {tmp}\HBDS\AppConfig\Config\Coordinator"; StatusMsg: "Patching Coordinators..."; Components: L2120i_Coord
Filename: "python.exe"; Parameters: "{tmp}\patch_698.py -n {tmp}\HIDS\AppConfig\Config\Coordinator"; StatusMsg: "Patching Coordinators..."; Components: L2130i_Coord