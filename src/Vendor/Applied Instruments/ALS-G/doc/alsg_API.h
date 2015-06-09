//---------------------------------------------------------------------------
#ifndef alsg_APIH
#define alsg_APIH
//---------------------------------------------------------------------------

// uiStatus: Status-Messages
#define STATUS_NO                         0
#define STATUS_ERROR                      1
#define STATUS_ABORT                      2

#define STATUS_IDLE                       5
#define STATUS_MOVE_TO_WAIT_POSITION      6
#define STATUS_WAIT_FOR_GCREADY           7

#define STATUS_GC_CLEAN                   11
#define STATUS_GC_PRE_CLEAN               12
#define STATUS_GC_PREPARE_INJECT          13
#define STATUS_GC_INJECT                  14
#define STATUS_GC_POST_CLEAN              15

#define STATUS_HPLC_CLEAN                 21
#define STATUS_HPLC_PRE_CLEAN             22
#define STATUS_HPLC_PREPARE_INJECT        23
#define STATUS_HPLC_LOAD                  24
#define STATUS_HPLC_INJECT                25
#define STATUS_HPLC_EXTRACT               26
#define STATUS_HPLC_POST_CLEAN            27
#define STATUS_HPLC_VALVE_CLEAN           28

// uiError: Error Messages
#define ERROR_NO                          0
#define ERROR_PARAMFILE_NOT_FOUND         1
#define ERROR_OPEN_IFACE_FAILED           2
#define ERROR_NO_DEVICE_CONNECTED         3

#define ERROR_MODE_RANGE                  10
#define ERROR_INJ_POINT_RANGE             11
#define ERROR_START_SIGNAL_RANGE          12
#define ERROR_GCREADY_CONTACT_RANGE       13
#define ERROR_WAIT_POS_RANGE              14
#define ERROR_TRAY_TYPE_RANGE             15
#define ERROR_WASH_STATION_TYPE_RANGE     16
#define ERROR_SYRINGE_VOLUME_RANGE        17
#define ERROR_PLUNGER_ZEROPOS_RANGE       18
#define ERROR_Z_UP_SPEED_RANGE            19
#define ERROR_Z_DOWN_SPEED_RANGE          20
#define ERROR_BUZZER_RANGE                21

#define ERROR_X_SPEED_RANGE               30
#define ERROR_Y_SPEED_RANGE               31
#define ERROR_INJ_POINT_POS_RANGE         32
#define ERROR_SYRINGE_EXCHANGE_POS_RANGE  33
#define ERROR_TRAY_I_POS_RANGE            34
#define ERROR_TRAY_II_POS_RANGE           35
#define ERROR_SAMPLE_I_DEPTH_RANGE        36
#define ERROR_SAMPLE_II_DEPTH_RANGE       37
#define ERROR_WASH_STATION_POS_RANGE      38
#define ERROR_SOLVENT_DEPTH_RANGE         39
#define ERROR_WASTE_DEPTH_RANGE           40
#define ERROR_ISTD_DEPTH_RANGE            41

#define ERROR_INJ_MODE_RANGE              50
#define ERROR_INJ_TECHNIQUE_RANGE         51
#define ERROR_INJ_MODE_PARAM_RANGE        52
#define ERROR_INJ_VOLUME_RANGE            53
#define ERROR_WASH_SYRINGE_RANGE          54
#define ERROR_VALVE_CLEAN_RANGE           55
#define ERROR_TRAY_RANGE                  56
#define ERROR_VIAL_RANGE                  57
#define ERROR_SOLVENT_RANGE               58
#define ERROR_WASTE_RANGE                 59
#define ERROR_WASHES_RANGE                60
#define ERROR_VOLUME_RANGE                61
#define ERROR_DELAY_RANGE                 62

#define ERROR_CMD                         70
#define ERROR_NO_HPLC_FUNCTION            71
#define ERROR_AXIS_RANGE                  72
#define ERROR_REF_STARTFREQ_RANGE         73
#define ERROR_REF_ENDFREQ_RANGE           74
#define ERROR_VEK_STARTFREQ_RANGE         75
#define ERROR_VEK_ENDFREQ_RANGE           76
#define ERROR_Z_SPEED_RANGE               77
#define ERROR_U_SPEED_RANGE               78
#define ERROR_HPLC_VALVE_POS_ERROR        79
#define ERROR_VIAL_MISSING                80
#define ERROR_MISSING_STEP_GOTO_WAIT      81
#define ERROR_Z_POS_RANGE                 82
#define ERROR_U_POS_RANGE                 83

