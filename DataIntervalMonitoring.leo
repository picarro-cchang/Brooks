<?xml version="1.0" encoding="utf-8"?>
<!-- Created by Leo: http://leoeditor.com/leo_toc.html -->
<leo_file xmlns:leo="http://leoeditor.com/namespaces/leo-python-editor/1.1" >
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.5" body_secondary_ratio="0.5">
	<global_window_position top="50" left="50" height="500" width="700"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="sze.20150504102303.2" a="E"><vh>Monitoring data rate</vh>
<v t="sze.20150506185525.1" a="E"><vh>Changed code</vh>
<v t="sze.20150506170401.1"><vh>&lt;&lt;Initialization code&gt;&gt;</vh></v>
<v t="sze.20150506165934.1"><vh>&lt;&lt;AnalyzerStatus Masks&gt;&gt;</vh></v>
<v t="sze.20150506164942.1"><vh>&lt;&lt;Update AnalyzerStatus&gt;&gt;</vh></v>
<v t="sze.20150506170022.1"><vh>&lt;&lt;Alarm Parameters&gt;&gt;</vh></v>
<v t="sze.20150506194536.1"><vh>&lt;&lt;Setup Constants&gt;&gt;</vh></v>
<v t="sze.20150506182103.1"><vh>&lt;&lt;Report persistent variables&gt;&gt;</vh></v>
</v>
</v>
<v t="sze.20150507213556.1" a="E"><vh>Reorganizing PeripheralStatus</vh>
<v t="sze.20150507214535.1" a="E"><vh>Changed code</vh>
<v t="sze.20150507214410.2"><vh>class PeripheralStatus</vh></v>
<v t="sze.20150507215103.1"><vh>OLD: class PeripheralStatus</vh></v>
<v t="sze.20150507213822.15"><vh>trueWindSource</vh></v>
<v t="sze.20150506164740.1"><vh>&lt;&lt;Check for unstable wind speed and correlation between car speed and wind speed&gt;&gt;</vh></v>
<v t="sze.20150507215022.1"><vh>&lt;&lt;OLD: Check for unstable wind speed and correlation between car speed and wind speed&gt;&gt;</vh></v>
</v>
</v>
<v t="sze.20150507214331.1"><vh>@clean Host\PeriphIntrf\PeripheralStatus.py</vh>
<v t="sze.20150507214410.2"></v>
</v>
<v t="sze.20150507213649.1" a="E"><vh>@clean Config\FEDS\AppConfig\Scripts\PeriphIntrf\processorFindWindInstNoCompass.py</vh>
<v t="sze.20150507213822.1"><vh>processorFindWindInstNoCompass declarations</vh></v>
<v t="sze.20150507213822.2"><vh>class RawSource</vh>
<v t="sze.20150507213822.3"><vh>__init__</vh></v>
<v t="sze.20150507213822.4"><vh>getDataTupleType</vh></v>
<v t="sze.20150507213822.5"><vh>getFromQueue</vh></v>
<v t="sze.20150507213822.6"><vh>getOldestTimestamp</vh></v>
<v t="sze.20150507213822.7"><vh>getData</vh></v>
</v>
<v t="sze.20150507213822.8"><vh>class GpsSource</vh></v>
<v t="sze.20150507213822.9"><vh>class WsSource</vh></v>
<v t="sze.20150507213822.10"><vh>distVincenty</vh></v>
<v t="sze.20150507213822.11"><vh>toXY</vh></v>
<v t="sze.20150507213822.12"><vh>syncSources</vh></v>
<v t="sze.20150507213822.13"><vh>syncCdataSource</vh></v>
<v t="sze.20150507213822.14"><vh>derivCdataSource</vh></v>
<v t="sze.20150507213822.15"></v>
<v t="sze.20150507213822.16"><vh>windStatistics</vh></v>
<v t="sze.20150507213822.17"><vh>runAsScript</vh></v>
</v>
<v t="sze.20150504115900.1"><vh>@clean Config\FEDS\AppConfig\Scripts\Fitter\fitScriptFCDS_fast.py</vh>
<v t="sze.20150504120336.1"><vh>fitScriptFCDS_fast declarations</vh></v>
<v t="sze.20150504120336.2"><vh>expAverage</vh></v>
<v t="sze.20150504120336.3"><vh>initExpAverage</vh></v>
<v t="sze.20150504120336.4"><vh>fitQuality</vh></v>
<v t="sze.20150504120336.5"><vh>outlierFilter</vh></v>
<v t="sze.20150504120336.6"><vh>initialize_CFADS_Baseline</vh></v>
<v t="sze.20150504120336.7"><vh>initialize_CH4_Baseline</vh></v>
</v>
<v t="sze.20150506155541.1" a="E"><vh>@clean Config\FEDS\AppConfig\Scripts\DataManager\analyze_FBDS.py</vh>
<v t="sze.20150506155630.1"><vh>&lt;&lt;analyze_FBDS declarations&gt;&gt;</vh></v>
<v t="sze.20150506155630.2"><vh>evalLeaves</vh></v>
<v t="sze.20150506155630.3"><vh>clipReportData</vh></v>
<v t="sze.20150506155630.4"><vh>applyLinear</vh></v>
<v t="sze.20150506155630.5"><vh>apply2Linear</vh></v>
<v t="sze.20150506155630.6"><vh>protDivide</vh></v>
<v t="sze.20150506155630.7"><vh>expAverage</vh></v>
<v t="sze.20150506155630.8"><vh>boxAverage</vh></v>
<v t="sze.20150506155630.9"><vh>unstableWindSpeed</vh></v>
<v t="sze.20150506165859.1"><vh>&lt;&lt;SystemStatus Masks&gt;&gt;</vh></v>
<v t="sze.20150506165934.1"></v>
<v t="sze.20150506170022.1"></v>
<v t="sze.20150506194536.1"></v>
<v t="sze.20150506170104.1"><vh>&lt;&lt;Initialize System status flags&gt;&gt;</vh></v>
<v t="sze.20150506170135.1"><vh>&lt;&lt;Valve masks&gt;&gt;</vh></v>
<v t="sze.20150506170401.1"></v>
<v t="sze.20150506170534.1"><vh>&lt;&lt;Handle PeakDetector&gt;&gt;</vh></v>
<v t="sze.20150506170721.1"><vh>&lt;&lt;Ensure sensor minimal log is not running&gt;&gt;</vh></v>
<v t="sze.20150506162409.1"><vh>&lt;&lt;Handle command-line options&gt;&gt;</vh></v>
<v t="sze.20150506162645.1"><vh>&lt;&lt;Get info from InstrCal file&gt;&gt;</vh></v>
<v t="sze.20150506163129.1"><vh>&lt;&lt;Analyze Fit Output Data&gt;&gt;</vh></v>
<v t="sze.20150506163215.1"><vh>&lt;&lt;Analyze Peripheral Data&gt;&gt;</vh></v>
<v t="sze.20150506163404.1"><vh>&lt;&lt;Process Instrument Status&gt;&gt;</vh></v>
<v t="sze.20150506163500.1"><vh>&lt;&lt;Check data processing latency&gt;&gt;</vh></v>
<v t="sze.20150506163547.1"><vh>&lt;&lt;Check if warm box temperature is within WB_TEMP_ISO_THRESHOLD of setpoint&gt;&gt;</vh></v>
<v t="sze.20150506163653.1"><vh>&lt;&lt;Turn off heater&gt;&gt;</vh></v>
<v t="sze.20150506163722.1"><vh>&lt;&lt;Handle anemometer anomalies&gt;&gt;</vh></v>
<v t="sze.20150506163829.1"><vh>&lt;&lt;Update wavelength monitor offsets&gt;&gt;</vh></v>
<v t="sze.20150506164313.1"><vh>&lt;&lt;ChemDetect processing&gt;&gt;</vh></v>
<v t="sze.20150506181818.1"><vh>&lt;&lt;Handle AnalyzerStatus ChemDetect mask&gt;&gt;</vh></v>
<v t="sze.20150506181637.1"><vh>&lt;&lt;Set up alarmActive when not in capture mode&gt;&gt;</vh></v>
<v t="sze.20150506164529.1"><vh>&lt;&lt;Check mobile kit flow sensor reading&gt;&gt;</vh></v>
<v t="sze.20150506164740.1"></v>
<v t="sze.20150506164942.1"></v>
<v t="sze.20150506181904.1"><vh>&lt;&lt;Handle SystemStatus&gt;&gt;</vh></v>
<v t="sze.20150506182103.1"></v>
<v t="sze.20150506182201.1"><vh>&lt;&lt;Execute laser ageing script&gt;&gt;</vh></v>
<v t="sze.20150506182135.1"><vh>&lt;&lt;Report DATA and NEW_DATA&gt;&gt;</vh></v>
</v>
<v t="sze.20150507075702.1"><vh>@clean Host\Tests\AccessSurveyorDatabase\database_queries.py</vh>
<v t="sze.20150507075745.1"><vh>database_queries declarations</vh></v>
<v t="sze.20150507075745.2"><vh>getAnalyzerId</vh></v>
<v t="sze.20150507075745.3"><vh>getSurveysForAnalyzer</vh></v>
<v t="sze.20150507075745.4"><vh>getSurveyMinData</vh></v>
<v t="sze.20150507075745.5"><vh>get_backtraj_data</vh></v>
</v>
<v t="sze.20150507075912.1"><vh>@clean Host\Tests\AccessSurveyorDatabase\example_access.py</vh></v>
<v t="sze.20150507082344.1"><vh>@clean Host\Tests\AccessSurveyorDatabase\find_max_rel_speed.py</vh></v>
<v t="sze.20150508000110.1"><vh>@clean Host\Tests\AccessSurveyorDatabase\find_max_wind_speed.py</vh></v>
<v t="sze.20150508003853.1"><vh>@clean Host\Tests\AccessSurveyorDatabase\max_wind_speed.csv</vh></v>
<v t="sze.20150506154736.2"><vh>Recovered Nodes</vh>
<v t="sze.20150506154736.3"><vh>Recovered node "fitScriptFCDS_fast declarations" from fitScriptFCDS_fast.py</vh>
<v t="sze.20150506154736.4"><vh>old:fitScriptFCDS_fast declarations</vh></v>
<v t="sze.20150506154736.5"><vh>new:fitScriptFCDS_fast declarations</vh></v>
</v>
</v>
<v t="sze.20150510223148.1" a="E"><vh>Recovered Nodes</vh>
<v t="sze.20150510223148.2"><vh>Recovered node "&lt;&lt;analyze_FBDS declarations&gt;&gt;" from analyze_FBDS.py</vh>
<v t="sze.20150510223148.3"><vh>old:&lt;&lt;analyze_FBDS declarations&gt;&gt;</vh></v>
<v t="sze.20150510223148.4"><vh>new:&lt;&lt;analyze_FBDS declarations&gt;&gt;</vh></v>
</v>
<v t="sze.20150510223148.5"><vh>Recovered node "&lt;&lt;Setup Constants&gt;&gt;" from analyze_FBDS.py</vh>
<v t="sze.20150510223148.6"><vh>old:&lt;&lt;Setup Constants&gt;&gt;</vh></v>
<v t="sze.20150510223148.7"><vh>new:&lt;&lt;Setup Constants&gt;&gt;</vh></v>
</v>
<v t="sze.20150510223148.8"><vh>Recovered node "&lt;&lt;Update AnalyzerStatus&gt;&gt;" from analyze_FBDS.py</vh>
<v t="sze.20150510223148.9"><vh>old:&lt;&lt;Update AnalyzerStatus&gt;&gt;</vh></v>
<v t="sze.20150510223148.10"><vh>new:&lt;&lt;Update AnalyzerStatus&gt;&gt;</vh></v>
</v>
</v>
</vnodes>
<tnodes>
<t tx="sze.20150504102303.2">FEDS2008 10.100.3.42

20140504
Interval 0.115s in survey mode (FCDS_highspeed)
Intervals 0.71s and 1.12s in isotopic capture mode (_FB2xxx_mobile_v29.sch)

John modified Fitter_FCDS_Fast.ini so that it reports the interval and spectrumID

Script0 = ../../Scripts/Fitter/fitScriptFCDS_fast.py
Script1 = ../../../CommonConfig/Scripts/Fitter/fitScriptLaserCurrentAverage.py

It seems that we should check the concentration as well and set the acquisition rate to the nominal value whenever the concentration is greater than 5 ppm.
In this way, slow-downs due to high concentration will not cause the alarm to be raised.</t>
<t tx="sze.20150504115900.1">@language python
@tabwidth -4
@others
if INIT:
    fname = os.path.join(BASEPATH,r"./FCDS/spectral library FCDS v2_2.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    fname = os.path.join(BASEPATH,r"../../../InstrConfig/Calibration/InstrCal/FitterConfig.ini")
    instrParams = getInstrParams(fname)
     
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C12only_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C12only_FC_FY_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C13only_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/iCH4_C13only_FC_FY_v3_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CH4+C2H6+H2O+CO2_v1_1.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./FCDS/C12interferences_v1_1.ini")))
    
    anCO2 = []
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 VC VY v1_1.ini")))
    anCO2.append(Analysis(os.path.join(BASEPATH,r"./FCDS/CO2 6056 FC FY v1_1.ini")))   
  
    anH2O = []
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FCDS/H2O_v3_2.ini")))
    anH2O.append(Analysis(os.path.join(BASEPATH,r"./FCDS/H2O_FC_FY_v3_1.ini")))
    
    an12CH4 = []
    an12CH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_1 2008 0304.ini")))
    an12CH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC VY v2_0 2008 0304.ini")))
    an12CH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 2008 0304.ini")))
    
    anH2OCFADS = []
    anH2OCFADS.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 v1_2 2011 0328.ini")))
    anH2OCFADS.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 FC v1_1 2011 0309.ini")))
    anH2OCFADS.append(Analysis(os.path.join(BASEPATH,r"./CFADS/FADS-1 H2O+CH4 v1_1 2011 0309.ini")))
 
    #  Import calibration constants from fitter_config.ini at initialization
    CFADS_baseline_level = instrParams['CFADS_baseline']
    CFADS_baseline_slope = instrParams['CFADS_Baseline_slope']
    CFADS_A0 = instrParams['CFADS_Sine0_ampl']
    CFADS_Nu0 = instrParams['CFADS_Sine0_freq']
    CFADS_Per0 = instrParams['CFADS_Sine0_period']
    CFADS_Phi0 = instrParams['CFADS_Sine0_phase']
    CFADS_A1 = instrParams['CFADS_Sine1_ampl']
    CFADS_Nu1 = instrParams['CFADS_Sine1_freq']
    CFADS_Per1 = instrParams['CFADS_Sine1_period']
    CFADS_Phi1 = instrParams['CFADS_Sine1_phase']
    ch4_baseline_level = instrParams['CH4_Baseline_level']
    ch4_baseline_slope = instrParams['CH4_Baseline_slope']
    ch4_A0 = instrParams['CH4_Sine0_ampl']
    ch4_Nu0 = instrParams['CH4_Sine0_freq']
    ch4_Per0 = instrParams['CH4_Sine0_period']
    ch4_Phi0 = instrParams['CH4_Sine0_phase']
    ch4_A1 = instrParams['CH4_Sine1_ampl']
    ch4_Nu1 = instrParams['CH4_Sine1_freq']
    ch4_Per1 = instrParams['CH4_Sine1_period']
    ch4_Phi1 = instrParams['CH4_Sine1_phase']

    H1_wd = instrParams['Water_lin_wd']
    H2_wd = instrParams['Water_quad_wd']
    
    H1_wd_CFADS_CH4 = instrParams['Water_lin_wd_CFADS_CH4']
    H2_wd_CFADS_CH4 = instrParams['Water_quad_wd_CFADS_CH4']
    
    H1_wd_iCH4 = instrParams['Water_lin_wd_iCH4']
    H2_wd_iCH4 = instrParams['Water_quad_wd_iCH4']
    
    P0_off = instrParams['Peak0_offset']
    P5_off = instrParams['Peak5_offset']
    P5_quad = instrParams['Peak5_quad']
    P5_A1 = instrParams['Peak5_CO2_lin']
    P5_H1 = instrParams['Peak5_water_lin']
    P5_M1H1 = instrParams['Peak5_water_CH4_bilin']
    P30_off = instrParams['Peak30_offset']
    P30_M1 = instrParams['Peak30_methane_linear']
    P24_off = instrParams['Peak24_offset']
    P24_M1 = instrParams['Peak24_methane_linear']
    H1 = instrParams['Water_lin']
    H2 = instrParams['Water_quad']
    C12_conc_lin = instrParams['C12_lin']

#   Globals for the isotopic methane fit 
    ch4_res12 = 0
    ch4_res13 = 0
    ch4_res_w = 0
    HC_res = 0
    last_time = None
    peak_0 = 1e-10
    peak0_spec = 1e-10
    peak0_spec_dry = 1e-10
    peak_5 = 0
    peak5_spec = 0
    peak5_spec_dry = 0
    peak_20 = 0
    peak_30 = 0
    peak24_spec = 0
    peak30_spec = 0
    c13toc12 = 0
    y_0 = 0
    vy_0 = 0
    y_5 = 0
    vy_5 = 0
    y_24 = 0
    vy_24 = 0
    y_30 = 0
    vy_30 = 0    
    base_0 = 0
    base_5 = 0
    base_24 = 0
    base_30 = 0
    shift_0 = 0
    adjust_0 = 0
    shift_5 = 0
    adjust_5 = 0
    shift_24 = 0
    adjust_24 = 0    
    shift_30 = 0
    adjust_30 = 0
    str_0 = 0
    str_30 = 0
    C12H4_conc_raw = 0
    C12H4_conc_raw_dry = 0
    C13H4_conc_raw = 0
    C13H4_conc_raw_dry = 0
    delta_no_bookend = 0
    h2o_conc_pct = 0
    ch4_conc_diff = 0
    C12H4_conc_raw_old = 0
    ch4_from_h2o = 0
    
    ntopper_12 = 0
    tiptop_12 = 0
    tipstd_12 = 0
    ntopper_13 = 0
    tiptop_13 = 0
    tipstd_13 = 0
    peakheight_0 = 0
    peakheight_5 = 0
    peakheight_ratio = 0
    delta_from_height = 0
    
    HC_base_offset = 0
    HC_slope_offset = 0
    HC_shift = 0
    HC_CH4_conc = 0
    HC_C12_conc = 0
    HC_H2O_conc = 0
    HC_C2H6_conc = 0
    
    PPF_res = 0
    PPF_base_offset = 0
    PPF_slope_offset = 0
    PPF_shift = 0
    PPF_CH4_conc = 0
    PPF_C12_conc = 0
    PPF_H2O_conc = 0
    PPF_C2H6_conc = 0
    PPF_C2H4_conc = 0
    PPF_NH3_conc = 0
    PPF_H2S_conc = 0
    
# CFADS 12CH4 and H2O
    peak_75 = 0.0
    base_75 = 0.0
    str_75 = 0.0
    y_75 = 0.0
    shift_75 = 0.0
    h2o_conc = 0.0
    CFADS_h2o_conc = 0.0
    adjust_75 = 0.0
        
    CFADS_counter = -25
    CFADS_base = 0.0
    CFADS_base_avg = instrParams['CFADS_baseline']
    ch4_low_shift = 0.0
    ch4_high_shift = 0.0
    ch4_high_adjust = 0.0
    CFADS_ch4_amp = 0.0
    ch4_splinemax = 0.5
    ch4_splinemax_dry = 0.5
    ch4_splinemax_for_correction = 0.0
    ch4_vy = 0.0
    ch4_y_avg = 1.08
    ch4_conc_ppmv_final = 0.0
    ch4_conc_ppmv_final_dry = 0.0  
    ch4_conc_for_correction = 0.0
    ch4_conc_diff = 0.0
    ch4_from_h2o = 0.0
    CFADS_ch4_y = 0.0
    
#  New CO2 in CFADS methane region (6056.6 wvn)
    adjust_24 = 0.0
    shift_24 = 0.0
    strength_24 = 0.0
    y_24 = 0.0
    base_24 = 0.0
    peak_24 = 0.0
    co2_conc = 0.0

    ignore_count = 5
    last_time = None
    
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA

d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.30,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=10)
d.sparse(maxPoints=1000,width=0.005,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",outlierThreshold=4)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(array(d.groupSizes)))

P = d["cavitypressure"]
T = d["cavitytemperature"]
dasTemp = d.sensorDict["DasTemp"]

species = (d.subschemeId &amp; 0x1FF)[0]

tstart = time.clock()
RESULT = {}
r = None

in25 = (d.fitData["freq"] &gt;= 6056.81) &amp; (d.fitData["freq"] &lt;= 6057.39)
good25 = sum(in25)
in150 = (d.fitData["freq"] &gt;= 6028.4) &amp; (d.fitData["freq"] &lt;= 6029.2)
good150 = sum(in150)
fast_flag = -1
interval = 0

if species == 150 and good150 &gt; 35:
    fast_flag = 0
    initialize_CH4_Baseline()
    init[20,"strength"] = 0.07726*strength_24
    r = anCH4[0](d,init,deps)   #  First fit (12)CH4
    ANALYSIS.append(r)
    shift_0 = r["base",3]
    vy_0 = r[0,"y"]
    if (r[0,"peak"] &gt; 2) and (abs(shift_0) &lt; 0.04) and (abs(vy_0-1.18) &lt; 0.3):   
        adjust_0 = shift_0
        init["base",3] = shift_0
        init[0,"y"] = vy_0
    else:
        adjust_0 = 0.0
        
    r = anCH4[1](d,init,deps)
    ANALYSIS.append(r)
        
    ch4_res12 = r["std_dev_res"]
    y_0 = r[0,"y"]
    base_0 = r[0,"base"]
    peak_0 = r[0,"peak"]
    str_0 = r[0,"strength"]
    
    C12H4_conc_raw = 0.40148*peak_0
    ch4_conc_diff = abs(C12H4_conc_raw_old - C12H4_conc_raw)
    C12H4_conc_raw_old = C12H4_conc_raw
    
    f = d.waveNumber
    l = 1000*d.uncorrectedAbsorbance
    up_flag = (d.extra1 &gt; 0)
    down_flag = (d.extra1 == 0)
    t = d.timestamp

    topper_12 = (f &gt;= 6028.552) &amp; (f &lt;= 6028.554)
    top_loss_12 = l[topper_12]
    ntopper_12 = len(l[topper_12])
    if ntopper_12 &gt; 0:
        good_topper_12 = outlierFilter(top_loss_12,3)
        tiptop_12 = mean(top_loss_12[good_topper_12])
        tipstd_12 = std(top_loss_12[good_topper_12])
        ntopper_12 = len(top_loss_12[good_topper_12])
        peakheight_0 = (tiptop_12 - base_0)
    else:
        tiptop_12 = tipstd_12 = peakheight_0 = 0.0

    peak0_spec = peakheight_0 + P0_off
        
    wd_ratio_iCH4 = 1.0 + h2o_conc_pct*(H1_wd_iCH4 + H2_wd_iCH4*h2o_conc_pct)
    peak0_spec_dry = peak0_spec/wd_ratio_iCH4
    C12H4_conc_raw_dry = C12H4_conc_raw/wd_ratio_iCH4 
    
    init["base",3] = 0
    init[8,"strength"] = 0.1556*str_0
    init[20,"strength"] = 0.07726*strength_24
    init[21,"strength"] = 0.08073*strength_24
    r = anH2O[0](d,init,deps)   #  Next fit the water region with overlaping methane
    ANALYSIS.append(r)
    shift_30 = r["base",3]
    vy_30 = r[30,"y"]
 
    if (r[30,"peak"] &gt; 10) and (abs(shift_30) &lt; 0.04) and (abs(vy_30-1.35) &lt; 0.5):
        #  If the water peak is strong and believeable, use it as is    
        adjust_30 = shift_30
    elif (r[8,"peak"] &gt; 5) and (abs(shift_30) &lt; 0.04):
        #  If water is weak but methane is strong, use methane centration and fixed nominal ys
        adjust_30 = shift_30
        init["base",3] = shift_30
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)
    else:
        #  If water and methane are both weak, use FY FC at nominal center frequency to estimate water 
        adjust_30 = 0.0
        r = anH2O[1](d,init,deps)
        ANALYSIS.append(r)

    ch4_res_w = r["std_dev_res"]
    y_30 = r[30,"y"]
    base_30 = r[30,"base"]
    peak_30 = r[30,"peak"]
    str_30 = r[30,"strength"]
    peak30_spec = peak_30 + P30_off + P30_M1*peak0_spec
    h2o_conc_pct = peak30_spec/61.0
    ch4_from_h2o = 1.5621*r[8,"peak"]
    
    init["base",3] = 0
    init[21,"strength"] = 0.08073*strength_24
    init[1002,2] = str_0   #  Now initialize (12)CH4 spline and fit the (13)CH4 triplet
    r = anCH4[2](d,init,deps)
    ANALYSIS.append(r)
    shift_5 = r["base",3]
    vy_5 = r[5,"y"]
 
    if (r[5,"peak"] &gt; 2) and (abs(shift_5) &lt; 0.04) and (abs(vy_5-1.14) &lt; 0.3):   
        adjust_5 = shift_5
        init["base",3] = shift_5
        init[5,"y"] =  0.966*y_0
    else:
        adjust_5 = 0.0
        
    r = anCH4[3](d,init,deps)
    ANALYSIS.append(r)
        
    ch4_res13 = r["std_dev_res"]
    y_5 = r[5,"y"]
    base_5 = r[5,"base"]
    peak_5 = r[5,"peak"]
     
    topper_13 = (f &gt;= 6029.102) &amp; (f &lt;= 6029.104)
    top_loss_13 = l[topper_13]
    ntopper_13 = len(l[topper_13])
    if ntopper_13 &gt; 0:
        good_topper_13 = outlierFilter(top_loss_13,3)
        tiptop_13 = mean(top_loss_13[good_topper_13])
        tipstd_13 = std(top_loss_13[good_topper_13])
        ntopper_13 = len(top_loss_13[good_topper_13])
        peakheight_5 = 0.9655*(tiptop_13 - base_5)  #Conversion from global peak to peak5 component
    else:
        tiptop_13 = tipstd_13 = peakheight_5 = 0.0
        
    init["base",3] = 0
    init[0,"strength"] = 0
    init[0,"y"] = y_0
    init[30,"strength"] = str_30
    init[30,"y"] = y_30
    init[20,"strength"] = 0.07726*strength_24
    init[21,"strength"] = 0.08073*strength_24
    init[1002,2] = str_0   #  Finally fit the entire spectrum looking for ethane on top of methane and water
    r = anCH4[4](d,init,deps)
    ANALYSIS.append(r)
    HC_res = r["std_dev_res"]
    HC_base_offset = r["base",0]-ch4_baseline_level
    HC_slope_offset = r["base",1]-ch4_baseline_slope
    HC_shift = r["base",3]
    HC_CH4_conc = 100*r[1002,2]
    HC_C12_conc = 0.40148*r[0,"peak"]
    HC_H2O_conc = r[30,"peak"]/61.0
    HC_C2H6_conc = 400*r[1003,2]
    
    #  Another postfit with more interfering species
    r = anCH4[5](d,init,deps)
    ANALYSIS.append(r)
    PPF_res = r["std_dev_res"]
    PPF_base_offset = r["base",0]-ch4_baseline_level
    PPF_slope_offset = r["base",1]-ch4_baseline_slope
    PPF_shift = r["base",3]
    PPF_CH4_conc = 100*r[1002,2]
    PPF_C12_conc = 0.40148*r[0,"peak"]
    PPF_H2O_conc = r[30,"peak"]/61.0
    PPF_C2H6_conc = 400*r[1003,2]
    PPF_C2H4_conc = r[1004,2]
    PPF_NH3_conc = 50*r[1005,2]
    PPF_H2S_conc = 1000*r[1006,2]

