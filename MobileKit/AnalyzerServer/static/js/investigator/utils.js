var mapmaster = mapmaster || {};
window.log = function() {
    log.history = log.history || []; // store logs to an array for reference
    log.history.push(arguments);
    if (this.console) {
        console.log(Array.prototype.slice.call(arguments));
    }
    // $('#debugoutput').html(Array.prototype.slice.call(arguments))
};

window.getURLParameter = function(name) {
    return decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
    );
}

window.blog = function(num){
    var out = "";
    var test = function(val){
        if(num & val){
            out = "1" + out;
        }else{
            out = "0" + out;
        }
    }

    test(1)
    for(var i = 1 ; i <= 8 ; i++){
        test(Math.pow(2,i))
    }
    log(out);
    return out;
}

window.ll = function(){
  $('#debugoutput').prepend('<span>' + Array.prototype.slice.call(arguments) + '</span><br/>');
};

var startTime = 0;
var endTime = 0;

var startTimes = {};
var endTimes = {};

function startTimer(label){
    startTimes[label] = Date.now();
}

function stopTimer(label){
    endTimes[label] = Date.now();
    log("timer:" + label, endTimes[label] - startTimes[label]);
    // startTime = endTime = 0;
}

var simplifyPath = function( points, tolerance ) {
    log('timing start:',  points.length);
    startTimer();
    var R = 6371;
    var arr = [];
    for(var i = 0 ; i < 100 ; i++){
        var p = points[i];
        var p2 = points[i+1];
        var lat2 = p2.pdata.lat;
        var lat1= p.pdata.lat;
        var lon2 = p2.pdata.lon;
        var lon1 = p.pdata.lon;
        var x = (lon2-lon1) * Math.cos((lat1+lat2)/2);
        var y = (lat2-lat1);
        var d = Math.sqrt(x*x + y*y) * R;
        // log(d - arr[arr.length - 1])
        arr.push(d);
    }
    
    stopTimer('timer 2:' + arr.slice(0,20));
    return arr;
};


function get_time_zone_offset() {
    var current_date, gmt_offset;
    current_date = new Date();
    gmt_offset = current_date.getTimezoneOffset() / 60;
    $('#gmt_offset').val(gmt_offset);
    rtn_offset = $('#gmt_offset').val();
    // alert(rtn_offset)
    return gmt_offset;
}

// Calculate the additional wind direction standard deviation based on the wind speed and the car speed.
//  This is an empirical model to estimate the performace of the measurement process.
//  N.B. This must be consistent with that used for calculation of swath width
function astd(wind,vcar){
    return Math.min(Math.PI,CSTATE.astd_a*(CSTATE.astd_b+CSTATE.astd_c*vcar)/(wind+0.01));
}

// Calculate the total standard deviation of the wind in DEGREES given the wind speed, the standard deviation
//  in DEGREES from WIND_DIR_SDEV and the speed of the car. Uses astd to provide the additional standard deviation
//  estimate
function totSdev(wind,wSdev,vcar){
    var dstd = CNSNT.dtr * wSdev;
    var extra = astd(wind,vcar);
    return CNSNT.rtd*Math.sqrt(dstd*dstd + extra*extra);
}


// Current State
if (!mapmaster.CSTATE) {
    mapmaster.CSTATE = {};
}


