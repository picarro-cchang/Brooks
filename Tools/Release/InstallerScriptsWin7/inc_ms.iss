; Microsoft files to include in installs
;
; For now don't include this file. ISCC barfs because it can't find MyAfterInstall
; (defined in inc_code.iss)
; Even though this file was included  *after* inc_code.iss it bailed so maybe
; each file needs to work standalone?

[Files]
Source: {#resourceDir}\MSVCP71.DLL; DestDir: {sys}; Flags: replacesameversion; AfterInstall: MyAfterInstall
