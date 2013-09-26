[Setup]
AppContact = support@picarro.com
AppName = Picarro Patch Installer
AppPublisher = Picarro Inc.
AppPublisherURL = http://www.picarro.com
AppVersion = 20130925
AppCopyright = Copyright 2012-2013 Picarro Inc.
DefaultDirName = c:\Picarro\G2000
OutputBaseFilename = setup_CFFDS_20130925

[Types]
Name: "CFFDS"; Description: "CFFDS update"

[Components]
Name: "CFFDS"; Description: "CFFDS config update installer"; Types: CFFDS; Flags: fixed

[Files]
Source: "patch_20130925.py"; DestDir: "{tmp}"
Source: "Path.py"; DestDir: "{tmp}"
Source: "CFFDS\AppConfig\Config\Fitter\*"; DestDir: "{tmp}\CFFDS\AppConfig\Config\Fitter"; Components: CFFDS; Flags: recursesubdirs
Source: "CFFDS\AppConfig\Scripts\DataManager\*"; DestDir: "{tmp}\CFFDS\AppConfig\Scripts\DataManager"; Components: CFFDS; Flags: recursesubdirs
Source: "CFFDS\AppConfig\Scripts\Fitter\*"; DestDir: "{tmp}\CFFDS\AppConfig\Scripts\Fitter"; Components: CFFDS; Flags: recursesubdirs

[Run]
Filename: "python.exe"; Parameters: "{tmp}\patch_20130925.py -n {tmp}\CFFDS"; StatusMsg: "Patching CFFDS Configuration..."; Components: CFFDS
