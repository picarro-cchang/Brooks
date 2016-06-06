; [Code] section common to all apps
; Task 1: Kill Host software if it's running
; Task 2: Saves and restores the InstrConfig folder

[Code]
var
    savedInstrConfig : String;
    instrConfig : String;
    analyzerType: AnsiString;
    UserSelectionPage: TInputOptionWizardPage;

function InitializeSetup(): Boolean;
var
    SignatureFile : String;
begin
    SignatureFile := 'C:\Picarro\G2000\installerSignature.txt';
    if FileExists(SignatureFile) then
        begin
            if LoadStringFromFile(SignatureFile, analyzerType) then
                analyzerType := Trim(analyzerType)
            else
                analyzerType := '';
        end
    else
        analyzerType := '';
    Result := True;
end;

procedure InitializeWizard;
begin
    { Create the page }
    UserSelectionPage := CreateInputOptionPage(wpWelcome,
        'Select analyzer to install',
        'Please select the analyzer type to be installed on this system.',
        'Click Next to continue.',
        True, False);
    UserSelectionPage.Add('FEDS (P3200, methane analyzer)');
    UserSelectionPage.Add('RFADS (P3300, ethane analyzer)');
    if (analyzerType = 'FEDS') then
        UserSelectionPage.Values[0] := True
    else if (analyzerType = 'RFADS') then
        UserSelectionPage.Values[1] := True
    else
        UserSelectionPage.Values[0] := True;
end;
    
procedure MyBeforeInstall();
var
    dateTime : String;
    app : String;
    PythonExe : String;
    KillHostSoftware : String;
    version : String;
    ResultCode : Integer;
begin
    {MsgBox('MyBeforeInstall', mbInformation, MB_OK)}
    {Kill host software that is already running}
    PythonExe := 'C:\Python27\python.exe';
    KillHostSoftware := ExpandConstant('{app}') + '\HostExe\KillHostSoftware.py';
    Exec(PythonExe, KillHostSoftware, '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    
    {Backup instrConfig}
    dateTime := GetDateTimeString('_yyyymmdd_hhnnss',#0,#0);
    app := ExpandConstant('{app}');
    savedInstrConfig := app+'\InstrConfig'+dateTime;
    instrConfig := app+'\InstrConfig';
    Exec(ExpandConstant('{sys}\xcopy.exe'), '/E /Y /I '+instrConfig+' '+savedInstrConfig, '', SW_SHOW,
    ewWaitUntilTerminated, ResultCode);
    {Don't use RenameFile because it will fail if the instrConfig is open in Windows Explorer when installer is running}
    {RenameFile(instrConfig,savedInstrConfig);}
end;

procedure MyAfterInstall();
var
    ResultCode : Integer;
begin
    {MsgBox('MyAfterInstall', mbInformation, MB_OK)}
    Exec(ExpandConstant('{sys}\xcopy.exe'), '/E /Y /I '+savedInstrConfig+' '+instrConfig, '', SW_SHOW,
    ewWaitUntilTerminated, ResultCode);
end;

function CheckForFEDS(): Boolean;
begin
    if (UserSelectionPage.Values[0] = True) then
        Result := True
    else
        Result := False;
end;

function CheckForRFADS(): Boolean;
begin
    if (UserSelectionPage.Values[1] = True) then
        Result := True
    else
        Result := False;
end;
[Files]

; Files section is needed so ISCC knows where the Code section ends
