; DatViewer component
;
; Currently this is distributed as source code.

[Files]
; Program
Source: {#sandboxDir}\host\AddOns\DatViewer\DatViewer.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\DatViewer\DateRangeSelectorFrame.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\DatViewer\Analysis.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\DatViewer\FileOperations.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\DatViewer\timestamp.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\DatViewer\CustomConfigObj.pyc; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
; Manual
Source: {#sandboxDir}\host\AddOns\DatViewer\Manual\*; DestDir: {app}\DatViewer\Manual; Flags: recursesubdirs replacesameversion
; tzlocal
Source: {#sandboxDir}\host\AddOns\DatViewer\tzlocal\*; DestDir: C:\Python27\Lib\site-packages\tzlocal; Flags: recursesubdirs replacesameversion
; Resources
Source: {#sandboxDir}\host\AddOns\DatViewer\Scripts\*; DestDir: {app}\DatViewer\Scripts; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\AddOns\DatViewer\datViewer.ini; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion
Source: {#sandboxDir}\host\Assets\icons\{#diagnosticsIcon}; DestDir: {app}\DatViewer; Flags: recursesubdirs replacesameversion

[Icons]
Name: {userdesktop}\Picarro Utilities\Data File Viewer; Filename: C:\Python27\python.exe; Parameters: {app}\DatViewer\DatViewer.pyc; WorkingDir: {app}\DatViewer; IconFilename: {app}\DatViewer\{#diagnosticsIcon}