// Text Strings
mapmaster.TXT = {
    amp: 'Amp',
    sigma: 'HalfWidth',
    lat: 'Lat',
    lon: 'Long',
    ch4: 'CH4',
    conc: 'Concentration',
    delta: 'Delta',
    uncertainty: 'Uncertainty',
    note: 'Annotation',
    cancel: 'Cancel',
    ok: 'OK',
    save_note: 'Save Annotation',
    close: 'Close',
    download_files: 'Download Files',
    download_concs: 'Download Concentration',
    download_peaks: 'Download Peaks',
    download_analysis: 'Download Analysis',
    download_notes: 'Download Notes',
    anz_cntls: 'Surveyor Controls',
    restart_log: 'Restart Log',
    switch_to_cptr: 'Start Capture',
    start_survey: "Start Survey",
    stop_survey: "Stop Survey",
    complete_survey: "Complete Survey",
    cancl_ref: 'Cancel Reference',
    cancl_cptr: 'Cancel Capture',
    cancl_ana: 'Cancel Analysis',
    cancl_ana_time: 's left: Cancel',
    calibrate: 'Analyze Reference Gas',
    shutdown: 'Shutdown Surveyor',
    select_log: 'Select Log',
    switch_to_prime: 'Switch to Prime View',
    peak: 'Peak',
    analysis: 'Analysis',
    path: 'Route',
    note_list: 'Select Note to view',
    conn_warning_hdr: 'Connection Warning',
    conn_warning_txt: 'There is a problem with the network connection. Please verify connectivity.',
    survey_mode: 'Survey Mode',
    capture_mode: 'Capture Mode',
    analyzing_mode: 'Analyzing Peak',
    inactive_mode: 'Inactive Mode',
    cancelling_mode: 'Canceling...',
    priming_mode: 'Priming inlet',
    purging_mode: 'Purging inlet',
    injection_pending_mode: 'Injecting Gas',
    prime_conf_msg: 'Do you want to switch to Prime View Mode? \n\nWhen the browser is in Prime View Mode, you will have control of the Surveyor.',
    change_min_amp: 'Min Amplitude', //'Minimum Amplitude'
    change_stab_class: 'Stability Class', //'Stability Class'
    change_peak_threshold: 'Peak Threshold',
    restart_datalog_msg: 'Close current data log and open a new one?',
    shutdown_anz_msg: 'Do you want to shut down the Surveyor? \n\nWhen the analyzer is shutdown it can take 30 to 45 minutes warm up.',
    stop_survey_msg: 'Are you sure you want to stop collecting data?',
    cancel_cap_msg: 'Cancel capture and return to survey mode?',
    cancel_ana_msg: 'Cancel analysis and return to survey mode?',
    cancel_ref_msg: 'Cancel reference gas processing?',
    start_ref_msg: 'Connect reference gas bottle and open valve. Press OK when ready.',
    show_controls: 'Show Controls',
    show_anote: 'Show analysis annotations',
    click_show_cntls: 'Click to show controls',
    map_controls: 'Map Controls',
    anote: 'Analysis annotation',
    show_notes: 'Show user annotations on map',
    abubble: 'Isotopic Analysis',
    windRay: 'Wind Rays',
    show_markers: 'Show system markers on map',
    show_txt: 'Show',
    hide_txt: 'Hide',
    working: 'Working',
    calibration_pulse_injected: 'Reference gas injected',

    stream_title: 'Data Transfer Status Indicators',
    stream_ok: 'Data Transfer OK',
    stream_warning: 'Intermittent Data Transfer',
    stream_failed: 'Data Transfer Failed',
    gps_title: 'GPS Status Indicators',
    gps_ok: 'GPS OK',
    gps_warning: 'Unreliable GPS Signal',
    gps_failed: 'GPS Failed',
    gps_uninstalled: 'GPS Not Detectable',
    ws_title: 'Weather Station Status Indicators',
    ws_ok: 'Weather Station OK',
    ws_failed: 'Weather Station Failed',
    ws_uninstalled: 'Weather Station Not Detectable',
    analyzer_title: 'Current Surveyor Status',
    cavity_p: 'Cavity Pressure',
    cavity_t: 'Cavity Temperature',
    wb_t: 'Warm Box Temperature',

    stab_star: "*: Use reported weather data",
    stab_a: "A: Very Unstable",
    stab_b: "B: Unstable",
    stab_c: "C: Slightly Unstable",
    stab_d: "D: Neutral",
    stab_e: "E: Slightly Stable",
    stab_f: "F: Stable",

    export_as_txt: "Export data as txt file.",
    export_as_csv: "Export data as csv file.",

    copyClipboard: "Ctrl-C copies cursor position to clipboard",

    survey_time: "Survey time",
    day: "Day",
    night: "Night",
    sunlight: "Solar Radiation",
    strong_sunlight: "Strong",
    moderate_sunlight: "Moderate",
    overcast_sunlight: "Overcast",
    cloud: "Cloud Cover",
    less50_cloud: "&lt;50%",
    more50_cloud: "&gt;50%",
    wind: "Wind",
    calm_wind: "Calm",
    light_wind: "Light",
    strong_wind: "Strong",
    choose: "Please select an option",
    select_weather: "Weather Conditions"
};