#  Apply corrections to isotopic peak height here for high conc mode   
#  C. Rella &amp; Y. He 20111006 changed H2O-CH4 bilinear term to P5_M1H1*peak30_spec*peakheight_5 to address enriched 13C cases     
    peak5_spec = peakheight_5 + P5_off + P5_quad*peak0_spec + P5_A1*peak24_spec + P5_H1*peak30_spec + P5_M1H1*peak30_spec*peakheight_5
    C13H4_conc_raw = 0.007772*peakheight_5

#  Calculate isotopic ratio and delta    
    try:
        c13toc12 = peakheight_5/peakheight_0
    except:
        pass
    delta_no_bookend = 1723.1*c13toc12 - 1000
    ch4_high_adjust = 0.0
    
    if last_time != None:
        interval = r["time"]-last_time
    last_time = r["time"]
    

if species in [25,150] and good25&gt;9:     #high precision CH4 at 6057.09
    if species == 25:
        fast_flag = 1       
    else:
        fast_flag = 0
    init = InitialValues()
    initialize_CFADS_Baseline()
    r = an12CH4[0](d,init,deps)
    ANALYSIS.append(r)
    if species == 25:
        if last_time != None:
            interval = r["time"]-last_time
        last_time = r["time"]    
    ch4_vy = r[1002,5]
    vch4_conc_ppmv = 10*r[1002,2]
    ch4_high_shift = r["base",3]
#  Polishing step with fixed center, variable y if line is strong and shift is small
    if (r[1002,2] &gt; 0.005) and (abs(ch4_high_shift) &lt;= 0.07):
        init["base",3] = ch4_high_shift
        ch4_high_adjust = ch4_high_shift
        r = an12CH4[1](d,init,deps)
        ANALYSIS.append(r)
#  Polishing step with fixed center and y if line is weak or shift is large
    else:    
        init["base",3] = 0.0
        ch4_high_adjust = 0.0
        init[1002,5] = 1.08
        r = an12CH4[2](d,init,deps)
        ANALYSIS.append(r)
    
    CFADS_ch4_amp = r[1002,2]
    ch4_conc_raw = 10*r[1002,2]
    CFADS_ch4_y = r[1002,5]
    CFADS_base = r["base",0]
    ch4_adjconc_ppmv = CFADS_ch4_y*ch4_conc_raw*(140.0/P)
    ch4_splinemax = r[1002,"peak"]
    ch4_peakvalue = ch4_splinemax+CFADS_base
    CFADS_base_avg  = initExpAverage(CFADS_base_avg,CFADS_base,1,100,CFADS_counter)
    ch4_peak_baseavg = ch4_peakvalue-CFADS_base_avg
    ch4_conc_ppmv_final = ch4_peak_baseavg/216.3
    
    wd_ratio_CFADS_CH4 = 1.0 + h2o_conc_pct*(H1_wd_CFADS_CH4 + H2_wd_CFADS_CH4*h2o_conc_pct)
    ch4_splinemax_dry = ch4_splinemax/wd_ratio_CFADS_CH4
    ch4_conc_ppmv_final_dry = ch4_conc_ppmv_final/wd_ratio_CFADS_CH4 
    
    ch4_res = r["std_dev_res"]
    CFADS_counter += 1           

if species == 150 and good150&gt;4 and good150&lt;10:    #  Minimal (12)CH4 for WLM offset only
    fast_flag = 1
    initialize_CH4_Baseline()
    r = anCH4[0](d,init,deps)   
    ANALYSIS.append(r)
    shift_0 = r["base",3]
    peak_0 = r[0,"peak"]
    str_0 = r[0,"strength"]
    vy_0 = r[0,"y"]
    if (peak_0 &gt; 2) and (abs(shift_0) &lt; 0.04) and (abs(vy_0-1.18) &lt; 0.3):   
        adjust_0 = shift_0
    else:
        adjust_0 = 0.0

if species == 151 and good150&gt;5:                   #  Minimal (13)CH4 for WLM offset only
    fast_flag = 1
    initialize_CH4_Baseline()
    init[1002,2] = 0.01*ch4_conc_ppmv_final
    r = anCH4[2](d,init,deps)
    ANALYSIS.append(r)
    shift_5 = r["base",3]
    peak_5 = r[5,"peak"]
    vy_5 = r[5,"y"]
    if (peak_5 &gt; 2) and (abs(shift_5) &lt; 0.04) and (abs(vy_5-1.14) &lt; 0.3):   
        adjust_5 = shift_5
    else:
        adjust_5 = 0.0

if species == 152 and good150&gt;4:                   #  Minimal water (6028.8) for WLM offset only
    fast_flag = 1
    initialize_CH4_Baseline()
    init[8,"strength"] = 0.1556*str_0
    r = anH2O[0](d,init,deps)                      #  Check this -- may need to fix peak8
    ANALYSIS.append(r)
    shift_30 = r["base",3]
    vy_30 = r[30,"y"]
 
    if (r[30,"peak"] &gt; 10) and (abs(shift_30) &lt; 0.04) and (abs(vy_30-1.35) &lt; 0.5):
        #  If the water peak is strong and believeable, use centration    
        adjust_30 = shift_30
    elif (r[8,"peak"] &gt; 5) and (abs(shift_30) &lt; 0.04):
        #  If water is weak but methane is strong, use centration
        adjust_30 = shift_30
    else:
        #  If water and methane are both weak, no WLM adjust
        adjust_30 = 0.0		
    
if species == 153:                # CO2 at 6056.5 
    fast_flag = 0
    initialize_CFADS_Baseline()
    init[1002,2] = 0.5*h2o_conc_pct
    init[1003,2] = 0.009041*C12H4_conc_raw
    r = anCO2[0](d,init,deps)
    ANALYSIS.append(r)
    shift_24 = r["base",3]
    vy_24 = r[24,"y"]
 
    if (r[24,"peak"] &gt; 5) and (abs(shift_24) &lt; 0.04) and (abs(vy_24-1.86) &lt; 0.5):   
        adjust_24 = shift_24
        init[24,"y"] = vy_24
    else:
        adjust_24 = 0.0
    
    init["base",3] = adjust_24
    r = anCO2[1](d,init,deps)
    ANALYSIS.append(r)    
    y_24 = r[24,"y"]
    strength_24 = r[24,"strength"]
    base_24 = r[24,"base"]
    peak_24 = r[24,"peak"]
    peak24_spec = peak_24 + P24_off + P24_M1*peak0_spec
    #co2_conc = 7.718*peak_24
    co2_conc = 7.718*peak24_spec

if species ==11 and d["ngroups"]&gt;9:   #H2O at 6057.8
    fast_flag = 0
    initialize_CFADS_Baseline()
    r = anH2OCFADS[0](d,init,deps)
    ANALYSIS.append(r)
    if abs(r["base",3]) &gt;= 0.01 or abs(r[75,"y"]-0.83)&gt;0.3:
        r = anH2OCFADS[1](d,init,deps)
        ANALYSIS.append(r)
    h2o_res = r["std_dev_res"]
    peak_75 = r[75,"peak"]
    h2o_quality = fitQuality(h2o_res,peak_75,50,1)
    shift_75 = r["base",3]
    ch4_from_h2o_CFADS = 100.0*r[1002,2]
    
    str_75 = r[75,"strength"]
    y_75 = r[75,"y"]
    z_75 = r[75,"z"]
    base_75 = r[75,"base"]                    
    h2o_conc = peak_75 * 0.01002
    if peak_75 &gt; 3.0 and abs(shift_75) &lt; 0.03 and h2o_quality &lt; 1.5:
        adjust_75 = shift_75
    else:
        adjust_75 = 0.0
        
    r = anH2OCFADS[2](d,init,deps)     #  Original CFADS fit included for comparison
    ANALYSIS.append(r)
    if abs(r["base",3]) &gt;= 0.01:
        r = anH2OCFADS[1](d,init,deps)
        ANALYSIS.append(r)
    CFADS_h2o_conc = r[75,"peak"] * 0.01002

    
now = time.clock()
fit_time = now-tstart
if r != None:
    IgnoreThis = False
else:
    IgnoreThis = True

if not IgnoreThis:    
    RESULT = {"ch4_res12":ch4_res12,"ch4_res13":ch4_res13,"ch4_res_w":ch4_res_w,
            "12CH4_raw":C12H4_conc_raw,"12CH4_raw_dry":C12H4_conc_raw_dry,
            "13CH4_raw":C13H4_conc_raw,"HC_res":HC_res,
            "peak0_spec":peak0_spec,"peak5_spec":peak5_spec,"peak30_spec":peak30_spec,
            "delta_no_bookend":delta_no_bookend,"c-13toc-12":c13toc12,
            "vy_0":vy_0,"y_0":y_0,"base_0":base_0,"shift_0":shift_0,"adjust_0":adjust_0,
            "vy_5":vy_5,"y_5":y_5,"base_5":base_5,"shift_5":shift_5,"adjust_5":adjust_5,
            "vy_24":vy_24,"y_24":y_24,"base_24":base_24,"shift_24":shift_24,"adjust_24":adjust_24,
            "vy_30":vy_30,"y_30":y_30,"base_30":base_30,"shift_30":shift_30,"adjust_30":adjust_30,                        
            "peak_0":peak_0,"str_0":str_0,"peak_5":peak_5,"peak_24":peak_24,"peak24_spec":peak24_spec,"peak_30":peak_30,
            "interval":interval,"datapoints":d["datapoints"],"datagroups":d["ngroups"],
            "h2o_conc_pct":h2o_conc_pct,"peak30_spec":peak30_spec,
            "ntopper_12":ntopper_12,"tiptop_12":tiptop_12,"tipstd_12":tipstd_12,
            "ntopper_13":ntopper_13,"tiptop_13":tiptop_13,"tipstd_13":tipstd_13,
            "peakheight_5":peakheight_5,"peakheight_ratio":peakheight_ratio,
            "delta_from_height":delta_from_height,"ch4_from_h2o":ch4_from_h2o,
            "species":species,"fittime":fit_time,"peakheight_0":peakheight_0,
            "HC_base_offset":HC_base_offset,"HC_slope_offset":HC_slope_offset,
            "HC_shift":HC_shift,"HC_CH4_conc":HC_CH4_conc,"HC_C12_conc":HC_C12_conc,
            "HC_H2O_conc":HC_H2O_conc,"HC_C2H6_conc":HC_C2H6_conc,
            "PPF_res":PPF_res,"PPF_base_offset":PPF_base_offset,"PPF_slope_offset":PPF_slope_offset,
            "PPF_shift":PPF_shift,"PPF_CH4_conc":PPF_CH4_conc,"PPF_H2O_conc":PPF_H2O_conc,
            "PPF_C2H6_conc":PPF_C2H6_conc,"PPF_C2H4_conc":PPF_C2H4_conc,
            "PPF_NH3_conc":PPF_NH3_conc,"PPF_H2S_conc":PPF_H2S_conc,
            "ch4_vy":ch4_vy,"ch4_high_shift":ch4_high_shift,"ch4_high_adjust":ch4_high_adjust,"CFADS_ch4_amp":CFADS_ch4_amp,
            "CFADS_ch4_y":CFADS_ch4_y,"CFADS_base":CFADS_base,"ch4_splinemax":ch4_splinemax,
            "CFADS_base_avg":CFADS_base_avg,"ch4_conc_ppmv_final":ch4_conc_ppmv_final,
            "ch4_splinemax_dry":ch4_splinemax_dry,"ch4_conc_ppmv_final_dry":ch4_conc_ppmv_final_dry,            
            "peak_75":peak_75,"shift_75":shift_75,"str_75":str_75,
            "y_75":y_75,"base_75":base_75,"h2o_conc":h2o_conc,"adjust_75":adjust_75,"CFADS_h2o_conc":CFADS_h2o_conc,"co2_conc":co2_conc,         
            "cavity_pressure":P,"cavity_temperature":T,"das_temp":dasTemp,"fast_flag":fast_flag
            }
    RESULT.update(d.sensorDict)
    RESULT["solenoid_valves"] = RESULT["ValveMask"]
</t>
<t tx="sze.20150504120336.1">#  G2000 isotopic methane fitter for the FCDS variation -- C-13/C-12 only with CFADS spectroscopy for C-12 measurement
#  Spectral IDs
#     11 -- H2O at 6057.8 (CFADS)
#    150 -- Isomethane and water vapor from 6028.4 to 6029.4 combined with CFADS methane at 6057 wvn
#    153 -- (12)CO2 at 6056.7
#  Spectral IDs added for high speed methane measurement (19 Nov 2013)
#     25 -- (12)CH4 only at 6057 wvn
#    150 -- (12)CH4 only at 6028.5 wvn
#    151 -- (13)CH4 only at 6029 wvn
#    152 -- Water vapor at 6028.8 wvn

#  09 Sep 2011:  Adapted from earlier CBDS and CFIDS fitters
#  07 Nov 2011:  New variant for potential PG&amp;E application with different schemes:  6029 and 6057 regions collected as 1 SID
#  17 Nov 2011:  Fixed a bad bug in the peak 5 WLM adjust logic.  Consolidated concentration calibration factors and adjusted to match CFADS on FCDS2003.
#  17 Nov 2011:  Changed sigma filter on WLM setpoint from 3 to 10
#  18 Nov 2011:  Changed VC water fit to fix methane y-parameter and increased minimum peak requirement for water WLM adjust.
#  01 Dec 2011:  Major change -- merged with the fitter  variant developed for PG&amp;E(R:\crd_G2000\FCDS\1061-FCDS2003\Config\20111122)
#  02 Dec 2011:  Fixed major bug in initialization of 6057 methane (high precision) fit for merged fitter.
#  06 Dec 2011:  Removed base average from CFADS CH4 fitter
#  10 Jan 2012:  Fixed y-parameter of C-13 triplet fit based on y of C-12 singlet (more stable at low concentration)
#  20 Jan 2012:  Include neighboring CO2 peaks in methane region fits to improve WLM tracking for low methane and high [CO2]
#  27 Apr 2012:  Incorporated improvements from CFIDS fitter:  (1) CO2 lines in spectral model for 6029 region;
#                (2) W/D calculation; (3) initialization of y_5 based on y_0; (4) newer spectral library
#  29 May 2012:  Removed bogus factor 0.84 from methane conc conversion in 6029 wvn region (messed up 6056 spline)
#  28 Feb 2013:  Fixed logic in shift/adjust of SID 153 (CO2 at 6056.5)
#   7 Jun 2013:  Fixed bug in HP methane -- WLM adjust was stuck when measurement 6057 wvn inactive
#  19 Nov 2013:  Start work on a version for high speed CH4 concentration measurement
#  17 Dec 2013:  Added output to distinguish high-speed from normal mode of operation
#  29 Jan 2014:  Initialized methane amplitude in water fit (peak8) using peak0 amplitude
#                Fixed minor bug in logic for adjust_0 = 0 and adjust_5 = 0.
#   3 Feb 2014:  Added PPF to isotopic (slow) mode.  Removed up/down methane reporting.
#   4 May 2015:  Changed the definition of "interval" to mean period between successive high-speed CH4 or isotopic measurements

import os.path
import time
from numpy import *

</t>
<t tx="sze.20150504120336.2">def expAverage(xavg,x,n,dxMax):
    if xavg is None: return x
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)&lt;dxMax: return y
    elif y&gt;xavg: return xavg+dxMax
    else: return xavg-dxMax

</t>
<t tx="sze.20150504120336.3">def initExpAverage(xavg,x,hi,dxMax,count):
    if xavg is None: return x
    n = min(max(count,1),hi)
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)&lt;dxMax: return y
    elif y&gt;xavg: return xavg+dxMax
    else: return xavg-dxMax

</t>
<t tx="sze.20150504120336.4">def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))
    
