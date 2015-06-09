; [Code] section common to all apps
; Saves and restores the InstrConfig folder

[Code]
var
    savedInstrConfig : String;
    instrConfig : String;

procedure MyBeforeInstall();
var
    dateTime : String;
    app : String;
    ResultCode : Integer;
begin
    {MsgBox('MyBeforeInstall', mbInformation, MB_OK)}
    dateTime := GetDateTimeString('_yyyymmdd_hhnnss',#0,#0);
    app := ExpandConstant('{app}');
    savedInstrConfig := app+'\InstrConfig'+dateTime;
    instrConfig := app+'\InstrConfig';
    Exec(ExpandConstant('{sys}\xcopy.exe'), '/E /Y /I '+instrConfig+' '+savedInstrConfig, '', SW_SHOW,
    ewWaitUntilTerminated, ResultCode);
    {Don't use RenameFile because it will fail if the instrConfig is open in Windows Explorer when installer is running}
    {MsgBox('Renaming:' + instrConfig + ' to ' + savedInstrConfig, mbInformation, MB_OK);}
    {RenameFile(instrConfig,savedInstrConfig);}
    {MsgBox('Renaming Done', mbInformation, MB_OK);}
end;

procedure MyAfterInstall();
var
    ResultCode : Integer;
begin
    {MsgBox('MyAfterInstall', mbInformation, MB_OK)}
    {MsgBox('Running xcopy:', mbInformation, MB_OK);}
    Exec(ExpandConstant('{sys}\xcopy.exe'), '/E /Y /I '+savedInstrConfig+' '+instrConfig, '', SW_SHOW,
    ewWaitUntilTerminated, ResultCode);
    {MsgBox('xcopy Done', mbInformation, MB_OK);}
end;


[Files]

; Files section is needed so ISCC knows where the Code section ends