#define THROW_ABORT                       90

//---------------------------------------------------------------------------
// INITILALIZATION EXPORTED FUNCTIONS
//---------------------------------------------------------------------------
extern "C" __declspec (dllexport) BOOL _stdcall alsgConnect(INT16 nComPort);
		// nComPort:

extern "C" _declspec (dllexport) BOOL alsgCheckConnection(void);

extern "C" __declspec (dllexport) BOOL _stdcall alsgDisConnect(void);

extern "C" __declspec (dllexport) BOOL _stdcall alsgReadInit(char* szFileName);


//---------------------------------------------------------------------------
// INSTALLATION EXPORTED FUNCTIONS
//---------------------------------------------------------------------------
extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallMotorSpeed(INT16 nxSpeed, INT16 nySpeed);
		// ixSpeed: [60...260] mm/sec
		// iySpeed: [60...180] mm/sec

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallInjPointPos(INT16 nInj, double dxPos, double dyPos, double dzPos);
		// iInj: [0...3]
		// dxPos, dyPos, dzPos in mm

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallSyringeExchangePos(double dxPos, double dyPos, double dzPos);
		// dxPos, dyPos, dzPos in mm

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallPlungerNullPos(double duPos);
		// duPos in mm

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallTrayPos(INT16 iTray, double dxPos, double dyPos, double dzPos);
		// dzPos: bis zur Fläschchenerkennung

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallTraySampleDepth(INT16 nTray, double dzDepth);
		// dzDepth: Eintauchtiefe der Nadel ins Fläschchen

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallWashStationPos(double dxPos, double dyPos);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallWashStationSolventDepth(double dzDepth);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallWashStationWasteDepth(double dzDepth);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetInstallWashStationISTDDepth(double dzDepth);


//---------------------------------------------------------------------------
// CONFIGURATION EXPORTED FUNCTIONS
//---------------------------------------------------------------------------
extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigMode(INT16 nMode);
		// nMode:  0=GC_Mode  1=HPLC_Mode

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigInjPoints(INT16 nMaxInjPoint);
		// nMaxInjPoint: [0...3]

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigStartSignal(INT16 nContact);
		//  nContact:  0="GC-ready"  1="Remote"

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigReadyContact(INT16 nLogic);
		//  nLogic: 0="normally open"  1="normally closed"

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigWaitPos(INT16 nWaitPos);
		//  nWaitPos:  0="left"  1="right"

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigTray(INT16 nTray, INT16 nTrayTyp);
		//  nTray:  0='A'   nTrayTyp:	0=---
		//          1='B'			1=7x15   2µl      4=15x7  2µl
		//								2=4x8    10µl     5=8x4   10µl
		//								3=10x20  0.7µl

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigTrayMetrics(INT16 nTray, INT16 nVials, INT16 nCols, INT16 nRows, double dColDist, double dRowDist);
		// die Tray-Parameter werden bereits bei SetTrayTyp gesetzt !!!

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigWashStation(INT16 nType);
		//  iTyp:   0=Solvent, Waste
		//          1=Solvent1, Waste1, Solvent2, Waste2, Int.Standard
		//          2=Solvent1, Solvent2, Solvent3, Waste, Int.Standard

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigSyringeVol(INT16 nSyrVol);
		//  iSyrVol:  0=2ul  1=5ul  2=10ul  3=25ul  4=100ul

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigSyringeSpeed(INT16 nzUpSpeed, INT16 nzDownSpeed);
		// izUpSpeed:   [70...130] mm/sec
		// izDownSpeed: [70...180] mm/sec

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetConfigStartCycleBuzzer(INT16 nBuzzer);
		//  iBuzzer:  0=OFF  1=ON  ->  legt fest, ob der Buzzer beim Methoden-Start ertönt


