; DatViewer component
;
; Currently this is distributed as source code.

[Files]

Source: {#sandboxDir}\Host\DatViewer\DatViewer.py; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Host\DatViewer\datViewer.ini; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion


[Icons]

Name: {userdesktop}\Picarro Utilities\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: {app}\DatViewer\DatViewer.py -c DatViewer.ini; WorkingDir: {app}\DatViewer; IconFilename: {app}\HostExe\{#utilitiesIcon}