</t>
<t tx="sze.20150504120336.5">def outlierFilter(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = ones(x.shape,bool_)
    order = list(x.argsort())
    while len(order)&gt;minPoints:
        maxIndex = order.pop()
        good[maxIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[maxIndex]-mu)&gt;=(threshold*sigma):
            continue
        good[maxIndex] = 1
        minIndex = order.pop(0)
        good[minIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[minIndex]-mu)&gt;=(threshold*sigma):
            continue
        good[minIndex] = 1
        break
    return good
    
</t>
<t tx="sze.20150504120336.6">def initialize_CFADS_Baseline():
    init["base",1] = CFADS_baseline_slope
    init[1000,0] = CFADS_A0
    init[1000,1] = CFADS_Nu0
    init[1000,2] = CFADS_Per0
    init[1000,3] = CFADS_Phi0
    init[1001,0] = CFADS_A1
    init[1001,1] = CFADS_Nu1
    init[1001,2] = CFADS_Per1
    init[1001,3] = CFADS_Phi1
    
</t>
<t tx="sze.20150504120336.7">def initialize_CH4_Baseline():
    init["base",1] = ch4_baseline_slope
    init[1000,0] = ch4_A0
    init[1000,1] = ch4_Nu0
    init[1000,2] = ch4_Per0
    init[1000,3] = ch4_Phi0
    init[1001,0] = ch4_A1
    init[1001,1] = ch4_Nu1
    init[1001,2] = ch4_Per1
    init[1001,3] = ch4_Phi1

</t>
<t tx="sze.20150506154736.2"></t>
<t tx="sze.20150506154736.3">(uncached) sze.20150504120336.1
Diff...
  #  G2000 isotopic methane fitter for the FCDS variation -- C-13/C-12 only with CFADS spectroscopy for C-12 measurement
  #  Spectral IDs
  #     11 -- H2O at 6057.8 (CFADS)
  #    150 -- Isomethane and water vapor from 6028.4 to 6029.4 combined with CFADS methane at 6057 wvn
  #    153 -- (12)CO2 at 6056.7
  #  Spectral IDs added for high speed methane measurement (19 Nov 2013)
  #     25 -- (12)CH4 only at 6057 wvn
  #    150 -- (12)CH4 only at 6028.5 wvn
  #    151 -- (13)CH4 only at 6029 wvn
  #    152 -- Water vapor at 6028.8 wvn
  
  #  09 Sep 2011:  Adapted from earlier CBDS and CFIDS fitters
  #  07 Nov 2011:  New variant for potential PG&amp;E application with different schemes:  6029 and 6057 regions collected as 1 SID
  #  17 Nov 2011:  Fixed a bad bug in the peak 5 WLM adjust logic.  Consolidated concentration calibration factors and adjusted to match CFADS on FCDS2003.
  #  17 Nov 2011:  Changed sigma filter on WLM setpoint from 3 to 10
  #  18 Nov 2011:  Changed VC water fit to fix methane y-parameter and increased minimum peak requirement for water WLM adjust.
  #  01 Dec 2011:  Major change -- merged with the fitter  variant developed for PG&amp;E(R:\crd_G2000\FCDS\1061-FCDS2003\Config\20111122)
  #  02 Dec 2011:  Fixed major bug in initialization of 6057 methane (high precision) fit for merged fitter.
  #  06 Dec 2011:  Removed base average from CFADS CH4 fitter
  #  10 Jan 2012:  Fixed y-parameter of C-13 triplet fit based on y of C-12 singlet (more stable at low concentration)
  #  20 Jan 2012:  Include neighboring CO2 peaks in methane region fits to improve WLM tracking for low methane and high [CO2]
  #  27 Apr 2012:  Incorporated improvements from CFIDS fitter:  (1) CO2 lines in spectral model for 6029 region;
  #                (2) W/D calculation; (3) initialization of y_5 based on y_0; (4) newer spectral library
  #  29 May 2012:  Removed bogus factor 0.84 from methane conc conversion in 6029 wvn region (messed up 6056 spline)
  #  28 Feb 2013:  Fixed logic in shift/adjust of SID 153 (CO2 at 6056.5)
  #   7 Jun 2013:  Fixed bug in HP methane -- WLM adjust was stuck when measurement 6057 wvn inactive
  #  19 Nov 2013:  Start work on a version for high speed CH4 concentration measurement
  #  17 Dec 2013:  Added output to distinguish high-speed from normal mode of operation
  #  29 Jan 2014:  Initialized methane amplitude in water fit (peak8) using peak0 amplitude
  #                Fixed minor bug in logic for adjust_0 = 0 and adjust_5 = 0.
  #   3 Feb 2014:  Added PPF to isotopic (slow) mode.  Removed up/down methane reporting.
- #   4 May 2015:  Changed the definition of "interval" to mean period between successive high-speed CH4 or isotopic measurements
  
  import os.path
  import time
  from numpy import *
  
</t>
<t tx="sze.20150506154736.4">#  G2000 isotopic methane fitter for the FCDS variation -- C-13/C-12 only with CFADS spectroscopy for C-12 measurement
#  Spectral IDs
#     11 -- H2O at 6057.8 (CFADS)
#    150 -- Isomethane and water vapor from 6028.4 to 6029.4 combined with CFADS methane at 6057 wvn
#    153 -- (12)CO2 at 6056.7
#  Spectral IDs added for high speed methane measurement (19 Nov 2013)
#     25 -- (12)CH4 only at 6057 wvn
#    150 -- (12)CH4 only at 6028.5 wvn
#    151 -- (13)CH4 only at 6029 wvn
#    152 -- Water vapor at 6028.8 wvn

#  09 Sep 2011:  Adapted from earlier CBDS and CFIDS fitters
#  07 Nov 2011:  New variant for potential PG&amp;E application with different schemes:  6029 and 6057 regions collected as 1 SID
#  17 Nov 2011:  Fixed a bad bug in the peak 5 WLM adjust logic.  Consolidated concentration calibration factors and adjusted to match CFADS on FCDS2003.
#  17 Nov 2011:  Changed sigma filter on WLM setpoint from 3 to 10
#  18 Nov 2011:  Changed VC water fit to fix methane y-parameter and increased minimum peak requirement for water WLM adjust.
#  01 Dec 2011:  Major change -- merged with the fitter  variant developed for PG&amp;E(R:\crd_G2000\FCDS\1061-FCDS2003\Config\20111122)
#  02 Dec 2011:  Fixed major bug in initialization of 6057 methane (high precision) fit for merged fitter.
#  06 Dec 2011:  Removed base average from CFADS CH4 fitter
#  10 Jan 2012:  Fixed y-parameter of C-13 triplet fit based on y of C-12 singlet (more stable at low concentration)
#  20 Jan 2012:  Include neighboring CO2 peaks in methane region fits to improve WLM tracking for low methane and high [CO2]
#  27 Apr 2012:  Incorporated improvements from CFIDS fitter:  (1) CO2 lines in spectral model for 6029 region;
#                (2) W/D calculation; (3) initialization of y_5 based on y_0; (4) newer spectral library
#  29 May 2012:  Removed bogus factor 0.84 from methane conc conversion in 6029 wvn region (messed up 6056 spline)
#  28 Feb 2013:  Fixed logic in shift/adjust of SID 153 (CO2 at 6056.5)
#   7 Jun 2013:  Fixed bug in HP methane -- WLM adjust was stuck when measurement 6057 wvn inactive
#  19 Nov 2013:  Start work on a version for high speed CH4 concentration measurement
#  17 Dec 2013:  Added output to distinguish high-speed from normal mode of operation
#  29 Jan 2014:  Initialized methane amplitude in water fit (peak8) using peak0 amplitude
#                Fixed minor bug in logic for adjust_0 = 0 and adjust_5 = 0.
#   3 Feb 2014:  Added PPF to isotopic (slow) mode.  Removed up/down methane reporting.

import os.path
import time
from numpy import *

</t>
<t tx="sze.20150506154736.5">#  G2000 isotopic methane fitter for the FCDS variation -- C-13/C-12 only with CFADS spectroscopy for C-12 measurement
#  Spectral IDs
#     11 -- H2O at 6057.8 (CFADS)
#    150 -- Isomethane and water vapor from 6028.4 to 6029.4 combined with CFADS methane at 6057 wvn
#    153 -- (12)CO2 at 6056.7
#  Spectral IDs added for high speed methane measurement (19 Nov 2013)
#     25 -- (12)CH4 only at 6057 wvn
#    150 -- (12)CH4 only at 6028.5 wvn
#    151 -- (13)CH4 only at 6029 wvn
#    152 -- Water vapor at 6028.8 wvn

#  09 Sep 2011:  Adapted from earlier CBDS and CFIDS fitters
#  07 Nov 2011:  New variant for potential PG&amp;E application with different schemes:  6029 and 6057 regions collected as 1 SID
#  17 Nov 2011:  Fixed a bad bug in the peak 5 WLM adjust logic.  Consolidated concentration calibration factors and adjusted to match CFADS on FCDS2003.
#  17 Nov 2011:  Changed sigma filter on WLM setpoint from 3 to 10
#  18 Nov 2011:  Changed VC water fit to fix methane y-parameter and increased minimum peak requirement for water WLM adjust.
#  01 Dec 2011:  Major change -- merged with the fitter  variant developed for PG&amp;E(R:\crd_G2000\FCDS\1061-FCDS2003\Config\20111122)
#  02 Dec 2011:  Fixed major bug in initialization of 6057 methane (high precision) fit for merged fitter.
#  06 Dec 2011:  Removed base average from CFADS CH4 fitter
#  10 Jan 2012:  Fixed y-parameter of C-13 triplet fit based on y of C-12 singlet (more stable at low concentration)
#  20 Jan 2012:  Include neighboring CO2 peaks in methane region fits to improve WLM tracking for low methane and high [CO2]
#  27 Apr 2012:  Incorporated improvements from CFIDS fitter:  (1) CO2 lines in spectral model for 6029 region;
#                (2) W/D calculation; (3) initialization of y_5 based on y_0; (4) newer spectral library
#  29 May 2012:  Removed bogus factor 0.84 from methane conc conversion in 6029 wvn region (messed up 6056 spline)
#  28 Feb 2013:  Fixed logic in shift/adjust of SID 153 (CO2 at 6056.5)
#   7 Jun 2013:  Fixed bug in HP methane -- WLM adjust was stuck when measurement 6057 wvn inactive
#  19 Nov 2013:  Start work on a version for high speed CH4 concentration measurement
#  17 Dec 2013:  Added output to distinguish high-speed from normal mode of operation
#  29 Jan 2014:  Initialized methane amplitude in water fit (peak8) using peak0 amplitude
#                Fixed minor bug in logic for adjust_0 = 0 and adjust_5 = 0.
#   3 Feb 2014:  Added PPF to isotopic (slow) mode.  Removed up/down methane reporting.
#   4 May 2015:  Changed the definition of "interval" to mean period between successive high-speed CH4 or isotopic measurements

import os.path
import time
from numpy import *

</t>
<t tx="sze.20150506155541.1">@language python
@tabwidth -4
&lt;&lt;analyze_FBDS declarations&gt;&gt;

@others

CHEM_DETECT = 0
&lt;&lt;SystemStatus Masks&gt;&gt;
&lt;&lt;AnalyzerStatus Masks&gt;&gt;
&lt;&lt;Alarm Parameters&gt;&gt;
&lt;&lt;Setup Constants&gt;&gt;
&lt;&lt;Initialize System status flags&gt;&gt;
&lt;&lt;Valve masks&gt;&gt;

if _PERSISTENT_["init"]:
    &lt;&lt;Initialization code&gt;&gt;
    
&lt;&lt;Handle PeakDetector&gt;&gt;
&lt;&lt;Ensure sensor minimal log is not running&gt;&gt;


&lt;&lt;Handle command-line options&gt;&gt;
&lt;&lt;Get info from InstrCal file&gt;&gt;

Warmbox_setpoint = _DRIVER_.rdDasReg('WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER')
    
&lt;&lt;Analyze Fit Output Data&gt;&gt;
suppressReporting = _DATA_['fast_flag'] and _DATA_['species'] != 25

&lt;&lt;Analyze Peripheral Data&gt;&gt;
&lt;&lt;Process Instrument Status&gt;&gt;
&lt;&lt;Check data processing latency&gt;&gt;
&lt;&lt;Check if warm box temperature is within WB_TEMP_ISO_THRESHOLD of setpoint&gt;&gt;

if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    &lt;&lt;Turn off heater&gt;&gt;
    &lt;&lt;Handle anemometer anomalies&gt;&gt;
    &lt;&lt;Update wavelength monitor offsets&gt;&gt;
    
&lt;&lt;ChemDetect processing&gt;&gt;

if _DATA_["species"] in TARGET_SPECIES and _PERSISTENT_["plot_iCH4"] and not suppressReporting:
    &lt;&lt;Handle AnalyzerStatus ChemDetect mask&gt;&gt;
    &lt;&lt;Set up alarmActive when not in capture mode&gt;&gt;
    &lt;&lt;Check mobile kit flow sensor reading&gt;&gt;
    &lt;&lt;Check for unstable wind speed and correlation between car speed and wind speed&gt;&gt;
    &lt;&lt;Update AnalyzerStatus&gt;&gt;
    
&lt;&lt;Handle SystemStatus&gt;&gt;

if _DATA_["species"] in TARGET_SPECIES and _PERSISTENT_["plot_iCH4"] and not suppressReporting:
    &lt;&lt;Report persistent variables&gt;&gt;
    &lt;&lt;Execute laser ageing script&gt;&gt;
    &lt;&lt;Report DATA and NEW_DATA&gt;&gt;
</t>
<t tx="sze.20150506155630.1">#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
#              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the
#              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.
#  2011 0727 - modified isotopic methane analysis to use new schemes that report the entire spectrum in one piece
# 2014 0602 removed unnecessary sections left from CFI
#           added flag for isotopic capture when WB within .07 degC tolerance
#           improved reporting structure for Peripheral health monitoring

import os
import sys
import inspect
import traceback
import collections

from math import exp

import numpy
from numpy import mean, isfinite, isnan

from Host import PeriphIntrf
from Host.Common.EventManagerProxy import Log, LogExc
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
from Host.Common.timestamp import getTimestamp

here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path:
    sys.path.append(here)

from Chemdetect.instructionprocess import InstructionProcess # new ChemDetect
from Host.Common.CustomConfigObj import CustomConfigObj # new ChemDetect

</t>
<t tx="sze.20150506155630.2"># From fitterThread.py -- should be integrated into DM to use the "flat" .ini structure of FitterConfig.ini
def evalLeaves(d):
    for k in d:
        if isinstance(d[k],dict):
            evalLeaves(d[k])
        else:
            try:
                d[k] = eval(d[k])
            except:
                pass
    return d


</t>
<t tx="sze.20150506155630.3">def clipReportData(value):
    if value &gt; REPORT_UPPER_LIMIT:
        return REPORT_UPPER_LIMIT
    elif  value &lt; REPORT_LOWER_LIMIT:
        return REPORT_LOWER_LIMIT
    else:
        return value

</t>
<t tx="sze.20150506155630.4">def applyLinear(value,xform):
    return xform[0]*value + xform[1]

</t>
<t tx="sze.20150506155630.5">def apply2Linear(value,xform1,xform2):
    return applyLinear(applyLinear(value,xform1),xform2)

</t>
<t tx="sze.20150506155630.6">def protDivide(num,den):
    if den != 0:
        return num/den
    return 0

</t>
<t tx="sze.20150506155630.7">def expAverage(xavg,x,dt,tau):
    if xavg is None:
        xavg = x
    else:
        xavg = (1.0-exp(-dt/tau))*x + exp(-dt/tau)*xavg
    return xavg

</t>
<t tx="sze.20150506155630.8">def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] &gt; tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

</t>
<t tx="sze.20150506155630.9">def unstableWindSpeed(windSpeed):
    _PERSISTENT_['windSpeedBuffer'].append(windSpeed)
    windSpeedHistoryStd = numpy.std(_PERSISTENT_['windSpeedBuffer'], ddof=1)
    return windSpeed &gt; (2.6 * windSpeedHistoryStd)

</t>
<t tx="sze.20150506162409.1"># Handle options from command line
optDict = eval("dict(%s)" % _OPTIONS_)
conc = optDict.get("conc", "high").lower()
</t>
<t tx="sze.20150506162645.1"># Define linear transformtions for post-processing
DELTA_iCH4 = (_INSTR_["iCH4_concentration_iso_slope"],_INSTR_["iCH4_concentration_iso_intercept"])
RATIO_iCH4 = (_INSTR_["iCH4_concentration_r_slope"],_INSTR_["iCH4_concentration_r_intercept"])
C12_iCH4 = (_INSTR_["iCH4_concentration_c12_gal_slope"],_INSTR_["iCH4_concentration_c12_gal_intercept"])
C13_iCH4 = (_INSTR_["iCH4_concentration_c13_gal_slope"],_INSTR_["iCH4_concentration_c13_gal_intercept"])
C12_CH4_CFADS = (_INSTR_["CH4_CFADS_concentration_c12_gal_slope"],_INSTR_["CH4_CFADS_concentration_c12_gal_intercept"])
H2O = (_INSTR_["concentration_h2o_gal_slope"],_INSTR_["concentration_h2o_gal_intercept"])
CO2 = (_INSTR_["concentration_co2_gal_slope"],_INSTR_["concentration_co2_gal_intercept"])
DELTA_iCO2 = (_INSTR_["iCO2_concentration_iso_slope"],_INSTR_["iCO2_concentration_iso_intercept"])
RATIO_iCO2 = (_INSTR_["iCO2_concentration_r_slope"],_INSTR_["iCO2_concentration_r_intercept"])
C12_iCO2 = (_INSTR_["iCO2_concentration_c12_gal_slope"],_INSTR_["iCO2_concentration_c12_gal_intercept"])
C13_iCO2 = (_INSTR_["iCO2_concentration_c13_gal_slope"],_INSTR_["iCO2_concentration_c13_gal_intercept"])
DELTA_HIGH_CONC_iCH4 = (_INSTR_["iCH4_high_concentration_iso_slope"],_INSTR_["iCH4_high_concentration_iso_intercept"])
CH4_HIGH_THRESHOLD = _INSTR_["ch4_high_threshold"]
CH4_LOW_THRESHOLD = _INSTR_["ch4_low_threshold"]

P5_off_low_conc = _INSTR_["Peak5_offset_low_conc"]
P5_quad_low_conc = _INSTR_["Peak5_quad_low_conc"]
P5_A1_low_conc = _INSTR_["Peak5_CO2_lin_low_conc"]
P5_H1_low_conc = _INSTR_["Peak5_water_lin_low_conc"]
P5_H1M1_low_conc = _INSTR_["Peak5_water_bilin_low_conc"]

try:
    NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
except:
    NUM_BLOCKING_DATA = 20
</t>
<t tx="sze.20150506163129.1">#iCH4

_12_ch4_raw = 0.0

# Uses high concentration methane
try:
    _12_ch4_raw = _DATA_["12CH4_raw"]
    temp = applyLinear(_12_ch4_raw,C12_iCH4)
    _NEW_DATA_["12CH4_high_range"] = temp
    _NEW_DATA_["HR_12CH4"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["13CH4_raw"],C13_iCH4)  # Uses high concentration methane
    _NEW_DATA_["13CH4"] = temp
except:
    pass

# Calculate delta without CFADS laser
try:
    if _DATA_["species"] == 150:
        temp = protDivide(_DATA_["peak5_spec"],_DATA_["peak0_spec"])
        delta_high_conc_iCH4 = applyLinear(temp,DELTA_HIGH_CONC_iCH4)
        now = _OLD_DATA_["peak5_spec"][-1].time
        # calculate delta time interval
        if _PERSISTENT_["last_delta_time"] != 0:
            delta_interval = now - _PERSISTENT_["last_delta_time"]
        else:
            delta_interval = 0
        _PERSISTENT_["last_delta_time"] = now
        _PERSISTENT_["delta_high_conc_iCH4"] = delta_high_conc_iCH4
        _PERSISTENT_["delta_high_conc_iCH4_30s"] = boxAverage(_PERSISTENT_["buffer30_iCH4_high_conc"],delta_high_conc_iCH4,now,30)
        _PERSISTENT_["delta_high_conc_iCH4_2min"] = boxAverage(_PERSISTENT_["buffer120_iCH4_high_conc"],delta_high_conc_iCH4,now,120)
        _PERSISTENT_["delta_high_conc_iCH4_5min"] = boxAverage(_PERSISTENT_["buffer300_iCH4_high_conc"],delta_high_conc_iCH4,now,300)
        _PERSISTENT_["delta_interval"] = delta_interval
        # end of calculate delta time interval
        if _PERSISTENT_["num_delta_iCH4_values"] &lt;= NUM_BLOCKING_DATA:
            _PERSISTENT_["num_delta_iCH4_values"] += 1
        elif not _PERSISTENT_["plot_iCH4"]:
            _PERSISTENT_["plot_iCH4"] = True
except Exception,e:
    pass

_NEW_DATA_["HR_Delta_iCH4_Raw"] = _PERSISTENT_["delta_high_conc_iCH4"]
_NEW_DATA_["HR_Delta_iCH4_30s"] = _PERSISTENT_["delta_high_conc_iCH4_30s"]
_NEW_DATA_["HR_Delta_iCH4_2min"] = _PERSISTENT_["delta_high_conc_iCH4_2min"]
_NEW_DATA_["HR_Delta_iCH4_5min"] = _PERSISTENT_["delta_high_conc_iCH4_5min"]
_NEW_DATA_["delta_interval"] = _PERSISTENT_["delta_interval"]
_NEW_DATA_["HP_or_HR_mode"] = 1

# Calculate delta with CFADS laser
try:
    if _DATA_["species"]  == 150:
        peak5_spec_low_conc = _DATA_["peakheight_5"] + P5_off_low_conc + P5_quad_low_conc*(_DATA_["ch4_splinemax"])*(_DATA_["ch4_splinemax"])
        peak5_spec_low_conc += P5_A1_low_conc*_DATA_["peak24_spec"] + P5_H1_low_conc*_DATA_["peak30_spec"]+ P5_H1M1_low_conc*_DATA_["peak30_spec"]*_DATA_["peakheight_5"]
        temp = protDivide(peak5_spec_low_conc, _DATA_["ch4_splinemax"])
        delta_iCH4 = applyLinear(temp,DELTA_iCH4)
        _NEW_DATA_["HP_Delta_iCH4_Raw"] = delta_iCH4
        now = _OLD_DATA_["peak5_spec"][-1].time
        _NEW_DATA_["HP_Delta_iCH4_30s"] = boxAverage(_PERSISTENT_["buffer30_iCH4"],delta_iCH4,now,30)
        _NEW_DATA_["HP_Delta_iCH4_2min"] = boxAverage(_PERSISTENT_["buffer120_iCH4"],delta_iCH4,now,120)
        _NEW_DATA_["HP_Delta_iCH4_5min"] = boxAverage(_PERSISTENT_["buffer300_iCH4"],delta_iCH4,now,300)
        ratio_iCH4 = applyLinear(temp,RATIO_iCH4)
        _NEW_DATA_["Ratio_Raw_iCH4"] = ratio_iCH4
        _NEW_DATA_["Ratio_30s_iCH4"] = boxAverage(_PERSISTENT_["ratio30_iCH4"],ratio_iCH4,now,30)
        _NEW_DATA_["Ratio_2min_iCH4"] = boxAverage(_PERSISTENT_["ratio120_iCH4"],ratio_iCH4,now,120)
        _NEW_DATA_["Ratio_5min_iCH4"] = boxAverage(_PERSISTENT_["ratio300_iCH4"],ratio_iCH4,now,300)
    else:
        _NEW_DATA_["HP_Delta_iCH4_Raw"] = _OLD_DATA_["HP_Delta_iCH4_Raw"][-1].value
        _NEW_DATA_["HP_Delta_iCH4_30s"] = _OLD_DATA_["HP_Delta_iCH4_30s"][-1].value
        _NEW_DATA_["HP_Delta_iCH4_2min"] = _OLD_DATA_["HP_Delta_iCH4_2min"][-1].value
        _NEW_DATA_["HP_Delta_iCH4_5min"] = _OLD_DATA_["HP_Delta_iCH4_5min"][-1].value
        _NEW_DATA_["Ratio_Raw_iCH4"] = _OLD_DATA_["Ratio_Raw_iCH4"][-1].value
        _NEW_DATA_["Ratio_30s_iCH4"] = _OLD_DATA_["Ratio_30s_iCH4"][-1].value
        _NEW_DATA_["Ratio_2min_iCH4"] = _OLD_DATA_["Ratio_2min_iCH4"][-1].value
        _NEW_DATA_["Ratio_5min_iCH4"] = _OLD_DATA_["Ratio_5min_iCH4"][-1].value
except Exception,e:
    print "Error %s (%r)" % (e,e) #For VA: Errors happened are "deque index out of range" (due to IF line) (probably because there are no '-3' and '-2'
        #at the beginning of data) and "KeyError('Delta_Raw_iCH4',)" due to Delta_Raw_iCH4 line at the beginning of ELSE section

if "HP_Delta_iCH4_Raw" in _NEW_DATA_:
    _PERSISTENT_["Delta_iCH4_Raw"] = _NEW_DATA_["HP_Delta_iCH4_Raw"]

_NEW_DATA_["Delta_iCH4_Raw"] = _PERSISTENT_["Delta_iCH4_Raw"]

try:
    temp = applyLinear(_DATA_["h2o_conc_pct"],H2O)
    _NEW_DATA_["H2O"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["co2_conc"],CO2)
    _NEW_DATA_["CO2"] = temp
except:
    pass

# Uses low concentration methane (CFADS)
try:
    temp = applyLinear(_DATA_["ch4_conc_ppmv_final"],C12_CH4_CFADS)
    _NEW_DATA_["HP_12CH4"] = temp
    _DATA_["CH4"] = temp
except:
    pass

for v in ['HC_res2_a1', 'HC_res2_diff', 'HC_res2', 'HC_base_offset2_a1', 'HC_base_offset2_diff', 'HC_base_offset2']:
    _NEW_DATA_[v] = 0 # so these always exist in slow or fast modes
    
