; [Code] section common to all apps
; Task 1: Kill Host software if it's running
; Task 2: Saves and restores the InstrConfig folder

[Code]
var
    savedInstrConfig : String;
    instrConfig : String;
    hostExeExist : Boolean;

procedure BeforeInstallStopSupervisor();
var
    handle : Longint;
    StopSupervisor : String;
begin
    StopSupervisor := ExpandConstant('{app}') + '\HostExe\StopSupervisor.exe';
    hostExeExist := FileExists(StopSupervisor);
    handle := FindWindowByWindowName('Stop CRDS Software');
    if handle <> 0 then
    begin
        {Close StopSupervisor}
        PostMessage(handle, $0010, 0, 0);
        Sleep(1000);
    end;
end;    
    
procedure MyBeforeInstall();
var
    dateTime : String;
    app : String;
    StopSupervisor : String;
    version : String;
    ResultCode : Integer;
begin
    {MsgBox('MyBeforeInstall', mbInformation, MB_OK)}
    StopSupervisor := ExpandConstant('{app}') + '\HostExe\StopSupervisor.exe';
    if FileExists(StopSupervisor) and hostExeExist then
    begin
        if GetVersionNumbersString(StopSupervisor, version) then
            begin
                if CompareText(version, '2.3.0.0') >= 0 then
                    Exec(StopSupervisor, '-o 1', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
            end;
    end; 
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