//Constant Values
mapmaster.CNSNT = {
	svcurl:"/rest",
    annotation_url:false,
    callbacktest_url:"",
    analyzer_name:"",
    user_id:"",
    resturl:"/rest",
    resource_Admin:"admin",
    resource_AnzMeta:"",
    resource_AnzLog:"",
    resource_AnzLogMeta:"",
    resource_AnzLogNote:"",
    sys:"",
    identity:""
};


// initial "|" is expected with no trailing "|"
mapmaster.CNSNT.peak_bbl_clr = "|40FFFF|000000";
mapmaster.CNSNT.analysis_bbl_clr = "|FF8080|000000";
mapmaster.CNSNT.path_bbl_clr = "|FFFF90|000000";



// trailing "|" is expected
mapmaster.CNSNT.peak_bbl_tail = "bb|"; // tail bottom left
mapmaster.CNSNT.analysis_bbl_tail = "bb|";  // tail bottom left
mapmaster.CNSNT.path_bbl_tail = "bbtl|"; // tail top left

mapmaster.CNSNT.peak_bbl_anchor = null; //newPoint(0, 42); //d_bubble_text_small is 42px high
mapmaster.CNSNT.analysis_bbl_anchor = null; //newPoint(0, 42); //d_bubble_text_small is 42px high
mapmaster.CNSNT.path_bbl_anchor = null; //newPoint(0, 0);

mapmaster.CNSNT.peak_bbl_origin = null; //newPoint(0, 0);
mapmaster.CNSNT.analysis_bbl_origin = null; //newPoint(0, 0);
mapmaster.CNSNT.path_bbl_origin = null; //newPoint(0, 0);

mapmaster.CNSNT.normal_path_color = "#0000FF";
mapmaster.CNSNT.analyze_path_color = "#000000";
//mapmaster.CNSNT.inactive_path_color = "#996633";
mapmaster.CNSNT.inactive_path_color = "#FF0000";
mapmaster.CNSNT.streamwarning =  (1000 * 10);
mapmaster.CNSNT.streamerror =  (1000 * 30);

mapmaster.CNSNT.histMax = 200;

mapmaster.CSTATE.getDataLimit = 10000;

mapmaster.CSTATE.seedDataLimit = 10000;

mapmaster.CNSNT.fastUpdatePeriod = 1000;
mapmaster.CNSNT.datUpdatePeriod = 5000;
mapmaster.CNSNT.longDatUpdatePeriod = 500;
mapmaster.CNSNT.analysisUpdatePeriod = 1;
mapmaster.CNSNT.peakAndWindUpdatePeriod = 1;
mapmaster.CNSNT.noteUpdatePeriod = 1;
mapmaster.CNSNT.progressUpdatePeriod = 1;
mapmaster.CNSNT.modeUpdatePeriod = 1;
mapmaster.CNSNT.periphUpdatePeriod = 1;


mapmaster.CNSNT.hmargin = 30;
mapmaster.CNSNT.vmargin = 0;
mapmaster.CNSNT.map_topbuffer = 20;
mapmaster.CNSNT.map_bottombuffer = 0;

mapmaster.CNSNT.analysisNoteList = ['conc', 'delta', 'uncertainty', 'lat', 'lon'];

mapmaster.CNSNT.gmt_offset = get_time_zone_offset();


mapmaster.CNSNT.rest_default_timeout = 60000;

mapmaster.CNSNT.stab_control = {
    "*": mapmaster.TXT.stab_star
    , A: mapmaster.TXT.stab_a
    , B: mapmaster.TXT.stab_b
    , C: mapmaster.TXT.stab_c
    , D: mapmaster.TXT.stab_d
    , E: mapmaster.TXT.stab_e
    , F: mapmaster.TXT.stab_f
};

mapmaster.CNSNT.export_control = {
    "file": mapmaster.TXT.export_as_txt
  , "csv": mapmaster.TXT.export_as_csv
};