try: # new ChemDetect section
    Cor_HP_HCres_CO2 = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HP_HCres_CO2']
    Cor_HP_HCbaseoffset_H2O = _PERSISTENT_["chemdetect_inst"].current_var_values['Cor_HP_HCbaseoffset_H2O']
    _NEW_DATA_["HC_res2"] = _DATA_["HC_res"] - Cor_HP_HCres_CO2 * _NEW_DATA_["CO2"] # CO2 Correction on HC_res
    _NEW_DATA_["HC_base_offset2"]= _DATA_["HC_base_offset"] - Cor_HP_HCbaseoffset_H2O * _NEW_DATA_["H2O"] # H2O Cor on HC_base_offset
    a0_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_base_offset2_HP']
    a1_HC_base_offset2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_base_offset2_HP']
    a0_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a0_HC_res2_HP']
    a1_HC_res2 = _PERSISTENT_["chemdetect_inst"].current_var_values['a1_HC_res2_HP']

    HC_base_offset2_fit = a0_HC_base_offset2 + _NEW_DATA_["12CH4_high_range"] * a1_HC_base_offset2 #fit params obtained from 3D data 2011-09-25
    _NEW_DATA_["HC_base_offset2_diff"]= _NEW_DATA_["HC_base_offset2"] - HC_base_offset2_fit
    _NEW_DATA_["HC_base_offset2_a1"] = (_NEW_DATA_["HC_base_offset2"] - a0_HC_base_offset2) / _NEW_DATA_["12CH4_high_range"]
    HC_res2_fit = a0_HC_res2 + _NEW_DATA_["12CH4_high_range"] * a1_HC_res2  #fit params obtained from 3D data on 2011-09-25
    _NEW_DATA_["HC_res2_diff"] = _NEW_DATA_["HC_res2"] - HC_res2_fit
    _NEW_DATA_["HC_res2_a1"] = (_NEW_DATA_["HC_res2"] - a0_HC_res2) / _NEW_DATA_["12CH4_high_range"]
except:
    pass
try:
    _DATA_["CH4up"] = _DATA_["12CH4_up"]
    _DATA_["CH4down"] = _DATA_["12CH4_down"]
    _DATA_["CH4dt"] = _DATA_["C12H4_time_separation"]
except:
    pass
</t>
<t tx="sze.20150506163215.1"># Get peripheral data
try:
    if _PERIPH_INTRF_:
        try:
            interpData = _PERIPH_INTRF_( _DATA_["timestamp"], _PERIPH_INTRF_COLS_)
            for i in range(len(_PERIPH_INTRF_COLS_)):
                if interpData[i] is not None:
                    _NEW_DATA_[_PERIPH_INTRF_COLS_[i]] = interpData[i]
        except Exception, err:
            print "%r" % err
except:
    pass
</t>
<t tx="sze.20150506163404.1"># Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ &amp; INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ &amp; INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ &amp; INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ &amp; INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ &amp; INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
</t>
<t tx="sze.20150506163500.1">nowTs = getTimestamp()
delay = nowTs-_DATA_["timestamp"]
if delay &gt; max_delay*1000:
    Log("Large data processing latency, check excessive processor use",
        Data=dict(delay='%.1f s' % (0.001*delay,)),Level=2)
    good = False
</t>
<t tx="sze.20150506163547.1">if _DATA_['WarmBoxTemp'] &gt; Warmbox_setpoint - WB_TEMP_ISO_THRESHOLD and _DATA_['WarmBoxTemp'] &lt; Warmbox_setpoint + WB_TEMP_ISO_THRESHOLD:
    WBisoTempLocked = True
else:
    WBisoTempLocked = False
</t>
<t tx="sze.20150506163653.1"># Turn off heater on first good data
if _PERSISTENT_["turnOffHeater"]:
    Log("Heater turned off")
    _DRIVER_.wrDasReg("HEATER_TEMP_CNTRL_STATE_REGISTER","HEATER_CNTRL_DisabledState")
    _PERSISTENT_["turnOffHeater"] = False
</t>
<t tx="sze.20150506163722.1"># Wind anomaly handling
validWindCheck = True
windFields = ['PERIPHERAL_STATUS', 'CAR_SPEED', 'GPS_FIT']

for f in windFields:
    validWindCheck &amp;= (f in _NEW_DATA_)

if validWindCheck:
    if (int(_NEW_DATA_['PERIPHERAL_STATUS']) &amp; PeriphIntrf.PeripheralStatus.PeripheralStatus.WIND_ANOMALY) &gt; 0:
        if not isnan(_NEW_DATA_['CAR_SPEED']) and _NEW_DATA_['GPS_FIT'] == GPS_GOOD:
            Log("Wind NaN due to anomaly")
            _PERSISTENT_['inactiveForWind'] = True

        else:
            Log("Wind NaN due to GPS")
    else:
        if _PERSISTENT_['inactiveForWind']:
            Log("Survey status back to active after wind anomaly")
            _PERSISTENT_['inactiveForWind'] = False
