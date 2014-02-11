; Python-related commands common to all apps
; Since DatViewer is currently distributed as source, it is included here as its shortcut references Python by version

[Files]
Source: {#resourceDir}\Picarro.pth; DestDir: C:\Python27\Lib\site-packages; Flags: replacesameversion
Source: {#resourceDir}\DatViewer\*; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion

[Icons]
Name: {userdesktop}\Picarro Utilities\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: DatViewer.py -c DatViewer.ini; WorkingDir: {app}\DatViewer; IconFilename: {app}\HostExe\{#utilitiesIcon}