mapmaster.CNSNT.spacer_gif = '/static/images/icons/spacer.gif';

mapmaster.CNSNT.callbacktest_timeout = 4000;

mapmaster.CNSNT.gpsPort = 0;
mapmaster.CNSNT.wsPort = 1;
mapmaster.CNSNT.gpsUpdateTimeout = 60000;
mapmaster.CNSNT.wsUpdateTimeout = 60000;
mapmaster.CNSNT.turnOnAudio = false;

mapmaster.CNSNT.prime_view = true;
mapmaster.CNSNT.log_sel_opts = [];

mapmaster.CNSNT.mapControl = undefined;
mapmaster.CNSNT.mapControlDiv = undefined;

mapmaster.CNSNT.mapConcPlot = undefined;
mapmaster.CNSNT.mapConcPlotDiv = undefined;

mapmaster.CNSNT.earthRadius = 6378100;

mapmaster.CNSNT.dtr  = Math.PI/180.0;    // Degrees to radians
mapmaster.CNSNT.rtd  = 180.0/Math.PI;    // Radians to degrees

mapmaster.CNSNT.cookie_duration = 14;
mapmaster.CNSNT.dashboard_app = false;

mapmaster.CNSNT.loader_gif_img = '<img src="/static/images/ajax-loader.gif" alt="processing"/>';

mapmaster.CNSNT.INSTMGR_STATUS_READY = 0x0001;
mapmaster.CNSNT.INSTMGR_STATUS_MEAS_ACTIVE = 0x0002;
mapmaster.CNSNT.INSTMGR_STATUS_ERROR_IN_BUFFER = 0x0004;
mapmaster.CNSNT.INSTMGR_STATUS_GAS_FLOWING = 0x0040;
mapmaster.CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED = 0x0080;
mapmaster.CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED = 0x0100;
mapmaster.CNSNT.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED = 0x0200;
mapmaster.CNSNT.INSTMGR_STATUS_WARMING_UP = 0x2000;
mapmaster.CNSNT.INSTMGR_STATUS_SYSTEM_ERROR = 0x4000;
mapmaster.CNSNT.INSTMGR_STATUS_MASK = 0xFFFF;
mapmaster.CNSNT.INSTMGR_AUX_STATUS_SHIFT = 16;
mapmaster.CNSNT.INSTMGR_AUX_STATUS_WEATHER_MASK = 0x1F;

// Number of data points to defer warning about missing weather information
mapmaster.CNSNT.weatherMissingDefer  = 120;
mapmaster.CNSNT.weatherMissingInit   = 10;
mapmaster.CNSNT.classByWeather = { 0: "D",  8: "D", 16: "D", // Daytime, Overcast
                  2: "B", 10: "C", 18: "D", // Daytime, moderate sun
                  4: "A", 12: "B", 20: "C", // Daytime, strong sun
                  1: "F",  9: "E", 17: "D", // Nighttime, <50% cloud
                  3: "E", 11: "D", 19: "D"  // Nighttime, >50% cloud
                };

// Colors of concentration markers below and above threshold
mapmaster.CNSNT.concMarkerBelowThresholdColor = "#a0a0a0";
mapmaster.CNSNT.concMarkerAboveThresholdColor = "#0000ff";


mapmaster.CSTATE.firstData = true;
mapmaster.CSTATE.initialFnIsRun = false;
mapmaster.CSTATE.net_abort_count = 0;
mapmaster.CSTATE.follow = false;
mapmaster.CSTATE.overlay = false;

mapmaster.CSTATE.prime_available = false;
mapmaster.CSTATE.prime_test_count = 0;
mapmaster.CSTATE.green_count = 2;

mapmaster.CSTATE.resize_map_inprocess = false;
mapmaster.CSTATE.current_mode = 0;
mapmaster.CSTATE.getting_mode = false;
mapmaster.CSTATE.getting_periph_time = false;

mapmaster.CSTATE.getting_warming_status = false;
mapmaster.CSTATE.end_warming_status = false;

mapmaster.CSTATE.current_zoom = undefined;
mapmaster.CSTATE.current_mapTypeId = undefined;

