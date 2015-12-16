; DatViewer component
;
; Currently this is distributed as compiled source code.

[Files]
; Program
Source: {#sandboxDir}\AddOns\DatViewer\DatViewer.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\DateRangeSelectorFrame.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\Analysis.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\FileOperations.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\timestamp.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\CustomConfigObj.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
; Manual
Source: {#sandboxDir}\AddOns\DatViewer\Manual\*; DestDir: {app}\DatViewer\Manual; Flags: recursesubdirs replacesameversion
; tzlocal
Source: {#sandboxDir}\AddOns\DatViewer\tzlocal\*; DestDir: C:\Python27\Lib\site-packages\tzlocal; Flags: recursesubdirs replacesameversion
; Resources
Source: {#sandboxDir}\AddOns\DatViewer\Scripts\*; DestDir: {app}\DatViewer\Scripts; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\AddOns\DatViewer\datViewer.ini; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\Assets\icons\{#diagnosticsIcon}; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion

[Icons]

Name: {userdesktop}\Picarro Utilities\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: {app}\DatViewer\DatViewer.pyc; WorkingDir: {app}\DatViewer; IconFilename: {app}\DatViewer\{#diagnosticsIcon}
Name: {userdesktop}\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: {app}\DatViewer\DatViewer.pyc; WorkingDir: {app}\DatViewer; IconFilename: {app}\DatViewer\{#diagnosticsIcon}