//---------------------------------------------------------------------------
// METHOD EXPORTED FUNCTIONS
//---------------------------------------------------------------------------
extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodInjPointNo(INT16 nInjPoint);
		// nInjPoint: [0...3]

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodSimpleInjection(
	double dSampleVolume, INT16 nPumps, double dAirGapVolume);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodSandwichInjection(
	INT16 nSolvent, double dSolventVolume, double dAirGapVolumePre, double dSampleVolume, double dAirGapVolumePost);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodISTDInjection(
	double dAirGapVolumePre, double dISTDVolume, double dAirGapVolumePost, double dSampleVolume, double dAirGapVolume);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodPreInjWashes(
	INT16 nSolvent1, INT16 nSolvent2, INT16 nSolvent3, INT16 nSample);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodPostInjWashes(
	INT16 nSolvent1, INT16 nSolvent2, INT16 nSolvent3);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodSampleWashVol(
	double dWashVol);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodValveWashes(
	INT16 nSolvent1, INT16 nSolvent2);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodSpeed(
	double dSolventDraw, double dSampleDraw, double dInj, double dSolventDisp, double dSampleDisp, INT16 nSyrInsert);

extern "C" __declspec (dllexport) BOOL _stdcall alsgSetMethodDelay(double dPreInjDelay, double dPostInjDelay, INT16 nViscDelay, INT16 nSolvDelay);


//---------------------------------------------------------------------------
// IMMEDIATE EXPORTED FUNCTIONS
//---------------------------------------------------------------------------
extern "C" __declspec (dllexport) BOOL _stdcall alsgRunMethod(INT16 nTray, INT16 nVial, INT16 nReps);

extern "C" __declspec (dllexport) BOOL _stdcall alsgRunSyringeWash(INT16 nMode, INT16 nTray, INT16 nVial, INT16 nWashes);
		//  nMode:  0=Solvent1  (auch für HPLC)
		//          1=Solvent2  (auch für HPLC)
		//          2=Solvent3
		//          3=Sample    (auch für HPLC)
		//          4=IntStandard

extern "C" __declspec (dllexport) BOOL _stdcall alsgRunValveWash(INT16 nMode, INT16 nWashes);
		// nMode:   0=Solvent1
		//          1=Solvent2
		// nWashes: RunValveClean kann mehrmals hintereinander abgearbeitet werden

extern "C" __declspec (dllexport) BOOL _stdcall alsgRunReference(INT16 nAxis, INT16 nDirection);

extern "C" __declspec (dllexport) BOOL _stdcall alsgRunAbort(void);

extern "C" __declspec (dllexport) BOOL _stdcall alsgGetBusy(void);

extern "C" __declspec (dllexport) INT16 _stdcall alsgGetStatus(void);

extern "C" __declspec (dllexport) INT16 _stdcall alsgGetError(void);

extern "C" __declspec (dllexport) BOOL _stdcall alsgBeep(INT16 nReps);


//---------------------------------------------------------------------------
// DIAGNOSTIC EXPORTED FUNCTIONS
//---------------------------------------------------------------------------
extern "C" __declspec (dllexport) INT32 _stdcall alsgGetDiagPlungerStrokes(void);

extern "C" __declspec (dllexport) INT32 _stdcall alsgGetDiagInjections(INT16 nInjPoint);


//---------------------------------------------------------------------------
// MICROSSTEP EXPORTED FUNCTIONS
//---------------------------------------------------------------------------
extern "C" __declspec (dllexport) double _stdcall alsgStepGoToSyrExchange(INT16 nStep);

extern "C" __declspec (dllexport) BOOL _stdcall alsgStepGoToWait(void);

extern "C" __declspec (dllexport) BOOL _stdcall alsgStepGoToSolvent(INT16 nPos, double dRelDepth);

extern "C" __declspec (dllexport) BOOL _stdcall alsgStepGoToWaste(INT16 nPos, double dRelDepth);

extern "C" __declspec (dllexport) BOOL _stdcall alsgStepGoToVial(INT16 nTray, INT16 nPos, double dRelDepth);

extern "C" __declspec (dllexport) BOOL _stdcall alsgStepDraw(double dAmount, double dSpeed);

extern "C" __declspec (dllexport) BOOL _stdcall alsgStepDispense(double dAmount, double dSpeed);

extern "C" __declspec (dllexport) BOOL _stdcall alsgStepGoToInject(INT16 nInjPoint, double dRelDepth);


//---------------------------------------------------------------------------
// SYSTEM FUNCTIONS
//---------------------------------------------------------------------------
extern "C" _declspec (dllexport) double _stdcall alsgSysControl(INT16 nCmd, double dArg1, double dArg2, double dArg3, double dArg4, double dArg5, double dArg6, double dArg7, double dArg8);


#endif