// mapmaster.CSTATE.center_lon = -121.9588851928711;
mapmaster.CSTATE.center_lon = -121.9088851928711;
mapmaster.CSTATE.center_lat = 36.60628544518459;


mapmaster.CSTATE.alog = "";
mapmaster.CSTATE.alog_peaks = "";
mapmaster.CSTATE.alog_analysis = "";

mapmaster.CSTATE.showAnote = true;
mapmaster.CSTATE.showAbubble = true;
mapmaster.CSTATE.showWindRay = true;

mapmaster.CSTATE.lastwhere = '';
mapmaster.CSTATE.lastFit = '';
mapmaster.CSTATE.lastGpsUpdateStatus = 0; //0 = Not installed; 1 = Good; 2 = Failed
mapmaster.CSTATE.lastWsUpdateStatus = 0; //0 = Not installed; 1 = Good; 2 = Failed
mapmaster.CSTATE.lastPathColor = mapmaster.CNSNT.normal_path_color;
mapmaster.CSTATE.lastInst = '';
mapmaster.CSTATE.lastTimestring = '';
mapmaster.CSTATE.lastDataFilename = '';
mapmaster.CSTATE.lastPeakFilename = '';
mapmaster.CSTATE.lastAnalysisFilename = '';
mapmaster.CSTATE.laststreamtime = new Date().getTime();

mapmaster.CSTATE.counter = 0;
mapmaster.CSTATE.peakLine = 1;
mapmaster.CSTATE.analysisLine = 1;
mapmaster.CSTATE.clearAnalyses = false;
mapmaster.CSTATE.startNewPath = true;
mapmaster.CSTATE.nextAnalysisEtm = 0.0;
mapmaster.CSTATE.nextPeakEtm = 0.0;
mapmaster.CSTATE.nextDatEtm = 0.0;
mapmaster.CSTATE.nextAnalysisUtm = 0.0;
mapmaster.CSTATE.nextPeakUtm = 0.0;
mapmaster.CSTATE.nextDatUtm = 0.0;
mapmaster.CSTATE.clearAnalysisNote = false;
mapmaster.CSTATE.clearConcMarkers = false;

mapmaster.CSTATE.startPos = null;

mapmaster.CSTATE.ignoreTimer = false;
mapmaster.CSTATE.ignoreRequests = false;

mapmaster.CSTATE.path = null;
mapmaster.CSTATE.squares = {};
mapmaster.CSTATE.circles = {};
mapmaster.CSTATE.rays = {};

mapmaster.CSTATE.pathListener = {};
mapmaster.CSTATE.concMarkerListener = {};
mapmaster.CSTATE.markerByPos = {};
mapmaster.CSTATE.concPlotFollowing = [];
mapmaster.CSTATE.concPlotNotFollowing = [];

mapmaster.CSTATE.map  = null;
mapmaster.CSTATE.map2 = null;
mapmaster.CSTATE.carMarker = null;
mapmaster.CSTATE.mapListener = {};

mapmaster.CSTATE.marker = null;
mapmaster.CSTATE.gglOptions = null;
mapmaster.CSTATE.analysisMarkers = {};
mapmaster.CSTATE.windMarkers = {};
mapmaster.CSTATE.methaneHistory = [];
mapmaster.CSTATE.posHistory = [];

mapmaster.CSTATE.analysisNoteMarkers = {};
mapmaster.CSTATE.analysisNoteDict = {};
mapmaster.CSTATE.analysisNoteListener = {};
mapmaster.CSTATE.analysisBblListener = {};

mapmaster.CSTATE.pathGeoObjs = [];

mapmaster.CSTATE.pobj = [];

mapmaster.CSTATE.noteSortSel = undefined;
mapmaster.CSTATE.resize_for_conc_data = true;


mapmaster.CSTATE.exportClass = 'file';
mapmaster.CSTATE.stabClass = 'D';     // Pasquill-Gifford stability class
mapmaster.CSTATE.minLeak =   1.0;     // Minimum leak to consider in cubic feet/hour
mapmaster.CSTATE.minAmp = 0.1;