</t>
<t tx="sze.20150506163829.1">if _DATA_["species"] == 150: # Update the offset for virtual laser 3,4,5
    try:
        ch4_adjust = _DATA_["adjust_5"]
        ch4_adjust = min(max_adjust,max(-max_adjust,damp*ch4_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(3) + ch4_adjust
        _NEW_DATA_["wlm3_offset"] = newOffset0
        _PERSISTENT_["wlm3_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
    except:
        pass

    try:
        ch4_adjust = _DATA_["adjust_0"]
        ch4_adjust = min(max_adjust,max(-max_adjust,damp*ch4_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(4) + ch4_adjust
        _NEW_DATA_["wlm4_offset"] = newOffset0
        _PERSISTENT_["wlm4_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(4,float(newOffset0))
    except:
        pass

    try:
        h2o_adjust = _DATA_["adjust_30"]
        h2o_adjust = min(max_adjust,max(-max_adjust,damp*h2o_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(5) + h2o_adjust
        _NEW_DATA_["wlm5_offset"] = newOffset0
        _PERSISTENT_["wlm5_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
    except:
        pass

    try:
        ch4_high_adjust = _DATA_["ch4_high_adjust"]
        ch4_high_adjust = min(max_adjust,max(-max_adjust,damp*ch4_high_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(8) + ch4_high_adjust
        _NEW_DATA_["wlm8_offset"] = newOffset0
        _PERSISTENT_["wlm8_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(8,float(newOffset0))
    except:
        pass

elif _DATA_["species"] == 11: # Update the offset for virtual laser 7
    try:
        h2o_adjust = _DATA_["adjust_75"]
        h2o_adjust = min(max_adjust,max(-max_adjust,damp*h2o_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(7) + h2o_adjust
        _NEW_DATA_["wlm7_offset"] = newOffset0
        _PERSISTENT_["wlm7_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(7,float(newOffset0))
    except:
        pass

elif _DATA_["species"] == 153: # Update the offset for virtual laser 6
    try:
        co2_adjust = _DATA_["adjust_24"]
        co2_adjust = min(max_adjust,max(-max_adjust,damp*co2_adjust))
        newOffset0 = _FREQ_CONV_.getWlmOffset(6) + co2_adjust
        _NEW_DATA_["wlm6_offset"] = newOffset0
        _PERSISTENT_["wlm6_offset"] = newOffset0
        _FREQ_CONV_.setWlmOffset(6,float(newOffset0))
    except:
        pass
</t>
<t tx="sze.20150506164313.1"># Save all the variables defined in the _OLD_DATA_  and  _NEW_DATA_ arrays in the
# _PERSISTENT_ arrays so that they can be used in the ChemDetect spreadsheet.
for colname in _OLD_DATA_:    #  new ChemDetect section
    _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _OLD_DATA_[colname][-1].value

for colname in _NEW_DATA_:
    _PERSISTENT_["chemdetect_inst"].current_var_values[colname] = _NEW_DATA_[colname]

if _OLD_DATA_["species"][-1].value == 150 and not _DATA_['fast_flag']:
    _PERSISTENT_["chemdetect_inst"].process_set()

    if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
        pass
        #print "WARNING: ChemDetect Status is RED"
</t>
<t tx="sze.20150506164529.1">if 'MOBILE_FLOW' in _DATA_:
    if _DATA_['MOBILE_FLOW'] == IntakeFlowRateDisconnected:
        AnalyzerStatus |= AnalyzerStatusIntakeFlowDisconnected

    elif _DATA_['MOBILE_FLOW'] &lt; IntakeFlowRateMin and alarmActive and alarmActiveState:
        AnalyzerStatus |= AnalyzerStatusIntakeFlowRateMask

    elif _DATA_['MOBILE_FLOW'] &gt; IntakeFlowRateMax and alarmActive and alarmActiveState:
        AnalyzerStatus |= AnalyzerStatusIntakeFlowRateMask
</t>
<t tx="sze.20150506164740.1">windSpeed = 0.0
if ('WIND_N' in _DATA_) and ('WIND_E' in _DATA_):

    if (not numpy.isnan(_DATA_['WIND_N'])) and (not numpy.isnan(_DATA_['WIND_E'])):
        windN = _DATA_['WIND_N']
        windE = _DATA_['WIND_E']
        windSpeed = numpy.sqrt(windN * windN + windE * windE)

    if unstableWindSpeed(windSpeed):
        PeripheralStatus |= PeriphIntrf.PeripheralStatus.PeripheralStatus.WIND_UNSTABLE

carSpeed = 0.0
if ('CAR_VEL_N' in _DATA_) and ('CAR_VEL_E' in _DATA_):

    if (not numpy.isnan(_DATA_['CAR_VEL_N'])) and (not numpy.isnan(_DATA_['CAR_VEL_E'])):
        carN = _DATA_['CAR_VEL_N']
        carE = _DATA_['CAR_VEL_E']
        carSpeed = numpy.sqrt(carN * carN + carE * carE)

if carSpeed &gt; CarSpeedMaximum:
    PeripheralStatus |= PeriphIntrf.PeripheralStatus.PeripheralStatus.CAR_SPEED_TOO_LARGE
</t>
<t tx="sze.20150506164942.1"># Check for the interval between methane data points and set the AnalyzerStatusDataRateMask if the exponentially averaged rate
#  is too slow

tooSlow = False
dt = _DATA_['interval']
if _DATA_['SpectrumID'] == FastMethaneSpectrumId:
    if _DATA_["CH4"] &gt; MethaneConcThreshold:
        dt = 0.25
    _PERSISTENT_["fastMethaneInterval"] = expAverage(_PERSISTENT_["fastMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
    tooSlow = _PERSISTENT_["fastMethaneInterval"] &gt; FastMethaneIntervalMax
elif _DATA_['SpectrumID'] == IsotopicMethaneSpectrumId:
    if _DATA_["CH4"] &gt; MethaneConcThreshold:
        dt = 1.0
    _PERSISTENT_["isotopicMethaneInterval"] = expAverage(_PERSISTENT_["isotopicMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
    tooSlow = _PERSISTENT_["isotopicMethaneInterval"] &gt; IsotopicMethaneIntervalMax
if tooSlow:
    AnalyzerStatus |= AnalyzerStatusDataRateMask

if _DATA_['CFADS_base'] &gt; CavityBaselineLossScaleFactor * _PERSISTENT_['baselineCavityLoss']:
    AnalyzerStatus |= AnalyzerStatusCavityBaselineLossMask

if (_NEW_DATA_['delta_interval'] &gt; DeltaIntervalMax) and (not alarmActive) and alarmActiveState:
    AnalyzerStatus |= AnalyzerStatusSamplingIntervalMask

if _DATA_['spect_latency'] &gt; SpectrumLatencyMax:
    AnalyzerStatus |= AnalyzerStatusRingdownRateMask

if numpy.absolute(_DATA_['ch4_high_shift']) &gt; WlmShiftMax:
    AnalyzerStatus |= AnalyzerStatusWlmShiftMask

if numpy.absolute(_DATA_['ch4_high_adjust']) &gt; WlmAdjustMax:
    AnalyzerStatus |= AnalyzerStatusWlmAdjustMask

if (numpy.absolute(_DATA_['ch4_high_shift']) &gt;= WlmShiftAdjustLimit) and (numpy.absolute(_DATA_['ch4_high_adjust']) &lt; WlmShiftAdjustLimit):
    AnalyzerStatus |= AnalyzerStatusWlmShiftAdjustCorrelationMask

_PERSISTENT_['wlmOffsetBuffer'].append(_PERSISTENT_['wlm6_offset'])
wlm6OffsetMean = numpy.mean(_PERSISTENT_['wlmOffsetBuffer'])
wlm6OffsetMax = max(_PERSISTENT_['wlmOffsetBuffer'])
wlm6OffsetMin = min(_PERSISTENT_['wlmOffsetBuffer'])

if wlm6OffsetMean != 0.0:
    if ((wlm6OffsetMax - wlm6OffsetMin) / wlm6OffsetMean) &gt; WlmTargetFreqMaxDrift:
        AnalyzerStatus |= AnalyzerStatusWlmTargetFreqMask
        
# Set the InvalidData mask in the AnalyzerStatus. Currently it is set only if the data rate is too low.
if 0 != (AnalyzerStatus &amp; AnalyzerStatusDataRateMask):
    AnalyzerStatus |= AnalyzerStatusInvalidDataMask

        
</t>
<t tx="sze.20150506165859.1">SystemStatusPeripheralMask = 0x00000001
SystemStatusAnalyzerMask = 0x00000002
</t>
<t tx="sze.20150506165934.1">AnalyzerStatusIntakeFlowRateMask = 0x00000001
AnalyzerStatusCavityBaselineLossMask = 0x00000002
AnalyzerStatusSamplingIntervalMask = 0x00000004
AnalyzerStatusRingdownRateMask = 0x00000008
AnalyzerStatusWlmShiftMask = 0x00000010
AnalyzerStatusWlmAdjustMask = 0x00000020
AnalyzerStatusWlmShiftAdjustCorrelationMask = 0x00000040
AnalyzerStatusWlmTargetFreqMask = 0x00000080
AnalyzerStatusIntakeFlowDisconnected = 0x00000100
AnalyzerStatusChemDetectMask = 0x00000200
AnalyzerStatusDataRateMask = 0x00000400
# The following bit invalidates the data (shown as a red path)
AnalyzerStatusInvalidDataMask = 0x80000000
</t>
<t tx="sze.20150506170022.1"># Alarm parameters
IntakeFlowRateMin = 3.75
IntakeFlowRateMax = 5.0
IntakeFlowRateDisconnected = -9999.0
WindSpeedHistoryBufferLen = 100
CarSpeedMaximum = 35.0
DeltaIntervalMax = 1.6
SpectrumLatencyMax = 3.0
WlmShiftMax = 2e-3
WlmAdjustMax = 2e-3
WlmShiftAdjustLimit = 5e-5
WlmTargetFreqMaxDrift = 0.05
WlmTargetFreqHistoryBufferLen = 6000
CavityBaselineLossScaleFactor = 1.1
FastMethaneIntervalMax = 0.4
IsotopicMethaneIntervalMax = 1.6
</t>
<t tx="sze.20150506170104.1"># System status flags
SystemStatus = 0x00000000
AnalyzerStatus = 0x00000000
PeripheralStatus = 0x00000000
</t>
<t tx="sze.20150506170135.1"># Valve masks
VALVE_MASK_ACTIVE = 0x10
VALVE_MASK_CHECK_ALARM = 0x03
</t>
<t tx="sze.20150506170401.1">_PERSISTENT_["turnOffHeater"] = True
_PERSISTENT_["wlm1_offset"] = 0.0
_PERSISTENT_["wlm2_offset"] = 0.0
_PERSISTENT_["wlm3_offset"] = 0.0
_PERSISTENT_["wlm4_offset"] = 0.0
_PERSISTENT_["wlm5_offset"] = 0.0
_PERSISTENT_["wlm6_offset"] = 0.0
_PERSISTENT_["wlm7_offset"] = 0.0
_PERSISTENT_["wlm8_offset"] = 0.0
_PERSISTENT_["buffer30_iCH4"]  = []
_PERSISTENT_["buffer120_iCH4"] = []
_PERSISTENT_["buffer300_iCH4"] = []
_PERSISTENT_["buffer30_iCH4_high_conc"] = []
_PERSISTENT_["buffer120_iCH4_high_conc"] = []
_PERSISTENT_["buffer300_iCH4_high_conc"] = []
_PERSISTENT_["ratio30_iCH4"]  = []
_PERSISTENT_["ratio120_iCH4"] = []
_PERSISTENT_["ratio300_iCH4"] = []
_PERSISTENT_["buffer30_iCO2"]  = []
_PERSISTENT_["buffer120_iCO2"] = []
_PERSISTENT_["buffer300_iCO2"] = []
_PERSISTENT_["ratio30_iCO2"]  = []
_PERSISTENT_["ratio120_iCO2"] = []
_PERSISTENT_["ratio300_iCO2"] = []
_PERSISTENT_["init"] = False
_PERSISTENT_["num_delta_iCH4_values"] = 0
_PERSISTENT_["num_delta_iCO2_values"] = 0
_PERSISTENT_["plot_iCH4"] = False
_PERSISTENT_["plot_iCO2"] = False
_PERSISTENT_["last_delta_time"] = 0
_PERSISTENT_["delta_high_conc_iCH4"] = 0
_PERSISTENT_["delta_high_conc_iCH4_30s"] = 0
_PERSISTENT_["delta_high_conc_iCH4_2min"] = 0
_PERSISTENT_["delta_high_conc_iCH4_5min"] = 0
_PERSISTENT_["delta_interval"] = 0
_PERSISTENT_["Delta_iCH4_Raw"] = 0.0
_PERSISTENT_["fineLaserCurrent_6_mean"] = 0
_PERSISTENT_["windSpeedBuffer"] = collections.deque(maxlen=WindSpeedHistoryBufferLen)
_PERSISTENT_["wlmOffsetBuffer"] = collections.deque(maxlen=WlmTargetFreqHistoryBufferLen)
_PERSISTENT_["peakDetectState"] = collections.deque(maxlen=50)
_PERSISTENT_["fastMethaneInterval"] = 0.0
_PERSISTENT_["isotopicMethaneInterval"] = 0.0

WBisoTempLocked = False

# For ChemDetect
_PERSISTENT_["chemdetect_inst"] = InstructionProcess()
configFile = os.path.join(here,"..\..\..\InstrConfig\Calibration\InstrCal\ChemDetect\ChemDetect.ini")
configPath = os.path.split(configFile)[0]

config = CustomConfigObj(configFile)
# Get the ChemDetect excel file name from the ini file
ChemDetect_FileName = config.get("Main", "ChemDetect_FileName") 
_PERSISTENT_["chemdetect_inst"].load_set_from_csv(os.path.join(configPath,ChemDetect_FileName))
# need to replace with self.instruction_path
_PERSISTENT_["ChemDetect_previous"] = 0.0

_PERSISTENT_['outletValve_min'] = _DRIVER_.rdDasReg(
    'VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER')
_PERSISTENT_['outletValve_max'] = _DRIVER_.rdDasReg(
    'VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER')

_PERSISTENT_['inactiveForWind'] = False

#For Laser Aging
script = "adjustTempOffset.py"
scriptRelPath = os.path.join(here, '..', '..', '..', 'CommonConfig',
                             'Scripts', 'DataManager', script)
cp = file(os.path.join(here, scriptRelPath), "rU")
codeAsString = cp.read() + "\n"
cp.close()
_PERSISTENT_["adjustOffsetScript"] = compile(codeAsString, script, 'exec')

fitterConfigFile = os.path.join(here, '..', '..', '..', 'InstrConfig', 'Calibration', 'InstrCal', 'FitterConfig.ini')
fitterConfig = evalLeaves(CustomConfigObj(fitterConfigFile, list_values=False).copy())
_PERSISTENT_['baselineCavityLoss'] = fitterConfig['CFADS_baseline']
</t>
<t tx="sze.20150506170534.1"># read peak detect state register
# # Enumerated definitions for PEAK_DETECT_CNTRL_StateType
# PEAK_DETECT_CNTRL_StateType = c_uint
# PEAK_DETECT_CNTRL_IdleState = 0 # Idle
# PEAK_DETECT_CNTRL_ArmedState = 1 # Armed
# PEAK_DETECT_CNTRL_TriggerPendingState = 2 # Trigger Pending
# PEAK_DETECT_CNTRL_TriggeredState = 3 # Triggered
# PEAK_DETECT_CNTRL_InactiveState = 4 # Inactive
# PEAK_DETECT_CNTRL_CancellingState = 5 # Cancelling
# PEAK_DETECT_CNTRL_PrimingState = 6 # Priming
# PEAK_DETECT_CNTRL_PurgingState = 7 # Purging
# PEAK_DETECT_CNTRL_InjectionPendingState = 8 # Injection Pending
peakDetectState = _DRIVER_.rdDasReg('PEAK_DETECT_CNTRL_STATE_REGISTER') #integer value, see interface.py
_PERSISTENT_["peakDetectState"].append(peakDetectState)
#read peak detect register to get number of remaining samples
remainingPeakSamples = _DRIVER_.rdDasReg('PEAK_DETECT_CNTRL_REMAINING_TRIGGERED_SAMPLES_REGISTER') #number of samples integer, samples are 0.2 seconds
</t>
<t tx="sze.20150506170721.1">try:
    if _DATA_LOGGER_ and _DATA_LOGGER_.DATALOGGER_logEnabledRpc('DataLog_Sensor_Minimal'):
        try:
            _DATA_LOGGER_.DATALOGGER_stopLogRpc("DataLog_Sensor_Minimal")
        except Exception, err:
            pass###print "_DATA_LOGGER_ Error: %r" % err
except:
    pass
</t>
<t tx="sze.20150506181637.1"># Update the upper alarm status bits with some additional instrument status
# flags.
alarmActive = (int(_DATA_['ValveMask']) &amp; VALVE_MASK_CHECK_ALARM) == 0

alarmActiveState = numpy.sum( numpy.abs( numpy.diff(_PERSISTENT_["peakDetectState"]) ) ) &lt; 1
###print "alarmActive: " + str(alarmActive) + ", alarmActiveState: " + str(alarmActiveState)
</t>
<t tx="sze.20150506181818.1">if _OLD_DATA_["species"][-1].value == 150:
    if _PERSISTENT_["chemdetect_inst"].current_var_values['RED'] == True:
        CHEM_DETECT = 1.0  # BAD data
    else:
        CHEM_DETECT = 0.0  # Good data
else:
    CHEM_DETECT = _PERSISTENT_["ChemDetect_previous"]

_PERSISTENT_["ChemDetect_previous"] = CHEM_DETECT
if CHEM_DETECT == 1.0:
    AnalyzerStatus |= AnalyzerStatusChemDetectMask
</t>
<t tx="sze.20150506181904.1">if ('PERIPHERAL_STATUS' in _NEW_DATA_) and (int(_NEW_DATA_['PERIPHERAL_STATUS'])) &gt; 0:
    SystemStatus |= SystemStatusPeripheralMask

if AnalyzerStatus &gt; 0:
    SystemStatus |= SystemStatusAnalyzerMask
</t>
<t tx="sze.20150506182103.1">_REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
_REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
_REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
_REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
_REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]
_REPORT_["wlm6_offset"] = _PERSISTENT_["wlm6_offset"]
_REPORT_["wlm7_offset"] = _PERSISTENT_["wlm7_offset"]
_REPORT_["wlm8_offset"] = _PERSISTENT_["wlm8_offset"]
_REPORT_["SystemStatus"] = SystemStatus
if 'PERIPHERAL_STATUS' in _NEW_DATA_:
    _REPORT_['PeripheralStatus'] = PeripheralStatus | int(_NEW_DATA_['PERIPHERAL_STATUS'])
_REPORT_['AnalyzerStatus'] = AnalyzerStatus
_REPORT_["CHEM_DETECT"] = CHEM_DETECT
_REPORT_["WBisoTempLocked"] = WBisoTempLocked
_REPORT_["fineLaserCurrent_6_mean"] = _PERSISTENT_["fineLaserCurrent_6_mean"]  #report 0 for VL6 made to prevent new Column upon mode switch when WL is on to track CO2
_REPORT_["fastMethaneInterval"] = _PERSISTENT_["fastMethaneInterval"]
_REPORT_["isotopicMethaneInterval"] = _PERSISTENT_["isotopicMethaneInterval"]
</t>
<t tx="sze.20150506182135.1">for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    if k.startswith("Delta"):
        _REPORT_[k] = clipReportData(_NEW_DATA_[k])
    else:
        _REPORT_[k] = _NEW_DATA_[k]
</t>
<t tx="sze.20150506182201.1">exec _PERSISTENT_["adjustOffsetScript"] in globals()
</t>
<t tx="sze.20150506185525.1">@language python</t>
<t tx="sze.20150506194536.1"># Limits for delta values reported
REPORT_UPPER_LIMIT = 20000.0
REPORT_LOWER_LIMIT = -20000.0
# WB Temperature Proximity condition for isotopic measurement
WB_TEMP_ISO_THRESHOLD = 0.07
# SpectrumIds used
TARGET_SPECIES = [11, 25, 105, 106, 150, 153]
# Parameters for updating WLM Offsets
max_adjust = 1.0e-5
max_adjust_H2O = 1.0e-4
damp = 0.2
# Maximum delay before signalling data manager latency
max_delay = 20
# Constants for calculating mean interval between data points
FastMethaneSpectrumId = 25
IsotopicMethaneSpectrumId = 150
MethaneIntervalAveragingTime = 30.0
MethaneConcThreshold = 5.0
</t>
<t tx="sze.20150507075702.1">@language python
@tabwidth -4
@others
</t>
<t tx="sze.20150507075745.1">import numpy as np
import pyodbc

</t>
<t tx="sze.20150507075745.2">def getAnalyzerId(analyzer):
    
    # constructing and running query
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    analyzerId = None
    cursor.execute("""
        SELECT Id
            FROM [SurveyorEngineering].[dbo].[Analyzer]
            WHERE SerialNumber = '%s'
    """ % analyzer)
    for row in cursor:
        analyzerId = row[0]
    return analyzerId

</t>
<t tx="sze.20150507075745.3">def getSurveysForAnalyzer(analyzer,center,radius,num_points=20):
    
    angles = np.linspace(0.0,2*np.pi,num_points+1)[:-1]
    vectors = [cmath.rect(radius,angles[i]) for i in xrange(len(angles))]
    outline = [coordinatePlusDistance(center,vectors[i].real,vectors[i].imag)
              for i in xrange(len(vectors))]
    outline.append(outline[0])
    lat , lng = zip(*outline)
    outline = zip(lng,lat)
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    surveys = []
    start_epochs = []
    end_epochs = []
    cursor.execute("""
    
        declare @bounds geometry = geometry::STGeomFromText('POLYGON((%s))', 4326);
    
        SELECT DISTINCT Segment.SurveyId , Survey.StartEpoch, Survey.EndEpoch
        FROM     Segment INNER JOIN
                          Survey ON Segment.SurveyId = Survey.Id
        WHERE  (Segment.Shape.MakeValid().STIntersects(@bounds) = 1)
        AND   (Survey.AnalyzerId='%s')
        
    """ % (','.join([str(v[0])+' '+str(v[1]) for v in outline ]),analyzer_ID))
    for row in cursor:
        surveys.append(row[0])
        start_epochs.append(row[1])
        end_epochs.append(row[2])
        
    return surveys , start_epochs , end_epochs

 def getRelevantSurveyData(start_epoch,end_epoch,analyzer,center,radius,num_points):
    
    angles = np.linspace(0.0,2*np.pi,num_points+1)[:-1]
    vectors = [cmath.rect(radius,angles[i]) for i in xrange(len(angles))]
    outline = [coordinatePlusDistance(center,vectors[i].real,vectors[i].imag)
              for i in xrange(len(vectors))]
    outline.append(outline[0])
    lat , lng = zip(*outline)
    outline = zip(lng,lat)
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    min_data = {
    'EPOCH_TIME':[],
    'CH4': [],
    'GPS_ABS_LAT': [],
    'GPS_ABS_LONG': [],
    'CAR_VEL_N': [],
    'CAR_VEL_E': [],
    'WS_WIND_LAT': [],
    'WS_WIND_LON': [],
    'WIND_N': [],
    'WIND_E': [],
    'WIND_DIR_SDEV': [],
    }
    
    cursor.execute("""
    
        declare @bounds geometry = geometry::STGeomFromText('POLYGON((%s))', 4326);
    
        SELECT [EpochTime]
              ,[GpsLatitude]
              ,[GpsLongitude]
              ,[CarSpeedNorth]
              ,[CarSpeedEast]
              ,[WindSpeedNorth]
              ,[WindSpeedEast]
              ,[WindDirectionStdDev]
              ,[WindSpeedLateral]
              ,[WindSpeedLongitudinal]
              ,[CH4]
        FROM [SurveyorEngineering].[dbo].[Measurement]
        WHERE (EpochTime BETWEEN '%s' AND '%s')
        AND (AnalyzerId = '%s')
        AND (Shape.STIntersects(@bounds) = 1)
        AND (GpsFit=2)
        
    """ % (','.join([str(v[0])+' '+str(v[1]) for v in outline ]),str(start_epoch),str(end_epoch),analyzer_ID))
    
    for row in cursor:
        min_data['EPOCH_TIME'].append(row[0])
        min_data['GPS_ABS_LAT'].append(row[1])
        min_data['GPS_ABS_LONG'].append(row[2])
        min_data['CAR_VEL_N'].append(row[3])
        min_data['CAR_VEL_E'].append(row[4])
        min_data['WIND_N'].append(row[5])
        min_data['WIND_E'].append(row[6])
        min_data['WIND_DIR_SDEV'].append(row[7])
        min_data['WS_WIND_LAT'].append(row[8])
        min_data['WS_WIND_LON'].append(row[9])
        min_data['CH4'].append(row[10])
    for key in min_data.keys():
        min_data[key] = np.asarray(min_data[key])[::-1]
    min_data['CAR_SPEED'] = np.sqrt(min_data['CAR_VEL_N']**2+min_data['CAR_VEL_E']**2)
    
    return min_data

</t>
<t tx="sze.20150507075745.4">def getSurveyMinData(start_epoch,end_epoch,analyzer,plot=False):
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    min_data = {
    'EPOCH_TIME':[],
    'CH4': [],
    'GPS_ABS_LAT': [],
    'GPS_ABS_LONG': [],
    'CAR_VEL_N': [],
    'CAR_VEL_E': [],
    'WS_WIND_LAT': [],
    'WS_WIND_LON': [],
    'WIND_N': [],
    'WIND_E': [],
    'WIND_DIR_SDEV': [],
    }
    
    cursor.execute("""
    
        SELECT [EpochTime]
              ,[GpsLatitude]
              ,[GpsLongitude]
              ,[CarSpeedNorth]
              ,[CarSpeedEast]
              ,[WindSpeedNorth]
              ,[WindSpeedEast]
              ,[WindDirectionStdDev]
              ,[WindSpeedLateral]
              ,[WindSpeedLongitudinal]
              ,[CH4]
        FROM [SurveyorEngineering].[dbo].[Measurement]
        WHERE (EpochTime BETWEEN '%s' AND '%s')
        AND (AnalyzerId = '%s')
        AND (GpsFit=2)
        
    """ % (str(start_epoch),str(end_epoch),analyzer_ID))
    
    for row in cursor:
        min_data['EPOCH_TIME'].append(row[0])
        min_data['GPS_ABS_LAT'].append(row[1])
        min_data['GPS_ABS_LONG'].append(row[2])
        min_data['CAR_VEL_N'].append(row[3])
        min_data['CAR_VEL_E'].append(row[4])
        min_data['WIND_N'].append(row[5])
        min_data['WIND_E'].append(row[6])
        min_data['WIND_DIR_SDEV'].append(row[7])
        min_data['WS_WIND_LAT'].append(row[8])
        min_data['WS_WIND_LON'].append(row[9])
        min_data['CH4'].append(row[10])
        
    for key in min_data.keys():
        a = np.asarray(min_data[key],dtype=np.float)
        is_nan = np.isnan(a)
        if np.any(is_nan):
            good = np.where(is_nan==False)[0]
            bad = np.where(is_nan==True)[0]
            i = np.arange(a.size,dtype=np.int)
            a[bad] = np.interp(i[bad],i[good],a[good])
        min_data[key] = a
        
    if plot:
        plt.figure()
        plt.plot(min_data['GPS_ABS_LONG'],min_data['GPS_ABS_LAT'])
        plt.show()
    
    min_data['CAR_SPEED'] = np.sqrt(min_data['CAR_VEL_N']**2+min_data['CAR_VEL_E']**2)
    
    lat1 = min_data['GPS_ABS_LAT'][:-1]
    lng1 = min_data['GPS_ABS_LONG'][:-1]
    lat2 = min_data['GPS_ABS_LAT'][1:]
    lng2 = min_data['GPS_ABS_LONG'][1:]
    dist = haversine_vectorized(lat1,lng1,lat2,lng2)
    dist = np.cumsum(dist)
    dist = np.insert(dist,0,0.0)
    min_data['DISTANCE'] = dist
    
    return min_data

</t>
<t tx="sze.20150507075745.5">def get_backtraj_data(analyzer,epoch_time,duration):
    
    epoch_times = []
    lats = []
    lngs = []
    car_vel_norths = []
    car_vel_easts = []
    wind_lats = []
    wind_lngs = []
    
    analyzer_ID = getAnalyzerId(analyzer)
    
    server = "b-eng-db01.picarro.int"
    database = "SurveyorEngineering"
    uid = "engineering"
    password = "aDs76WoiJn"
    connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                            (server, database, uid, password))
    cursor = connection.cursor()
    
    cursor.execute("""
    
        SELECT [EpochTime]
              ,[GpsLatitude]
              ,[GpsLongitude]
              ,[CarSpeedNorth]
              ,[CarSpeedEast]
              ,[WindSpeedLateral]
              ,[WindSpeedLongitudinal]
        FROM [SurveyorEngineering].[dbo].[Measurement]
        WHERE (EpochTime BETWEEN '%s' AND '%s')
        AND (AnalyzerId = '%s')
        AND (GpsFit=2)
        
    """ % (str(epoch_time-duration),str(epoch_time),analyzer_ID))
    
    for row in cursor:
        epoch_times.append(row[0])
        lats.append(row[1])
        lngs.append(row[2])
        car_vel_norths.append(row[3])
        car_vel_easts.append(row[4])
        wind_lats.append(row[5])
        wind_lngs.append(row[6])
        
    return dict(epoch_time=np.asarray(epoch_times),latitude=np.asarray(lats),
                longitude=np.asarray(lngs),car_vel_n=np.asarray(car_vel_norths),
                car_vel_e=np.asarray(car_vel_easts),wind_lat=np.asarray(wind_lats),
                wind_lng=np.asarray(wind_lngs))
    
</t>
<t tx="sze.20150507075912.1">@language python
@tabwidth -4

import numpy as np
import pyodbc

# constructing and running query
server = "b-eng-db01.picarro.int"
database = "SurveyorEngineering"
uid = "engineering"
password = "aDs76WoiJn"
connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                        (server, database, uid, password))
cursor = connection.cursor()

# Get table names
cursor.execute("""
    SELECT DISTINCT TABLE_NAME
        FROM [SurveyorEngineering].INFORMATION_SCHEMA.COLUMNS
""")
print "\nTables Available"
for row in cursor:
    print row


# Get analyzer table column names
cursor.execute("""
    SELECT COLUMN_NAME
        FROM [SurveyorEngineering].INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Analyzer'
""")

print "\nAnalyzer table columns"
for row in cursor:
    print row

# Get analyzer names and Id
cursor.execute("""
    SELECT SerialNumber, Id
        FROM [SurveyorEngineering].[dbo].[Analyzer]
""")

print "\nAnalyzers in database"
for row in cursor:
    print row

# Get measurement table column names
print "\nMeasurement table columns"
cursor.execute("""
    SELECT COLUMN_NAME
        FROM [SurveyorEngineering].INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Measurement'
""")

for row in cursor:
    print row
</t>
<t tx="sze.20150507082344.1">@language python
@tabwidth -4

import numpy as np
import pyodbc

# constructing and running query
server = "b-eng-db01.picarro.int"
database = "SurveyorEngineering"
uid = "engineering"
password = "aDs76WoiJn"
connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                        (server, database, uid, password))
cursor = connection.cursor()

cursor.execute("""
    SELECT Tag, StartEpoch, EndEpoch, AnalyzerId
        FROM [SurveyorEngineering].[dbo].[Survey]
""")
surveys = cursor.fetchall()
for survey in surveys:
    startEpoch = survey[1]
    endEpoch = survey[2]
    analyzerId = survey[3]
    cursor.execute("""
        SELECT EpochTime, CarSpeedNorth, CarSpeedEast, WindSpeedLongitudinal
            FROM [SurveyorEngineering].[dbo].[Measurement] WHERE
            EpochTime &gt; %s AND EpochTime &lt; %s AND AnalyzerId = '%s'
    """ % (startEpoch, endEpoch, analyzerId))
    maxSpeed = []
    for row in cursor:
        if row[1] is not None:
            carSpeed = abs(row[1]+1j*row[2])
            wsLon = row[3]
            maxSpeed.append(abs(carSpeed - wsLon))
    if maxSpeed:
        print "%s, %.2f" % (survey[0], max(maxSpeed))
    
</t>
<t tx="sze.20150507213556.1">Removed PeripheralStatus.WIND_DIRECTION_NOT_AVAILABLE, since it is not an error but a condition which holds whenever the car speed is too low.
WIND_SPEED_CAR_SPEED_UNCORRELATED has been changed to CAR_SPEED_TOO_LARGE, since the test for large true wind speeds already signals WIND_ANOMALY.
The CAR_SPEED_TOO_LARGE test checks if car speed exceeds CarSpeedMaximum.
</t>
<t tx="sze.20150507213649.1">@language python
@tabwidth -4
@others
# This script is run by compiling it and executing it within an environment defined by the peripheral processor
if "DONE" not in locals():
    DONE = lambda: False
runAsScript()
</t>
<t tx="sze.20150507213822.1">#!/usr/bin/python
"""
FILE:
  processorFindWindInstNoCompass.py

DESCRIPTION:
  Peripheral Interface Processor script for finding true wind speed and direction

SEE ALSO:
  Specify any related information.

HISTORY:
   6-Feb-2012  sze  Initial version
  10-Dec-2013  sze  Added modifications for maximum true wind speed (MAXTRUEWINDSPEED 
                    parameter in the INI file). Added comments and assertions for type checking.
   2-Jan-2014  sze  Removed processing of compass for use with Gill anemometer

 Copyright (c) 2013-2014 Picarro, Inc. All rights reserved
"""
from Host.Common.namedtuple import namedtuple
from collections import deque
from Host.Common.configobj import ConfigObj
import Queue
import time

from numpy import angle, arcsin, arctan, arctan2, asarray, column_stack, concatenate, conj
from numpy import cos, exp, floor, imag, isfinite, isnan, mod, pi, real, sin, sqrt, tan

from Host.PeriphIntrf.PeripheralStatus import PeripheralStatus


NOT_A_NUMBER = 1e1000 / 1e1000
SourceTuple = namedtuple('SourceTuple', ['ts', 'valTuple'])


</t>
<t tx="sze.20150507213822.10">def distVincenty(lat1, lon1, lat2, lon2):
    """Calculate distance between points on ellipsoidal earth .
    
    The WGS-84 ellipsiod is used. 
    
    Args:
        lat1: Latitude in degrees of first point
        long1: Longitude in degrees of first point
        lat2: Latitude in degrees of second point
        long2: Longitude in degrees of second point
        
    Returns:
        Distance between points in meters
    """
    assert isinstance(lat1, float)
    assert isinstance(lon1, float)
    assert isinstance(lat2, float)
    assert isinstance(lon2, float)
    a = 6378137
    b = 6356752.3142
    f = 1 / 298.257223563
    toRad = pi / 180.0
    L = (lon2 - lon1) * toRad
    U1 = arctan((1 - f) * tan(lat1 * toRad))
    U2 = arctan((1 - f) * tan(lat2 * toRad))
    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)
  
    Lambda = L
    iterLimit = 100
    for _ in range(iterLimit):
        sinLambda = sin(Lambda)
        cosLambda = cos(Lambda)
        sinSigma = sqrt((cosU2 * sinLambda) * (cosU2 * sinLambda) +
                        (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) * (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda))
        if sinSigma == 0:
            return 0  # co-incident points
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = arctan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha * sinAlpha
        if cosSqAlpha == 0:
            cos2SigmaM = 0
        else:
            cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
        C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
        lambdaP = Lambda
        Lambda = L + (1 - C) * f * sinAlpha * \
            (sigma + C * sinSigma * (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM)))
        if abs(Lambda - lambdaP) &lt;= 1.e-12:
            break
    else:
        raise ValueError("Failed to converge")

    uSq = cosSqAlpha * (a * a - b * b) / (b * b)
    A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM) -
                 B / 6 * cos2SigmaM * (-3 + 4 * sinSigma * sinSigma) * (-3 + 4 * cos2SigmaM * cos2SigmaM)))
    return b * A * (sigma - deltaSigma)


</t>
<t tx="sze.20150507213822.11">def toXY(lat, lon, lat_ref, lon_ref):
    """Convert points on earth near a reference point to local (x,y) plane
    
    Args:
        lat: Latitude of point in degrees
        lon: Longitude of point in degrees
        lat_ref: Latitude of reference point in degrees
        lon_ref: Longitude of reference point in degrees
        
    Returns:
        Tuple of (x,y) coordinates of point (in meters) releative to reference. x is in the 
        easterly direction and y is in the northerly direction.
    """
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert isinstance(lat_ref, float)
    assert isinstance(lon_ref, float)
    
    x = distVincenty(lat_ref, lon_ref, lat_ref, lon)
    if lon &lt; lon_ref:
        x = -x
    y = distVincenty(lat_ref, lon, lat, lon)
    if lat &lt; lat_ref:
        y = -y
    return x, y


</t>
<t tx="sze.20150507213822.12">def syncSources(sourceList, msOffsetList, msInterval, sleepTime=0.01):
    """Synchronize a collection of sources to a common time grid.
    
    Linear interpolation is used as needed.
    
    Args:
        sourceList: List of sources which are descendents of RawSource
        msOffsetList: Per-source timestamp offset to apply before synchronization. The data for the source is
            sampled at the sum of the common (synchronized) timestamp and the offset for that source
        msInterval: Timestamps for the synchronized data sources are integer multiples of msInterval
        sleepTime: Time to sleep (in s) between calling getData for each source.
    Yields: 
        A tuple consisiting of a timestamp and a list of tuples of synchronized data, one from each source
    """
    assert isinstance(msInterval, (int, long, float))
    assert isinstance(sleepTime, (int, long, float))
    # First determine when to start synchronized timestamps
    oldestTs = []
    for s in sourceList:
        assert isinstance(s, RawSource)
        while True:
            ts = s.getOldestTimestamp()
            if ts is not None:
                oldestTs.append(ts)
                break
            time.sleep(sleepTime)
            
    oldestAvailableFromAll = max([ts - offset for ts, offset in zip(oldestTs, msOffsetList)])
    # Round to the grid of times which are multiples of msInterval
    ts = msInterval * (1 + oldestAvailableFromAll // msInterval)
    
    # Get all the valTuples at the specified timestamp
    while True:
        valTuples = []
        for s, offset in zip(sourceList, msOffsetList):
            assert isinstance(offset, (int, long, float))
            while True:
                d = s.getData(ts + offset)
                if DONE():
                    return
                if d is not None:
                    valTuples.append(d.valTuple)
                    break
                time.sleep(sleepTime)
        yield ts, valTuples
        ts += msInterval
        

</t>
<t tx="sze.20150507213822.13">StatusTuple = namedtuple('StatusTuple', ['status'])
SyncCdataTuple = namedtuple('SyncCdataTuple', StatusTuple._fields + ('ts', 'lon', 'lat', 'fit', 'zPos', 'rVel'))
DerivCdataTuple = namedtuple('DerivCdataTuple', SyncCdataTuple._fields + ('zVel', 'kappa'))
CalibCdataTuple = namedtuple('CalibCdataTuple', DerivCdataTuple._fields + ('tVel', 'wCorr'))
StatsCdataTuple = namedtuple('StatsCdataTuple', CalibCdataTuple._fields + ('wMean', 'aStdDev'))
    

def syncCdataSource(syncDataSrc):
    """Convert GPS lat and lon to Cartesian coordinates.
    
    Represent vectors of interest as complex numbers (North)+1j*(East) so that the argument of the 
    complex number is the bearing.
    
    Args:
        syncDataSrc: Synchronized data source with GPS and anemometer data
    Yields:
        SyncCdataTuple objects with fields:
            ts: millisecond timestamp
            lon: longitude (degrees)
            lat: latitude (degrees)
            fit: GPS fit flag (N.B. may be interpolated)
            
    """
    lon_ref, lat_ref = None, None
    x, y = 0.0, 0.0
    gpsOkThreshold = 4  # Need these many good GPS points before using data
    
    gpsCount = gpsOkThreshold
    for ts, [gps, anem] in syncDataSrc:
        lat, lon, fit = gps.GPS_ABS_LAT, gps.GPS_ABS_LONG, gps.GPS_FIT
        if gpsCount &gt; 0:
            gpsCount -= 1
        if fit &lt; 1.0:
            gpsCount = gpsOkThreshold  # Indicate bad GPS
        if lat_ref is None and gpsCount == 0:
            lat_ref, lon_ref = lat, lon
        if lat_ref is not None:
            if gpsCount == 0:
                x, y = toXY(lat, lon, lat_ref, lon_ref)
            else:
                x, y = NOT_A_NUMBER, NOT_A_NUMBER
        zPos = y + 1j * x
        rVel = (anem.WS_WIND_LON + 1j * anem.WS_WIND_LAT)
        yield SyncCdataTuple(anem.WS_STATUS, ts, lon, lat, fit, zPos, rVel)


</t>
<t tx="sze.20150507213822.14">def derivCdataSource(syncCdataSrc):
    """Compute velocity and curvature of path.
    
    Use centered 5-point finite difference to find velocity from position and 
    finite difference approximation to the curvature of the path.
    
    Args:
        syncCdataSrc: iterable with complex position in property zPos
    
    Yields:
        DerivCdataTuple containing all properties in the source followed by the complex
            velocity and the curvature of the path.
    """
    dBuff = []
    for d in syncCdataSrc:
        dBuff.append(d)
        dBuff[:] = dBuff[-5:]
        if len(dBuff) == 5:
            d4 = dBuff[4]
            d3 = dBuff[3]
            d2 = dBuff[2]
            d1 = dBuff[1]
            d0 = dBuff[0]
            # Use higher order velocity estimate
            zVel = (-d4.zPos + 8.0 * d3.zPos - 8.0 * d1.zPos + d0.zPos) / 12.0
            dz = d3.zPos - d1.zPos
            d2z = d3.zPos - 2 * d2.zPos + d1.zPos
            r = abs(dz)
            r2 = r * r
            # Calculate curvature of path, with protection for low speeds
            kappa = 4.0 * imag(conj(dz) * d2z) * r / (r2 * r2 + 4.0)
            yield DerivCdataTuple(*(d2 + (zVel, kappa)))

        
</t>
<t tx="sze.20150507213822.15">def trueWindSource(derivCdataSrc, distFromAxle, speedFactor=1.0, maxTrueWindSpeed=20.0):
    """Calculates the true wind velocity and updates compass calibration.

    This simply subtracts the vehicle velocity from the anemometer velocity. The calculation is done 
    in the frame of the anemometer, which is nominally aligned with the vehicle.
    
    Args:
        derivCdataSrc: Iterable containing the following properties:
            rVel: Apparent complex wind speed along (real) and across (imaginary) vehicle
            kappa: Inverse of radius of curvature of path
            zVel: Complex velocity of vehicle
        distFromAxle: Distance (m) that the GPS is in front of the rear axle of the vehicle
        speedFactor: Apparent wind velocity is multiplied by this factor before the car velocity is subtracted
        maxTrueWindSpeed: If the calculated wind speed exceeds this quantity, it is replaced by NOT_A_NUMBER
        
    Yields:
        CalibCdataTuple objects consisting of the properties of derivCdataSrc, the calculated true wind,
        and a list of correlations between car speed and the apparent wind velocity.
    """
    # If the reconstructed wind speed exceeds maxTrueWindSpeed, replace it with NaN since it is likely
    #  that the anemometer has failed.
    
    assert isinstance(distFromAxle, (int, long, float))
    assert isinstance(speedFactor, (int, long, float))
    assert isinstance(maxTrueWindSpeed, (int, long, float))

    rCorr = 0.0  # Rotation between axis of anemometer and axis of vehicle
    iCorr = 0.0
    optAngle = None    
        
    def whichBin(phi, nBins):
        return int(min(nBins - 1, floor(nBins * (mod(phi, 2 * pi) / (2 * pi)))))
    
    for i, d in enumerate(derivCdataSrc):
        # Rotate the anemometer measured wind to the axes of the vehicle

        sVel = d.rVel
        # Compute an angular correction based on the curvature of the path
        #  and the distance between anemometer and the rear axle of the car
        axleCorr = d.kappa * distFromAxle
                
        if isfinite(d.zVel):
            # Subtract velocity of vehicle
            cVel = speedFactor * sVel - abs(d.zVel) * exp(1j * axleCorr)
            #
            if abs(cVel) &gt; maxTrueWindSpeed:
                d = d._replace(status=int(d.status) | PeripheralStatus.WIND_ANOMALY)
                tVel = NOT_A_NUMBER
            else:
                # Rotate back to geographic coordinates, using GPS direction if car is travelling
                #  quickly or the previous direction if the speed falls below 1 m/s
                if abs(d.zVel) &gt; 1:
                    optAngle = angle(d.zVel)
                    
                if optAngle is not None:
                    tVel = cVel * exp(1j * optAngle)
                else:
                    tVel = NOT_A_NUMBER                    
        else:
            tVel = NOT_A_NUMBER
        
        # Determine the anemometer rotation
        if isfinite(d.zVel):      # Reject bad GPS data
            if abs(d.zVel) &gt; 3.0 and abs(d.zVel) &lt; 2.0 * (5.0 + abs(d.rVel)):  # Car is moving fast if speed &gt; 3m/s.
                # Also reject points where car speed is too great.
                rCorr += abs(d.zVel) * real(d.rVel)
                iCorr += abs(d.zVel) * imag(d.rVel)
                            
        yield CalibCdataTuple(*(d + (tVel, [rCorr, iCorr])))


</t>
<t tx="sze.20150507213822.16">def windStatistics(windSource, statsInterval):
    """Calculate wind statistics within a specified time interval.
    
    Args:
        windSource: iterable with a property .tVel, which, for each sample, is a complex number representing
            the instantaneous wind velocity. The real part is the component from the north and the imaginary
            part is the component from the east.
        statsInterval: number of samples over which to compute the mean and Yamartino standard deviation.
        
    Yields:
        ResultsTuple: all statistics + system status
    """
    assert isinstance(statsInterval, (int, long, float))
    wSum = 0.0
    aSum = 0.0
    buff = deque()
    for w in windSource:
        if isnan(w.tVel):
            wSum = 0.0
            aSum = 0.0
            buff.clear()
            wMean = NOT_A_NUMBER + 1j * NOT_A_NUMBER
            aStdDev = NOT_A_NUMBER
        else:
            buff.append(w.tVel)
            wSum += w.tVel
            aSum += exp(1j * angle(w.tVel))
            if len(buff) &gt; statsInterval:
                oldest = buff.popleft()
                wSum -= oldest
                aSum -= exp(1j * angle(oldest))
            n = len(buff)
            wMean = wSum / n
            if n &gt; 0:
                vmean = abs(aSum / n)
                eps = sqrt(1 - vmean * vmean)
                aStdDev = arcsin(eps) * (1 + 0.1547 * eps * eps * eps)
            else:
                aStdDev = pi / 2.0
            aStdDev = 180.0 / pi * aStdDev
        yield StatsCdataTuple(*(w + (wMean, aStdDev)))
        

</t>
<t tx="sze.20150507213822.17">def runAsScript():
    """Run the processor
    
    This needs to be run in an environment in which the following are defined:
        SENSORLIST: The list of data queues for the input sensors (GPS and Weather Station)
        PARAMS: Parameters used by the processor script
        WRITEOUTPUT: Function taking a timestamp and a list of outputs from the processor
        DONE: Function which when called returns a boolean indicating if there is no more data 
            to process
    """
    gpsSource = GpsSource(SENSORLIST[0])
    wsSource = WsSource(SENSORLIST[1])
    gpsDelay_ms = 0
    anemDelay_ms = round(1000 * float(PARAMS.get("ANEMDELAY", 1.5)))
    distFromAxle = float(PARAMS.get("DISTFROMAXLE", 1.5))
    speedFactor = float(PARAMS.get('SPEEDFACTOR', 1.0))
    maxTrueWindSpeed = float(PARAMS.get('MAXTRUEWINDSPEED', 20.0))

    msOffsets = [gpsDelay_ms, anemDelay_ms]  # ms offsets for GPS and anemometer
    syncDataSource = syncSources([gpsSource, wsSource], msOffsets, 1000)
    statsAvg = int(PARAMS.get("STATSAVG", 10))
    for d in windStatistics(trueWindSource(derivCdataSource(syncCdataSource(syncDataSource)), 
                                           distFromAxle, speedFactor, maxTrueWindSpeed), statsAvg):
        rCorr, iCorr = d.wCorr
        vCar = abs(d.zVel)
        WRITEOUTPUT(d.ts, [float(real(d.wMean)), float(imag(d.wMean)),    # Mean wind N and E
                           d.aStdDev,                                     # Wind direction std dev (degrees)
                           float(real(d.zVel)), float(imag(d.zVel)),      # Car velocity N and E
                           float(real(d.tVel)), float(imag(d.tVel)),      # Instantaneous wind N and E
                           (180 / pi) * arctan2(iCorr, rCorr),            # Angle of anemometer from true
                           vCar,                                          # Speed of car
                           d.status
        ])
        

</t>
<t tx="sze.20150507213822.2">class RawSource(object):
    """Interface to data being collected on a queue, allowing for interpolation to arbitrary times.
    
    The getData method is used to request the values at a specified timestamp. Linear
    interpolation is used to calculate the source tuple at the desired time, unless
    the requested timestamp is in the future of all the data present in the queue, in
    which case None is returned. Up to maxStore previous queue entries are buffered in
    a deque for the interpolation. If the requested timestamp is earlier than all the
    buffered entries, the first entry in the buffer is returned.
    
    Args:
        queue: queue which contains tuples consisting of a timestamp and a dictionary of
            key-value pairs representing the data at that timestamp
        maxStore: Maximum number of points to store for linear interpolation    
    """
    @others
</t>
<t tx="sze.20150507213822.3">def __init__(self, queue, maxStore=20):
    assert isinstance(queue, Queue.Queue)
    assert isinstance(maxStore, (int, long))
    self.queue = queue
    self.DataTuple = None
    self.oldData = deque()
    self.maxStore = maxStore
    self.latestTimestamp = None
    
</t>
<t tx="sze.20150507213822.4">def getDataTupleType(self, d):
    """Construct a namedtuple type for data in the queue.
    
    Sets self.DataTuple to a tuple whose fields are the keys of the dictionary
        specifying the data in the queue.
        
    Args:
        d a typical datum from the queue. This should be a tuple with a timestamp as
            the first element and a dictionary of values as the second element.
    """
    assert isinstance(d, tuple)
    assert isinstance(d[0], (int, long, float))
    assert isinstance(d[1], dict)
    self.DataTuple = namedtuple(self.__class__.__name__ + '_tuple', sorted(d[1].keys()))
    
</t>
<t tx="sze.20150507213822.5">def getFromQueue(self):
    """Gets a datum from the queue (if available) and adds it to the deque.
    
    The length of the deque is always kept no greater than self.maxStore. 

    Returns:
        True if a point was transferred from the queue to the deque
    """
    try:
        d = self.queue.get(block=False)
        if d is None:
            return False
        if self.DataTuple is None:
            self.getDataTupleType(d)
        self.oldData.append(SourceTuple(d[0], self.DataTuple(**d[1])))
        self.latestTimestamp = d[0]
        if len(self.oldData) &gt; self.maxStore:
            self.oldData.popleft()
        # print self.oldData
        return True
    except Queue.Empty:
        return False
        
</t>
<t tx="sze.20150507213822.6">def getOldestTimestamp(self):
    """Get the timestamp of the oldest data available in the deque.
    
    Returns:
        Timestamp of oldest data available, or None if no data are available
    """
    if not self.oldData:
        self.getFromQueue()
    return self.oldData[0].ts if self.oldData else None

</t>
<t tx="sze.20150507213822.7">def getData(self, requestTs):
    """Get data at specified timestamp using interpolation if needed.
    
    Args:
        requestTs: Time stamp at which data are required.
    Returns:
        SourceTuple consisting of requestTs and the interpolated data.
        None if no data are available.
    """
    assert isinstance(requestTs, (int, long, float))
    while self.latestTimestamp &lt; requestTs:
        if not self.getFromQueue():
            return None
    ts, savedTs = None, None
    valTuple, savedValTuple = None, None
    for (ts, valTuple) in reversed(self.oldData):
        if ts &lt; requestTs:
            alpha = float(requestTs - ts) / (savedTs - ts)
            di = tuple([alpha * y + (1 - alpha) * y_p for y, y_p in zip(savedValTuple, valTuple)])
            return SourceTuple(requestTs, self.DataTuple(*di))
        else:
            savedTs = ts
            savedValTuple = valTuple
    else:
        return self.oldData[0]
        

</t>
<t tx="sze.20150507213822.8">class GpsSource(RawSource):
    """Source for GPS data.
    """
    pass
    

</t>
<t tx="sze.20150507213822.9">class WsSource(RawSource):
    """Source for weather station data.
    """
    pass


</t>
<t tx="sze.20150507214331.1">@language python
@tabwidth -4
@others
</t>
<t tx="sze.20150507214410.2">"""
Copyright 2014 Picarro Inc.
"""
class PeripheralStatus(object):

    WIND_ANOMALY = 0x0001
    WIND_MESSAGE_CHECKSUM_ERROR = 0x0004
    WIND_AXIS1_FAILED = 0x0008
    WIND_AXIS2_FAILED = 0x0010
    WIND_NONVOLATILE_CHECKSUM_ERROR = 0x0020
    WIND_ROM_CHECKSUM_ERROR = 0x0040
    MALFORMED_DATA_STRING = 0x0080
    WIND_BAD_UNITS = 0x0100
    WIND_UNSTABLE = 0x0200
    CAR_SPEED_TOO_LARGE = 0x0400
    WIND_SENSOR_DISCONNECTED = 0x8000

    GPS_DISCONNECTED = 0x10000
    GPS_NOT_UPDATING = 0x20000

</t>
<t tx="sze.20150507214535.1">@language python</t>
<t tx="sze.20150507215022.1">if ('WIND_N' in _DATA_) and ('WIND_E' in _DATA_):
    windSpeed = 0.0

    if (not numpy.isnan(_DATA_['WIND_N'])) and (not numpy.isnan(_DATA_['WIND_E'])):
        windN = _DATA_['WIND_N']
        windE = _DATA_['WIND_E']
        windSpeed = numpy.sqrt(windN * windN + windE * windE)

    if unstableWindSpeed(windSpeed):
        PeripheralStatus |= PeriphIntrf.PeripheralStatus.PeripheralStatus.WIND_UNSTABLE

    if ('CAR_VEL_N' in _DATA_) and ('CAR_VEL_E' in _DATA_):
        carSpeed = 0.0

        if (not numpy.isnan(_DATA_['CAR_VEL_N'])) and (not numpy.isnan(_DATA_['CAR_VEL_E'])):
            carN = _DATA_['CAR_VEL_N']
            carE = _DATA_['CAR_VEL_E']
            carSpeed = numpy.sqrt(carN * carN + carE * carE)

        if (carSpeed != 0.0) and (carSpeed &gt; CarSpeedMaximum) and \
           (numpy.absolute((windSpeed / carSpeed) - 1.0) &gt; CarWindSpeedCorrelation):
            PeripheralStatus |= PeriphIntrf.PeripheralStatus.PeripheralStatus.WIND_SPEED_CAR_SPEED_UNCORRELATED</t>
<t tx="sze.20150507215103.1">"""
Copyright 2014 Picarro Inc.
"""
class PeripheralStatus(object):

    WIND_ANOMALY = 0x0001
    WIND_DIRECTION_NOT_AVAILABLE = 0x0002
    WIND_MESSAGE_CHECKSUM_ERROR = 0x0004
    WIND_AXIS1_FAILED = 0x0008
    WIND_AXIS2_FAILED = 0x0010
    WIND_NONVOLATILE_CHECKSUM_ERROR = 0x0020
    WIND_ROM_CHECKSUM_ERROR = 0x0040
    MALFORMED_DATA_STRING = 0x0080
    WIND_BAD_UNITS = 0x0100
    WIND_UNSTABLE = 0x0200
    WIND_SPEED_CAR_SPEED_UNCORRELATED = 0x0400
    WIND_SENSOR_DISCONNECTED = 0x8000

    GPS_DISCONNECTED = 0x10000
    GPS_NOT_UPDATING = 0x20000

</t>
<t tx="sze.20150508000110.1">@language python
@tabwidth -4

import numpy as np
import pyodbc

# constructing and running query
server = "b-eng-db01.picarro.int"
database = "SurveyorEngineering"
uid = "engineering"
password = "aDs76WoiJn"
connection = pyodbc.connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                        (server, database, uid, password))
cursor = connection.cursor()

cursor.execute("""
    SELECT Tag, StartEpoch, EndEpoch, AnalyzerId
        FROM [SurveyorEngineering].[dbo].[Survey]
""")
surveys = cursor.fetchall()
for survey in surveys:
    startEpoch = survey[1]
    endEpoch = survey[2]
    analyzerId = survey[3]
    cursor.execute("""
        SELECT EpochTime, WindSpeedNorth, WindSpeedEast
            FROM [SurveyorEngineering].[dbo].[Measurement] WHERE
            EpochTime &gt; %s AND EpochTime &lt; %s AND AnalyzerId = '%s'
    """ % (startEpoch, endEpoch, analyzerId))
    maxSpeed = []
    for row in cursor:
        if row[1] is not None:
            windSpeed = abs(row[1]+1j*row[2])
            maxSpeed.append(windSpeed)
    if maxSpeed:
        print "%s, %.2f" % (survey[0], max(maxSpeed))
    
</t>
<t tx="sze.20150508003853.1">requal-jw, 4.77
requal_sg, 2.09
2014-8-22-surveyareaB, 3.81
C3D5-areaB, 3.12
2014-8-22-surveyareaC, 6.04
C2D15, 3.93
C2D15, 3.82
C2D15, 3.35
C2D15, 3.49
C2D15, 2.97
C2D15, 4.67
C2D15, 2.18
C2D15-IsoCancel, 2.09
C2D15-IsoCancel, 1.42
C2D15-IsoCancel, 1.81
C2D15-IsoCancel, 1.96
C2D15-IsoCancel, 1.61
C2D15-IsoCancel, 2.81
C2D15-IsoCancel, 3.05
C2D15-Ref, 2.90
C2D15-Ref, 2.61
C2D15-Ref, 2.85
C2D15-Ref, 2.94
C2D15-Ref, 3.20
C2D15-Ref, 3.23
C2D15-Ref, 3.49
C2D15-SurveyB, 5.83
test, 9.27
C2D16-PositionUncertainty, 3.56
C2D16-PositionUncertainty, 4.12
C2D16-PositionUncertainty, 4.45
C2D16-PositionUncertainty, 3.12
C2D16-PositionUncertainty, 3.87
C2D16-PositionUncertainty, 5.21
C2D16-PositionUncertainty, 3.83
C2D16-PositionUncertainty, 5.23
C2D16-OrangeSmoke!, 4.89
C2D16-OrangeSmoke!, 4.76
hello, 2.78
test, 6.23
C2D17-test1140, 3.04
C2D17-test1126, 2.67
C2D17-test1126, 0.74
survey test, 7.54
2014-8-27-, 1.40
2014-8-27-offroad1, 4.67
off road, 5.24
None, 10.75
test, 3.31
C2D18-CR-50, 4.26
C2D18-CR-75, 4.14
C2D18-CR-100, 3.95
C2D18-CR-125, 4.72
C2D18-CR-150, 4.66
C2D18-CR-50, 4.32
C2D18-CR-75, 3.75
C2D18-CR-100, 4.89
C2D18-CR-125, 4.16
C2D18-CR-150, 4.14
C2D18-CR-150, 4.89
C2D18-CR-Direct, 4.96
C2D18-CR-Direct, 4.51
2014-8-29-ReferenceBottle, 2.84
2014-8-27-areaABottle, 3.05
Ref gas 1, 3.22
Survey 1 Area A, 3.92
2014-8-29-surveyrestarttest1, 4.75
elliptical speed test, 5.77
AreaC, 4.38
Area_D, 4.87
areab, 4.91
areabreproducefail, 4.10
090314_rouge_run2, 4.26
areaA, 4.12
areaA2, 4.47
090314_rouge_run1, 7.83
Alpha 2 rep, 3.30
RB-TestDrive, 2.52
RB-Std-TestDrive, 3.38
test-drive, 3.81
C3D1-RefGasCap1, 4.49
c3d1_refbottle, 4.33
c3d1_areaA, 4.56
C3D1-AreaA, 5.09
C3D1-RefGasCap2, 1.78
C3D1-RefGasCap2, 4.11
ref gas 1, 4.43
C3n1-areaA, 3.11
C3D1night_areaA, 2.33
C3D1-refrencebottle, 2.42
C3D1-areaA, 1.10
C3D1-AreaA2, 1.94
C3N1-area B, 7.73
C3D1night_areaB, 2.00
C3D1-AreaB, 2.21
ref gas 2, 3.90
C3D1-refbot, 1.91
c3d1night_refgas2, 1.79
Rakesh-TestSurvey-2014-09-05-2116, 2.79
c3d2_8hr, 5.51
C3D2-Continuous, 5.10
C3D2-8hr, 6.91
test-drive, 4.02
refgas, 3.21
RB-SanityTest-2014-09-05, 3.22
bug930, 1.89
C3D1-bug930, 2.03
bug958, 2.02
C3D2-bug958, 1.37
C3D2night_refgas1, 2.10
bug1154, 1.63
C3D2-refbot, 3.19
C3D2-areaA, 3.49
C3D2night_areaA, 1.68
C3D2-areaA, 1.64
isocap1, 1.85
isocap2, 0.62
C3D2-isocap1, 0.59
isocap3, 2.36
C3D2-isocap2, 2.13
C3D2-isocap3, 2.06
C3D2night_refgas2, 0.67
C3D2-areaC, 1.30
C3D2-refbot2, 2.85
backtest, 0.54
C3D3-refgas1, 2.68
C3D3-AreaA, 3.94
C3D3-areaA, 5.33
C3D3-areaC, 4.43
C3D3-AreaC, 4.23
C3D3-refgas2, 5.16
C3D3-RefGasCap2, 4.12
C3D4-RefGasCap, 2.11
C3D4-AreaB, 2.92
C3D4-refgas1, 4.36
C3D4-areaB, 3.43
C3D4-AreaC, 4.28
C3D4-areaC, 4.43
C3D4-areaA, 4.03
C3D4-AreaA, 4.63
C3D4-refgas2, 5.19
C3D4-RefGasCap2, 5.39
c3d3_refgas1, 2.35
c3d4_refgas1, 3.90
c3d3_areaB, 3.83
C3D3-wholeday, 5.53
c3d4_areaB, 3.70
c3d4_areaC, 4.26
c3d3_areaC, 4.93
c3d4_areaA, 6.29
c3d3_areaA, 4.92
c3d4_refgas2, 5.80
c3d3_refgas2, 2.21
C3D3night_refgas1, 1.54
ref gas 1, 3.41
C3D3-Task4-RefGasCap1, 3.89
C3n3-areaA, 2.15
C3N3-AreaA, 2.11
C3D3-Task5-AreaA, 2.82
isocap1, 4.67
c3n3_isocap1, 0.65
c3n3_areaC, 1.56
isocap1retry, 9.39
isocap2, 1.84
areaC, 1.25
C3D3-Task10-AreaC, 1.45
isocap3, 1.95
c3n3_isocap2, 0.67
C3D3-Task14-RefBotCap2, 1.89
C3N3-Refgas2, 0.49
avp sc1, 1.55
avp sc1, 1.79
avp sc1, 1.72
c3d4_restat1, 0.77
c3d4_restat2, 0.75
c3d4_restat3, 0.77
c3d4_restat4, 1.08
rlt1, 1.02
c3d4_restat5, 0.92
rlt2, 1.78
c3d4_restat6, 1.06
rlt3, 1.42
c3d4_restat7, 1.46
c3d4_restat8, 1.06
avp sc2, 2.60
rlt4, 1.80
c3d4_restat9, 1.68
rlt5, 1.62
c3d4_restat10, 1.38
rlt6, 1.47
c3d4_restat11, 1.49
rlt7, 1.54
avp sc2, 2.22
rlt8, 1.41
c3d4_restat12, 2.28
avp sc3, 2.81
c3d4_restat13, 1.93
rlt9, 1.58
c3d4_restat14, 1.83
rlt10, 2.12
avp sc3, 2.70
rlt11, 1.59
c3d4_restat15, 1.57
rlt12, 1.73
c3d4_restat16, 2.38
c3d4_restat17, 1.13
rlt13, 0.66
c3d4_restat18, 0.98
rlt14, 0.95
rlt15, 0.94
c3d4_restat19, 0.89
rlt16, 1.82
c3d4_restat20, 1.08
avp sc4, 2.07
rlt17, 1.11
c3d4_restat21, 1.79
avp sc5, 1.08
rlt18, 0.79
avp sc5, 3.57
rlt19, 1.72
c3d4_restat22, 1.33
rlt20, 1.60
c3d4_restat23, 1.27
rlt21, 0.84
c3d4_restat24, 2.17
rlt22, 1.55
rlt23, 1.65
c3d4_restat25, 1.33
c3d4_restat26, 1.98
rlt24, 1.75
c3d4_restat27, 2.15
rlt25, 2.13
c3d4_restat28, 2.19
rlt26, 1.49
rlt27, 1.11
c3d4_restat29, 0.96
rlt28, 0.61
rlt29, 1.31
c3d4_restat30, 1.09
c3d4_restat31, 0.94
rlt30, 2.06
c3d4_restat32, 1.66
rlt31, 1.38
rlt32, 1.76
c3d4_restat33, 1.41
rlt33, 2.18
c3d4_restat34, 2.23
rlt34, 1.15
c3d4_restat35, 1.27
c3d4_restat36, 1.29
rlt35, 1.63
c3d4_restat37, 1.56
rlt36, 1.29
c3d4_restat38, 1.75
rlt37, 1.84
c3d4_restat39, 1.28
rlt38, 1.77
rlt39, 1.66
c3d4_restat40, 1.15
rlt40, 1.34
c3d4_restat41, 1.50
c3d4_restat42, 1.59
rlt41, 1.08
rlt42, 1.70
c3d4_restat43, 1.66
rlt43, 1.23
rlt44, 1.40
c3d4_restat44, 1.16
c3d4_restat45, 1.22
rlt45, 1.84
c3d4_restat46, 2.03
rlt46, 1.85
c3d4_restat47, 2.16
rlt47, 1.68
c3d4_restat48, 1.33
rlt48, 1.63
c3d4_restat49, 1.32
rlt49, 1.52
c3d4_restat50, 1.33
rlt50, 1.59
c3d4_restat51, 1.52
rlt51, 1.48
c3d4_restat52, 1.85
rlt52, 1.38
c3d4_restat53, 1.81
rlt53, 1.77
c3d4_restat54, 1.72
rlt54, 1.65
c3d4_restat55, 1.41
rlt55, 1.60
c3d4_restat56, 2.37
rlt56, 1.58
rlt57, 1.50
c3d4_restat57, 1.13
rlt58, 1.73
c3d4_restat58, 1.40
rlt59, 0.89
c3d4_restat59, 1.29
rlt60, 1.86
c3d4_restat60, 2.22
rlt61, 1.54
rlt62, 1.67
rlt63, 2.18
rlt64, 1.70
rlt65, 1.76
rlt66, 1.63
c3d4_restat61, 1.98
rlt67, 2.12
rlt68, 1.42
c3d4_restat63, 2.29
rlt69, 2.11
c3d4_restat64, 1.32
rlt70, 2.20
c3d4_restat65, 2.61
c3d4_restat66, 2.48
c3d4_restat67, 2.85
rlt71, 1.99
c3d4_restat68, 2.66
rlt72, 2.09
c3d4_restat69, 1.77
c3d4_restat72, 2.70
rlt7, 2.51
c3d4_restat71, 2.77
rlt73, 2.18
c3d4_restat72(2), 2.88
c3d4_restat73, 3.44
rlt74, 1.72
c3d4_restat74, 3.00
rlt75, 2.58
c3d4_restat75, 3.43
rlt76, 2.76
c3d4_restat76, 2.79
rlt77, 1.64
c3d4_restat77, 2.81
rlt78, 2.17
c3d4_restat78, 3.60
rlt79, 2.71
c3d4_restat79, 3.07
c3d4_restat80, 2.99
c3d4_restat81, 3.09
c3d4_restat82, 1.86
rlt80, 2.30
c3d4_restat83, 3.17
c3d4_restat84, 3.19
rlt81, 1.80
rlt82, 1.89
c3d4_restat85, 2.47
rlt83, 2.16
c3d4_restat86, 3.58
rlt84, 2.41
rlt85, 1.97
c3d4_restat87, 2.48
c3d4_restat88, 2.72
c3d4_restat89, 2.50
c3d4_restat90, 3.19
c3d4_restat91, 3.04
c3d4_restat92, 2.35
c3d4_restat93, 1.90
c3d4_restat94, 2.10
c3d4_restat95, 2.27
c3d4_restat96, 2.75
c3d4_restat97, 2.96
c3d4_restat98, 3.32
c3d4_restat99, 3.06
c3d4_restat100, 4.37
C3D4-areaB, 3.96
c3d4_areaB, 3.90
Lab Test 20140909, 5.51
DrivingSurveyAreaA, 3.29
Lab Test 20140909_2, 5.53
Lab Test 20140909_3, 4.29
Test 20140909_3, 5.51
Test_20140909_4, 5.97
Test_20140909_5, 3.20
Test_20140909_6, 17.59
Test 20140909_6, 5.53
test 20140909_6, 3.67
test 20140909_7, 5.52
tesr, 1.74
tesr, 0.80
tesr, 1.22
Test 20140909_7, 18.18
c3n4_refgas1, 2.62
refgas, 2.92
C3D4-Task4-refbotcap, 3.03
C3N4-AreaA, 2.29
areaA, 2.16
C3D4-Task11-AreaC, 1.89
isocap1, 1.63
c3n4-AreaB, 1.16
areaB, 2.17
C3D4-isocap1, 1.29
C3D4-AreaB, 1.68
c3n4_areaC, 1.04
areaC, 3.55
C3D4-refbot2, 0.55
C3D5-refgas, 1.84
Lab Test 20140910_1, 17.14
C3D5-areaA, 2.59
RefGasCap1, 3.53
SurveyAreaA, 3.72
c3d5_refgas1, 6.91
c3d5_areaA, 3.25
C3D5-areaB, 3.25
avp sc 9/10 v1, 3.32
avp sc 9/10 v1, 3.34
avp sc 9/10 v1, 3.19
avp sc 9/10 v1, 4.93
C3D5-areaC, 3.34
SurveyAreaB, 3.82
c3d5_areaB, 3.67
c3d5-refgas2, 4.20
mfg test 20140910_1, 4.97
RefGasCap2, 4.31
c3n5_refgas1, 3.31
refgas1, 3.38
C3N5-Refgas1, 3.81
c3n5_AreaA, 2.44
AreaA, 2.50
C3N5-Area, 1.90
C3N5-AreaA, 2.53
isocap1, 3.14
isocap2, 1.39
c3n5_isocap1, 1.35
isocap3, 1.47
c3n5_isocap2, 1.69
C3N5-Isocap1, 1.27
C3N5-Isocap2, 1.64
c3n5_isocap3, 1.74
aeaB, 1.65
C3N5-isocap3, 1.29
C3N5-isocap4, 1.42
c3n5_areaB, 0.93
areaC, 0.23
areaC, 3.20
None, 0.96
refgas2, 2.86
c3n5_areac, 0.28
c3n5_refgas2, 1.68
c3d6_refgas1, 2.01
c3d6_areaA, 3.77
c3d6-refgas, 3.48
c3d6-areaA, 2.64
RefGasCap1, 5.82
c3d6-areaA2, 2.70
SurveyAreaC, 3.24
test, 3.95
c3d6-areaB, 0.86
c3d6-areaB2, 2.81
c3d6-areaB2, 3.61
c3d5_areaB, 3.62
SurveyAreaB, 3.57
c3d6-areaC, 3.17
c3d6-areaCmanual, 3.82
SurveyAreaA, 3.48
c3d6_areaC, 3.69
RefGasCap2, 4.91
c3d6-refgas2, 3.16
c3d6_refgas2, 4.66
c3d6_refgas3, 4.91
c3n6_refgas1, 2.38
c3n6_AreaA, 1.15
C3D6N-AreaA, 1.39
isocap1, 1.18
c3n6_refgas2, 0.82
c3d7-areaC, 2.38
test, 1.94
c3d7-areaC2, 3.07
c3d7-areaC3, 3.30
mfgtest 20140912_1, 4.52
Test1, 2.03
test2, 1.91
TestDrive, 2.50
c3n7_refgas1, 2.39
c3n7-refbot1, 1.45
c3n7_areaA, 1.56
c3n7_AreaA, 1.66
c3n7-areaB, 3.16
c3n7-AreaB, 1.40
c3n7-Refgas2, 1.48
mfg altitude test 1, 12.88
None, 3.31
6hrsurvey, 1.22
6hrsurvey, 7.46
SpeedFac, 3.31
DrivingSurvey, 3.57
DrivingSurvey1_2, 1.15
DrivingSurvey1_2, 5.05
AreaB, 5.07
DrivingSurvey1_2, 6.41
Refgas, 5.32
sk-2014-09-16-1058, 2.42
vale test 9/16, 5.05
SpeedFactor, 3.98
shortsurvey, 6.23
DrivingSurvey1, 3.15
09162014-Refgas2, 3.31
DrivingSurvey1_2, 3.82
09162014-Refgas3, 4.03
DriveSurveyIsoCap, 4.26
refgas1, 2.17
avp 5ref gas, 2.15
DrivingSurvey1, 6.47
09178014-Refgas, 5.37
5refbots, 4.50
DrivingSurvey2, 6.26
last2refbot, 3.21
Palo Alto daytime extended survey 9/17, 6.99
freedrive, 7.33
isocapture, 7.04
09172014-local, 4.08
None, 0.00
longrun, 7.04
DriveSurvey1, 7.71
6hrsurvey, 8.15
09182014-8hoursurvey, 7.36
run card ttest 1, 4.92
run card ttest 2, 4.29
6hrsurvey, 10.23
DriveSurvey, 8.99
09192014-8hoursurvey2, 6.99
longdrive, 7.32
lunch, 4.69
afterlunch, 7.92
house test, 5.65
pointlesstest, 5.77
avp to hay 9/19, 4.14
avp to hay 9/19, 5.07
avp to hay 9/19, 4.45
avp to hay 9/19, 5.88
house test parallel, 4.34
house test parallel, 4.88
avp to sc 9/20, 5.85
avp to sc 9/20, 2.49
8hrsurvey, 8.06
09222014-8hoursurvey3, 6.69
DriveSurvey, 9.33
longsurvey_092214, 9.82
avp to lick 9/22, 6.90
avp to lick 9/22, 6.51
avp after lick, 5.62
49errefsurvey, 7.33
49er ref survey, 6.89
49errefsurvey2, 7.73
49er ref survey redo, 6.81
avp to hay 9/22, 8.47
avp to sc 9/23, 6.25
longsurvey_092314, 7.87
None, 3.44
Derek_test, 5.65
mfg test ew 2, 5.35
gpstest, 5.76
None, 4.71
mfg twst ew 3, 5.71
avp to hay 9/23, 6.10
avp to hay 9/23, 5.74
avp to sc 9/24, 5.86
quicktest, 1.74
test1, 2.32
DriveSurvey, 8.45
longsurvey_092414, 5.37
09242014-8hourdrive4, 5.42
09242014, 4.99
derek2_escape_20140924, 7.43
PicarroToSite, 6.03
Area2Run1, 1.50
area1survey1, 1.57
Area1-Survey1, 1.95
Area2Run2, 1.81
area1survey2, 1.40
Area1-Survey2, 2.74
area2survey1, 2.47
Area1Run1, 4.66
Area2-Survey1, 3.39
Area1Run2, 4.22
area2survey2, 2.73
SiteToPicarro, 3.45
Area2-Survey2, 3.04
ToPicarro, 0.66
ToPicarro, 4.24
topicarro, 4.57
refgas, 2.49
RefGasIsoCap, 3.28
isocap, 3.36
john'stest, 4.32
likkerrun, 4.75
refgas, 3.67
RefGasTest, 2.17
gas station leak, 5.87
avp to hay 9/25, 4.80
avp to sr 9/26, 2.32
avp pge 9/26, 3.69
toarea, 5.51
area2run1, 2.84
Area1-Survey1, 2.75
area2run2, 2.62
Area2Run1, 2.89
Area2-Survey1, 3.20
Area2Run2, 2.83
None, 4.44
topicarro, 4.68
area1run1, 2.56
Test1, 3.22
SystemTest, 5.50
small survey, 4.97
RefgasCap, 5.46
RefgasCap2, 4.37
hay speed test, 3.65
None, 4.09
PicarroToSite, 6.80
lickobservedrive, 6.34
Area2MenloPark, 2.12
Area2-Survey1, 2.47
Area1MenloPark, 2.22
Area1-Survey1, 2.78
SiteToPicarro, 4.63
Topicarro, 5.86
IsoCapTest, 4.61
None, 1.56
OsoCapTest2, 5.37
TestLoop, 3.06
backpackcheck, 3.35
LoopTest, 2.80
TestLoop2, 3.29
Refgascap, 3.74
backpackcheck, 5.27
RefGas_N_IsoCap_Test, 4.04
mfg test 1 , 3.91
lindentree, 3.72
Loop, 4.62
10012014, 3.21
benton st &amp;kensington ave, 3.32
blackfield ct, 3.42
benton and wood duck, 3.88
RefGasIsoCapTest, 3.20
robinson, 3.80
blackcield ct, 3.53
kensgton ct, 3.16
Tolick, 10.05
test isotopic 20141001, 3.56
TestReferenceGas, 2.80
RefGasIsoCapTest, 3.89
RefGasIsoTCapTest, 3.41
10022014, 6.12
beta 4 castle way, 1.79
beta 4 1165 saxon way, 1.85
beta 4 1165 saxon waysurvey 2, 1.08
beta 4 olive, 1.94
beta 4 reyna ct, 2.17
340 san mateo dr, 1.63
400 claire pl, 1.67
speed, 9.03
cotton st 1300, 2.06
10032014, 17.26
 1945 valparaiso ave, 1.56
cottton streetjand hill vbew corner leak, 2.31
santa clara and plive, 2.04
Drive1, 11.42
10032014-2, 3.76
fremont pl, 1.41
fremont pl 2, 1.51
1012 college ave, 2.52
1012 college ave 2, 2.68
arbor rd , 1.05
abror, 1.42
fremont st, 2.00
arbor 3school out, 2.58
roble ct, 2.54
DriveTest, 1.93
wallea dr, 1.25
reyna redo, 1.76
avp to berk 10/4/14, 4.48
avp to berk 10/4/14, 11.83
avp from berk 10/04/14, 7.42
avp to hay10/04/14, 3.68
avp to hay10/04/14, 3.17
avp to sc 10/6/14, 5.61
avp to sc 10/6/14, 2.99
CWP_TEST, 2.54
10062014, 3.27
princeton isocap, 0.15
graceland, 6.64
10062014-2, 4.19
requal, 2.74
10062014-3, 4.57
WhiteEscapeTest, 3.47
testsurvey, 5.11
WhiteEscapeTest2, 3.28
avp to hay, 3.75
10072014-8hoursdrive, 3.37
10072014-8hoursdrive, 8.44
manual 0.12, 3.49
GPS_FOV_Test1, 2.61
avp in sc 10/7/14, 6.07
manual 0.3, 2.64
GPS_FOV_Test3, 1.30
GPS_FOV_Test2, 1.26
GPS_FOV_Test4, 0.98
ToPaloAlto, 8.01
manual 1.0, 3.27
rapidresp, 2.95
operator, 3.47
iso repeats, 4.49
Test, 7.13
avp to sun 10/7, 7.11
Quimby run, 6.73
avp to quimby, 6.38
None, 3.58
None, 4.09
avp to hay 10/7, 5.49
None, 4.74
survey map area xyz1, 2.12
None, 5.96
longsurvey, 5.98
None, 2.86
8hr survey, 6.31
None, 1.84
None, 17.38
None, 14.12
None, 7.84
avp sc 1, 3.64
bugTestAnders, 4.57
None, 3.41
None, 17.42
andersBugTest2, 3.75
Jay smoke test, 10.73
None, 6.83
None, 5.52
None, 5.35
Test survey processing, 7.92
8hr survey, 7.29
6hr survey, 3.90
Drive1, 4.62
10092014, 5.48
DriveFOV2, 2.44
DriveFOV3, 2.00
DriveFOV3_10MPH, 2.40
DriveFOV4_25MPH, 1.78
DriveFOV2_1, 2.64
DriveFOV2_2, 2.21
DriveFOV2_3, 2.26
ToMenloPark, 6.95
10092014-8hoursdrive, 5.44
IsoCap_MenloPark, 3.66
isocaps, 6.28
FastGPS-1-AreaA, 5.00
FastGPS-2-AreaA, 3.31
isocaps2, 3.10
isocaps2, 5.52
8hr survey, 7.35
Isocap, 6.44
FastGPS-3-AreaA, 4.74
FastGPS-4-AreaA, 4.61
postupgratedrive, 6.16
Isocap2, 4.48
Isocap3, 4.25
Isocap4 @corner, 3.53
FastGPS-5-PuffTest, 2.07
controlled captures, 3.76
quickrun, 4.45
controlledisocaps, 3.41
cancelledcapture, 3.00
calibrationcap1, 4.89
calibrationcap2, 3.17
calibrationcap3, 2.82
calibrationcap4, 2.79
calibrationcap5, 2.43
calibrationcap6, 3.06
calibrationcap7, 2.86
10122014-8hoursdrive, 4.88
calibrationcap7cont, 3.03
calibrationcap7cont2, 3.13
calibrationcap8, 3.59
calibrationcap8, 4.37
calibrationcap8cont, 2.64
calibrationcap8cont, 3.89
calibrationcap9, 3.69
aaatest, 0.70
aaatest, 1.29
TestDrive, 9.82
alarmTest1, 1.96
alarmRTesr3, 3.10
isocap1, 3.80
isocap2, 4.91
teat, 2.71
isocap3, 5.50
DriveTest2, 4.32
isocap4, 4.97
10132014, 5.33
TESTdrive, 3.31
isocap5, 6.37
isocap6, 5.60
isocap, 3.61
10142014, 7.19
LongSurvey, 8.31
pause, 6.70
startstoptest, 7.84
longSurvey, 9.04
pause, 5.08
pause, 9.34
GPS test, 4.72
GPS test 2, 3.79
GPS test 3, 4.93
10152014-8hoursdrive, 5.72
LongSurvey, 6.62
bug1304, 3.60
Ref bottle test, 1.36
alarmtest, 2.04
alarmtest, 2.55
bug 1304_1, 5.59
Dual-Max, 5.66
forced refgas fail2, 3.33
Dual-Max, 6.00
forced refgas fail3, 3.69
Rapid response, 2.72
Operator, 3.76
C3D2-Continous, 3.84
RapidResponseTest, 2.36
C3D2-Continous, 0.75
C3D2-Continuous, 2.10
Fast-Location1, 0.86
Fast-1.38Lm-4m-20mph, 2.07
test-max, 2.44
C3D2-Continuous, 2.00
Fast-1.37Lm-4m-20mph, 1.35
test-max, 2.27
refgascap1, 1.94
test-max, 3.29
Fast-0.47Lm-5m-20mph, 3.55
test-max, 1.32
test-max, 4.12
C3D2-Continuous, 2.31
Fast-0.47Lm-5m-20mph, 3.68
test-max, 4.29
Fast-0.47Lm-4m-20mph, 4.08
C3D2-Continuous, 2.86
Fast-0.47Lm-5m-40mph, 5.16
isoGPStest, 4.20
Fast-123Lm-5m-20mph, 4.02
Fast-123Lm-5m-40mph, 4.42
surveyinredwoodcity, 5.63
connor's test, 5.29
Fast-1.16Lm-13m-40mph, 5.06
Fast-1.16Lm-13m-20mph, 4.60
refgas, 3.60
christest, 3.77
chris2, 1.92
chris3, 2.06
vale test, 2.31
vale test2, 2.10
Men'o8hrCD, 6.30
RB-S1-2014-10-19-1006, 2.02
DF1400_20141020, 4.16
ref gas measurments, 1.90
history, 2.56
history, 3.98
history, 2.58
Menlo8hrCD, 8.38
8 hour jon training, 8.37
disconnect anem, 1.63
Menlo-Night-8h, 5.55
4hoursurvey, 7.65
MultipleRefGasTest, 4.17
MultiRefGas, 4.32
MultiIsoCap, 2.87
None, 1.85
RefGasCap-2014-10-22-1800, 2.43
refgas-2014-22-10-1600, 2.38
skref-2014-22-10-1809, 2.62
skref-2014-22-10-1809, 0.90
vale night dual system menlo park, 5.22
vale night dual system menlo park, 1.11
vale night dual system menlo park, 1.09
vale night dual system menlo park, 1.27
vale night dual system menlo park, 4.80
P3200-S_Beta2_Day1, 3.03
10232014-survey1, 3.76
P3200-S_Beta2_Day1, 5.15
10232014-survey2, 5.54
ref gas test, 2.00
Ref Gas Test, 1.54
10242014-4hoursdrive, 1.67
Ref Gas Test, 1.32
RB-Test- 2014-10-24-1132, 0.67
RB-Test-2014-10-24-1139, 0.70
RB-Test- 2014-10-24-1154, 0.47
MtHamiltonRefGasIsoCap, 6.56
Ref Gas Test, 1.79
Ref Gas Test, 6.97
4hoursdriveinmelonpark, 4.84
10262014-8hoursdrive, 6.61
10252014-8hr-cd, 6.81
8 hour menlo jdang, 8.36
10262014-8hourdrive, 8.06
8hr-menlo-areaAB, 8.24
enterprise, 4.77
to sf, 6.53
sf rr, 2.82
10272014, 3.90
RB-Sanity-2014-10-27-1825, 2.24
Menlo8hrCD, 3.44
Menlo2hrc.03, 5.07
Menlo2hrC.3, 2.67
MultiRefGasIsoCap, 4.16
Menlo2hrC.03, 7.74
Menlo2hrD.3, 1.12
MenloC, 1.55
MenloC, 1.97
MenloC, 1.24
Menlo2hrD, 2.10
pausetest, 4.50
pausetest, 4.30
Menlo8hrAB, 4.86
Menlo4hrA, 5.36
Menlo4hrC, 19.58
to sf, 13.42
Menlo4hrB, 4.32
Menlo4hrD, 2.78
MenloLongSurveyAB, 5.71
attitudetest, 7.07
MenloA, 3.16
IsotopicCaptureinRain, 1.43
isocap, 1.62
melonparkdriving, 6.98
MenloSunDrive, 4.18
Menlo4hrC, 8.35
melonC, 3.09
melonC, 1.83
melonC, 2.80
melonC, 2.37
melonC, 2.92
melonC, 4.42
Menlo2hrB, 2.77
Lisa intro, 3.42
Lisa intro, 5.87
Menlo2hrA, 1.76
MenloC2Hr, 15.04
MenloD2hr, 5.12
MenloC, 2.13
MenloC, 2.25
MenloC, 1.91
MenloC, 18.36
MenloC, 1.79
MenloC, 1.96
clisa, 3.65
MenloC, 1.71
clisa, 3.32
clisa, 0.83
vale pause test, 2.20
vale pause test, 2.36
vale pause test, 0.47
MelonC, 1.79
MenloC, 0.77
MenloAreaA, 7.52
MenloAreaB, 2.96
pausefunction, 16.32
pausefunction, 2.43
menloC, 4.82
pausefunction, 2.72
pausefunction, 3.48
test1, 4.92
test1, 1.49
test1, 1.08
test1, 2.20
pausefunction, 2.55
to sf, 6.47
mfg test 20141106, 5.54
mfg test2 20141106, 2.22
Menlo-M, 16.02
Menlo-N, 1.75
Menlo-O, 2.37
Menlo-iso, 0.86
MenloD, 4.77
MenloD, 1.99
MenloD, 4.77
MenloD, 1.94
MenloC, 3.17
MenloD, 1.90
MenloD, 2.55
MenloC, 2.48
MenloD, 2.00
MenloC, 1.90
MenloD, 2.67
MenloC, 1.89
MenloC, 2.23
MenloD, 2.42
MenloC, 2.60
MenloD, 2.72
MenloC, 2.16
MenloD, 2.33
MenloC, 2.16
MenloD, 2.36
MenloC, 2.40
MenloD, 1.69
MenloD, 1.34
MenloD, 1.87
MenloC, 1.72
MenloD, 2.24
MenloC, 2.41
MenloD, 2.34
MenloC, 2.61
mfg test2 20141107, 4.53
MenloC, 1.76
MenloD, 3.97
MenloC, 2.02
MenloD, 1.78
MenloC, 1.92
MenloD, 2.76
MenloC, 2.48
MenloD, 1.39
MenloC, 1.73
MenloD, 2.08
MenloC, 1.51
MenloD, 5.91
MenloC, 1.31
MenloC, 8.29
MenloD, 1.42
MenloC, 1.48
MenloC, 4.52
Nov9 Pause Test, 2.77
Nov9 Pause Test, 2.65
Nov9 Pause Test, 1.50
Nov9 Pause Test, 2.62
Nov9 Pause Test, 1.82
Nov9 Pause Test, 1.55
Nov9 Pause Test, 13.11
Nov9 Pause Test, 1.77
Nov9 Pause Test, 2.26
Nov9 Pause Test, 1.93
Nov9 Pause Test, 2.46
Nov9 Pause Test, 2.05
Nov9 Pause Test, 2.42
Nov9 Pause Test, 4.21
Nov9 Pause Test, 1.39
Nov9 Pause Test, 1.93
Nov9 Pause Test, 2.33
Nov9 Pause Test, 2.18
Nov9 Pause Test, 1.35
Nov9 Pause Test, 1.49
Nov9 Pause Test, 1.78
Nov9 Pause Test, 2.45
Nov9 Pause Test, 2.06
Nov9 Pause Test, 16.44
Nov9 Pause Test, 0.95
Menlo-GPStest-AreaC, 3.39
mfg test 20141110, 2.71
GPS test corners, 1.67
11102014, 6.27
GPS test corners, 1.18
Menlo-GPStest-Creek, 2.17
vale pause test, 1.90
vale pause test, 2.14
vale pause test, 2.03
vale pause test, 3.66
Menlo-GPStest-Arbor, 3.91
Menlo-GPStest-Arbor-2, 2.51
Menlo-GPStest-Arbor-2, 1.62
mfg test 20141110 2, 7.06
Menlo-GPStest-Creek-2, 1.91
mfg test 20141110 3, 4.20
Menlo-GPStest-Alto, 1.96
Menlo-GPStest-Arbor-3, 2.24
MenloC8hr, 5.13
mfg test 20141111 1, 3.71
gpstest, 7.07
gpstest, 3.21
vale san jose leak, 4.08
cvale pause test, 2.65
cvale pause test, 2.14
gpstest, 3.51
gpstest, 2.25
gpstest, 3.38
gpstest, 4.72
mfg test 20141111 2, 3.17
MenloC, 2.40
None, 5.31
MenloC, 0.98
MenloC, 3.86
MenloC, 0.62
MenloC, 1.27
MenloC, 0.62
MenloC, 1.52
MenloC, 0.98
MenloC, 0.67
MenloC, 0.81
MenloC, 0.86
MenloC, 1.27
MenloC, 0.70
MenloC, 1.13
MenloC, 0.72
MenloC, 0.78
MenloC, 0.96
MenloC, 0.58
MenloC, 0.77
MenloC, 1.03
MenloC, 1.54
MenloC, 0.60
MenloC, 0.89
MenloC, 0.45
MenloC, 1.07
MenloC, 0.78
MenloC, 1.38
MenloC, 1.44
MenloC, 0.93
MenloC, 2.02
MenloC, 1.09
MenloC, 0.79
MenloC, 1.13
MenloC, 0.70
MenloC , 0.71
MenloC, 0.81
MenloC, 6.36
MenloC, 1.29
MenloC, 3.16
MenloC, 0.96
MenloC1, 0.39
MenloC, 0.84
MenloC, 0.75
MenloC, 1.42
avp sc 11/12, 1.50
avp sc 11/12, 1.36
avp sc 11/12, 2.34
avp sc 11/12, 1.96
avp sc 11/12, 3.27
avp sc 11/12, 2.81
avp sc 11/12 a, 1.94
avp sc 11/12, 2.47
avp sc 11/12, 0.80
avp sc 11/12 a, 1.29
avp sc 11/12, 2.88
avp sc 11/12, 1.35
avp sc 11/12 a, 1.64
avp sc 11/12, 1.10
avp sc 11/12, 1.08
avp sc 11/12 a, 1.64
avp sc 11/12, 1.93
avp sc 11/12 a, 3.06
avp sc 11/12, 2.82
zankertasman, 3.61
avp menlo 11/12, 6.94
RB-Test-2014-11-12-1444, 1.06
mfg test 20141112 1, 3.14
iso capture, 5.51
zankertasman, 4.49
avp menlo 11/12, 3.22
isotopic, 3.11
mfg test 20141112 2, 2.74
MelnoC, 4.78
MenloD, 1.22
Ref, 0.66
Ref, 0.48
Ref, 1.55
Ref, 1.01
Thermo Genic, 3.19
MenloC, 3.58
Bio Genic, 5.24
SantaClaraA, 3.84
Ref, 4.34
SantaClaraA, 3.70
Refgas jy, 1.69
santaclaraC, 4.26
Refgas jy, 3.04
santaclaraC, 3.39
santaclaraA, 3.36
santaclaraA, 1.09
santaclaraA, 3.32
SantaClaraB, 3.89
santaclaraA, 3.38
gpstest, 5.36
2042 health, 1.20
2042 Ref, 1.60
2042 Iso PatrickHenry, 3.11
2042 Iso Zanker, 2.41
Redwood#, 6.56
Redwood #, 1.99
2042 GPS, 5.73
Redwood M, 1.23
Redwood M, 1.66
Redwood#, 0.40
Redwood#, 0.43
Redwood#, 0.62
Redwood#, 0.50
Redwood#, 7.86
Redwood #, 0.62
Redwood #, 1.20
Redwood #, 0.94
Redwood #, 0.69
Redwood #, 0.92
Redwood #, 1.45
CMCFT, 0.59
CMCFT, 0.64
CMCFT, 0.74
CMCFT, 0.79
CMCFT, 0.72
CMCFT, 0.59
CMCFT, 0.65
Redwood O, 1.46
Redwood #, 0.23
Redwood O, 1.41
2042 Ref, 4.21
Redwood M, 0.38
Redwood O, 0.33
RedwoodGrey, 6.77
biogenic capture, 2.81
redwood grey, 8.58
captures, 4.13
redwood grey, 5.62
RedwoodGrey, 7.46
captures_bio, 6.14
thermogenic capture, 2.83
dfCaptures, 2.04
dfCaptures, 3.65
iso cap, 4.19
captures_regas, 2.39
captures_regas, 2.14
RedwoodGrey, 1.26
Redwood8hr, 4.87
Redwood8hr, 4.01
Redwood8hr, 0.43
Redwood8hr, 0.32
Redwood8hr, 0.17
Redwood8hr, 0.45
Redwood8hr, 2.11
Redwood8hr, 0.73
Emerald GPS, 5.51
Test1, 6.51
Day 4 Redwood, 5.45
Day 4 Redwood, 7.46
</t>
<t tx="sze.20150510223148.1"></t>
<t tx="sze.20150510223148.10"># Check for the interval between methane data points and set the AnalyzerStatusDataRateMask if the exponentially averaged rate
#  is too slow

tooSlow = False
dt = _DATA_['interval']
if _DATA_['SpectrumID'] == FastMethaneSpectrumId:
    if _DATA_["CH4"] &gt; MethaneConcThreshold:
        dt = 0.25
    _PERSISTENT_["fastMethaneInterval"] = expAverage(_PERSISTENT_["fastMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
    tooSlow = _PERSISTENT_["fastMethaneInterval"] &gt; FastMethaneIntervalMax
elif _DATA_['SpectrumID'] == IsotopicMethaneSpectrumId:
    if _DATA_["CH4"] &gt; MethaneConcThreshold:
        dt = 1.0
    _PERSISTENT_["isotopicMethaneInterval"] = expAverage(_PERSISTENT_["isotopicMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
    tooSlow = _PERSISTENT_["isotopicMethaneInterval"] &gt; IsotopicMethaneIntervalMax
if tooSlow:
    AnalyzerStatus |= AnalyzerStatusDataRateMask

if _DATA_['CFADS_base'] &gt; CavityBaselineLossScaleFactor * _PERSISTENT_['baselineCavityLoss']:
    AnalyzerStatus |= AnalyzerStatusCavityBaselineLossMask

if (_NEW_DATA_['delta_interval'] &gt; DeltaIntervalMax) and (not alarmActive) and alarmActiveState:
    AnalyzerStatus |= AnalyzerStatusSamplingIntervalMask

if _DATA_['spect_latency'] &gt; SpectrumLatencyMax:
    AnalyzerStatus |= AnalyzerStatusRingdownRateMask

if numpy.absolute(_DATA_['ch4_high_shift']) &gt; WlmShiftMax:
    AnalyzerStatus |= AnalyzerStatusWlmShiftMask

if numpy.absolute(_DATA_['ch4_high_adjust']) &gt; WlmAdjustMax:
    AnalyzerStatus |= AnalyzerStatusWlmAdjustMask

if (numpy.absolute(_DATA_['ch4_high_shift']) &gt;= WlmShiftAdjustLimit) and (numpy.absolute(_DATA_['ch4_high_adjust']) &lt; WlmShiftAdjustLimit):
    AnalyzerStatus |= AnalyzerStatusWlmShiftAdjustCorrelationMask

_PERSISTENT_['wlmOffsetBuffer'].append(_PERSISTENT_['wlm6_offset'])
wlm6OffsetMean = numpy.mean(_PERSISTENT_['wlmOffsetBuffer'])
wlm6OffsetMax = max(_PERSISTENT_['wlmOffsetBuffer'])
wlm6OffsetMin = min(_PERSISTENT_['wlmOffsetBuffer'])

if wlm6OffsetMean != 0.0:
    if ((wlm6OffsetMax - wlm6OffsetMin) / wlm6OffsetMean) &gt; WlmTargetFreqMaxDrift:
        AnalyzerStatus |= AnalyzerStatusWlmTargetFreqMask
        
# Set the InvalidData mask in the AnalyzerStatus. Currently it is set only if the data rate is too low.
if 0 != (AnalyzerStatus &amp; AnalyzerStatusDataRateMask):
    AnalyzerStatus |= AnalyzerStatusInvalidDataMask

        
</t>
<t tx="sze.20150510223148.2">(uncached) sze.20150506155630.1
Diff...
- #  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
  #  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
  #  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
  #              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the
  #              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.
  #  2011 0727 - modified isotopic methane analysis to use new schemes that report the entire spectrum in one piece
  # 2014 0602 removed unnecessary sections left from CFI
  #           added flag for isotopic capture when WB within .07 degC tolerance
  #           improved reporting structure for Peripheral health monitoring
  
  import os
  import sys
  import inspect
  import traceback
  import collections
  
  from math import exp
  
  import numpy
  from numpy import mean, isfinite, isnan
  
  from Host import PeriphIntrf
  from Host.Common.EventManagerProxy import Log, LogExc
  from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
  from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
  from Host.Common.timestamp import getTimestamp
  
  here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
  if here not in sys.path:
      sys.path.append(here)
  
  from Chemdetect.instructionprocess import InstructionProcess # new ChemDetect
  from Host.Common.CustomConfigObj import CustomConfigObj # new ChemDetect
  
</t>
<t tx="sze.20150510223148.3">#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
#              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the
#              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.
#  2011 0727 - modified isotopic methane analysis to use new schemes that report the entire spectrum in one piece
# 2014 0602 removed unnecessary sections left from CFI
#           added flag for isotopic capture when WB within .07 degC tolerance
#           improved reporting structure for Peripheral health monitoring

import os
import sys
import inspect
import traceback
import collections

from math import exp

import numpy
from numpy import mean, isfinite, isnan

from Host import PeriphIntrf
from Host.Common.EventManagerProxy import Log, LogExc
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
from Host.Common.timestamp import getTimestamp

here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path:
    sys.path.append(here)

from Chemdetect.instructionprocess import InstructionProcess # new ChemDetect
from Host.Common.CustomConfigObj import CustomConfigObj # new ChemDetect

</t>
<t tx="sze.20150510223148.4">#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  Data analysis script for the experimental instrument combining CBDS with CFADS for methane and water
#  2011 0323 - removed wlm3 feedback for SID 109 (old water at 6250) and used VL3 for the
#              high precision CH4 measurement, SID 25.  Now wlm4 is used exclusively for the
#              low precision CH4 measurement, SID 29, which is also used for iCO2 correction.
#  2011 0727 - modified isotopic methane analysis to use new schemes that report the entire spectrum in one piece
# 2014 0602 removed unnecessary sections left from CFI
#           added flag for isotopic capture when WB within .07 degC tolerance
#           improved reporting structure for Peripheral health monitoring

import os
import sys
import inspect
import traceback
import collections

from math import exp

import numpy
from numpy import mean, isfinite, isnan

from Host import PeriphIntrf
from Host.Common.EventManagerProxy import Log, LogExc
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
from Host.Common.timestamp import getTimestamp

here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path:
    sys.path.append(here)

from Chemdetect.instructionprocess import InstructionProcess # new ChemDetect
from Host.Common.CustomConfigObj import CustomConfigObj # new ChemDetect

</t>
<t tx="sze.20150510223148.5">(uncached) sze.20150506194536.1
Diff...
  # Limits for delta values reported
  REPORT_UPPER_LIMIT = 20000.0
  REPORT_LOWER_LIMIT = -20000.0
  # WB Temperature Proximity condition for isotopic measurement
  WB_TEMP_ISO_THRESHOLD = 0.07
  # SpectrumIds used
  TARGET_SPECIES = [11, 25, 105, 106, 150, 153]
  # Parameters for updating WLM Offsets
  max_adjust = 1.0e-5
  max_adjust_H2O = 1.0e-4
  damp = 0.2
  # Maximum delay before signalling data manager latency
  max_delay = 20
  # Constants for calculating mean interval between data points
  FastMethaneSpectrumId = 25
  IsotopicMethaneSpectrumId = 150
- MethaneIntervalAveragingTime = 30.0
?                                    -
+ MethaneIntervalAveragingTime = 30.0- MethaneConcThreshold = 5.0
</t>
<t tx="sze.20150510223148.6"># Limits for delta values reported
REPORT_UPPER_LIMIT = 20000.0
REPORT_LOWER_LIMIT = -20000.0
# WB Temperature Proximity condition for isotopic measurement
WB_TEMP_ISO_THRESHOLD = 0.07
# SpectrumIds used
TARGET_SPECIES = [11, 25, 105, 106, 150, 153]
# Parameters for updating WLM Offsets
max_adjust = 1.0e-5
max_adjust_H2O = 1.0e-4
damp = 0.2
# Maximum delay before signalling data manager latency
max_delay = 20
# Constants for calculating mean interval between data points
FastMethaneSpectrumId = 25
IsotopicMethaneSpectrumId = 150
MethaneIntervalAveragingTime = 30.0</t>
<t tx="sze.20150510223148.7"># Limits for delta values reported
REPORT_UPPER_LIMIT = 20000.0
REPORT_LOWER_LIMIT = -20000.0
# WB Temperature Proximity condition for isotopic measurement
WB_TEMP_ISO_THRESHOLD = 0.07
# SpectrumIds used
TARGET_SPECIES = [11, 25, 105, 106, 150, 153]
# Parameters for updating WLM Offsets
max_adjust = 1.0e-5
max_adjust_H2O = 1.0e-4
damp = 0.2
# Maximum delay before signalling data manager latency
max_delay = 20
# Constants for calculating mean interval between data points
FastMethaneSpectrumId = 25
IsotopicMethaneSpectrumId = 150
MethaneIntervalAveragingTime = 30.0
MethaneConcThreshold = 5.0
</t>
<t tx="sze.20150510223148.8">(uncached) sze.20150506164942.1
Diff...
  # Check for the interval between methane data points and set the AnalyzerStatusDataRateMask if the exponentially averaged rate
  #  is too slow
- 
  tooSlow = False
  dt = _DATA_['interval']
  if _DATA_['SpectrumID'] == FastMethaneSpectrumId:
-     if _DATA_["CH4"] &gt; MethaneConcThreshold:
-         dt = 0.25
      _PERSISTENT_["fastMethaneInterval"] = expAverage(_PERSISTENT_["fastMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
      tooSlow = _PERSISTENT_["fastMethaneInterval"] &gt; FastMethaneIntervalMax
  elif _DATA_['SpectrumID'] == IsotopicMethaneSpectrumId:
-     if _DATA_["CH4"] &gt; MethaneConcThreshold:
-         dt = 1.0
      _PERSISTENT_["isotopicMethaneInterval"] = expAverage(_PERSISTENT_["isotopicMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
      tooSlow = _PERSISTENT_["isotopicMethaneInterval"] &gt; IsotopicMethaneIntervalMax
  if tooSlow:
      AnalyzerStatus |= AnalyzerStatusDataRateMask
  
  if _DATA_['CFADS_base'] &gt; CavityBaselineLossScaleFactor * _PERSISTENT_['baselineCavityLoss']:
      AnalyzerStatus |= AnalyzerStatusCavityBaselineLossMask
  
  if (_NEW_DATA_['delta_interval'] &gt; DeltaIntervalMax) and (not alarmActive) and alarmActiveState:
      AnalyzerStatus |= AnalyzerStatusSamplingIntervalMask
  
  if _DATA_['spect_latency'] &gt; SpectrumLatencyMax:
      AnalyzerStatus |= AnalyzerStatusRingdownRateMask
  
  if numpy.absolute(_DATA_['ch4_high_shift']) &gt; WlmShiftMax:
      AnalyzerStatus |= AnalyzerStatusWlmShiftMask
  
  if numpy.absolute(_DATA_['ch4_high_adjust']) &gt; WlmAdjustMax:
      AnalyzerStatus |= AnalyzerStatusWlmAdjustMask
  
  if (numpy.absolute(_DATA_['ch4_high_shift']) &gt;= WlmShiftAdjustLimit) and (numpy.absolute(_DATA_['ch4_high_adjust']) &lt; WlmShiftAdjustLimit):
      AnalyzerStatus |= AnalyzerStatusWlmShiftAdjustCorrelationMask
  
  _PERSISTENT_['wlmOffsetBuffer'].append(_PERSISTENT_['wlm6_offset'])
  wlm6OffsetMean = numpy.mean(_PERSISTENT_['wlmOffsetBuffer'])
  wlm6OffsetMax = max(_PERSISTENT_['wlmOffsetBuffer'])
  wlm6OffsetMin = min(_PERSISTENT_['wlmOffsetBuffer'])
  
  if wlm6OffsetMean != 0.0:
      if ((wlm6OffsetMax - wlm6OffsetMin) / wlm6OffsetMean) &gt; WlmTargetFreqMaxDrift:
          AnalyzerStatus |= AnalyzerStatusWlmTargetFreqMask
          
  # Set the InvalidData mask in the AnalyzerStatus. Currently it is set only if the data rate is too low.
  if 0 != (AnalyzerStatus &amp; AnalyzerStatusDataRateMask):
      AnalyzerStatus |= AnalyzerStatusInvalidDataMask
  
-         
?         -
+         </t>
<t tx="sze.20150510223148.9"># Check for the interval between methane data points and set the AnalyzerStatusDataRateMask if the exponentially averaged rate
#  is too slow
tooSlow = False
dt = _DATA_['interval']
if _DATA_['SpectrumID'] == FastMethaneSpectrumId:
    _PERSISTENT_["fastMethaneInterval"] = expAverage(_PERSISTENT_["fastMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
    tooSlow = _PERSISTENT_["fastMethaneInterval"] &gt; FastMethaneIntervalMax
elif _DATA_['SpectrumID'] == IsotopicMethaneSpectrumId:
    _PERSISTENT_["isotopicMethaneInterval"] = expAverage(_PERSISTENT_["isotopicMethaneInterval"], dt, dt, MethaneIntervalAveragingTime)
    tooSlow = _PERSISTENT_["isotopicMethaneInterval"] &gt; IsotopicMethaneIntervalMax
if tooSlow:
    AnalyzerStatus |= AnalyzerStatusDataRateMask

if _DATA_['CFADS_base'] &gt; CavityBaselineLossScaleFactor * _PERSISTENT_['baselineCavityLoss']:
    AnalyzerStatus |= AnalyzerStatusCavityBaselineLossMask

if (_NEW_DATA_['delta_interval'] &gt; DeltaIntervalMax) and (not alarmActive) and alarmActiveState:
    AnalyzerStatus |= AnalyzerStatusSamplingIntervalMask

if _DATA_['spect_latency'] &gt; SpectrumLatencyMax:
    AnalyzerStatus |= AnalyzerStatusRingdownRateMask

if numpy.absolute(_DATA_['ch4_high_shift']) &gt; WlmShiftMax:
    AnalyzerStatus |= AnalyzerStatusWlmShiftMask

if numpy.absolute(_DATA_['ch4_high_adjust']) &gt; WlmAdjustMax:
    AnalyzerStatus |= AnalyzerStatusWlmAdjustMask

if (numpy.absolute(_DATA_['ch4_high_shift']) &gt;= WlmShiftAdjustLimit) and (numpy.absolute(_DATA_['ch4_high_adjust']) &lt; WlmShiftAdjustLimit):
    AnalyzerStatus |= AnalyzerStatusWlmShiftAdjustCorrelationMask

_PERSISTENT_['wlmOffsetBuffer'].append(_PERSISTENT_['wlm6_offset'])
wlm6OffsetMean = numpy.mean(_PERSISTENT_['wlmOffsetBuffer'])
wlm6OffsetMax = max(_PERSISTENT_['wlmOffsetBuffer'])
wlm6OffsetMin = min(_PERSISTENT_['wlmOffsetBuffer'])

if wlm6OffsetMean != 0.0:
    if ((wlm6OffsetMax - wlm6OffsetMin) / wlm6OffsetMean) &gt; WlmTargetFreqMaxDrift:
        AnalyzerStatus |= AnalyzerStatusWlmTargetFreqMask
        
# Set the InvalidData mask in the AnalyzerStatus. Currently it is set only if the data rate is too low.
if 0 != (AnalyzerStatus &amp; AnalyzerStatusDataRateMask):
    AnalyzerStatus |= AnalyzerStatusInvalidDataMask

        </t>
</tnodes>
</leo_file>