// Parameters for estimating addtional standard deviation in wind direction
mapmaster.CSTATE.astd_a  = 0.15*Math.PI;
mapmaster.CSTATE.astd_b  = 0.25;          // Wind speed in m/s for standard deviation to be astd_a
mapmaster.CSTATE.astd_c  = 0.0;           // Factor multiplying car speed in m/s

// Variable to indicate when weather information is missing
mapmaster.CSTATE.weatherMissingCountdown = mapmaster.CNSNT.weatherMissingInit;
mapmaster.CSTATE.showingWeatherDialog = false;
mapmaster.CSTATE.inferredStabClass = null;
mapmaster.CSTATE.prevInferredStabClass = null;

mapmaster.CSTATE.windRayByPos = {};
mapmaster.CSTATE.concMarkerOffset = null;
mapmaster.CSTATE.concMarkerScale = 20.0;
mapmaster.CSTATE.peakThreshold = 0.0;

mapmaster.CSTATE.concMarkerLayer = null;
mapmaster.CSTATE.windRayLayer = null;
mapmaster.CSTATE.analysisMarkerLayer = null;
mapmaster.CSTATE.layerControl = null;

//Html button
mapmaster.HBTN = {
        exptLogBtn: '<div><button id="id_exptLogBtn" type="button" onclick="exportLog();" class="btn btn-fullwidth">' + mapmaster.TXT.download_concs + '</button></div>',
        exptPeakBtn: '<div><button id="id_exptPeakBtn" type="button" onclick="exportPeaks();" class="btn btn-fullwidth">' + mapmaster.TXT.download_peaks + '</button></div>',
        exptAnalysisBtn: '<div><button id="id_exptAnalysisBtn" type="button" onclick="exportAnalysis();" class="btn btn-fullwidth">' + mapmaster.TXT.download_analysis + '</button></div>',
        exptNoteBtn: '<div><button id="id_exptNoteBtn" type="button" onclick="exportNotes();" class="btn btn-fullwidth">' + mapmaster.TXT.download_notes + '</button></div>',
        restartBtn: '<div><button id="id_restartBtn" type="button" onclick="restart_datalog();" class="btn btn-fullwidth">' + mapmaster.TXT.restart_log + '</button></div>',
        captureBtn: '<div><button id="id_captureBtn" type="button" onclick="captureSwitch();" class="btn btn-fullwidth">' + mapmaster.TXT.switch_to_cptr + '</button></div>',
        cancelCapBtn: '<div><button id="id_cancelCapBtn" type="button" onclick="cancelCapSwitch();" class="btn btn-fullwidth">' + mapmaster.TXT.cancl_cptr + '</button></div>',
        cancelAnaBtn: '<div><button id="id_cancelAnaBtn" type="button" onclick="cancelAnaSwitch();" class="btn btn-fullwidth">' + mapmaster.TXT.cancl_ana + '</button></div>',
        calibrateBtn: '<div><button id="id_calibrateBtn" type="button" onclick="referenceGas();" class="btn btn-fullwidth">' + mapmaster.TXT.calibrate + '</button></div>',
        shutdownBtn: '<div><button id="id_shutdownBtn" type="button" onclick="shutdown_analyzer();" class="btn btn-danger btn-fullwidth">' + mapmaster.TXT.shutdown + '</button></div>',
        downloadBtn: '<div><button id="id_downloadBtn" type="button" onclick="modalPaneExportControls();" class="btn btn-fullwidth">' + mapmaster.TXT.download_files + '</button></div>',
        analyzerCntlBtn: '<div><button id="id_analyzerCntlBtn" type="button" onclick="modalPanePrimeControls();" class="btn btn-fullwidth">' + mapmaster.TXT.anz_cntls + '</button></div>',
        warningCloseBtn: '<div><button id="id_warningCloseBtn" onclick="restoreModalDiv();" class="btn btn-fullwidth">' + mapmaster.TXT.close + '</button></div>',
        modChangeCloseBtn: '<div><button id="id_modChangeCloseBtn" onclick="restoreModChangeDiv();" class="btn btn-fullwidth">' + mapmaster.TXT.close + '</button></div>',
        switchLogBtn: '<div><button id="id_switchLogBtn" onclick="switchLog();" class="btn btn-fullwidth">' + mapmaster.TXT.select_log + '</button></div>',
        switchToPrimeBtn: '<div><button id="id_switchToPrimeBtn" onclick="switchToPrime();" class="btn btn-fullwidth">' + mapmaster.TXT.switch_to_prime + '</button></div>',
        changeMinAmpCancelBtn: '<div><button id="id_changeMinAmpCancelBtn" onclick="changeMinAmpVal(false);" class="btn btn-fullwidth">' + mapmaster.TXT.cancel + '</button></div>',
        changeMinAmpOkBtn: '<div><button id="id_changeMinAmpOkBtn" onclick="changeMinAmpVal(true);" class="btn btn-fullwidth">' + mapmaster.TXT.ok + '</button></div>',
        changeStabClassCancelBtn: '<div><button id="id_changeStabClassCancelBtn" onclick="changeStabClassVal(false);" class="btn btn-fullwidth">' + mapmaster.TXT.cancel + '</button></div>',
        changeStabClassOkBtn: '<div><button id="id_changeStabClassOkBtn" onclick="changeStabClassVal(true);" class="btn btn-fullwidth">' + mapmaster.TXT.ok + '</button></div>',
        changePeakThresholdCancelBtn: '<div><button id="id_changePeakThresholdCancelBtn" onclick="changePeakThresholdVal(false);" class="btn btn-fullwidth">' + mapmaster.TXT.cancel + '</button></div>',
        changePeakThresholdOkBtn: '<div><button id="id_changePeakThresholdOkBtn" onclick="changePeakThresholdVal(true);" class="btn btn-fullwidth">' + mapmaster.TXT.ok + '</button></div>',

        changeMinAmpOkHidBtn: '<div style="display: hidden;"><button id="id_changeMinAmpOkHidBtn" onclick="changeMinAmpVal(true);"/></div>',
        surveyOnOffBtn: '<div><button id="id_surveyOnOffBtn" type="button" onclick="stopSurvey();" class="btn btn-fullwidth">' + mapmaster.TXT.stop_survey + '</button></div>',
        completeSurveyBtn: '<div><button id="id_completeSurveyBtn" type="button" onclick="completeSurvey();" class="btn btn-fullwidth">' + mapmaster.TXT.complete_survey + '</button></div>',
        copyClipboardOkBtn: '<div><button id="id_copyClipboardOkBtn" type="button" onclick="copyCliboard();" class="btn btn-fullwidth">' + mapmaster.TXT.ok + '</button></div>',
        weatherFormOkBtn: '<div><button id="id_weatherFormOkBtn" type="button" class="btn btn-fullwidth">' + mapmaster.TXT.ok + '</button></div>',
        repaintDataBtn: '<div><button id="id_repaintDataBtn" type="button" onclick="repaintData();" class="btn btn-fullwidth">' + 'Repaint Data' + '</button></div>'
    };

// List of Html buttons (<li>....</li><li>....</li>...)
mapmaster.LBTNS = {
        downloadBtns: '<li>' + mapmaster.HBTN.downloadBtn + '</li>',
        analyzerCntlBtns: '<li>' + mapmaster.HBTN.surveyOnOffBtn + '</li><br/><li>' + mapmaster.HBTN.captureBtn + '</li><br/><li>' + mapmaster.HBTN.analyzerCntlBtn + '</li><br/>' + mapmaster.HBTN.repaintDataBtn + '</li><br/>'
    };

var COOKIE_PREFIX = "p3gdu";
mapmaster.COOKIE_NAMES = {
    mapTypeId: COOKIE_PREFIX + '_mapTypeId',
    anote: COOKIE_PREFIX + '_anote',
    abubble: COOKIE_PREFIX + '_abubble',
    follow: COOKIE_PREFIX + '_follow',
    zoom: COOKIE_PREFIX + '_zoom',
    center_latitude: COOKIE_PREFIX + '_center_latitude',
    center_longitude: COOKIE_PREFIX + '_center_longitude',
    windRay: COOKIE_PREFIX + '_windRay',
    dspStabClass: COOKIE_PREFIX + '_dspStabClass',
    dspExportClass: COOKIE_PREFIX + '_dspExportClass',
    weather: COOKIE_PREFIX + '_weather'
};