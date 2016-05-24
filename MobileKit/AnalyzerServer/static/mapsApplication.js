/* jshint undef:true, unused:true, laxcomma:true, trailing:false, -W014, -W069, -W083 */
/*globals $, alert, clearTimeout, confirm, console, document, encodeGeoHash */
/*globals getCookie, google, p3RestApi, PLAT_IMG_BASE, PLATOBJS, setCookie, setTimeout, window */
// 'use strict';
/**
 * write log to console. 
 * If last argument is "debug" then only write if debug system option is set.
 * 
 * Examples:
 *      gdu_logger("Some debug message", some_object, "debug");
 *      gdu_logger("Some Message that always displays on console");
 * 
 * @param {String or Object} 
 * @param {String or Object} 
 * @param {String} "debug" optional  
 * @return {null}
 */

var GDUDEBUG = false;

var gdu_logger = function() {
    var i, len, printMe;
    len = arguments.length;
    
    printMe = true;
    
    if (len > 0) {
        if (arguments[len-1] === "debug") {
            if (GDUDEBUG !== true) {
                printMe = false;
            }
        }
    }
    
    if (printMe === true) {
        var tm = new Date();
        for(i = 0; i < len; i += 1) {
            if (arguments[i] !== "debug") {
                console.log(tm.toTimeString() + " gdu.js " + tm.getMilliseconds(), "::: ", arguments[i]);
            }
        }
    }
};

this.gdu_logger = gdu_logger;
    
var COOKIE_PREFIX = "p3gdu";
var COOKIE_NAMES = {};

//Html button
var HBTN = {
        exptLogBtn: '<div><button id="id_exptLogBtn" type="button" onclick="exportLog();" class="btn btn-fullwidth">' + P3TXT.download_concs + '</button></div>',
        exptPeakBtn: '<div><button id="id_exptPeakBtn" type="button" onclick="exportPeaks();" class="btn btn-fullwidth">' + P3TXT.download_peaks + '</button></div>',
        exptAnalysisBtn: '<div><button id="id_exptAnalysisBtn" type="button" onclick="exportAnalysis();" class="btn btn-fullwidth">' + P3TXT.download_analysis + '</button></div>',
        exptNoteBtn: '<div><button id="id_exptNoteBtn" type="button" onclick="exportNotes();" class="btn btn-fullwidth">' + P3TXT.download_notes + '</button></div>',

        exptLogBtnDis: '<div><button id="id_exptLogBtn" disabled type="button" onclick="exportLog();" class="btn btn-fullwidth">' + P3TXT.download_concs + '</button></div>',
        exptPeakBtnDis: '<div><button id="id_exptPeakBtn" disabled type="button" onclick="exportPeaks();" class="btn btn-fullwidth">' + P3TXT.download_peaks + '</button></div>',
        exptAnalysisBtnDis: '<div><button id="id_exptAnalysisBtn" disabled type="button" onclick="exportAnalysis();" class="btn btn-fullwidth">' + P3TXT.download_analysis + '</button></div>',
        exptNoteBtnDis: '<div><button id="id_exptNoteBtn" disabled type="button" onclick="exportNotes();" class="btn btn-fullwidth">' + P3TXT.download_notes + '</button></div>',

        restartBtn: '<div><button id="id_restartBtn" type="button" onclick="restart_datalog();" class="btn btn-fullwidth">' + P3TXT.restart_log + '</button></div>',
        captureBtn: '<div><button id="id_captureBtn" type="button" onclick="captureSwitch();" class="btn btn-fullwidth">' + P3TXT.switch_to_cptr + '</button></div>',
        cancelCapBtn: '<div><button id="id_cancelCapBtn" type="button" onclick="cancelCapSwitch();" class="btn btn-fullwidth">' + P3TXT.cancl_cptr + '</button></div>',
        cancelAnaBtn: '<div><button id="id_cancelAnaBtn" type="button" onclick="cancelAnaSwitch();" class="btn btn-fullwidth">' + P3TXT.cancl_ana + '</button></div>',
        calibrateBtn: '<div><button id="id_calibrateBtn" type="button" onclick="referenceGas();" class="btn btn-fullwidth">' + P3TXT.calibrate + '</button></div>',
        shutdownBtn: '<div><button id="id_shutdownBtn" type="button" onclick="shutdown_analyzer();" class="btn btn-danger btn-fullwidth">' + P3TXT.shutdown + '</button></div>',
        downloadBtn: '<div><button id="id_downloadBtn" type="button" onclick="modalPaneExportControls();" class="btn btn-fullwidth">' + P3TXT.download_files + '</button></div>',
        analyzerCntlBtn: '<div><button id="id_analyzerCntlBtn" type="button" onclick="modalPanePrimeControls();" class="btn btn-fullwidth">' + P3TXT.anz_cntls + '</button></div>',
        warningCloseBtn: '<div><button id="id_warningCloseBtn" onclick="restoreModalDiv();" class="btn btn-fullwidth">' + P3TXT.close + '</button></div>',
        modChangeCloseBtn: '<div><button id="id_modChangeCloseBtn" onclick="restoreModChangeDiv();" class="btn btn-fullwidth">' + P3TXT.close + '</button></div>',
        switchLogBtn: '<div><button id="id_switchLogBtn" onclick="switchLog();" class="btn btn-fullwidth">' + P3TXT.select_log + '</button></div>',
        switchToPrimeBtn: '<div><button id="id_switchToPrimeBtn" onclick="switchToPrime();" class="btn btn-fullwidth">' + P3TXT.switch_to_prime + '</button></div>',
        changeMinAmpCancelBtn: '<div><button id="id_changeMinAmpCancelBtn" onclick="changeMinAmpVal(false);" class="btn btn-fullwidth">' + P3TXT.cancel + '</button></div>',
        changeMinAmpOkBtn: '<div><button id="id_changeMinAmpOkBtn" onclick="changeMinAmpVal(true);" class="btn btn-fullwidth">' + P3TXT.ok + '</button></div>',
        changeStabClassCancelBtn: '<div><button id="id_changeStabClassCancelBtn" onclick="changeStabClassVal(false);" class="btn btn-fullwidth">' + P3TXT.cancel + '</button></div>',
        changeStabClassOkBtn: '<div><button id="id_changeStabClassOkBtn" onclick="changeStabClassVal(true);" class="btn btn-fullwidth">' + P3TXT.ok + '</button></div>',
        
        changeMinAmpOkHidBtn: '<div style="display: hidden;"><button id="id_changeMinAmpOkHidBtn" onclick="changeMinAmpVal(true);"/></div>',
        allHliteCntl: '<div><button id="id_allHliteCntl" type="button" onclick="removeAllHlites();" class="btn btn-fullwidth">' + P3TXT.remove_all_plat_hlite + '</button></div>',
        surveyOnOffBtn: '<div><button id="id_surveyOnOffBtn" type="button" onclick="stopSurvey();" class="btn btn-fullwidth">' + P3TXT.stop_survey + '</button></div>',
        completeSurveyBtn: '<div><button id="id_completeSurveyBtn" type="button" onclick="completeSurvey();" class="btn btn-fullwidth">' + P3TXT.complete_survey + '</button></div>',
        copyClipboardOkBtn: '<div><button id="id_copyClipboardOkBtn" type="button" onclick="copyCliboard();" class="btn btn-fullwidth">' + P3TXT.ok + '</button></div>',
        weatherFormOkBtn: '<div><button id="id_weatherFormOkBtn" type="button" class="btn btn-fullwidth">' + P3TXT.ok + '</button></div>'
    };

// List of Html buttons (<li>....</li><li>....</li>...)
var LBTNS = {
        downloadBtns: '<li>' + HBTN.downloadBtn + '</li>',
        analyzerCntlBtns: '<li>' + HBTN.surveyOnOffBtn + '</li><br/><li>' + HBTN.captureBtn + '</li><br/><li>' + HBTN.analyzerCntlBtn + '</li><br/>'
    };

// Fixed HTML pane
function modalNetWarning() {
    var hdr, body, footer, c1array, c2array;
    
    body = '<p><h3>' + P3TXT.conn_warning_txt + '</h3></p>';
    
    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.conn_warning_hdr + '</h3>');
    c2array.push(HBTN.warningCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    footer = "";
    
    return setModalChrome(
        hdr,
        body,
        footer
        );   
}

//Constant Values
if (!CNSNT) {
    var CNSNT = {};
    CNSNT.svcurl = "/rest";
    CNSNT.annotation_url = false;
    CNSNT.callbacktest_url = "";
    CNSNT.analyzer_name = "";
    CNSNT.user_id = "";
    CNSNT.resturl = "/rest";
    CNSNT.resource_Admin = "admin";
    CNSNT.resource_AnzMeta = "";
    CNSNT.resource_AnzLog = "";
    CNSNT.resource_AnzLogMeta = "";
    CNSNT.resource_AnzLogNote = "";
    CNSNT.resource_AnzLrt = "";
    CNSNT.sys = "";
    CNSNT.identity = "";
}

CNSNT.google_maptype_name = {
    "ROADMAP": true
    , "SATELLITE": true
    , "HYBRID": true
    , "TERRAIN": true
}

CNSNT.baidu_maptype_name = {
    "BMAP_NORMAL_MAP": "地图"
    , "BMAP_PERSPECTIVE_MAP": "三维"
    , "BMAP_SATELLITE_MAP": "卫星"
    , "BMAP_HYBRID_MAP": "混合"
};
CNSNT.baidu_name_maptype = {};
for (var ky in CNSNT.baidu_maptype_name) {
    if (CNSNT.baidu_maptype_name.hasOwnProperty(ky)) {
        CNSNT.baidu_name_maptype[CNSNT.baidu_maptype_name[ky]] = ky;
    }
}

// initial "|" is expected with no trailing "|"
CNSNT.peak_bbl_clr = "|40FFFF|000000";
CNSNT.analysis_bbl_clr = "|FF8080|000000";
CNSNT.path_bbl_clr = "|FFFF90|000000";

// trailing "|" is expected
CNSNT.peak_bbl_tail = "bb|"; // tail bottom left
CNSNT.analysis_bbl_tail = "bb|";  // tail bottom left
CNSNT.path_bbl_tail = "bbtl|"; // tail top left

CNSNT.peak_bbl_anchor = null; //newPoint(0, 42); //d_bubble_text_small is 42px high 
CNSNT.analysis_bbl_anchor = null; //newPoint(0, 42); //d_bubble_text_small is 42px high
CNSNT.path_bbl_anchor = null; //newPoint(0, 0);

CNSNT.peak_bbl_origin = null; //newPoint(0, 0);
CNSNT.analysis_bbl_origin = null; //newPoint(0, 0);
CNSNT.path_bbl_origin = null; //newPoint(0, 0);

CNSNT.normal_path_color = "#0000FF";
CNSNT.analyze_path_color = "#000000";
//CNSNT.inactive_path_color = "#996633";
CNSNT.inactive_path_color = "#FF0000";
CNSNT.streamwarning =  (1000 * 10);
CNSNT.streamerror =  (1000 * 30);

CNSNT.normal_plat_outline_color = "#000000";
CNSNT.normal_plat_outline_opacity = 0.4;
CNSNT.normal_plat_outline_weight = 0.5;
CNSNT.hlite_plat_outline_color = "#000000";
CNSNT.hlite_plat_outline_opacity = 0.8;
CNSNT.hlite_plat_outline_weight = 2;
CNSNT.active_plat_outline_color = "#008000";
CNSNT.active_plat_outline_opacity = 0.8;
CNSNT.active_plat_outline_weight = 3;

CNSNT.histMax = 200;

CNSNT.datUpdatePeriod = 500; 
CNSNT.analysisUpdatePeriod = 1500;
CNSNT.peakAndWindUpdatePeriod = 1500;
CNSNT.noteUpdatePeriod = 1500;
CNSNT.progressUpdatePeriod = 2000;
CNSNT.modeUpdatePeriod = 2000;
CNSNT.periphUpdatePeriod = 5000;
CNSNT.swathUpdatePeriod = 1000;
CNSNT.swathMaxSkip = 10;

CNSNT.datUpdatePeriodSlow = 5000; 
CNSNT.analysisUpdatePeriodSlow = 10000;
CNSNT.peakAndWindUpdatePeriodSlow = 10000;
CNSNT.noteUpdatePeriodSlow = 10000;
CNSNT.swathUpdatePeriodSlow = 10000;

//        CNSNT.datUpdatePeriod = 5000;
//        CNSNT.analysisUpdatePeriod = 5000;
//        CNSNT.peakAndWindUpdatePeriod = 5000;
//        CNSNT.noteUpdatePeriod = 5000;
//        CNSNT.progressUpdatePeriod = 5000;
//        CNSNT.modeUpdatePeriod = 5000;
//        CNSNT.periphUpdatePeriod = 5000;
//        CNSNT.swathUpdatePeriod = 5000;

CNSNT.hmargin = 30;
CNSNT.vmargin = 0;
CNSNT.map_topbuffer = 0;
CNSNT.map_bottombuffer = 0; 

CNSNT.peakNoteList = ['amp', 'ch4', 'sigma', 'lat', 'lon'];
CNSNT.analysisNoteList = ['conc', 'delta', 'uncertainty', 'lat', 'lon'];
CNSNT.datNoteList = ['ch4', 'lat', 'lon'];

CNSNT.gmt_offset = get_time_zone_offset();

CNSNT.rest_default_timeout = 60000;

CNSNT.stab_control = {
    "*": P3TXT.stab_star
    , A: P3TXT.stab_a
    , B: P3TXT.stab_b
    , C: P3TXT.stab_c
    , D: P3TXT.stab_d
    , E: P3TXT.stab_e
    , F: P3TXT.stab_f
};

CNSNT.export_control = {
    "file": P3TXT.export_as_txt
  , "csv": P3TXT.export_as_csv
};


CNSNT.spacer_gif = '/static/images/icons/spacer.gif';

CNSNT.callbacktest_timeout = 4000;

CNSNT.gpsPort = 0;
CNSNT.wsPort = 1;
CNSNT.gpsUpdateTimeout = 60000;
CNSNT.wsUpdateTimeout = 60000;
CNSNT.turnOnAudio = false;

CNSNT.local_view = (window.location.port == 5000);
CNSNT.prime_view = true;
CNSNT.log_sel_opts = [];

CNSNT.mapControl = undefined;
CNSNT.mapControlDiv = undefined;

CNSNT.earthRadius = 6378100;
CNSNT.swath_color = "#0000CC"; 
CNSNT.swath_opacity = 0.3;
CNSNT.swathWindow = 10;

CNSNT.dtr  = Math.PI/180.0;    // Degrees to radians
CNSNT.rtd  = 180.0/Math.PI;    // Radians to degrees

CNSNT.cookie_duration = 14;
CNSNT.dashboard_app = false;

CNSNT.loader_gif_img = '<img src="/static/images/ajax-loader.gif" alt="processing"/>';

CNSNT.INSTMGR_STATUS_READY = 0x0001;
CNSNT.INSTMGR_STATUS_MEAS_ACTIVE = 0x0002;
CNSNT.INSTMGR_STATUS_ERROR_IN_BUFFER = 0x0004;
CNSNT.INSTMGR_STATUS_GAS_FLOWING = 0x0040;
CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED = 0x0080;
CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED = 0x0100;
CNSNT.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED = 0x0200;
CNSNT.INSTMGR_STATUS_WARMING_UP = 0x2000;
CNSNT.INSTMGR_STATUS_SYSTEM_ERROR = 0x4000;
CNSNT.INSTMGR_STATUS_MASK = 0xFFFF;
CNSNT.INSTMGR_AUX_STATUS_SHIFT = 16;
CNSNT.INSTMGR_AUX_STATUS_WEATHER_MASK = 0x1F;

// Number of data points to defer warning about missing weather information
CNSNT.weatherMissingDefer  = 120;
CNSNT.weatherMissingInit   = 10;
CNSNT.classByWeather = { 0: "D",  8: "D", 16: "D", // Daytime, Overcast
                  2: "B", 10: "C", 18: "D", // Daytime, moderate sun
                  4: "A", 12: "B", 20: "C", // Daytime, strong sun
                  1: "F",  9: "E", 17: "D", // Nighttime, <50% cloud
                  3: "E", 11: "D", 19: "D"  // Nighttime, >50% cloud
                };

var statusPane = function () {
    var pane = '<table style="width: 100%;">';
    pane += '<tr>';
    pane += '<td style="width:25%; padding:5px 0px 10px 10px;">';
    pane += '<img class="stream-ok" src="' + CNSNT.spacer_gif + '" onclick="showStream();" name="stream_stat" id="id_stream_stat" />';
    pane += '</td>';
    pane += '<td style="width:25%; padding:5px 0px 10px 10px;">';
    pane += '<img class="analyzer-ok" src="' + CNSNT.spacer_gif + '" onclick="showAnalyzer();" name="analyzer_stat" id="id_analyzer_stat" />';
    pane += '</td>';
    pane += '<td style="width:25%; padding:5px 0px 10px 10px;">';
    pane += '<img class="gps-uninstalled" src="' + CNSNT.spacer_gif + '" onclick="showGps();" name="gps_stat" id="id_gps_stat" />';
    pane += '</td>';
    pane += '<td style="width:25%; padding:5px 0px 10px 10px;">';
    pane += '<img class="ws-uninstalled" src="' + CNSNT.spacer_gif + '" onclick="showWs();" name="ws_stat" id="id_ws_stat" />';
    pane += '</td>';
    pane += '</tr>';
    pane += '</table>';
    return pane;
}; 

var followPane = function () {
    var pane = '<table style="width: 100%;">'
        + '<tr>'
        + '<td style="width:50%; padding-left:15px;">'
        + '<img class="follow" src="' + CNSNT.spacer_gif + '" data-checked="true" onclick="changeFollow();" name="follow" id="id_follow" />'
        + '</td>'
//        + '<td style="width:33.33%;">'
//        + '<img class="overlay" src="' + CNSNT.spacer_gif + '" data-checked="true" onclick="changeOverlay();" name="overlay" id="id_overlay" />'
//        + '</td>'
        + '<td style="width:50%; padding-right:15px; text-align:right;">'
        + '<img class="wifi" src="' + CNSNT.spacer_gif + '" name="data_alert" id="id_data_alert" />'
        + '</td>'
        + '</tr>'
        + '</table>';

    return pane;
};

var modePane = function() {
    var pane = '';
    
    if (CNSNT.prime_view) {
        pane = '<div style="margin-left:20px;">'
            + '<h2 id="mode">' + P3TXT.survey_mode + '</h2>'
            + '</div>';
    }
    
    return pane;
};

// Current State
if (!CSTATE) {
    var CSTATE = {};
}
CSTATE.firstData = true;
CSTATE.initialFnIsRun = false;
CSTATE.net_abort_count = 0;
CSTATE.follow = true;
CSTATE.overlay = false;
CSTATE.activePlatName = "";
        
CSTATE.prime_available = false;
CSTATE.prime_test_count = 0;
CSTATE.green_count = 2;

CSTATE.resize_map_inprocess = false;
CSTATE.current_mode = 0;
CSTATE.getting_mode = false;
CSTATE.getting_periph_time = false;

CSTATE.getting_warming_status = false;
CSTATE.end_warming_status = false;
        
CSTATE.current_zoom = undefined;
CSTATE.current_mapTypeId = undefined;

CSTATE.center_lon = -121.98432;
CSTATE.center_lat = 37.39604;

CSTATE.alog = "";
CSTATE.alog_peaks = "";
CSTATE.alog_analysis = "";

CSTATE.showDnote = true,
CSTATE.showPnote = true;
CSTATE.showAnote = true;
CSTATE.showPbubble = true;
CSTATE.showAbubble = true;
CSTATE.showWbubble = true;
CSTATE.showSwath = true;
CSTATE.showPlatOutlines = false;

CSTATE.lastwhere = '';
CSTATE.lastFit = '';
CSTATE.lastGpsUpdateStatus = 0; //0 = Not installed; 1 = Good; 2 = Failed
CSTATE.lastWsUpdateStatus = 0; //0 = Not installed; 1 = Good; 2 = Failed
CSTATE.lastPathColor = CNSNT.normal_path_color;
CSTATE.lastInst = '';
CSTATE.lastTimestring = '';
CSTATE.lastDataFilename = '';
CSTATE.lastPeakFilename = '';
CSTATE.lastAnalysisFilename = '';
CSTATE.laststreamtime = new Date().getTime();

CSTATE.counter = 0;
CSTATE.peakLine = 1;
CSTATE.clearLeaks = false;
CSTATE.clearWind = false;
CSTATE.analysisLine = 1;
CSTATE.clearAnalyses = false;

CSTATE.fov_lrt_parms_hash = null; // makeFov Stat Doc
CSTATE.fov_lrt_start_ts = null; // makeFov Stat Doc
CSTATE.fov_status = null; // makeFov Stat Doc
CSTATE.fov_lrtrow = 0; // last lrtRow for the FOV

CSTATE.swathLine = 1;
CSTATE.clearSwath = false;
CSTATE.startNewPath = true;
CSTATE.nextAnalysisEtm = 0.0;
CSTATE.nextPeakEtm = 0.0;
CSTATE.nextDatEtm = 0.0;
CSTATE.nextAnalysisUtm = 0.0;
CSTATE.nextPeakUtm = 0.0;
CSTATE.nextDatUtm = 0.0;
CSTATE.clearDatNote = false;
CSTATE.clearPeakNote = false;
CSTATE.clearAnalysisNote = false;

CSTATE.startPos = null;

CSTATE.ignoreTimer = false;
CSTATE.ignoreRequests = false;

CSTATE.path = null;
CSTATE.pathListener = {};
        
CSTATE.map = undefined;
CSTATE.mapListener = {};
        
CSTATE.marker = null;

CSTATE.gglOptions = null;
CSTATE.baiduOptions = null;

CSTATE.peakMarkers = [];
CSTATE.analysisMarkers = [];
CSTATE.windMarkers = [];
CSTATE.methaneHistory = [];

        
CSTATE.peakNoteMarkers = {};
CSTATE.peakNoteDict = {};
CSTATE.peakNoteListener = {};
CSTATE.peakBblListener = {};

CSTATE.analysisNoteMarkers = {};
CSTATE.analysisNoteDict = {};
CSTATE.analysisNoteListener = {};
CSTATE.analysisBblListener = {};

CSTATE.datNoteMarkers = {};
CSTATE.datNoteDict = {};
CSTATE.datNoteListener = {};

// the following help specify the polygon which represents
//  the effective map area associated with the path
CSTATE.swathPolys  = [];
CSTATE.swathPathShowArray = [];
CSTATE.lastMeasPathLoc = null;
CSTATE.lastMeasPathDeltaLat = null;
CSTATE.lastMeasPathDeltaLon = null;
CSTATE.lastSwathParams = {};
CSTATE.lastSwathOutput = {};
CSTATE.swathSkipCount = 0;
        
CSTATE.pobj = [];
        
CSTATE.noteSortSel = undefined;
CSTATE.resize_for_conc_data = true;

CSTATE.datUpdatePeriod = CNSNT.datUpdatePeriod;
CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriod;
CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriod;
CSTATE.noteUpdatePeriod = CNSNT.noteUpdatePeriod;
CSTATE.swathUpdatePeriod = CNSNT.swathUpdatePeriod;

CSTATE.getDataLimit = 1000; //2000;
CSTATE.getSwathLimit = 500; //1000;
        
CSTATE.exportClass = 'file';   
CSTATE.stabClass = 'D';     // Pasquill-Gifford stability class
CSTATE.minLeak =   1.0;     // Minimum leak to consider in cubic feet/hour
CSTATE.fovMinAmp = 0.03;    // Minimum amplitude for calculation of field of view
CSTATE.minAmp = 0.1;

        
// Parameters for estimating addtional standard deviation in wind direction
CSTATE.astd_a  = 0.15*Math.PI;
CSTATE.astd_b  = 0.25;          // Wind speed in m/s for standard deviation to be astd_a
CSTATE.astd_c  = 0.0;           // Factor multiplying car speed in m/s
       
// Variable to indicate when weather information is missing
CSTATE.weatherMissingCountdown = CNSNT.weatherMissingInit;
CSTATE.showingWeatherDialog = false;
CSTATE.inferredStabClass = null;
CSTATE.prevInferredStabClass = null;

// show download buttons for peaks & analysis
CSTATE.peaksDownload = false;
CSTATE.analysisDownload = false;

var TIMER = {
        prime: null,
        resize: null,
        data: null, // timer for getData
        dnote: null, // timer for getDatNotes
        pnote: null, // timer for getPeakNotes
        analysis: null, // timer for showAnalysis (getAnalysis)
        anote: null, // timer for getAnalysisNotes
        peakAndWind: null, // timer for showLeaksAndWind
        progress: null, //timer for updateProgress
        mode: null, // timer for getMode 
        periph: null, // timer for checkPeriphUpdate
        swath: null, // timer for showing swath
        centerTimer: null // timer for centering the map
    };
    
var modeStrings = {0: P3TXT.survey_mode, 1: P3TXT.capture_mode, 2: P3TXT.capture_mode, 3: P3TXT.analyzing_mode, 4: P3TXT.inactive_mode, 
                   5: P3TXT.cancelling_mode, 6: P3TXT.priming_mode, 7: P3TXT.purging_mode, 8: P3TXT.injection_pending_mode };
                   
// Calculate the additional wind direction standard deviation based on the wind speed and the car speed.
//  This is an empirical model to estimate the performace of the measurement process.
//  N.B. This must be consistent with that used for calculation of swath width

function astd(wind,vcar)
{
    return Math.min(Math.PI,CSTATE.astd_a*(CSTATE.astd_b+CSTATE.astd_c*vcar)/(wind+0.01));
}

function totSdev(wind,wSdev,vcar)
// Calculate the total standard deviation of the wind in DEGREES given the wind speed, the standard deviation
//  in DEGREES from WIND_DIR_SDEV and the speed of the car. Uses astd to provide the additional standard deviation
//  estimate
{
    var dstd = CNSNT.dtr * wSdev;
    var extra = astd(wind,vcar);
    return CNSNT.rtd*Math.sqrt(dstd*dstd + extra*extra);
}

// tableChrome NOTE: first element (index 0) in each cNarray is the "style" tag for the td div
function tableChrome(tblStyle, trStyle, c1array, c2array, c3array, c4array) {
    var tbl, i, len, body, c1sty, c2sty, c3sty, c4sty;
    tbl = '';
    body = '';
    
    c1sty = '';
    c2sty = '';
    c3sty = '';
    c4sty = '';
    
    // all passed arrays must be of same length
    if (c2array !== undefined) {
        if (c1array.length !== c2array.length) {
            return tbl;
        }
    }
    if (c3array !== undefined) {
        if (c1array.length !== c3array.length) {
            return tbl;
        }
    }
    if (c4array !== undefined) {
        if (c1array.length !== c4array.length) {
            return tbl;
        }
    }
    
    len = c1array.length;
    for (i = 0; i < len; i += 1) {
        if (i === 0) {
            c1sty = c1array[i];
            if (c2array !== undefined) {
                c2sty = c2array[i];
            }
            if (c3array !== undefined) {
                c3sty = c3array[i];
            }
            if (c4array !== undefined) {
                c4sty = c4array[i];
            }
        } else {
            body += '<tr ' + trStyle + '>';
            
            body += '<td ' + c1sty + '>' + c1array[i] + '</td>';
            if (c2array !== undefined) {
                body += '<td ' + c2sty + '>' + c2array[i] + '</td>';
            }
            if (c3array !== undefined) {
                body += '<td ' + c3sty + '>' + c3array[i] + '</td>';
            }
            if (c4array !== undefined) {
                body += '<td ' + c4sty + '>' + c4array[i] + '</td>';
            }
            
            body += '</tr>';
        }
    }
    
    tbl += '<table ' + tblStyle + '>';
    tbl += body;
    tbl += '</table>';

    return tbl;
}


// ALL Map API interaction should be here

function positionMapControlDiv() {
    var pge_wdth, hgth_top, lpge_wdth, new_width, new_height, new_top, cen;
    pge_wdth = $('#id_topbar').width(); // - ($('#id_sidebar').width() + 20);
    hgth_top = $('#id_topbar').height() + $('#id_feedback').height() + $('#id_content_title').height();

    $("#id_mapControlDiv").css('position', 'absolute');
    $("#id_mapControlDiv").css('top', hgth_top + 10);
    $("#id_mapControlDiv").css('bottom', 'auto');
    $("#id_mapControlDiv").css('left', pge_wdth - 230);
    $("#id_mapControlDiv").css('right', 'auto');
}

function baiduMapTypeFromName(mtname) {
    var mt;
    switch(mtname) {
        case "BMAP_NORMAL_MAP":
            mt = BMAP_NORMAL_MAP;
            break;
        case "BMAP_HYBIRD_MAP":
            mt = BMAP_HYBIRD_MAP;
            break;
        case "BMAP_PERSPECTIVE_MAP":
            mt = BMAP_PERSPECTIVE_MAP;
            break;
        case "BMAP_SATELLITE_MAP":
            mt = BMAP_SATELLITE_MAP;
            break;
        default:
            mt = BMAP_NORMAL_MAP;
            break;
    }
    //console.log(mtname, mt);
    return mt
}

function slowConvert(lngArray, latArray, done) {
    var newLngArray = [], newLatArray = [];
    var nLeft = lngArray.length;
    for (var i=0; i<lngArray.length; i++) {
        var where = new BMap.Point(lngArray[i], latArray[i]);
        var cb = (function (j) {
            return function(point) {
                newLngArray[j] = point.lng;
                newLatArray[j] = point.lat;
                nLeft -= 1;
                if (nLeft === 0) done(null,newLngArray,newLatArray);
            };
        })(i);
        BMap.Convertor.translate(where, 0, cb);
    }
}

function batchConvert(lngArray, latArray, done) {
    var dLng = 0.008, dLat = 0.03;
    var minLng = 72.004; //, maxLng = 137.8347;
    var minLat = 0.8293; //, maxLat = 55.8271;

    function transform(xfm, lng, lat) {
        // Apply the transform in xfm to coordinates (lng,lat)
        // xfm = [lngBase, latBase, sLng0, sLat0, dsLngdLng, dsLatdLng, dsLngdLat, dsLatdLat]
        var cLng = lng - xfm[0];
        var cLat = lat - xfm[1];
        var sLng = xfm[2]+ cLng*xfm[4] + cLat*xfm[6];
        var sLat = xfm[3]+ cLng*xfm[5] + cLat*xfm[7];
        return [lng+sLng, lat+sLat];
    }

    function processSingle(lng, lat, cb) {
        // Find lower left corner of interpolation cell as a base 36 "key"
        var lngIndex = Math.floor((lng - minLng)/dLng);
        var latIndex = Math.floor((lat - minLat)/dLat);
        var key = (10000*lngIndex + latIndex).toString(36);
        // Fill the xform dictionary by calling Baidu API if this cell has
        //  not yet been seen
        if (key in localStorage) {
            cb(null, transform(JSON.parse(localStorage[key]),lng,lat));
        }
        else {
            var lngBase = minLng + lngIndex*dLng;
            var latBase = minLat + latIndex*dLat;
            var oldLng = [lngBase, lngBase+dLng, lngBase];
            var oldLat = [latBase, latBase, latBase+dLat];
            slowConvert(oldLng, oldLat, function (err, newLng, newLat) {
                if (err) done(err);
                else {
                    // Calculate shifts in the coordinates at three anchor points
                    var sLng = [], sLat = [];
                    sLng[0] = newLng[0] - oldLng[0]; sLat[0] = newLat[0] - oldLat[0];
                    sLng[1] = newLng[1] - oldLng[1]; sLat[1] = newLat[1] - oldLat[1];
                    sLng[2] = newLng[2] - oldLng[2]; sLat[2] = newLat[2] - oldLat[2];
                    // Compute derivatives of the shift function using finite differences
                    localStorage[key] = JSON.stringify([lngBase, latBase,
                        sLng[0], sLat[0],
                        (sLng[1]-sLng[0])/dLng, (sLat[1]-sLat[0])/dLng,
                        (sLng[2]-sLng[0])/dLat, (sLat[2]-sLat[0])/dLat]);
                    cb(null, transform(JSON.parse(localStorage[key]),lng,lat));
                }
            });
        }
    }

    if (lngArray.length !== latArray.length) {
        done(new Error("Longitude and latitude arrays must be of equal length"));
    }
    else {
        var newLngArray = [];
        var newLatArray = [];
        var k = 0;
        var next = function () {
            if (k == latArray.length) done(null, newLngArray, newLatArray);
            else {
                processSingle(lngArray[k], latArray[k], function (err, newCoords) {
                    if (err) done (err);
                    else {
                        newLngArray.push(newCoords[0]);
                        newLatArray.push(newCoords[1]);
                        k += 1;
                        next();
                    }
                });
            }
        };
        next();
    }
}


function doConvertThenProcess(data, processTheData) {
    switch(CNSNT.provider) {
        case "google":
            processTheData();
            break;

        case "baidu":
            if (CNSNT.provider_gpsconvert === true) {
                batchConvert(data.result.GPS_ABS_LONG
                    , data.result.GPS_ABS_LAT
                    , function(err, new_lngs, new_lats) {

                        if (err) {
                            console.log("some bacthConvert err: ", err);
                        } else {
                            data.result.GPS_ABS_LONG = new_lngs;
                            data.result.GPS_ABS_LAT = new_lats;
                            processTheData();
                        }
                    });
            } else {
                processTheData();
            }
            break;
    }
};

function newMap(canvas) {
    if (!CNSNT.hasOwnProperty("provider")) {
        CNSNT.provider = "google";
    }
    if (!CNSNT.hasOwnProperty("provider_gpsconvert")) {
        CNSNT.provider_gpsconvert = false;
    }
    switch(CNSNT.provider) {
        case "google":
            return new google.maps.Map(canvas, CSTATE.gglOptions);
            break;

        case "baidu":
            //console.log("CSTATE.baiduOptions", CSTATE.baiduOptions);
            return new BMap.Map(canvas, CSTATE.baiduOptions);
            break;
    }
}
function newLatLng(lat, lng) {
    switch(CNSNT.provider) {
        case "google":
            return new google.maps.LatLng(lat, lng);
            break;

        case "baidu":
            return new BMap.Point(lng, lat);
            break;
    }
    // return new Microsoft.Maps.Location(lat, lng);
}

function newPolyline(map, clr) {
    switch(CNSNT.provider) {
        case "google":
            var pl = new google.maps.Polyline(
                {path: new google.maps.MVCArray(),
                    strokeColor: clr,
                    strokeOpactity: 1.0,
                    strokeWeight: 2}
            );
            pl.setMap(map);
            return pl;
            break;

        case "baidu":
            var pl = new BMap.Polyline([]
                , {strokeColor: clr
                    , strokeOpactity: 1.0
                    , strokeWeight: 2});
            map.addOverlay(pl);
            return pl;
            break;
    }

}

function newPolygonWithoutOutline(map, clr, opacity, vertices, visible) {
    switch(CNSNT.provider) {
        case "google":
            var poly = new google.maps.Polygon(
                {   paths: vertices,
                    strokeColor: "#000000",
                    strokeOpacity: 0.0,
                    strokeWeight: 0,
                    fillColor: clr,
                    visible: visible,
                    fillOpacity: opacity}
            );
            poly.setMap(map);
            return poly;
            break;

        case "baidu":
            var poly = new BMap.Polygon(vertices
                , {strokeColor: "#000000"
                   , strokeOpacity: 0.0
                   , strokeWeight: 0.01
                   , fillColor: clr
                   //, visible: visible
                   , fillOpacity: opacity}
            );
            map.addOverlay(poly);
            return poly;
            break;
    }
}

function pushToPath(path, where) {
    switch(CNSNT.provider) {
        case "google":
            path.getPath().push(where);
            break;

        case "baidu":
            if (!CSTATE.hasOwnProperty('cpoints')) {
                CSTATE.cpoints = [];
            }

            //console.log("baidu where:", where)
            //alert("pause");
            if (where.lng == 0) {
                alert("lng is 0");
            }
            if (where.lat == 0) {
                alert("lat is 0");
            }
            CSTATE.cpoints.push(where);
            break;
    }
}

function newPoint(x, y) {
    switch(CNSNT.provider) {
        case "google":
            return new google.maps.Point(x, y);
            break;

        case "baidu":
            return new BMap.Point(x, y);
            break;
    }
    // return new Microsoft.Maps.Point(x, y);
}

function newRectangle(minlng, maxlng, minlat, maxlat) {
    switch(CNSNT.provider) {
        case "google":
            var sw, ne, bounds, rectOpts, rect;

            sw = newLatLng(minlat, minlng);
            ne = newLatLng(maxlat, maxlng);
            bounds = new google.maps.LatLngBounds(sw, ne);

            rectOpts = {
                strokeColor: CNSNT.normal_plat_outline_color,
                strokeOpacity: CNSNT.normal_plat_outline_opacity,
                strokeWeight: CNSNT.normal_plat_outline_weight,
                fillColor: "#FFFFFF",
                fillOpacity: 0,
                bounds: bounds,
                editable: false,
                visible: true
            };
            rect = new google.maps.Rectangle(rectOpts);
            return rect;
            break;

        case "baidu":
            var vertices, sw, se, nw, ne;
            sw = newLatLng(minlat, minlng);
            se = newLatLng(minlat, maxlng);
            ne = newLatLng(maxlat, minlng);
            nw = newLatLng(maxlat, maxlng);
            vertices = [sw, se, ne, nw];
            var poly = new BMap.Polygon(vertices
                , {strokeColor: CNSNT.normal_plat_outline_color
                    , strokeOpacity: CNSNT.normal_plat_outline_opacity
                    , strokeWeight: CNSNT.normal_plat_outline_weight
                    , fillColor: "#FFFFFF"
                    , fillOpacity: 0
                }
            );
            map.addOverlay(poly);
            return poly;
            break;
    }
}

function newGroundOverlay(minlng, maxlng, minlat, maxlat, img) {
    switch(CNSNT.provider) {
        case "google":
            var sw, ne, bounds, goOpts, go;

            sw = newLatLng(minlat, minlng);
            ne = newLatLng(maxlat, maxlng);
            bounds = new google.maps.LatLngBounds(sw, ne);

            go = new google.maps.GroundOverlay(img, bounds);
            return go;
            break;

        case "baidu":
            return null;
            break;
    }
}
function baidu_checkZoom() {
    var zm = CSTATE.map.getZoom();
    if (zm !== CSTATE.current_zoom) {
        CSTATE.current_zoom = zm;
        setCookie(COOKIE_NAMES.zoom, CSTATE.current_zoom, CNSNT.cookie_duration);
    }
}

function centerTheMap(cen) {
    switch(CNSNT.provider) {
        case "google":
            CSTATE.map.setCenter(cen);
            break;

        case "baidu":
            baidu_checkZoom();
            CSTATE.map.centerAndZoom(cen, CSTATE.current_zoom);
            break;
    }
}

function centerTheMapLast() {
    if (CSTATE.lastwhere) {
        switch(CNSNT.provider) {
            case "google":
                CSTATE.map.setCenter(CSTATE.lastwhere);
                break;

            case "baidu":
                baidu_checkZoom();
                CSTATE.map.centerAndZoom(CSTATE.lastwhere, CSTATE.current_zoom);
                preserveLastCenter(CSTATE.lastwhere);
                break;
        }
    }
}

function centerTheMapLastTimed() {
    if (CSTATE.follow) {
        centerTheMapLast();
    }
    TIMER.centerTimer = null;
}


function newAnzLocationMarker(map) {
    switch(CNSNT.provider) {
        case "google":
            var mk = new google.maps.Marker({position: map.getCenter(), visible: false});
            mk.setMap(map);
            return mk;
            break;

        case "baidu":
            var mk_icon = new BMap.Icon("http://api.map.baidu.com/images/marker_red_sprite.png"
                , new BMap.Size(46, 50)

            );
            var mk = new BMap.Marker( map.getCenter(), {icon: mk_icon, offset: new BMap.Size(11.5, -5)} );
            map.addOverlay(mk);
            return mk;
            break;
    }
}

function newToken(map, latlng) {
    var size = 2.0;
    var token = makeToken(size,"rgba(64,255,255,255)","black");

    switch(CNSNT.provider) {
        case "google":
            var mk_icon = new google.maps.MarkerImage(token.url,null,null,newPoint(token.radius,token.radius));
            var mk = new google.maps.Marker({position: latlng,
                icon: mk_icon});
            mk.setMap(map);
            return mk;
            break;

        case "baidu":
            var mk_icon = new BMap.Icon(token.url, new BMap.Size(2*token.radius,2*token.radius));
            var mk = new BMap.Marker( latlng
                , {icon: mk_icon
                });
            map.addOverlay(mk);
            return mk;
            break;
    }
}

function newPeakMarker(map, latLng, amp, sigma, ch4) {
    //console.log("newPeakMarker");
    var size, fontsize, mk;
    size = Math.max(0.75,0.25*Math.round(4.0*Math.pow(amp, 1.0 / 4.0)));
    fontsize = 20.0 * size;
    var marker_url = makeMarker(size,"rgba(64,255,255,255)","black",ch4.toFixed(1),"bold "+ fontsize +"px sans-serif","black");

    switch(CNSNT.provider) {
        case "google":
            mk = new google.maps.Marker({position: latLng,
                title: P3TXT.amp + ": " + amp.toFixed(2) + " " + P3TXT.sigma + ": " + sigma.toFixed(1),
                icon: marker_url
            });
            mk.setMap(map);
            return mk;
            break;

        case "baidu":
            var mk_icon = new BMap.Icon(marker_url, new BMap.Size(36 * size + 1,65 * size + 1));
            var mk = new BMap.Marker( latLng
                , {icon: mk_icon
                    , offset: new BMap.Size(0, -1*(65 * size + 1)/2)
                    , title: P3TXT.amp + ": " + amp.toFixed(2) + " " + P3TXT.sigma + ": " + sigma.toFixed(1)
                    , enableClicking: true
                });
            mk.setZIndex(10);
            map.addOverlay(mk);
            return mk;
            break;
    }

    // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null); 
    // map.entities.push(mk);
    // return mk;
}

function newWindMarker(map, latLng, radius, dir, dirSdev, amp, sigma) {
    var wr, wedge, sz;
    wedge = makeWindWedge(radius,dir,2*dirSdev);
    switch(CNSNT.provider) {
        case "google":
            wr = new google.maps.Marker({position: latLng
                , icon: new google.maps.MarkerImage(wedge.url,null,null,newPoint(wedge.radius,wedge.radius))
                ,zIndex:0
            });
            wr.setMap(map);
            return wr;
            break;

        case "baidu":
            var mk_icon = new BMap.Icon(wedge.url, new BMap.Size(2*wedge.radius, 2*wedge.radius));
            var mk = new BMap.Marker( latLng
                , {icon: mk_icon
                , title: P3TXT.amp + ": " + amp.toFixed(2) + " " + P3TXT.sigma + ": " + sigma.toFixed(1)
                });
            mk.setZIndex(0);
            map.addOverlay(mk);
            return mk;
            break;
    }

}

function newAnalysisMarker(map, latLng, delta, uncertainty, disposition) {
    var amarker, mk, mk_text, mk_icon, txtpx;

    mk_text = delta.toFixed(1) + " +/- " + uncertainty.toFixed(1);
    txtpx = mk_text.length * 7.6; // This is just an average that seems to works with bold 14px sans-serif

    var fillColor = "#FF8080";
    var txtColor = "black";
    var strokeColor = "black";

    switch(disposition) {
        case 1.0:
            fillColor = "#9C9C9C";
            break;

        case 2.0:
        case 3.0:
        case 4.0:
            fillColor = "red";
            txtColor = "white";
            strokeColor = "black";
            break;
    }

    amarker = makeAnalysisMarker(txtpx, fillColor, strokeColor, mk_text,"bold 14px sans-serif",
				 txtColor);

    switch(CNSNT.provider) {
        case "google":
            mk = new google.maps.Marker({position: latLng
                , icon: new google.maps.MarkerImage(amarker.url,null,null,newPoint(amarker.width/2,(amarker.height/2)-10))
                ,zIndex:11
            });
            mk.setMap(map);

            return mk;
            break;

        case "baidu":
            mk_icon = new BMap.Icon(amarker.url, new BMap.Size(amarker.width, amarker.height));
            mk = new BMap.Marker( latLng
                , {icon: mk_icon
                   , offset: new BMap.Size(0, 0)
                   , title: mk_text
                   , enableClicking: true
                });
            mk.setZIndex(11);
            map.addOverlay(mk);
            return mk;
            break;
    }
    // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null);
    // map.entities.push(mk);
    // return mk;
}

function newNoteMarker(map, latLng, text, cat) {
    var mk, pathTxt, mkrUrlFrag, mkrClr, mkrBbl, mkrOrigin, mkrAnchor;
    pathTxt = (text.length <= 20) ? text : text.substring(0, 20) + " ...";
    if (cat === "peak") {
        mkrClr = CNSNT.peak_bbl_clr;
        mkrBbl = CNSNT.peak_bbl_tail;
        mkrOrigin = CNSNT.peak_bbl_origin;
        mkrAnchor = CNSNT.peak_bbl_anchor;
    } else {
        if (cat === "analysis") {
            mkrClr = CNSNT.analysis_bbl_clr;
            mkrBbl = CNSNT.analysis_bbl_tail;
            mkrOrigin = CNSNT.analysis_bbl_origin;
            mkrAnchor = CNSNT.analysis_bbl_anchor;
        } else {
            mkrClr = CNSNT.path_bbl_clr;
            mkrBbl = CNSNT.path_bbl_tail;
            mkrOrigin = CNSNT.path_bbl_origin;
            mkrAnchor = CNSNT.path_bbl_anchor;
        }
    }
    switch(CNSNT.provider) {
        case "google":
            mkrUrlFrag = "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=" + mkrBbl + pathTxt + mkrClr;
            mk = new google.maps.Marker({position: latLng,
                    icon: new google.maps.MarkerImage(
                        mkrUrlFrag,
                        null,
                        mkrOrigin,
                        mkrAnchor
                    )}
            );
            mk.setMap(map);
            return mk;
            break;

        case "baidu":
            break;
    }
    // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null);
    // map.entities.push(mk);
    // return mk;
}

function updateNoteMarkerText(map, mkr, text, cat) {
    var pathTxt, mkrUrlFrag, mkrClr, mkrBbl, mkrOrigin, mkrAnchor, micon;
    pathTxt = (text.length <= 20) ? text : text.substring(0, 20) + " ...";
    if (cat === "peak") {
        mkrClr = CNSNT.peak_bbl_clr;
        mkrBbl = CNSNT.peak_bbl_tail;
        mkrOrigin = CNSNT.peak_bbl_origin;
        mkrAnchor = CNSNT.peak_bbl_anchor;
    } else {
        if (cat === "analysis") {
            mkrClr = CNSNT.analysis_bbl_clr;
            mkrBbl = CNSNT.analysis_bbl_tail;
            mkrOrigin = CNSNT.analysis_bbl_origin;
            mkrAnchor = CNSNT.analysis_bbl_anchor;
        } else {
            mkrClr = CNSNT.path_bbl_clr;
            mkrBbl = CNSNT.path_bbl_tail;
            mkrOrigin = CNSNT.path_bbl_origin;
            mkrAnchor = CNSNT.path_bbl_anchor;
        }
    }
    switch(CNSNT.provider) {
        case "google":
            mkrUrlFrag = "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=" + mkrBbl + pathTxt + mkrClr;
            micon = new google.maps.MarkerImage(
                mkrUrlFrag,
                null,
                mkrOrigin,
                mkrAnchor
            );
            mkr.setIcon(micon);
            break;

        case "baidu":
            break;
    }
}

function newDomEventListener(lobj, levent, lfn) {
    var lstnr;
    switch(CNSNT.provider) {
        case "google":
            lstnr = new google.maps.event.addDomListener(lobj, levent, lfn);
            return lstnr;
            break;

        case "baidu":
            return null;
            break;
    }
}

function newEventListener(lobj, levent, lfn) {
    var lstnr;
    switch(CNSNT.provider) {
        case "google":
            lstnr = new google.maps.event.addListener(lobj, levent, lfn);
            return lstnr;
            break;

        case "baidu":
            lobj.addEventListener(levent, lfn);
            return null;
            break;
    }
}

function removeMarkerFromMap(mkr, map) {
    switch(CNSNT.provider) {
        case "google":
            mkr.setMap(null);
            break;

        case "baidu":
            map.removeOverlay(mkr);
            break;
    }
}

function removeListener(handle) {
    switch(CNSNT.provider) {
        case "google":
            google.maps.event.removeListener(handle);
            break;

        case "baidu":
            break;
    }
}

function attachPlatListener(plat, plname) {
    var platClickListener;
    platClickListener = newEventListener(plat, 'click', function() {
        modalPanePlatControls(plname);
    });
    PLATOBJS[plname].listener = platClickListener;
}

function attachGoListener(plat, plname) {
    var goClickListener;
    goClickListener = newEventListener(plat, 'click', function() {
        modalPanePlatControls(plname);
    });
    PLATOBJS[plname].go_listener = goClickListener;
}

function removeGoListener(plobj) {
    switch(CNSNT.provider) {
        case "google":
            google.maps.event.removeListener(plobj.go_listener);
            break;

        case "baidu":
            break;
    }
    plobj.go_listener = null;
}

function getLatFromLoc(loc) {
    switch(CNSNT.provider) {
        case "google":
            return loc.lat();
            break;

        case "baidu":
            return loc.lat;
            break;
    }
}

function getLngFromLoc(loc) {
    switch(CNSNT.provider) {
        case "google":
            return loc.lng();
            break;

        case "baidu":
            return loc.lng;
            break;
    }
}

function getPathStrokeColor(path) {
    switch(CNSNT.provider) {
        case "google":
            return path.strokeColor;
            break;

        case "baidu":
            return path.getStrokeColor();
            break;
    }
}


function getPathLength(path) {
    switch(CNSNT.provider) {
        case "google":
            return path.getPath().getLength();
            break;

        case "baidu":
            return path.getPath().length;
            break;
    }
}

function getLastPathPoint(path) {
    switch(CNSNT.provider) {
        case "google":
            var pathLen = path.getPath().getLength();
            if (pathLen > 0) {
                return path.getPath().getAt(pathLen - 1);
            } else {
                return 0;
            }
            break;

        case "baidu":
            var pathLen = CSTATE.cpoints.length;
            if (pathLen > 0) {
                return CSTATE.cpoints[pathLen - 1];
            } else {
                return 0;
            }
            break;
    }
}

// ALL Map API interactions go above HERE!!

function clearPeakMarkerArray() {
    var i, ky;
    CSTATE.clearLeaks = true;
    CSTATE.peakNoteDict = {};
    for (i = 0; i < CSTATE.peakMarkers.length; i += 1) {

        removeMarkerFromMap(CSTATE.peakMarkers[i], CSTATE.map);
    }
    for (ky in CSTATE.peakBblListener) {
        removeListener(CSTATE.peakBblListener[ky]);
    }
    CSTATE.peakMarkers = [];
    CSTATE.peakBblListener = {};
    CSTATE.peakLine = 1;
}

function clearAnalysisMarkerArray() {
    var i, ky;
    CSTATE.clearAnalyses = true;
    CSTATE.analysisNoteDict = {};
    for (i = 0; i < CSTATE.analysisMarkers.length; i += 1) {
        removeMarkerFromMap(CSTATE.analysisMarkers[i], CSTATE.map);
    }
    for (ky in CSTATE.analysisBblListener) {
        removeListener(CSTATE.analysisBblListener[ky]);
    }
    CSTATE.analysisMarkers = [];
    CSTATE.analysisBblListener = {};
    CSTATE.analysisLine = 1;
}

function clearSwathPolys() {
    var i;
    CSTATE.clearSwath = true;
    for (i = 0; i < CSTATE.swathPolys.length; i += 1) {
        removeMarkerFromMap(CSTATE.swathPolys[i], CSTATE.map);
    }
    CSTATE.swathPolys = [];
    //CSTATE.swathPathShowArray = [];
    CSTATE.lastMeasPathLoc = null;
    CSTATE.lastMeasPathDeltaLat = null;
    CSTATE.lastMeasPathDeltaLon = null;
    CSTATE.swathLine = 1;
    
    CSTATE.fov_lrt_parms_hash = null; // makeFov Stat Doc
    CSTATE.fov_lrt_start_ts = null; // makeFov Stat Doc
    CSTATE.fov_status = null; // makeFov Stat Doc
    CSTATE.fov_lrtrow = 0; // last lrtRow for the FOV
    
    CSTATE.swathUpdatePeriod = CNSNT.swathUpdatePeriod   
}

function clearWindMarkerArray() {
    var i;
    CSTATE.clearWind = true;
    for (i = 0; i < CSTATE.windMarkers.length; i += 1) {
        removeMarkerFromMap(CSTATE.windMarkers[i], CSTATE.map);
    }
    CSTATE.windMarkers = [];
    CSTATE.peakLine = 1;
}

function clearDatNoteMarkers(emptyTheDict) {
    var ky;
    CSTATE.clearDatNote = true;
    for (ky in CSTATE.datNoteMarkers) {
        removeMarkerFromMap(CSTATE.datNoteMarkers[i], CSTATE.map);
    }
    for (ky in CSTATE.datNoteListener) {
        removeListener(CSTATE.datNoteListener[ky]);
    }
    CSTATE.datNoteMarkers = {};
    CSTATE.datNoteListener = {};
    CSTATE.nextDatEtm = 0.0;
    CSTATE.nextDatUtm = 0.0;
    if (emptyTheDict) {
        CSTATE.datNoteDict = {};
        CSTATE.pathGeoObjs = [];
    }
}

function clearAnalysisNoteMarkers() {
    var ky;
    CSTATE.clearAnalysisNote = true;
    for (ky in CSTATE.analysisNoteMarkers) {
        removeMarkerFromMap(CSTATE.analysisNoteMarkers[i], CSTATE.map);
    }
    for (ky in CSTATE.analysisNoteListener) {
        removeListener(CSTATE.analysisNoteListener[ky]);
    }
    CSTATE.analysisNoteMarkers = {};
    CSTATE.analysisNoteListener = {};
    CSTATE.nextAnalysisEtm = 0.0;
    CSTATE.nextAnalysisUtm = 0.0;
}

function clearPeakNoteMarkers() {
    var ky;
    CSTATE.clearPeakNote = true;
    for (ky in CSTATE.peakNoteMarkers) {
        removeMarkerFromMap(CSTATE.peakNoteMarkers[i], CSTATE.map);
    }
    for (ky in CSTATE.peakNoteListener) {
        removeListener(CSTATE.peakNoteListener[ky]);
    }
    CSTATE.peakNoteMarkers = {};
    CSTATE.peakNoteListener = {};
    CSTATE.nextPeakEtm = 0.0;
    CSTATE.nextPeakUtm = 0.0;
}

function clearMapListener() {
    for (var ky in CSTATE.mapListener) {
        removeListener(CSTATE.mapListener[ky]);
    }
    CSTATE.mapListener = {};
}

function clearPathListener() {
    for (var ky in CSTATE.pathListener) {
        removeListener(CSTATE.pathListener[ky]);
    }
    CSTATE.pathListener = {};
}

function showSwath() {
    var i;
    for (i=0;i<CSTATE.swathPolys.length;i++) CSTATE.swathPolys[i].setVisible(true);
}

function hideSwath() {
    var i;
    for (i=0;i<CSTATE.swathPolys.length;i++) CSTATE.swathPolys[i].setVisible(false);
}

function single_quote(txt) {
    return "'" + txt + "'";
}

function double_quote(txt) {
    return '"' + txt + '"';
}

function resetLeakPosition() {
    clearPeakMarkerArray();
    clearAnalysisMarkerArray();
    clearWindMarkerArray();
    clearSwathPolys();
}

function timeStringFromEtm(etm) {
    var gmtoffset_mil, etm_mil, tmil, tdate, tstring;
    etm_mil = (etm * 1000);
    tdate = new Date(etm_mil);
    //tstring = tdate.toLocaleDateString() + " " + tdate.toLocaleTimeString();
    tstring = tdate.toString().substring(0,24);
    return tstring;
}

function MapControl(controlDiv, map) {
    var controlUI, controlText;

    // Set CSS styles for the DIV containing the control
    // Setting padding to 5 px will offset the control
    // from the edge of the map.
    controlDiv.style.padding = '5px';

    // Set CSS for the control border.
    controlUI = document.createElement('DIV');
    controlUI.style.backgroundColor = 'white';
    controlUI.style.borderStyle = 'solid';
    controlUI.style.borderWidth = '2px';
    controlUI.style.cursor = 'pointer';
    controlUI.style.textAlign = 'center';
    controlUI.title = P3TXT.click_show_cntls;
    controlDiv.appendChild(controlUI);

    // Set CSS for the control interior.
    controlText = document.createElement('DIV');
    controlText.style.fontFamily = 'Arial,sans-serif';
    controlText.style.fontSize = '12px';
    controlText.style.paddingLeft = '4px';
    controlText.style.paddingRight = '4px';
    controlText.innerHTML = P3TXT.map_controls  + "<br/>" + CSTATE.minAmp + "&nbsp; &nbsp;" + CSTATE.stabClass;
    controlUI.appendChild(controlText);

    newDomEventListener(controlUI, 'click', function () {
        modalPaneMapControls();
    });
    
    this.changeControlText = function(newText) {
        controlText.innerHTML = newText;
    };
}

function initialize_map() {
    var where, mapListener;
    if (!CNSNT.hasOwnProperty("provider")) {
        CNSNT.provider = "google";
    }
    if (!CNSNT.hasOwnProperty("provider_gpsconvert")) {
        CNSNT.provider_gpsconvert = false;
    }
    CSTATE.map = newMap(document.getElementById("map_canvas"));
    CNSNT.peak_bbl_anchor = newPoint(0, 42); //d_bubble_text_small is 42px high
    CNSNT.analysis_bbl_anchor = newPoint(0, 42); //d_bubble_text_small is 42px high
    CNSNT.path_bbl_anchor = newPoint(0, 0);

    CNSNT.peak_bbl_origin = newPoint(0, 0);
    CNSNT.analysis_bbl_origin = newPoint(0, 0);
    CNSNT.path_bbl_origin = newPoint(0, 0);

    clearMapListener();

    switch(CNSNT.provider) {
        case "google":
            CNSNT.mapControlDiv = document.createElement('DIV');
            CNSNT.mapControl = new MapControl(CNSNT.mapControlDiv, CSTATE.map);
            CNSNT.mapControlDiv.index = 1;

            CSTATE.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(CNSNT.mapControlDiv);

            mapListener = newEventListener(CSTATE.map, 'center_changed', function () {
                where = CSTATE.map.getCenter();
                preserveLastCenter(where);
            });
            CSTATE.mapListener[mapListener] = mapListener;

            mapListener = newEventListener(CSTATE.map, 'zoom_changed', function () {
                CSTATE.current_zoom = CSTATE.map.getZoom();
                setCookie(COOKIE_NAMES.zoom, CSTATE.current_zoom, CNSNT.cookie_duration);
                CSTATE.gglOptions["zoom"] = CSTATE.current_zoom;
            });
            CSTATE.mapListener[mapListener] = mapListener;

            mapListener = newEventListener(CSTATE.map, 'maptypeid_changed', function () {
                CSTATE.current_mapTypeId = CSTATE.map.getMapTypeId();
                setCookie(COOKIE_NAMES.mapTypeId, CSTATE.current_mapTypeId, CNSNT.cookie_duration);
            });
            CSTATE.mapListener[mapListener] = mapListener;

            newEventListener(CSTATE.map,"rightclick",function(event) {
                var lat = getLatFromLoc(event.latLng);
                var lng = getLngFromLoc(event.latLng);
                modalPaneCopyClipboard(lat.toFixed(5) + ', ' + lng.toFixed(5));
            });

            break;

        case "baidu":
            CSTATE.map.addControl(new BMap.MapTypeControl());
            CSTATE.map.addControl(new BMap.NavigationControl());
            CSTATE.map.addControl(new BMap.ScaleControl());
            CSTATE.map.setZoom(CSTATE.current_zoom);

// creating a div to hold the picarro map control element
            CNSNT.mapControlDiv = document.createElement('a');
            CNSNT.mapControlDiv.id = 'id_mapControlDiv';
            CNSNT.mapControl = new MapControl(CNSNT.mapControlDiv, CSTATE.map);
            CNSNT.mapControlDiv.index = 1;

            var kids = $("#top_right").find("#id_mapControlDiv");
            if (kids.length === 0) {
                $("#top_right").append(CNSNT.mapControlDiv);
            }
            CNSNT.mapControlDiv.onclick = function() {
                modalPaneMapControls();
            };

            //CSTATE.map.setMapType(baiduMapTypeFromName(CSTATE.current_mapTypeId));
            where = newLatLng(CSTATE.center_lat, CSTATE.center_lon);
            centerTheMap(where);

            mapListener = newEventListener(CSTATE.map, 'moveend', function () {
                //console.log("moveend");
                where = CSTATE.map.getCenter();
                preserveLastCenter(where);
            });
            CSTATE.mapListener[mapListener] = mapListener;

            mapListener = newEventListener(CSTATE.map, 'zoomend', function () {
                //console.log("zoomend");
                CSTATE.current_zoom = CSTATE.map.getZoom();
                setCookie(COOKIE_NAMES.zoom, CSTATE.current_zoom, CNSNT.cookie_duration);
            });
            CSTATE.mapListener[mapListener] = mapListener;

            mapListener = newEventListener(CSTATE.map, 'maptypechange', function () {
                //console.log("maptypechange");

                var typeName = CSTATE.map.getMapType().getName();
                if (CNSNT.baidu_name_maptype.hasOwnProperty(typeName)) {
                    CSTATE.current_mapTypeId = CNSNT.baidu_name_maptype[typeName];
                    setCookie(COOKIE_NAMES.mapTypeId, CSTATE.current_mapTypeId, CNSNT.cookie_duration);
                    //console.log('set maptype', CSTATE.current_mapTypeId);
                }
            });
            CSTATE.mapListener[mapListener] = mapListener;
            newEventListener(CSTATE.map,"rightclick",function(event) {
                console.log("point", event.point);
                var lat = getLatFromLoc(event.point);
                var lng = getLngFromLoc(event.point);
                modalPaneCopyClipboard(lat.toFixed(5) + ', ' + lng.toFixed(5));
            });

            break;
    }

    CSTATE.path = newPolyline(CSTATE.map, CNSNT.normal_path_color);
    clearPathListener();
    
    CSTATE.prevInferredStabClass = null;
    CSTATE.swathPolys = [];
    CSTATE.swathPathShowArray = [];
    CSTATE.lastMeasPathLoc = null;
    CSTATE.lastMeasPathDeltaLat = null;
    CSTATE.lastMeasPathDeltaLon = null;

    var pathListener = newEventListener(CSTATE.path, 'click', function (event) {
        var newhash, closepobjs, i, pobj;
        newhash = encodeGeoHash(getLatFromLoc(event.latLng)
            , getLngFromLoc(event.latLng));
        closepobjs = getNearest(newhash, 1);
        for (i = 0; i < closepobjs.length; i += 1) {
            pobj = closepobjs[i];
            break;
        }
        if (pobj) {
            if (CSTATE.datNoteDict[pobj.etm] === undefined) {
                CSTATE.datNoteDict[pobj.etm] = pobj;
            }
            notePane(pobj.etm, 'path');
        } else {
            alert("There was no path found under your click.");
        }
    });
    CSTATE.pathListener[pathListener] = pathListener;
    
    switch(CNSNT.provider) {
        case "google":
            if (CSTATE.marker) {
                CSTATE.marker.setMap(null);
            }
            break;
        case "baidu":
            break;
    }
    CSTATE.marker = newAnzLocationMarker(CSTATE.map);
    
    if (CSTATE.overlay) {
        showTifCb();
    }
    CSTATE.firstData = true; 
}

function preserveLastCenter(where) {
    var whlat = getLatFromLoc(where);
    var whlng = getLngFromLoc(where);
    CSTATE.center_lat = whlat;
    CSTATE.center_lon = whlng;
    setCookie(COOKIE_NAMES.center_latitude, CSTATE.center_lat, CNSNT.cookie_duration);
    setCookie(COOKIE_NAMES.center_longitude, CSTATE.center_lon, CNSNT.cookie_duration);
    $("#center_latitude").val(whlat);
    $("#center_longitude").val(whlng);
}

function resize_map() {
    var pge_wdth, hgth_top, lpge_wdth, new_width, new_height, new_top, cen;
    pge_wdth = $('#id_topbar').width() - ($('#id_sidebar').width() + 20);
    hgth_top = $('#id_topbar').height() + $('#id_feedback').height() + $('#id_content_title').height();


    if ($('#id_sidebar')) {
        lpge_wdth = $('#id_sidebar').width();
    } else {
        lpge_wdth = 0;
    }
    new_width = pge_wdth - CNSNT.hmargin;
    new_height = winH - hgth_top - CNSNT.hmargin - 40;
    new_top = hgth_top + CNSNT.vmargin;

    $("#id_modal_span").css('position', 'absolute');
    $("#id_modal_span").css('top', hgth_top);

    var placeholder_wdth = document.getElementById("placeholder").clientWidth;
    var concData_wdth = document.getElementById("concData").clientWidth;
    var placeConc = placeholder_wdth + concData_wdth + 5;
    
    var idwdth = document.getElementById("id_feedback").clientWidth;
    var idhgth = document.getElementById("concData").clientHeight;
    //alert("id_feedback height: " + idhgth + "  width: " + idwdth);
    
    if (placeConc > idwdth) {
        new_top = new_top + idhgth;
        new_height = new_height - idhgth;
        $("#id_modal_span").css('left', CNSNT.hmargin);
    } else {
        $("#id_modal_span").css('left', lpge_wdth + CNSNT.hmargin);
    }
    
    $("#id_side_modal_span").css('position', 'absolute');
    $("#id_side_modal_span").css('top', hgth_top);
    new_top = new_top + CNSNT.map_topbuffer;
    new_height = new_height - CNSNT.map_bottombuffer;
    $("#id_side_modal_span").css('left', CNSNT.hmargin);

    $('#map_canvas').css('position', 'absolute');
    $('#map_canvas').css('left', lpge_wdth + CNSNT.hmargin);
    $('#map_canvas').css('top', new_top);
    $('#map_canvas').css('height', new_height);
    $('#map_canvas').css('width', new_width);
    $('#id_feedback').css('width', new_width);

    if (CSTATE.map) {
        cen = CSTATE.map.getCenter();
        if (CNSNT.provider === 'google') {
            google.maps.event.trigger(CSTATE.map, 'resize');
        }
        centerTheMap(cen);
    }

    switch(CNSNT.provider) {
        case "google":
            break;

        case "baidu":
            positionMapControlDiv();
            break;
    }

    CSTATE.resize_map_inprocess = false;
}

function resize_page() {
    if (!CSTATE.resize_map_inprocess) {
        CSTATE.resize_map_inprocess = true;
        if (TIMER) {
            TIMER.resize = setTimeout(resize_map, 25);
        }
    }
}

function setModalChrome(hdr, msg, click) {
    var modalChrome = "";
    modalChrome = '<div class="modal" style="position: relative; top: auto; left: auto; margin: 0 auto; z-index: 1">';

    modalChrome += '<div class="modal-header">';
    modalChrome += hdr;
    modalChrome += '</div>';
    modalChrome += '<div class="modal-body">';
    modalChrome += msg;
    modalChrome += '</div>';
    modalChrome += '<div class="modal-footer">';
    modalChrome += click ? click: "";
    modalChrome += '</div>';
    
    
    modalChrome += '</div>';

    return modalChrome;
}

function modalPanePrimeControls() {
    var capOrCan, i, modalChrome, hdr, body, footer, c1array, c2array;

    c1array = [];
    c2array = [];
    
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    
    c1array.push(HBTN.restartBtn);
    c2array.push(HBTN.calibrateBtn);
    
    //c1array.push(HBTN.completeSurveyBtn);
    //c2array.push('');
    
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.anz_cntls + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);


    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push(HBTN.shutdownBtn);
    c2array.push('');
    footer = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
    $("#id_restartBtn").focus();
}

function modalPaneExportControls() {
    var modalChrome, exportBtns, hdr, body, footer, c1array, c2array;

    c1array = [];
    c2array = [];
    
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    c1array.push(exportClassCntl('style="width: 100%;"'));
    c2array.push(HBTN.exptLogBtn);

    c1array.push('');
    if (CSTATE.peaksDownload === true) {
        c2array.push(HBTN.exptPeakBtn);
    } else {
        c2array.push(HBTN.exptPeakBtnDis);
    }

    c1array.push('');
    if (CSTATE.analysisDownload === true) {
        c2array.push(HBTN.exptAnalysisBtn);
    } else {
        c2array.push(HBTN.exptAnalysisBtnDis);
    }

    //c1array.push('');
    //c2array.push(HBTN.exptNoteBtn);
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.download_files + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
    $("#id_restartBtn").focus();
}

function modalPaneCopyClipboard(string) {
    var modalChrome, hdr, body, footer, c1array, c2array;
    var textinput;
    
    textinput = '<div><input type="text" id="id_copystr" style="width:90%; height:25px; font-size:20px; text-align:center;" value="' + string + '"/></div>';

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    c1array.push(textinput);
    c2array.push(HBTN.copyClipboardOkBtn);
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    hdr = '<h3>' + P3TXT.copyClipboard + '</h3>';

    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
    $("#id_copystr").select();
    $("#id_copystr").focus();
}

function doExport(alog) {
    var ltype = "dat";
    if (alog.indexOf(".analysis") !== -1) {
        ltype = "analysis";
    } else {
        if (alog.indexOf(".peaks") !== -1) {
            ltype = "peaks";
        } else {
            if (alog.indexOf(".notes") !== -1) {
                ltype = "notes";
            }
        }
    }

    var restFn, params;
    
    switch(ltype) {
    case "notes":
        if (!CSTATE.hasOwnProperty("AnzLogNote")) {
            init_anzlognote_rest();
        }
        
        params = {"qry": "byEpoch"
                , "alog": alog
                , "logtype": ltype
                , "startEtm": 0
                , "rtnFmt": "file"
        };
        
        restFn = CSTATE.AnzLogNote;
        break;
        
    default:
        if (!CSTATE.hasOwnProperty("AnzLog")) {
            init_anzlog_rest();
        }
        
        params = {"qry": "byPos"
                , "alog": alog
                , "logtype": ltype
                , "startPos": 0
                , "limit": "all"
                , "rtnFmt": CSTATE.exportClass
        };
    
        restFn = CSTATE.AnzLog;
        break;
    }
    
    restFn.geturl({"qryobj": params, "existing_tkt": true}
        // error CB
        , function(err) {
            alert(err);
        }
        
        // successCB
        , function(rtn_code, rtnobj) {
            var expturl = rtnobj;
            
            switch(ltype) {
            case "dat":
                $('#id_exptLogBtn').html(P3TXT.download_concs);
                $('#id_exptLogBtn').redraw;
                break;
                
            case "peaks":
                $('#id_exptPeakBtn').html(P3TXT.download_peaks);
                $('#id_exptPeakBtn').redraw;
                break;
                
            case "analysis":
                $('#id_exptAnalysisBtn').html(P3TXT.download_analysis);
                $('#id_exptAnalysisBtn').redraw;
                break;
                
            case "notes":
                $('#id_exptNoteBtn').html(P3TXT.download_notes);
                $('#id_exptNoteBtn').redraw;
                break;
            }
            //alert("expturl at 1628:" + expturl);
            window.location = expturl;
    });
}

function exportLog() {
    var url = CNSNT.svcurl + '/sendLog?alog=' + CSTATE.alog;
    
    $('#id_exptLogBtn').html(P3TXT.working + "...");
    $('#id_exptLogBtn').redraw;
    
    doExport(CSTATE.alog);
}

function exportPeaks() {
    var apath, url;

    $('#id_exptPeakBtn').html(P3TXT.working + "...");
    $('#id_exptPeakBtn').redraw;
    
    apath = CSTATE.alog.replace(".dat", ".peaks");
    doExport(apath);
}

function exportAnalysis() {
    var apath, url;

    $('#id_exptAnalysisBtn').html(P3TXT.working + "...");
    $('#id_exptAnalysisBtn').redraw;
    
    apath = CSTATE.alog.replace(".dat", ".analysis");
    doExport(apath);
}

function exportNotes() {
    var apath, url;

    $('#id_exptNoteBtn').html(P3TXT.working + "...");
    $('#id_exptNoteBtn').redraw;
    
    apath = CSTATE.alog.replace(".dat", ".notes");
    doExport(apath);
}

function modalPaneSelectLog() {
    var options, i, len, row, selected, opendiv, closediv, btns, modalChangeMinAmp, hdr, body, footer, c1array, c2array;
    options = "";

    len = CNSNT.log_sel_opts.length;
    for (i = 0; i < len; i += 1) {
        row = CNSNT.log_sel_opts[i];
        selected = "";
        if (CSTATE.alog === row[0]) {
            selected = ' selected="selected" ';
        }
        options += '<option value="' + row[0] + '"' + selected + '>' + row[1] + '</option>';
    }

    c1array = [];
    c2array = [];
    
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    
    c1array.push('<select id="id_selectLog" class="large" style="width: 100%;">' + options + '</select>');
    c2array.push(HBTN.switchLogBtn);
    
    if (CSTATE.prime_available) {
        c1array.push("");
        c2array.push("");
        c1array.push('');
        c2array.push(HBTN.switchToPrimeBtn);
    }
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    
    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.select_log + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    footer = '';
    
    modalChangeMinAmp = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChangeMinAmp);
    $("#id_modal_span").css("z-index", 9999);
    $("#id_amplitude").focus();
}

function switchLog() {
    var newlog, newtitle, i, len, row, selected;

    newlog = $("#id_selectLog").val();
    newtitle = "";

    len = CNSNT.log_sel_opts.length;
    for (i = 0; i < len; i += 1) {
        row = CNSNT.log_sel_opts[i];
        selected = "";
        if (newlog === row[0]) {
            newtitle = row[1];
        }
    }

    if (newlog !== CSTATE.alog) {
        initialize_map();
        CSTATE.alog = newlog;
        CSTATE.alog_peaks = CSTATE.alog.replace(".dat", ".peaks");
        CSTATE.alog_analysis = CSTATE.alog.replace(".dat", ".analysis");
        CSTATE.startPos = null;
        resetLeakPosition();
        clearPeakNoteMarkers();
        clearAnalysisNoteMarkers();
        clearDatNoteMarkers(true);

        $("#id_selectLogBtn").html(newtitle);
        if (CNSNT.prime_view) {
            $("#concentrationSparkline").html("Loading..");
            $("#id_exportButton_span").html("");
            $("#id_selectAnalyzerBtn").css("display", "none");
            $("#id_selectAnalyzerBtn").css("visibility", "hidden");
        } else {
            $('#concentrationSparkline').html("");
            if (newtitle === "Live") {
                $("#id_exportButton_span").html("");
            } else {
                if (TEMPLATE_PARAMS.allow_download === true) {
                    $("#id_exportButton_span").html(LBTNS.downloadBtns + '<br/>');
                } else {
                    $("#id_exportButton_span").html("");
                }
            }
        }
    }
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);
}

function switchToPrime() {
    var baseurl, url;

    if (confirm(P3TXT.prime_conf_msg)) {
        baseurl = CNSNT.svcurl.replace("rest", "gduprime");
        url = baseurl + '/' + CNSNT.analyzer_name;
        window.location = url;
        restoreModChangeDiv();
    }
}

function dateFromLogName(LogName) {
    //AnzLogLogger.log("LogName: " + LogName)
    var tmp, yyyy, mm, dd, hh, mn, ss;
    tmp = LogName.split("-");
    yyyy = parseInt(tmp[1].substring(0,4),10);
    mm = parseInt(tmp[1].substring(4,6),10);
    dd = parseInt(tmp[1].substring(6,8),10);

    hh = parseInt(tmp[2].substring(0,2),10);
    mn = parseInt(tmp[2].substring(2,4),10);
    ss = parseInt(tmp[2].substring(4,6),10);

    return new Date(yyyy, mm - 1, dd, hh, mn, ss);
}

function anzFromLogname(logname) {
    var tmp = logname.split("-");
    var anz = tmp[0];
    var aymd = tmp[1];
    var ahms = tmp[2];

    var nameDte = dateFromLogName(logname);
    //logger.log("nameDte", nameDte);
    var etmname = (nameDte.getTime() / 1000);

    return {"anz": anz
        , "ymd": aymd
        , "hms": ahms
        , "etmname": etmname
        , "nameDte": nameDte
    };
}; //anzFromLogname


function getPrimeIp() {
    var anz;
    if (CSTATE.alog.indexOf("@@Live:") >= 0) {
        anz = CSTATE.alog.substring(7);
    } else {
        var name_obj = anzFromLogname(CSTATE.alog);
        anz = name_obj.anz;
    }

    if (!CSTATE.hasOwnProperty("AnzMeta")) {
        init_anzmeta_rest();
    }
    CSTATE.AnzMeta.resource("/" + anz
        // error CB
        , function(err) {
            CSTATE.prime_available = false;
            TIMER.prime = setTimeout(getPrimeIp, 5000);
        }

        // successCB
        , function(rtn_code, rtnobj) {
            rt = rtnobj[0];
            if (rt.hasOwnProperty('PRIVATE_IP')) {
                CSTATE.callbacktest_url = 'http://' + rt["PRIVATE_IP"];
                testPrime();
            } else {
                CSTATE.prime_available = false;
                TIMER.prime = setTimeout(getPrimeIp, 10000);
            }
        });
};

function testPrime() {
    var params, url;

    if (CSTATE.prime_test_count >= 10) {
        TIMER.prime = null;
    } else {
        if (CNSNT.prime_view) {
            TIMER.prime = null;
        } else {
            params = {};
            url = CSTATE.callbacktest_url + '/rest/' + 'getDateTime';

            $.ajax({
                dataType: "jsonp",
                url: url,
                type: "get",
                timeout: CNSNT.callbacktest_timeout,
                success: function () {
                    CSTATE.prime_available = true;
                    TIMER.prime = null;
                },
                error: function () {
                    CSTATE.prime_available = false;
                    TIMER.prime = setTimeout(primeTimer, 10000);
                }
                });
        }
    }
}

function primeTimer() {
    testPrime();
    CSTATE.prime_test_count += 1;
}

function restoreModChangeDiv() {
    if (TIMER.progress !== null) {
        clearTimeout(TIMER.progress);
        TIMER.progress = null;
        CSTATE.end_warming_status = true;
    }
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);
}

function restoreModalDiv() {
    $("#id_modal").html("");
    CSTATE.net_abort_count = 0;
}

function changeMinAmpVal(reqbool) {
    CSTATE.ignoreTimer = true;
    if (reqbool) {
        changeMinAmp();
    }
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);
    CSTATE.ignoreTimer = false;
}

function changeStabClassVal(reqbool) {
    CSTATE.ignoreTimer = true;
    if (reqbool) {
        changeStabClass();
    }
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);
    CSTATE.ignoreTimer = false;
}

function copyCliboard() {
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);
}

function workingBtnPassThrough(btnBase) {
    $('#id_' + btnBase).html(P3TXT.working + "...");
    $('#id_' + btnBase).redraw;
    setTimeout(btnBase + '()', 2);
}

function showDnoteCb() {
    var btxt;

    if (CSTATE.showDnote === false) {
        CSTATE.showDnote = true;
    } else {
        CSTATE.showDnote = false;
        clearDatNoteMarkers(false);
    }
    setCookie(COOKIE_NAMES.dnote, (CSTATE.showDnote) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showDnote) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.dnote;
    $('#id_showDnoteCb').html(btxt);
}

function showPnoteCb() {
    var btxt;

    if (CSTATE.showPnote === false) {
        CSTATE.showPnote = true;
    } else {
        CSTATE.showPnote = false;
        clearPeakNoteMarkers();
    }
    setCookie(COOKIE_NAMES.pnote, (CSTATE.showPnote) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showPnote) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.pnote;
    $('#id_showPnoteCb').html(btxt);
}

function showAnoteCb() {
    var btxt;

    if (CSTATE.showAnote === false) {
        CSTATE.showAnote = true;
    } else {
        CSTATE.showAnote = false;
        clearAnalysisNoteMarkers();
    }
    setCookie(COOKIE_NAMES.anote, (CSTATE.showAnote) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showAnote) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.anote;
    $('#id_showAnoteCb').html(btxt);
}

function showPbubbleCb() {
    var btxt;

    if (CSTATE.showPbubble === false) {
        CSTATE.showPbubble = true;
    } else {
        CSTATE.showPbubble = false;
    }
    clearPeakMarkerArray();
    clearWindMarkerArray();
    setCookie(COOKIE_NAMES.pbubble, (CSTATE.showPbubble) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showPbubble) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.pbubble;
    $('#id_showPbubbleCb').html(btxt);
}

function showPlatCb() {
    var btxt, showPlatCntl;
    if (!CSTATE.showPlatOutlines) {
        CSTATE.showPlatOutlines = true;
        show_plat_outlines();
    } else {
        CSTATE.showPlatOutlines = false;
        hide_plat_outlines();
    }
    setCookie(COOKIE_NAMES.platOutlines, (CSTATE.showPlatOutlines) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showPlatOutlines) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.plat_outline;
    $('#id_showPlatCb').html(btxt);
}

function showAbubbleCb() {
    var btxt;

    if (CSTATE.showAbubble === false) {
        CSTATE.showAbubble = true;
    } else {
        CSTATE.showAbubble = false;
        clearAnalysisMarkerArray();
    }
    setCookie(COOKIE_NAMES.abubble, (CSTATE.showAbubble) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showAbubble) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.abubble;
    $('#id_showAbubbleCb').html(btxt);
}

function showWbubbleCb() {
    var btxt;

    if (CSTATE.showWbubble === false) {
        CSTATE.showWbubble = true;
    } else {
        CSTATE.showWbubble = false;
    }
    clearPeakMarkerArray();
    clearWindMarkerArray();
    setCookie(COOKIE_NAMES.wbubble, (CSTATE.showWbubble) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showWbubble) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.wbubble;
    $('#id_showWbubbleCb').html(btxt);
}

function showSwathCb() {
    var btxt;

    if (CSTATE.showSwath === false) {
        CSTATE.showSwath = true;
        showSwath();
    } else {
        CSTATE.showSwath = false;
        hideSwath();
    }
    setCookie(COOKIE_NAMES.swath, (CSTATE.showSwath) ? "1" : "0", CNSNT.cookie_duration);

    btxt = P3TXT.show_txt;
    if (CSTATE.showSwath) {
        btxt = P3TXT.hide_txt;
    }
    btxt += " " + P3TXT.swath;
    $('#id_showSwathCb').html(btxt);
}

function requestMinAmpChange() {
    var modalChrome, hdr, body, footer, c1array, c2array;
    var textinput;
    
    textinput = '<div><input type="text" id="id_amplitude" style="width:90%; height:25px; font-size:20px; text-align:center;" value="' + CSTATE.minAmp + '"/></div>';

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    c1array.push(textinput);
    c2array.push(HBTN.changeMinAmpOkBtn);
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.change_min_amp + '</h3>');
    c2array.push(HBTN.changeMinAmpCancelBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
    $("#id_amplitude").focus();
}

function requestStabClassChange() {
    var modalChrome, hdr, body, footer, c1array, c2array;

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    c1array.push(stabClassCntl('style="width: 100%;"'));
    c2array.push(HBTN.changeStabClassOkBtn);
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.change_stab_class + '</h3>');
    c2array.push(HBTN.changeStabClassCancelBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
    $("#id_amplitude").focus();
}

function updateNote(cat, logname, etm, note, type) {
    var datadict, method, docrow;
    
    var updateTheDict = function(cat) {
        if (cat === 'peak') {
            datadict = CSTATE.peakNoteDict[etm];
        } else {
            if (cat === 'analysis') {
                datadict = CSTATE.analysisNoteDict[etm];
            } else {
                datadict = CSTATE.datNoteDict[etm];
            }
        }
        if (datadict) {
            datadict.lock = false;
        } else {
            datadict = {lock: false};
        }
        if (cat === 'peak') {
            CSTATE.peakNoteDict[etm] = datadict;
        } else {
            if (cat === 'analysis') {
                CSTATE.analysisNoteDict[etm] = datadict;
            } else {
                CSTATE.datNoteDict[etm] = datadict;
            }
        }
    }; //updateTheDict
    
    var successInsNote = function (data, cat) {
        if (data) {
            if (data.indexOf("ERROR: invalid ticket") !== -1) {
                TIMER.getAnalyzerList = setTimeout(getAnalyzerListTimer, CNSNT.fast_timer);
                return;
            } else {
                updateTheDict(cat);
            }
        }
    }; // successInsNote

    var errorInsNote = function (cat) {
        updateTheDict(cat);
    }; // errorInsNote
    

    //alert("updateNote: " + logname + "\n" + etm + "\n" + note + "\n" + type);
    if (cat === 'peak') {
        datadict = CSTATE.peakNoteDict[etm];
    } else {
        if (cat === 'analysis') {
            datadict = CSTATE.analysisNoteDict[etm];
        } else {
            datadict = CSTATE.datNoteDict[etm];
        }
    }
    if (datadict) {
        datadict.note = note;
        datadict.db = true;
        datadict.lock = true;
    } else {
        datadict = {"note": note, "db": true, "lock": true};
    }
    var ltype = 'dat';
    if (cat === 'peak') {
        CSTATE.peakNoteDict[etm] = datadict;
        ltype = 'peaks';
    } else {
        if (cat === 'analysis') {
            CSTATE.analysisNoteDict[etm] = datadict;
            ltype = 'analysis';
        } else {
            CSTATE.datNoteDict[etm] = datadict;
            ltype = 'dat';
        }
    }
    docrow = {"LOGNAME": logname
            , "EPOCH_TIME": etm
            , "LOGTYPE": ltype
            , "NOTE_TXT": note};

    if (type === 'add') {
        docrow.INSERT_USER = CNSNT.user_id;
    } else {
        docrow.UPDATE_USER = CNSNT.user_id;
    }
    
    if (!CSTATE.hasOwnProperty("AnzLogNote")) {
        init_anzlognote_rest();
    }
    CSTATE.AnzLogNote.data(docrow
        // error CB
        , function(err) {
            errorInsNote("error getting peaks data");
        }
        
        // successCB
        , function(rtn_code, rtnobj) {
            successInsNote(rtnobj, cat);
    });
    
} //updateNote

function noteUpdate(reqbool, etm, cat) {
    var noteText, datadict, currnote, ntype, fname, pathCoords, pathMarker, mkr, mkrClr, mkrBbl, mkrOrigin, mkrAnchor;

    if (reqbool) {
        if (cat === 'peak') {
            datadict = CSTATE.peakNoteDict[etm];
            fname = CSTATE.lastPeakFilename;
        } else {
            if (cat === 'analysis') {
                datadict = CSTATE.analysisNoteDict[etm];
                fname = CSTATE.lastAnalysisFilename;
            } else {
                datadict = CSTATE.datNoteDict[etm];
                fname = CSTATE.lastDataFilename;
            }
        }
        noteText = $("#id_note").val();
        currnote = datadict.note;
        if (datadict.db === true) {
            ntype = "update";
        } else {
            ntype = "add";
        }

        if (noteText !== currnote) {
            if (cat === "peak") {
                mkrClr = CNSNT.peak_bbl_clr;
                mkrBbl = CNSNT.peak_bbl_tail;
                mkrOrigin = CNSNT.peak_bbl_origin;
                mkrAnchor = CNSNT.peak_bbl_anchor;
                mkr = CSTATE.peakNoteMarkers[etm];
            } else {
                if (cat === "analysis") {
                    mkrClr = CNSNT.analysis_bbl_clr;
                    mkrBbl = CNSNT.analysis_bbl_tail;
                    mkrOrigin = CNSNT.analysis_bbl_origin;
                    mkrAnchor = CNSNT.analysis_bbl_anchor;
                    mkr = CSTATE.analysisNoteMarkers[etm];
                } else {
                    mkrClr = CNSNT.path_bbl_clr;
                    mkrBbl = CNSNT.path_bbl_tail;
                    mkrOrigin = CNSNT.path_bbl_origin;
                    mkrAnchor = CNSNT.path_bbl_anchor;
                    mkr = CSTATE.datNoteMarkers[etm];
                }
            }
            if (ntype === "add") {
                pathCoords = newLatLng(datadict.lat, datadict.lon);
                pathMarker = newNoteMarker(CSTATE.map, pathCoords, noteText, cat);

                if (cat === 'peak') {
                    CSTATE.peakNoteMarkers[etm] = pathMarker;
                } else {
                    if (cat === 'analysis') {
                        CSTATE.analysisNoteMarkers[etm] = pathMarker;
                    } else {
                        CSTATE.datNoteMarkers[etm] = pathMarker;
                    }
                }
                attachMarkerListener(pathMarker, etm, cat);
            } else {
                updateNoteMarkerText(CSTATE.map, mkr, noteText, cat);
            }

            CSTATE.ignoreTimer = true;
            //alert("NEW\netm: " + etm + "\ntext: " + noteText);
            updateNote(cat, fname, etm, noteText, ntype);
            CSTATE.ignoreTimer = false;
        }
    }
    $("#id_smodal").html("");
}

function sortNoteList(a, b) {
    return a.etm - b.etm;
}

function notePaneSwitch(selobj) {
    var idx;
    idx = selobj.selectedIndex;
    notePane(CSTATE.noteSortSel[idx].etm, CSTATE.noteSortSel[idx].cat);
}

function notePane(etm, cat) {
    var k, kk, ko, options, lst, selected, dsp, noteSel, logseldiv, modalPinNote, hdr, body, buttons, proplist, vlu, datadict, currnote, catstr;

    noteSel = [];
    for (kk in CSTATE.peakNoteDict) {
        ko = {
            etm: kk,
            timeStrings: timeStringFromEtm(parseFloat(kk)),
            cat: "peak"
        };
        noteSel.push(ko);
    }
    for (kk in CSTATE.analysisNoteDict) {
        ko = {
            etm: kk,
            timeStrings: timeStringFromEtm(parseFloat(kk)),
            cat: "analysis"
        };
        noteSel.push(ko);
    }
    for (kk in CSTATE.datNoteDict) {
        ko = {
            etm: kk,
            timeStrings: timeStringFromEtm(parseFloat(kk)),
            cat: "path"
        };
        noteSel.push(ko);
    }
    options = "";
    CSTATE.noteSortSel = noteSel.sort(sortNoteList);
    for (var i = 0; i < CSTATE.noteSortSel.length; i += 1) {
        selected = "";
        if (CSTATE.noteSortSel[i].cat === cat && CSTATE.noteSortSel[i].etm === etm.toString()) {
            selected = ' selected="selected" ';
        }
        dsp = P3TXT[CSTATE.noteSortSel[i].cat] + ": " + CSTATE.noteSortSel[i].timeStrings;
        options += '<option value="' + CSTATE.noteSortSel[i].cat + ":" + CSTATE.noteSortSel[i].etm + '"' + selected + '>' + dsp + '</option>';
    }
    logseldiv = "";
    k = 'note_list';
    vlu = '<select onchange="notePaneSwitch(this)">';
    vlu += options;
    vlu += '</select>';
    logseldiv += '<div class="clearfix">';
    logseldiv += '<label for="id_' + k + '">' + P3TXT[k]  +  '</label>';
    logseldiv += '<div class="input">';
    logseldiv += '<span id="id_' + k + '" class="input large">' + vlu + '</span>';
    logseldiv += '</div>';
    logseldiv += '</div>';
    logseldiv += '<br/>';

    catstr = "'" + cat + "'";
    if (cat === 'peak') {
        datadict = CSTATE.peakNoteDict[etm];
        lst = CNSNT.peakNoteList;
    } else {
        if (cat === 'analysis') {
            datadict = CSTATE.analysisNoteDict[etm];
            lst = CNSNT.analysisNoteList;
        } else {
            datadict = CSTATE.datNoteDict[etm];
            lst = CNSNT.datNoteList;
        }
    }

    hdr = '<h3>' + P3TXT[cat]  +  ':&nbsp;' + timeStringFromEtm(etm) + '</h3>';
    proplist = '';

    $.each(lst, function (ky) {
        k = lst[ky];
        if (datadict[k]) {
            if (k === 'amp') {
                vlu = datadict[k].toFixed(2);
            } else {
                if (k === 'sigma') {
                    vlu = datadict[k].toFixed(1);
                } else {
                    vlu = datadict[k].toFixed(3);
                }
            }
            proplist += '<div class="clearfix">';
            proplist += '<label for="id_' + k + '">' + P3TXT[k]  +  '</label>';
            proplist += '<div class="input">';
            proplist += '<span id="id_' + k + '" class="uneditable-input">' + vlu + '</span>';
            proplist += '</div>';
            proplist += '</div>';
        }
    });
    if (datadict.note) {
        currnote = datadict.note;
    } else {
        currnote = '';
    }

    if (CNSNT.annotation_url) {
        proplist += '<div class="clearfix">';
        proplist += '<label for="id_note">' + P3TXT.note + '</label>';
        proplist += '<div class="input">';

        if (datadict.lock === true) {
            proplist += '<span class="large uneditable-input" id="id_note" name="textarea">';
            proplist += currnote;
            proplist += '</span>';
        } else {
            proplist += '<textarea class="large" id="id_note" name="textarea">';
            proplist += currnote;
            proplist += '</textarea>';
        }

        proplist += '</div>';
        proplist += '</div>';
    }

    body = '';
    body += logseldiv;
    body += '<div class="row">';
    body += '<div class="span2 columns">';
    body += '<fieldset>';
    body += proplist;
    body += '</fieldset>';
    body += '</div>';
    body += '</div>';


    buttons = '';
    if (CNSNT.annotation_url) {
        buttons += '<div style="display: hidden;"><button onclick="noteUpdate(true, ' + etm + ',' + catstr + ');"/></div>';
    }
    buttons += '<div><button onclick="noteUpdate(false, ' + etm + ',' + catstr + ');" class="btn large">' + P3TXT.close + '</button></div>';

    if (CNSNT.annotation_url) {
        buttons += '<div><button onclick="noteUpdate(true, ' + etm + ', ' + catstr + ');" class="btn large">' + P3TXT.save_note + '</button></div>';
    }

    modalPinNote = setModalChrome(hdr, body, buttons);

    $("#id_smodal").html(modalPinNote);
    $("#id_smodal").css("z-index", 9999);
    $("#id_side_modal_span").css("z-index", 9999);
    $("#id_note").focus();

}

function modalPaneMapControls() {
    var modalPane, showDnoteCntl, showPlatCntl, showPnoteCntl
        , showAbubbleCntl, showPbubbleCntl, showAnoteCntl
        , showWbubbleCntl, showSwathCntl, changeMinAmpCntl
        , changeStabClassCntl;
    var dchkd, pchkd, achkd, pbchkd, abchkd, wbchkd, platchkd, swchkd, hdr, body, footer, c1array, c2array;

    dchkd = P3TXT.show_txt;
    if (CSTATE.showDnote) {
        dchkd = P3TXT.hide_txt;
    }
    dchkd += " " + P3TXT.dnote;
    
    pchkd = P3TXT.show_txt;
    if (CSTATE.showPnote) {
        pchkd = P3TXT.hide_txt;
    }
    pchkd += " " + P3TXT.pnote;
    
    achkd = P3TXT.show_txt;
    if (CSTATE.showAnote) {
        achkd = P3TXT.hide_txt;
    }
    achkd += " " + P3TXT.anote;
    
    pbchkd = P3TXT.show_txt;
    if (CSTATE.showPbubble) {
        pbchkd = P3TXT.hide_txt;
    }
    pbchkd += " " + P3TXT.pbubble;
    
    abchkd = P3TXT.show_txt;
    if (CSTATE.showAbubble) {
        abchkd = P3TXT.hide_txt;
    }
    abchkd += " " + P3TXT.abubble;

    platchkd = P3TXT.show_txt;
    if (CSTATE.showPlatOutlines) {
        platchkd = P3TXT.hide_txt;
    }
    platchkd += " " + P3TXT.plat_outline;

    wbchkd = P3TXT.show_txt;
    if (CSTATE.showWbubble) {
        wbchkd = P3TXT.hide_txt;
    }
    wbchkd += " " + P3TXT.wbubble;

    swchkd = P3TXT.show_txt;
    if (CSTATE.showSwath) {
        swchkd = P3TXT.hide_txt;
    }
    swchkd += " " + P3TXT.swath;
    
    showDnoteCntl = '<div><button id="id_showDnoteCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showDnoteCb") + ');" class="btn btn-fullwidth">' + dchkd + '</button></div>';
    showPnoteCntl = '<div><button id="id_showPnoteCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showPnoteCb") + ');" class="btn btn-fullwidth">' + pchkd + '</button></div>';
    showAnoteCntl = '<div><button id="id_showAnoteCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showAnoteCb") + ');" class="btn btn-fullwidth">' + achkd + '</button></div>';

    showPbubbleCntl = '<div><button id="id_showPbubbleCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showPbubbleCb") + ');" class="btn btn-fullwidth">' + pbchkd + '</button></div>';
    showAbubbleCntl = '<div><button id="id_showAbubbleCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showAbubbleCb") + ');" class="btn btn-fullwidth">' + abchkd + '</button></div>';

    showPlatCntl = '<div><button id="id_showPlatCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showPlatCb") + ');" class="btn btn-fullwidth">' + platchkd + '</button></div>';
    showWbubbleCntl = '<div><button id="id_showWbubbleCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showWbubbleCb") + ');" class="btn btn-fullwidth">' + wbchkd + '</button></div>';
    showSwathCntl   = '<div><button id="id_showSwathCb"   type="button" onclick="workingBtnPassThrough(' + single_quote("showSwathCb") + ');"   class="btn btn-fullwidth">' + swchkd + '</button></div>';
    changeMinAmpCntl = '<div><button id="id_changeMinAmp"  type="button" onclick="workingBtnPassThrough(' + single_quote("requestMinAmpChange") + ');"   class="btn btn-fullwidth">' + P3TXT.change_min_amp + ': ' + CSTATE.minAmp + '</button></div>';
    changeStabClassCntl = '<div><button id="id_changeStabClass"  type="button" onclick="workingBtnPassThrough(' + single_quote("requestStabClassChange") + ');"   class="btn btn-fullwidth">' + P3TXT.change_stab_class + ': ' + CSTATE.stabClass + '</button></div>';
    
    body = "";
    c1array = [];
    c2array = [];
    
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    
    c1array.push(changeMinAmpCntl);
    c2array.push(changeStabClassCntl);
    
    
    c1array.push(showPbubbleCntl);
    c2array.push(showAbubbleCntl);
    
    c1array.push(showWbubbleCntl);
    c2array.push(showSwathCntl);
    
    /* c1array.push(showPlatCntl);
    
    if (CNSNT.annotation_url) {
        c2array.push(showPnoteCntl);
        c1array.push(showAnoteCntl);
        
        c2array.push(showDnoteCntl);
    }
    else {
        c2array.push('');
    }
    */

    if (CNSNT.annotation_url) {
        c1array.push(showPnoteCntl);
        c2array.push(showAnoteCntl);
        
        c1array.push(showDnoteCntl);
        c2array.push('');
    }

    //body += '<div class="clearfix">';
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    //body += tbl;
    //body += '</div>';

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.map_controls + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    footer = '';

    modalPane = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalPane);
    $("#id_modal_span").css("z-index", 9999);
    $("#id_showDnoteCb").focus();
}

function modalPanePlatControls(plname) {
    var activeCntl, acntl, modalPane, plobj, hcntl, hliteCntl, showTifCntl, hdr, body, footer, c1array, c2array;
    plobj = PLATOBJS[plname];

    hcntl = P3TXT.hlite_plat;
    if (plobj.hlite === true) {
        hcntl = P3TXT.remove_plat_hlite;
    }
    hliteCntl = '<div><button id="id_hliteCntl" type="button" onclick="hlitePlat(' + single_quote(plname) + ');" class="btn btn-fullwidth">' + hcntl + '</button></div>';

    acntl = P3TXT.select_active_plat;
    if (plobj.active === true) {
        acntl = P3TXT.remove_active_plat;
    } 
    activeCntl = '<div><button id="id_activeCntl" type="button" onclick="setActivePlat(' + single_quote(plname) + ');" class="btn btn-fullwidth">' + acntl + '</button></div>';
    
    c1array = [];
    c2array = [];
    
    c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    c2array.push('style="border-style: none; width: 50%;"');
    
    c1array.push(hliteCntl);
    c2array.push(activeCntl);
    c1array.push('<span id="allHliteCntlSpan">' + HBTN.allHliteCntl + '</span>');
    c2array.push("");
    
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    
    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push("<h3>" + P3TXT.plat + " " + plname.replace('.tif', '') + "</h3>");
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    footer = "";

    modalPane = setModalChrome(
    hdr,
    body,
    footer
    );

    $("#id_mod_change").html(modalPane);
    $("#id_modal_span").css("z-index", 9999);
}

function removeAllHlites() {
    var plname, plobj, rect;
    $("#allHliteCntlSpan").html(CNSNT.loader_gif_img);
    if (PLATOBJS) {
        for (plname in PLATOBJS) {
            plobj = PLATOBJS[plname];
            if (plobj.hlite === true) {
                hlitePlat(plname);
            }
        }
    }
    $("#allHliteCntlSpan").html(HBTN.allHliteCntl);
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);

}

function hlitePlat(plname) {
    var plobj, hcntl;
    plobj = PLATOBJS[plname];

    if (plobj.hlite === true) {
        hcntl = P3TXT.hlite_plat;
        plobj.hlite = false;
        if (!plobj.active) {
            plobj.rect.setOptions({
                strokeColor: CNSNT.normal_plat_outline_color,
                strokeOpacity: CNSNT.normal_plat_outline_opacity,
                strokeWeight: CNSNT.normal_plat_outline_weight,
                visible: true
            });
        }
    } else {
        hcntl = P3TXT.remove_plat_hlite;
        plobj.hlite = true;
        if (!plobj.active) {
            plobj.rect.setOptions({
                strokeColor: CNSNT.hlite_plat_outline_color,
                strokeOpacity: CNSNT.hlite_plat_outline_opacity,
                strokeWeight: CNSNT.hlite_plat_outline_weight,
                visible: true
            });
        }
    }
    plobj.rect.setMap(null);
    plobj.rect.setMap(CSTATE.map);
    
    $("#id_hliteCntl").html(hcntl);
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);
}

function restoreHlitePlat(plobj) {
    if (plobj.hlite === true) {
        plobj.rect.setOptions({
            strokeColor: CNSNT.hlite_plat_outline_color,
            strokeOpacity: CNSNT.hlite_plat_outline_opacity,
            strokeWeight: CNSNT.hlite_plat_outline_weight,
            visible: true
        });
    } else {
        plobj.rect.setOptions({
            strokeColor: CNSNT.normal_plat_outline_color,
            strokeOpacity: CNSNT.normal_plat_outline_opacity,
            strokeWeight: CNSNT.normal_plat_outline_weight,
            visible: true
        });
    } 
}

function setActivePlat(plname) {
    var plobj, actPlObj, acntl;
    plobj = PLATOBJS[plname];

    // Remove the old active plat if it's different from the current selection (only one can be active)
    if ((CSTATE.activePlatName !== plname) && (CSTATE.activePlatName !== "")) {
        try {
            actPlObj = PLATOBJS[CSTATE.activePlatName];
            if (actPlObj.active === true) {
                actPlObj.active = false;
                restoreHlitePlat(actPlObj);
            }
            // Hide the overlay of old active plat
            if (CSTATE.overlay) {
                hideTifCb();
            }
        } catch(err) {
            actPlObj = null;
        }
    }
    
    if (plobj.active === true) {
        if (CSTATE.overlay) {
            hideTifCb();
        }
        CSTATE.activePlatName = "";
        acntl = P3TXT.select_active_plat;
        plobj.active = false;
        restoreHlitePlat(plobj);
    } else {
        CSTATE.activePlatName = plname;
        acntl = P3TXT.remove_active_plat;
        plobj.active = true;
        plobj.rect.setOptions({
            strokeColor: CNSNT.active_plat_outline_color,
            strokeOpacity: CNSNT.active_plat_outline_opacity,
            strokeWeight: CNSNT.active_plat_outline_weight,
            visible: true
        });
        if (CSTATE.overlay) {
            showTifCb();
        }
    }
    setCookie(COOKIE_NAMES.activePlatName, CSTATE.activePlatName, CNSNT.cookie_duration);
    plobj.rect.setMap(null);
    plobj.rect.setMap(CSTATE.map);
    $("#id_activeCntl").html(acntl);
    $("#id_mod_change").html("");
    $("#id_modal_span").css("z-index", 0);
}

function colorPathFromValveMask(value) {
    var value_float, value_int, clr, value_binstr, valve0_bit, valve4_bit;
    value_float = parseFloat(value);
    value_int = Math.round(value_float);
    clr = CSTATE.lastPathColor;
    if (Math.abs(value_float - value_int) <= 1e-4) {
        // Only change the path color when valve mask is an integer
        value_binstr = value_int.toString(2);
        valve0_bit = value_binstr.substring(value_binstr.length-1, value_binstr.length);
        valve4_bit = value_binstr.substring(value_binstr.length-5, value_binstr.length-4);
        if (valve0_bit === "1") {
            clr = CNSNT.analyze_path_color;
        } else if (valve4_bit === "1") {
            clr = CNSNT.inactive_path_color;
        } else {
            clr = CNSNT.normal_path_color;
        }
        CSTATE.lastPathColor = clr;
    }
    return clr;
}

function colorPathFromInstrumentStatus(clr, instStatus) {
    // Modify color to CNSNT.inactive_path_color if instrument status is not good
    var good = CNSNT.INSTMGR_STATUS_READY | CNSNT.INSTMGR_STATUS_MEAS_ACTIVE |
    CNSNT.INSTMGR_STATUS_GAS_FLOWING | CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED |
    CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED | CNSNT.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED;
    
    if ((instStatus & CNSNT.INSTMGR_STATUS_MASK) !== good) {
        clr = CNSNT.inactive_path_color;
        CSTATE.lastPathColor = clr;        
    }
    return clr;
}

function widthFunc(windspeed,windDirSdev) {
    var v0 = 5; // 5m/s gives maximum width
    var w0 = 100;   // Maximum width is 100m
    return w0*Math.exp(1.0)*(windspeed/v0)*Math.exp(-windspeed/v0);
}

function updatePath(pdata, clr, etm, setThePath_flag) {
    //alert("updatePath");
    var where, lastPoint, pathLen, npdata;
    lastPoint = null;
    where = newLatLng(pdata.lat, pdata.lon);
    
    if (clr === CNSNT.analyze_path_color) {
        $("#analysis").html("");
    }
    // when path color needs to change, we instatiate a new path
    // this is because strokeColor changes the entire Polyline, not just
    // new points
    var pscolor = getPathStrokeColor(CSTATE.path);
    if (CSTATE.startNewPath || clr !== pscolor) {
        pathLen = getPathLength(CSTATE.path);
        if (pathLen > 0) {
            lastPoint = getLastPathPoint(CSTATE.path);
        }
        CSTATE.path = newPolyline(CSTATE.map, clr);

        clearPathListener();
        CSTATE.cpoints = [];

        var pathListener = newEventListener(CSTATE.path, 'click', function (event) {
            var newhash, closepobjs, i, pobj;
            newhash = encodeGeoHash(getLatFromLoc(event.latLng)
                , getLngFromLoc(event.latLng));
            closepobjs = getNearest(newhash, 1);
            for (i = 0; i < closepobjs.length; i += 1) {
                pobj = closepobjs[i];
                break;
            }
            if (pobj) {
                if (CSTATE.datNoteDict[pobj.etm] === undefined) {
                    CSTATE.datNoteDict[pobj.etm] = pobj;
                }
                notePane(pobj.etm, 'path');
            } else {
                alert("There was no path found under your click.");
            }
        });
        CSTATE.pathListener[pathListener] = pathListener;

        if (lastPoint && !CSTATE.startNewPath) {
            pushToPath(CSTATE.path, lastPoint);
            if (setThePath_flag === true) {
                if (CNSNT.provider === 'baidu') {
                    CSTATE.path.setPath(CSTATE.cpoints)
                }

            }
        }
    }
    pushToPath(CSTATE.path, where);
    if (setThePath_flag === true) {
        if (CNSNT.provider === 'baidu') {
            CSTATE.path.setPath(CSTATE.cpoints)
        }

    }
    //console.log("updatePath where:", where);
    CSTATE.startNewPath = false;
    npdata = pdata;
    var whlat = getLatFromLoc(where);
    var whlng = getLngFromLoc(where);
    npdata.geohash = encodeGeoHash(whlat, whlng);
    CSTATE.pathGeoObjs.push(npdata);
}

/*
function makeWindRose(radius,meanBearing,shaftLength,halfWidth) {
    var wMin = meanBearing - halfWidth;
    var height = 2*radius;
    $("#windRose").sparkline([2*halfWidth,360-2*halfWidth],{"type":"pie","height":height+"px","offset":-90+wMin,"sliceColors":["#ffff00","#cccccc"]});
};
*/

function makeToken(size,fillColor,strokeColor) {
    var ctx = document.createElement("canvas").getContext("2d");
    var r = 2.0 * size;
    ctx.canvas.width = 2*r;
    ctx.canvas.height = 2*r;
    ctx.lineWidth = 1;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = fillColor;
    ctx.beginPath();
    ctx.arc(r, r, r, 0.0, 2*Math.PI, false);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    return {radius:r, url:ctx.canvas.toDataURL("image/png")};
}

function makeMarker(size,fillColor,strokeColor,msg,font,textColor) {
    var ctx = document.createElement("canvas").getContext("2d");
    var b = 1.25 * size;
    var t = 2.0 * size;
    var nx = 36 * size + 1;
    var ny = 65 * size + 1;
    var r = 0.5 * (nx - 1 - t);
    var h = ny - 1 - t;
    var phi = Math.PI * 45.0/180.0;
    var sinPhi = Math.sin(phi);
    var cosPhi = Math.cos(phi);
    var theta = 0.5 * Math.PI - phi;
    var xoff = r + 0.5 * t;
    var yoff = r + 0.5 * t;
    var knot = (r - b * sinPhi) / cosPhi;
    ctx.canvas.width = nx;
    ctx.canvas.height = ny;
    ctx.beginPath();
    ctx.lineWidth = t;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = fillColor;
    ctx.translate(xoff, yoff);
    ctx.moveTo(-b, (h - r));
    ctx.quadraticCurveTo(-b, knot, -r * sinPhi, r * cosPhi);
    ctx.arc(0, 0, r, Math.PI - theta, theta, false);
    ctx.quadraticCurveTo(b, knot, b, (h - r));
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = textColor;
    ctx.font = font;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(msg,0,1.5*size);
    return ctx.canvas.toDataURL("image/png");
}

function makeWindRose(canvasHeight,radius,meanBearing,halfWidth,shaftLength,arrowheadSide,arrowheadAngle) {
    var sph = Math.sin(0.5*arrowheadAngle*CNSNT.dtr), cph = Math.cos(0.5*arrowheadAngle*CNSNT.dtr);
    var centerX, centerY, context;
    var wMean = CNSNT.dtr*(meanBearing);
    var sth = Math.sin(wMean), cth = Math.cos(wMean);
    var wMin = CNSNT.dtr*(meanBearing - halfWidth);
    var wMax = CNSNT.dtr*(meanBearing + halfWidth);
    var canvas = document.getElementById("windCanvas");
    var centerX = canvasHeight/2, centerY = canvasHeight/2;
    var shaft = Math.min(shaftLength,radius);
    radius = Math.min(canvasHeight/2,radius);
    canvas.height = canvasHeight;
    canvas.width = canvasHeight;
    context = canvas.getContext("2d");
    context.beginPath();
    context.arc(centerX,centerY,radius,0,2*Math.PI,false);
    context.fillStyle = "#cccccc";
    context.fill();
    context.beginPath();
    context.moveTo(centerX,centerY);
    context.arc(centerX,centerY,radius,1.5*Math.PI+wMin,1.5*Math.PI+wMax,false);
    context.lineTo(centerX,centerY);
    context.fillStyle = "#ffff00";
    context.fill();
    context.beginPath();
    context.moveTo(centerX+shaft*sth,centerY-shaft*cth);
    context.lineTo(centerX,centerY);
    context.strokeStyle = "#000000";
    context.lineWidth = 3;
    context.stroke();
    context.beginPath();
    context.moveTo(centerX-arrowheadSide*cth*sph,centerY-arrowheadSide*sth*sph);
    context.lineTo(centerX-arrowheadSide*sth*cph,centerY+arrowheadSide*cth*cph);
    context.lineTo(centerX+arrowheadSide*cth*sph,centerY+arrowheadSide*sth*sph);
    context.closePath();
    context.fillStyle = "#000000";
    context.fill();
}

function makeWindWedge(radius,meanBearing,halfWidth) {
    var context;
    var wMin = CNSNT.dtr*(meanBearing - halfWidth);
    var wMax = CNSNT.dtr*(meanBearing + halfWidth);
    var height = 2*radius;
    var centerX = radius, centerY = radius;
    var canvas = document.createElement("canvas");
    canvas.height = height;
    canvas.width = height;
    context = canvas.getContext("2d");
    context.globalAlpha = 0.75;
    context.beginPath();
    context.moveTo(centerX,centerY);
    context.arc(centerX,centerY,radius,1.5*Math.PI+wMin,1.5*Math.PI+wMax,false);
    context.lineTo(centerX,centerY);
    context.fillStyle = "#ffff00";
    context.fill();
    context.lineWidth = 1;
    context.strokeStyle = "black";
    context.stroke();
    return {radius:radius,url:canvas.toDataURL("image/png")};
}

function makeAnalysisMarker(txtlenpx, fillColor, strokeColor, msg, font, textColor) {
    var canvas, ch, cw, cntrx, startx, stopx, ctx;
    canvas = document.createElement("canvas");

    ch = 2*(txtlenpx + 10);
    cw = ch;
    cntrx = ch/2;
    startx = cntrx+10;
    stopx = cntrx+txtlenpx-1;
    
// canvas is square, pointer is exact center of the square.
// this allows the image to be positioned directly on the map
// without an offset when map provider is baidu (baidu does strange things with offsets and zooming and gps conversion)
    canvas.height = ch;
    canvas.width = cw;
    ctx = canvas.getContext("2d");
    ctx.beginPath();
    ctx.strokeStyle=strokeColor;
    ctx.lineWidth="1";

    ctx.moveTo(startx, 110);
    ctx.lineTo(cntrx, 100);
    ctx.lineTo(startx+10, 110);
    ctx.lineTo(stopx, 110);
    ctx.quadraticCurveTo(stopx+10, 110, stopx+10, 120);
    ctx.lineTo(stopx+10, 125);
    ctx.quadraticCurveTo(stopx+10, 135, stopx, 135);
    ctx.lineTo(startx+10, 135);
    ctx.quadraticCurveTo(startx, 135, startx, 125);
    ctx.lineTo(startx, 110);
    ctx.fillStyle = fillColor;
    ctx.fill();

    ctx.stroke();

    ctx.fillStyle = textColor;
    ctx.font = font;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(msg,startx+50,125);

    return {url: canvas.toDataURL("image/png"), height: ch, width: cw};
}

function getNearest(currentHash, maxNeighbors) {
    var matching, accuracy, matchCount, i, tmp;
    matching = {};
    accuracy = 12;
    matchCount = 0;
    while (matchCount < maxNeighbors && accuracy > 0) {
        var cmpHash = currentHash.substring(0, accuracy);
        for (i = 0; i < CSTATE.pathGeoObjs.length; i += 1) {
            if (matching.hasOwnProperty(CSTATE.pathGeoObjs[i].geohash)) {
                continue;
            }
            if (CSTATE.pathGeoObjs[i].geohash.substring(0, accuracy) === cmpHash) {
                matching[CSTATE.pathGeoObjs[i].geohash] = CSTATE.pathGeoObjs[i];
                matchCount += 1;
                if (matchCount === maxNeighbors) {
                    break;
                }
            }
        }
        accuracy -= 1;
    }
    tmp = [];
    for (i in matching) {
        tmp.push(matching[i]);
    }
    return tmp;
}

function initialize_gdu(winH, winW) {
    var mapTypeCookie, current_zoom, followCookie, overlayCookie, minAmpCookie;
    var latCookie, lonCookie, dnoteCookie, pnoteCookie, anoteCookie;
    var latlng, new_height;
    var abubbleCookie, pbubbleCookie, wbubbleCookie, swathCookie, activePlatNameCookie;
    var platCookie, dspStabClassCookie, dspExportClassCookie;

    initialize_btns();
    resize_map();

    switch(CNSNT.provider) {
        case "google":
            if (CNSNT.prime_view) {
                CSTATE.current_mapTypeId = google.maps.MapTypeId.ROADMAP;
            } else {
                CSTATE.current_mapTypeId = google.maps.MapTypeId.ROADMAP;
                mapTypeCookie = getCookie(COOKIE_NAMES.mapTypeId);
                if (mapTypeCookie) {
                    if (mapTypeCookie in CNSNT.google_maptype_name) {
                        CSTATE.current_mapTypeId = mapTypeCookie;
                    }
                }
            }
            break;

        case "baidu":
            if (CNSNT.prime_view) {
                CSTATE.current_mapTypeId = "BMAP_NORMAL_MAP";
            } else {
                CSTATE.current_mapTypeId = "BMAP_NORMAL_MAP";
                mapTypeCookie = getCookie(COOKIE_NAMES.mapTypeId);
                if (mapTypeCookie) {
                    CSTATE.current_mapTypeId = mapTypeCookie;
                    //console.log('initial maptype', CSTATE.current_mapTypeId);
                }
            }
            break;
    }

    dnoteCookie = getCookie(COOKIE_NAMES.dnote);
    if (dnoteCookie) {
        CSTATE.showDnote = parseInt(dnoteCookie, 2);
    }

    pnoteCookie = getCookie(COOKIE_NAMES.pnote);
    if (pnoteCookie) {
        CSTATE.showPnote = parseInt(pnoteCookie, 2);
    }

    anoteCookie = getCookie(COOKIE_NAMES.anote);
    if (anoteCookie) {
        CSTATE.showAnote = parseInt(anoteCookie, 2);
    }

    pbubbleCookie = getCookie(COOKIE_NAMES.pbubble);
    if (pbubbleCookie) {
        CSTATE.showPbubble = parseInt(pbubbleCookie, 2);
    }
    //console.log("CSTATE.showPbubble: " + CSTATE.showPbubble);

    abubbleCookie = getCookie(COOKIE_NAMES.abubble);
    if (abubbleCookie) {
        CSTATE.showAbubble = parseInt(abubbleCookie, 2);
    }

    platCookie = getCookie(COOKIE_NAMES.platOutlines);
    if (platCookie) {
        CSTATE.showPlatOutlines = parseInt(platCookie, 2);
    }

    wbubbleCookie = getCookie(COOKIE_NAMES.wbubble);
    if (wbubbleCookie) {
        CSTATE.showWbubble = parseInt(wbubbleCookie, 2);
    }
    
    swathCookie = getCookie(COOKIE_NAMES.swath);
    if (swathCookie) {
        var value = parseInt(swathCookie, 2);
        CSTATE.showSwath = !(value === 0);
    }

    activePlatNameCookie = getCookie(COOKIE_NAMES.activePlatName);
    if (activePlatNameCookie) {
        setActivePlat(activePlatNameCookie);
    }

    dspStabClassCookie = getCookie(COOKIE_NAMES.dspStabClass);
    if (dspStabClassCookie) {
        CSTATE.stabClass = dspStabClassCookie;
    }

    dspExportClassCookie = getCookie(COOKIE_NAMES.dspExportClass);
    if (dspExportClassCookie) {
        CSTATE.exportClass = dspExportClassCookie;
    }
    
    followCookie = getCookie(COOKIE_NAMES.follow);
    if (followCookie) {
        CSTATE.follow = parseInt(followCookie, 2);
    }
    if (CSTATE.follow) {
        $("#id_follow").attr("class","follow-checked").attr("data-checked",'false');
    } else {
        $("#id_follow").attr("class","follow").attr("data-checked",'true');
    }

    overlayCookie = getCookie("pcubed_overlay");
    if (overlayCookie) {
        CSTATE.overlay = parseInt(overlayCookie, 2);
    }
    if (CSTATE.overlay) {
        $("#id_overlay").attr("class","overlay-checked").attr("data-checked",'false');
    } else {
        $("#id_overlay").attr("class","overlay").attr("data-checked",'true');
    }
    
    minAmpCookie = getCookie("pcubed_minAmp");
    if (minAmpCookie) {
        CSTATE.minAmp = parseFloat(minAmpCookie);
    }
    $("#id_amplitude_btn").html(CSTATE.minAmp);

    current_zoom = getCookie(COOKIE_NAMES.zoom);
    if (current_zoom) {
        CSTATE.current_zoom = parseInt(current_zoom, 10);
    } else {
        CSTATE.current_zoom = 14;
    }

    latCookie = getCookie(COOKIE_NAMES.center_latitude);
    if (latCookie) {
        CSTATE.center_lat = parseFloat(latCookie);
    }

    lonCookie = getCookie(COOKIE_NAMES.center_longitude);
    if (lonCookie) {
        CSTATE.center_lon = parseFloat(lonCookie);
    }

    latlng = newLatLng(CSTATE.center_lat, CSTATE.center_lon);
    switch(CNSNT.provider) {
        case "google":
            CSTATE.gglOptions = {
                zoom: CSTATE.current_zoom,
                center: latlng,
                mapTypeId: CSTATE.current_mapTypeId,
                rotateControl: false,
                scaleControl: true,
                zoomControl: true,
                zoomControlOptions: {style: google.maps.ZoomControlStyle.SMALL}
            };
            break;

        case "baidu":
            CSTATE.baiduOptions = {
                mapType: baiduMapTypeFromName(CSTATE.current_mapTypeId)
            }
            break;
    }

    if (!CNSNT.local_view) {
            //initialize rest API
            init_anzlrt_rest();
            init_anzlog_rest();
            init_anzlognote_rest();
    }
    
    initialize_map();
    TIMER.data = setTimeout(datTimer, 1000);
}

function init_anzlrt_rest() {
    // anzlrt_defn_obj
    var anzlrt_defn_obj = {};
    anzlrt_defn_obj.host = CNSNT.host;
    anzlrt_defn_obj.port = CNSNT.port;
    anzlrt_defn_obj.site = CNSNT.site;
    anzlrt_defn_obj.identity = CNSNT.identity;
    anzlrt_defn_obj.psys = CNSNT.sys;
    anzlrt_defn_obj.svc = CNSNT.svc;
    anzlrt_defn_obj.version = CNSNT.version;
    anzlrt_defn_obj.resource = "AnzLrt";
    anzlrt_defn_obj.rprocs = ["AnzLrt:getStatus", "AnzLrt:byRowFov"];
    anzlrt_defn_obj.jsonp = true;
    anzlrt_defn_obj.api_timeout = 60.0;

    anzlrt_defn_obj.debug = GDUDEBUG;
    
    CSTATE.AnzLrt = new p3RestApi(anzlrt_defn_obj);
}

function init_anzlog_rest() {
    // anzlog_defn_obj
    var anzlog_defn_obj = {};
    anzlog_defn_obj.host = CNSNT.host;
    anzlog_defn_obj.port = CNSNT.port;
    anzlog_defn_obj.site = CNSNT.site;
    anzlog_defn_obj.identity = CNSNT.identity;
    anzlog_defn_obj.psys = CNSNT.sys;
    anzlog_defn_obj.svc = CNSNT.svc;
    anzlog_defn_obj.version = CNSNT.version;
    anzlog_defn_obj.resource = "AnzLog";
    anzlog_defn_obj.rprocs = ["AnzLog:makeFov", "AnzLog:byPos", "AnzLog:byEpoch"];
    anzlog_defn_obj.jsonp = true;
    anzlog_defn_obj.api_timeout = 60.0;

    anzlog_defn_obj.debug = GDUDEBUG;
    
    CSTATE.AnzLog = new p3RestApi(anzlog_defn_obj);
}

function init_anzlognote_rest() {
    // anzlognote_defn_obj
    var anzlognote_defn_obj = {};
    anzlognote_defn_obj.host = CNSNT.host;
    anzlognote_defn_obj.port = CNSNT.port;
    anzlognote_defn_obj.site = CNSNT.site;
    anzlognote_defn_obj.identity = CNSNT.identity;
    anzlognote_defn_obj.psys = CNSNT.sys;
    anzlognote_defn_obj.svc = CNSNT.svc;
    anzlognote_defn_obj.version = CNSNT.version;
    anzlognote_defn_obj.resource = "AnzLogNote";
    anzlognote_defn_obj.rprocs = ["AnzLogNote:byEpoch", "AnzLogNote:data"];
    anzlognote_defn_obj.jsonp = true;
    anzlognote_defn_obj.api_timeout = 60.0;

    anzlognote_defn_obj.debug = GDUDEBUG;
    
    CSTATE.AnzLogNote = new p3RestApi(anzlognote_defn_obj);
}

function init_anzmeta_rest() {
    // anzmeta_defn_obj
    var anzmeta_defn_obj = {};
    anzmeta_defn_obj.host = CNSNT.host;
    anzmeta_defn_obj.port = CNSNT.port;
    anzmeta_defn_obj.site = CNSNT.site;
    anzmeta_defn_obj.identity = CNSNT.identity;
    anzmeta_defn_obj.psys = CNSNT.sys;
    anzmeta_defn_obj.svc = CNSNT.svc;
    anzmeta_defn_obj.version = CNSNT.version;
    anzmeta_defn_obj.resource = "AnzMeta";
    anzmeta_defn_obj.rprocs = ["AnzMeta:resource"];
    anzmeta_defn_obj.jsonp = true;
    anzmeta_defn_obj.api_timeout = 60.0;

    anzmeta_defn_obj.debug = GDUDEBUG;

    CSTATE.AnzMeta = new p3RestApi(anzmeta_defn_obj);
}

function initialize_btns() {
    var type;
    $('#cancel').hide();

    $('#id_statusPane').html(statusPane());
    $('#id_followPane').html(followPane());
    $('#id_modePane').html(modePane());
    
    if (CNSNT.prime_view) {
        $("#id_primeControlButton_span").html(LBTNS.analyzerCntlBtns);
    } else {
        getPrimeIp();
        //testPrime();
        $("#id_primeControlButton_span").html("");
        $("#id_exportButton_span").html("");
        type = $("#id_selectLogBtn").html();
        if (type === "Live") {
            $("#id_exportButton_span").html("");
        } else {
            if (TEMPLATE_PARAMS.allow_download === true) {
                $("#id_exportButton_span").html(LBTNS.downloadBtns + '<br/>');
            } else {
                $("#id_exportButton_span").html("");
            }
        }
    }
}

function weather_dialog() {
    CSTATE.showingWeatherDialog = true;
    var init = getCookie(COOKIE_NAMES.weather);
    try {
        init = JSON.parse(init);
        if (null === init) throw "null";
    }
    catch (e) {
        init = [0,0,0];
    }
    makeWeatherForm(function (result) {
        var code, dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        setCookie(COOKIE_NAMES.weather, JSON.stringify(result), CNSNT.cookie_duration);
        // Convert the reported weather into a code for inclusion in the auxiliary instrument status
        //  Note that 1 is added so that we can tell if there is no weather information in the file
        code = (8*result[2] + 2*result[1] + result[0]) + 1;
        CSTATE.inferredStabClass = CNSNT.classByWeather[code-1];
        // alert('Inferred stability class: ' + inferredStabClass);
        _changeStabClass(CSTATE.inferredStabClass);
        call_rest(CNSNT.svcurl, "restartDatalog", dtype, {weatherCode:code});
        restoreModChangeDiv();
        CSTATE.weatherMissingCountdown = CNSNT.weatherMissingDefer;
        CSTATE.showingWeatherDialog = false;
    },init);
}

function restart_datalog() {
    var init;
    if (confirm(P3TXT.restart_datalog_msg)) {
        weather_dialog(); 
    }
}

function shutdown_analyzer() {
    if (confirm(P3TXT.shutdown_anz_msg)) {
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "shutdownAnalyzer", dtype, {});
        restoreModChangeDiv();
    }
}

function get_time_zone_offset() {
    var current_date, gmt_offset;
    current_date = new Date();
    gmt_offset = current_date.getTimezoneOffset() / 60;
    $('#gmt_offset').val(gmt_offset);
    var rtn_offset = $('#gmt_offset').val();
    // alert(rtn_offset)
    return gmt_offset;
}

function call_rest(call_url, method, dtype, params, success_callback, error_callback) {
    var url;
    if (!params.hasOwnProperty("requestor_uid")) {
        if (CNSNT.user_id !== "") {
            params["requestor_uid"] = CNSNT.user_id;
        }
    }
    if (dtype === "jsonp") {
        url = call_url + '/' + method + "?callback=?";
        $.jsonp({
            data: $.param(params),
            url: url,
            type: "get",
            timeout: CNSNT.rest_default_timeout,
            success: success_callback,
            error: error_callback
        });
    } else {
        url = call_url + '/' + method;
        $.ajax({contentType: "application/json",
            data: $.param(params),
            dataType: dtype,
            url: url,
            type: "get",
            timeout: CNSNT.rest_default_timeout,
            success: success_callback,
            error: error_callback
            });
    }
}

function get_ticket(initialFn, expt) {
    var params, ruri, resource;
    if (CSTATE.ticket !== "WAITING") {
        var successTicket = function(json, textStatus) {
            CSTATE.net_abort_count = 0;
            if (json.ticket) {
                CSTATE.ticket = json.ticket;
                if (CSTATE.initialFnIsRun === false) {
                    //alert("time to init the fn");
                    if (initialFn) {
                        initialFn(winH, winW);
                    }
                    CSTATE.initialFnIsRun = true;
                }
            }
        };
        var successTicketExport = function(json, textStatus) {
            var rui, resource, tkt, fmt;
            var ifn = expt;
            var alog = ifn.replace("export:", "");
            var ltype = "dat";
            if (alog.indexOf(".analysis") !== -1) {
                ltype = "analysis";
            } else {
                if (alog.indexOf(".peaks") !== -1) {
                    ltype = "peaks";
                } else {
                    if (alog.indexOf(".notes") !== -1) {
                        ltype = "notes";
                    }
                }
            }
            if (json.ticket) {
                var expturl;
                tkt = json.ticket;
                ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
                if (ltype === "notes") {
                    resource = CNSNT.resource_AnzLogNote;
                } else {
                    resource = CNSNT.resource_AnzLog; //"gdu/<TICKET>/1.0/AnzLogMeta"
                }
                resource = resource.replace("&lt;TICKET&gt;", tkt);
                resource = resource.replace("<TICKET>", tkt);
                
                if (ltype === "notes") {
                    expturl = ruri + "/" + resource 
                    + "?qry=byEpoch&alog=" + alog
                    + "&logtype=" + ltype
                    + "&startEtm=0&rtnFmt=file";
                } else {
                    expturl = ruri + "/" + resource 
                    + "?qry=byPos&alog=" + alog
                    + "&logtype=" + ltype
                    + "&startPos=0&rtnFmt=" + CSTATE.exportClass
                    + "&limit=all";
                }

                switch(ltype) {
                case "dat":
                    $('#id_exptLogBtn').html(P3TXT.download_concs);
                    $('#id_exptLogBtn').redraw;
                    break;
                    
                case "peaks":
                    $('#id_exptPeakBtn').html(P3TXT.download_peaks);
                    $('#id_exptPeakBtn').redraw;
                    break;
                    
                case "analysis":
                    $('#id_exptAnalysisBtn').html(P3TXT.download_analysis);
                    $('#id_exptAnalysisBtn').redraw;
                    break;
                    
                case "notes":
                    $('#id_exptNoteBtn').html(P3TXT.download_notes);
                    $('#id_exptNoteBtn').redraw;
                    break;
                }
                alert("expturl: " + expturl);
                window.location = expturl;
            }
        }; //successTicketExport
        var errorTicket = function(xOptions, textStatus) {
            //alert("we have an error");
            CSTATE.ticket = "ERROR";
            
            //var opts = "";
            //var sep = "";
            //for (arg in xOptions) {
            //    opts += sep + arg + ": " + xOptions[arg];
            //    sep = "\n";
            //}
            //alert("textStatus: " + textStatus
            //    + "\nopts: " + opts
            //);
            
            alert("Ticket error. Please refresh the page. \nIf the error continues, contact Customer Support.");
        };
        var errorTicketExport = function(xOptions, textStatus) {
            //alert("we have an error");
            //var opts = "";
            //var sep = "";
            //for (arg in xOptions) {
            //    opts += sep + arg + ": " + xOptions[arg];
            //    sep = "\n";
            //}
            //alert("textStatus: " + textStatus
            //    + "\nopts: " + opts
            //);
            
            alert("Ticket error. Please refresh the page. \nIf the error continues, contact Customer Support.");
        };
        var eTicketFn, sTicketFn;
        if (expt && expt.indexOf("export") !== -1)  {
            sTicketFn = successTicketExport;
            eTicketFn = errorTicketExport;
        } else {
            CSTATE.ticket = "WAITING";
            sTicketFn = successTicket;
            eTicketFn = errorTicket;
        }
        ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
        resource = CNSNT.resource_Admin; //"sec/abcdefg/1.0/Admin"
        resource = insertTicket(resource);
        params = {"qry":"issueTicket"
            , "sys": CNSNT.sys
            , "identity": CNSNT.identity
            , "rprocs": '["AnzMeta:byAnz","AnzLogMeta:byEpoch", "AnzLogNote:byEpoch", "AnzLog:byPos", "AnzLogNote:dataIns", "AnzLog:makeSwath"]'
        };
        call_rest(ruri, resource, "jsonp", params, sTicketFn, eTicketFn);
    }
}

function insertTicket(uri) {
    var nuri;
    // sometimes HLL programs try to be "helpful" and convert the < and > strings
    // into &lt; and &gt; tokens.  So we have to beware.
    nuri = uri.replace("&lt;TICKET&gt;", CSTATE.ticket);
    return nuri.replace("<TICKET>", CSTATE.ticket);
}

function changeFollow() {
    var checked = $("#id_follow").attr("data-checked");
    if (checked == 'true') {
        if (CSTATE.lastwhere && CSTATE.map) {
            centerTheMap(CSTATE.lastwhere);
        }
        $("#id_follow").attr("class","follow-checked").attr("data-checked",'false');
        CSTATE.follow = true;
    } else {
        CSTATE.follow = false;
        $("#id_follow").attr("class","follow").attr("data-checked",'true');
    }
    setCookie(COOKIE_NAMES.follow, (CSTATE.follow) ? "1" : "0", CNSNT.cookie_duration);
}

function changeOverlay() {
    var checked = $("#id_overlay").attr("data-checked");
    if (checked == 'true') {
        showTifCb();
        $("#id_overlay").attr("class","overlay-checked").attr("data-checked",'false');
        CSTATE.overlay = true;
    } else {
        hideTifCb();
        $("#id_overlay").attr("class","overlay").attr("data-checked",'true');
        CSTATE.overlay = false;
    }
    setCookie("pcubed_overlay", (CSTATE.overlay) ? "1" : "0", CNSNT.cookie_duration);
}

function showTifCb() {
    var plobj, img;
    try {
        plobj = PLATOBJS[CSTATE.activePlatName];
        img = PLAT_IMG_BASE + CSTATE.activePlatName.replace('tif', 'png');
        if (plobj.go === null) {
            plobj.go = newGroundOverlay(plobj.minlng, plobj.maxlng, plobj.minlat, plobj.maxlat, img);
            attachGoListener(plobj.go, CSTATE.activePlatName);
        }
        plobj.go.setMap(null);
        plobj.go.setMap(CSTATE.map);
    } catch(err) {
        plobj = null;
    }
}

function hideTifCb() {
    var plobj;
    try {
        plobj = PLATOBJS[CSTATE.activePlatName];
        if (plobj.go !== null) {
            plobj.go.setMap(null);
        }
    } catch(err) {
        plobj = null;
    }
}

function changeMinAmp() {
    var minAmpFloat;
    CSTATE.minAmp = $("#id_amplitude").val();
    try {
        minAmpFloat = parseFloat(CSTATE.minAmp);
        if (isNaN(minAmpFloat)) {
            minAmpFloat = 0.1;
        }
        CSTATE.minAmp = minAmpFloat;
    } catch (err) {
        CSTATE.minAmp = 0.1;
    }
    if (CSTATE.minAmp < CSTATE.fovMinAmp) CSTATE.minAmp = CSTATE.fovMinAmp;
    
    CNSNT.mapControl.changeControlText(P3TXT.map_controls  + "<br/>" + CSTATE.minAmp + "&nbsp; &nbsp;" + CSTATE.stabClass);
    $("#id_amplitude_btn").html(CSTATE.minAmp);
    setCookie("pcubed_minAmp", CSTATE.minAmp, CNSNT.cookie_duration);
    //resetLeakPosition();
    clearPeakMarkerArray();
    clearWindMarkerArray();
}

function stabClassCntl(style) {
    var ht, opendiv, closediv, len, i, options, vlu, selcntl, selected, sty;
    sty = "";
    if (style) {
        sty = style;
    }
    ht = "";
    options = "";
    for (var sc in CNSNT.stab_control) {
        vlu = sc; //CNSNT.stab_control[sc];
        selected = "";
        if (vlu === CSTATE.stabClass) {
            selected = ' selected="selected" ';
        }
        options += '<option value="' + vlu + '"' + selected + '>' + CNSNT.stab_control[sc]
            + '</option>';
    }
    selcntl = '<select ' + sty + ' id="id_stabClassCntl">'
        + options + '</select>';
    return selcntl;
}

function _changeStabClass(value) {
    var isc = "";
    if (value !== CSTATE.stabClass || ((value === "*") && (CSTATE.inferredStabClass != CSTATE.prevInferredStabClass))) {
        CSTATE.stabClass = value;
        CSTATE.prevInferredStabClass = CSTATE.inferredStabClass;
        setCookie(COOKIE_NAMES.dspStabClass, CSTATE.stabClass, CNSNT.cookie_duration);
        if (value === "*") isc = CSTATE.inferredStabClass;
        CNSNT.mapControl.changeControlText(P3TXT.map_controls  + "<br/>" + CSTATE.minAmp + "&nbsp; &nbsp;" + isc + CSTATE.stabClass);
        clearSwathPolys();
    }
}

function changeStabClass() {
    var value;
    value = $("#id_stabClassCntl").val();
    _changeStabClass(value);
}

function exportClassCntl(style) {
    var ht, opendiv, closediv, len, i, options, vlu, selcntl, selected, sty;
    sty = "";
    if (style) {
        sty = style;
    }
    ht = "";
    options = "";
    for (var sc in CNSNT.export_control) {
        vlu = sc; //CNSNT.export_control[sc];
        selected = "";
        if (vlu === CSTATE.exportClass) {
            selected = ' selected="selected" ';
        }
        options += '<option value="' + vlu + '"' + selected + '>' + CNSNT.export_control[sc]
            + '</option>';
    }
    selcntl = '<select ' + sty + ' id="id_exportClassCntl" onchange="changeExportClass()">'
        + options + '</select>';
    return selcntl;
}

function changeExportClass() {
    var value, len, i, aname, mhtml;
    value = $("#id_exportClassCntl").val();
    if (value !== CSTATE.exportClass) {
        CSTATE.exportClass = value;
        setCookie(COOKIE_NAMES.dspExportClass, CSTATE.exportClass, CNSNT.cookie_duration);
    }
}

function setGduTimer(tcat) {
    if (tcat === "dat") {
        TIMER.data = setTimeout(datTimer, CSTATE.datUpdatePeriod);
        return;
    }
    if (tcat === "analysis") {
        TIMER.analysis = setTimeout(analysisTimer, CSTATE.analysisUpdatePeriod);
        return;
    }
    if (tcat === "peakAndWind") {
        TIMER.peakAndWind = setTimeout(peakAndWindTimer, CSTATE.peakAndWindUpdatePeriod);
        return;
    }
    if (tcat === "dnote") {
        TIMER.dnote = setTimeout(dnoteTimer, CSTATE.noteUpdatePeriod);
        return;
    }
    if (tcat === "pnote") {
        TIMER.pnote = setTimeout(pnoteTimer, CSTATE.noteUpdatePeriod);
        return;
    }
    if (tcat === "anote") {
        TIMER.anote = setTimeout(anoteTimer, CSTATE.noteUpdatePeriod);
        return;
    }
    if (tcat === "mode") {
        TIMER.mode = setTimeout(modeTimer, CNSNT.modeUpdatePeriod);
        return;
    }
    if (tcat === "periph") {
        TIMER.periph = setTimeout(periphTimer, CNSNT.periphUpdatePeriod);
        return;
    }
    if (tcat === "swath") {
        TIMER.swath = setTimeout(swathTimer, CSTATE.swathUpdatePeriod);
        return;
    }
}

function datTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('dat');
        return;
    }
    getData();
}

function peakAndWindTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('peakAndWind');
        return;
    }
    showLeaksAndWind();
}

function analysisTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('analysis');
        return;
    }
    showAnalysis();
}

function dnoteTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('dnote');
        return;
    }
    getNotes("path");
}

function pnoteTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('pnote');
        return;
    }
    getNotes("peak");
}

function anoteTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('anote');
        return;
    }
    getNotes("analysis");
}

function modeTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('mode');
        return;
    }
    getMode();
}

function periphTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('periph');
        return;
    }
    checkPeriphUpdate();
}

function swathTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('swath');
        return;
    }
    fetchSwath();
}

function statCheck() {
    var dte, curtime, streamdiff;
    var good = CNSNT.INSTMGR_STATUS_READY | CNSNT.INSTMGR_STATUS_MEAS_ACTIVE |
               CNSNT.INSTMGR_STATUS_GAS_FLOWING | CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED |
               CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED | CNSNT.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED;

    //$('#id_statusPane').html(statusPane());
    dte = new Date();
    curtime = dte.getTime();
    streamdiff = curtime - CSTATE.laststreamtime;
    if (streamdiff > CNSNT.streamerror) {
        $("#id_stream_stat").attr("class", "stream-failed");
        $("#id_analyzer_stat").attr("class", "analyzer-failed");
        if (CSTATE.lastGpsUpdateStatus !== 0) {
            $("#id_gps_stat").attr("class", "gps-failed");
        }
        if (CSTATE.lastWsUpdateStatus !== 0) {
            $("#id_ws_stat").attr("class", "ws-failed");
        }
    } else {
        if (streamdiff > CNSNT.streamwarning) {
            $("#id_stream_stat").attr("class", "stream-warning");
        } else {
            $("#id_stream_stat").attr("class", "stream-ok");
            
            if (CSTATE.lastGpsUpdateStatus === 2) {
                $("#id_gps_stat").attr("class", "gps-failed");
            } else if (CSTATE.lastGpsUpdateStatus === 1) {
                if (CSTATE.lastFit === 0) {
                    $("#id_gps_stat").attr("class", "gps-warning");
                } else {
                    $("#id_gps_stat").attr("class", "gps-ok");
                }
            }

            if (CSTATE.lastWsUpdateStatus === 2) {
                $("#id_ws_stat").attr("class", "ws-failed");
            } else if (CSTATE.lastWsUpdateStatus === 1) {
                $("#id_ws_stat").attr("class", "ws-ok");
            }
            
            if ((CSTATE.lastInst & CNSNT.INSTMGR_STATUS_MASK) !== good) {
                $("#id_analyzer_stat").attr("class", "analyzer-failed");
            } else {
                $("#id_analyzer_stat").attr("class", "analyzer-ok");
            }
        }
    }
}

function getData() {
    var successData = function(data) {
        var resultWasReturned, newTimestring, newFit, newInst, i, clr, pdata, weatherCode;
        CSTATE.net_abort_count = 0;
        restoreModalDiv();
        resultWasReturned = false;
        CSTATE.counter += 1;
        CSTATE.green_count = (CSTATE.green_count+1) % 4;
        if (CSTATE.green_count === 0) {
            $("#id_data_alert").attr("class","wifi-0");
        } else if (CSTATE.green_count === 1) {
            $("#id_data_alert").attr("class","wifi-1");
        } else if (CSTATE.green_count === 2) {
            $("#id_data_alert").attr("class","wifi-2");
        } else if (CSTATE.green_count === 3) {
            $("#id_data_alert").attr("class","wifi-3");
        }
        // $("#counter").html("<h4>" + "Counter: " + CSTATE.counter + "</h4>");
        if (data.result) {
            if (data.result.filename) {
                if (CSTATE.lastDataFilename === data.result.filename) {
                    if (data.result.GPS_ABS_LAT) {
                        if (data.result.GPS_ABS_LONG) {
                            resultWasReturned = true;
                        }
                    }
                } else {
                    initialize_map();
                    CSTATE.startPos = null;
                    resetLeakPosition();
                    clearPeakNoteMarkers();
                    clearAnalysisNoteMarkers();
                    clearDatNoteMarkers(true);

                    if (CSTATE.showPlatOutlines) {
                        show_plat_outlines();
                    } else {
                        hide_plat_outlines();
                    }

                }
                CSTATE.lastDataFilename = data.result.filename;
                CSTATE.lastPeakFilename = CSTATE.lastDataFilename.replace(".dat", ".peaks");
                CSTATE.lastAnalysisFilename = CSTATE.lastDataFilename.replace(".dat", ".analysis");
            } else {
                // alert("data and data.result: ", JSON.stringify(data.result));
            }
        } else {
            if (data && (data.indexOf("ERROR: invalid ticket") !== -1)) {
                statCheck();
                setGduTimer('dat');
                return;
            }
        }
        if (resultWasReturned === true) {
            CSTATE.startPos = data.result.lastPos;
            if (data.result.EPOCH_TIME) {
                if (data.result.EPOCH_TIME.length > 0) {
                    newTimestring = timeStringFromEtm(data.result.EPOCH_TIME[data.result.EPOCH_TIME.length - 1]);
                    if (CSTATE.lastTimestring !== newTimestring) {
                        var dte = new Date();
                        CSTATE.laststreamtime = dte.getTime();
                        $("#placeholder").html("<h4>" + newTimestring + "</h4>");
                        CSTATE.lastTimestring = newTimestring;
                    }
                }
                if (data.result.GPS_FIT) {
                    if (data.result.GPS_FIT.length > 0) {
                        newFit = data.result.GPS_FIT[data.result.GPS_FIT.length - 1];
                        if (CSTATE.lastFit !== newFit) {
                            CSTATE.lastFit = newFit;
                        }
                    }
                }
                if (data.result.INST_STATUS) {
                    if (data.result.INST_STATUS.length > 0) {
                        newInst = data.result.INST_STATUS[data.result.INST_STATUS.length - 1];
                        weatherCode = (newInst >> CNSNT.INSTMGR_AUX_STATUS_SHIFT) & CNSNT.INSTMGR_AUX_STATUS_WEATHER_MASK;
                        if (0 === weatherCode) {
                            CSTATE.weatherMissingCountdown -= 1;
                            if (CSTATE.weatherMissingCountdown <= 0 && CNSNT.prime_view === true) {
                                if (!CSTATE.showingWeatherDialog) {
                                    CSTATE.showingWeatherDialog = true;
                                    weather_dialog();
                                }
                            }
                        }
                        else {
                            CSTATE.weatherMissingCountdown = CNSNT.weatherMissingDefer;
                            //if (!CNSNT.prime_view) {
                                CSTATE.inferredStabClass = CNSNT.classByWeather[weatherCode-1];
                                _changeStabClass(CSTATE.stabClass);
                            //}
                        }
                        if (CSTATE.lastInst !== newInst) {
                            CSTATE.lastInst = newInst;
                        }
                    }
                }

                var n = data.result.CH4.length;
                if (n > 0) {
                    var processTheData = function() {
                        var where = newLatLng(data.result.GPS_ABS_LAT[n - 1], data.result.GPS_ABS_LONG[n - 1]);
                        if (data.result.GPS_FIT) {
                            if (CNSNT.provider === 'google') {
                                if (data.result.GPS_FIT[n - 1] !== 0) {
                                    CSTATE.marker.setVisible(true);
                                } else {
                                    CSTATE.marker.setVisible(false);
                                }
                            }
                            CSTATE.lastwhere = where;
                            CSTATE.marker.setPosition(where);
                            CSTATE.marker.setZIndex(9999);

                            if (CSTATE.alog.indexOf("@@Live:") < 0) {
                                if (TIMER.centerTimer === null) {
                                    TIMER.centerTimer = setTimeout(centerTheMapLastTimed, 2000);
                                }
                            } else {
                                if (CSTATE.follow) {
                                    centerTheMap(where);
                                }
                            }
                        } else {
                            CSTATE.lastwhere = where;
                            if (CSTATE.alog.indexOf("@@Live:") < 0) {
                                if (TIMER.centerTimer === null) {
                                    TIMER.centerTimer = setTimeout(centerTheMapLastTimed, 2000);
                                }
                            } else {
                                if (CSTATE.follow) {
                                    centerTheMap(where);
                                }
                            }
                            CSTATE.marker.setPosition(where);
                            CSTATE.marker.setZIndex(9999);
                            if (CNSNT.provider === 'google') {
                                CSTATE.marker.setVisible(true);
                            }
                        }
                        if (n > 1) {
                            CSTATE.methaneHistory = CSTATE.methaneHistory.concat(data.result.CH4.slice(1));
                            if (CSTATE.methaneHistory.length >= CNSNT.histMax) {
                                CSTATE.methaneHistory.splice(0, CSTATE.methaneHistory.length - CNSNT.histMax);
                            }
                            if (CNSNT.prime_view) {
                                $('#concentrationSparkline').sparkline(CSTATE.methaneHistory, {"chartRangeMin": 1.8, "width": "130px", "height": "50px"});
                                if ('WIND_DIR_SDEV' in data.result) {
                                    var speed = Math.sqrt(data.result.WIND_E[n-1]*data.result.WIND_E[n-1]+
                                        data.result.WIND_N[n-1]*data.result.WIND_N[n-1]);
                                    var speed_mph = speed * 2.236936;
                                    var direction = CNSNT.rtd*Math.atan2(data.result.WIND_E[n-1],data.result.WIND_N[n-1]);
                                    var stddev = data.result.WIND_DIR_SDEV[n-1];
                                    var vCar = 0.0;
                                    if ("CAR_SPEED" in data.result) vCar = data.result.CAR_SPEED[n-1];
                                    stddev = totSdev(speed,stddev,vCar);
                                    if (stddev>90.0) stddev = 90.0;
                                    $("#windData").html("<b style='font-size:12px; color:#404040;'>" + "Wind: " + speed_mph.toFixed(2) + " mph" + "</b>");
                                    makeWindRose(70,27,direction,2*stddev,5.0*speed,15.0,60.0);
                                }
                            } else {
                                $('#concentrationSparkline').html("");
                                $("#windData").html("");
                            }
                            $("#concData").html("<b style='font-size:12px; color:#404040;'>" + "CH4: " + data.result.CH4[n - 1].toFixed(3) + " ppm" + "</b>");
                            for (i = 1; i < n; i += 1) {
                                var last_i = n - 1;
                                clr = data.result.ValveMask ? colorPathFromValveMask(data.result.ValveMask[i]) : CNSNT.normal_path_color;

                                // Assume the default value is "okay" if the data does not have this column.
                                var instStatus = CNSNT.INSTMGR_STATUS_READY | CNSNT.INSTMGR_STATUS_MEAS_ACTIVE |
                                    CNSNT.INSTMGR_STATUS_GAS_FLOWING | CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED |
                                    CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED | CNSNT.INSTMGR_WARM_CHAMBER_TEMP_LOCKED;

                                if (data.result.hasOwnProperty("INST_STATUS")) {
                                    instStatus = data.result.INST_STATUS[i] & CNSNT.INSTMGR_STATUS_MASK;
                                }

                                clr = colorPathFromInstrumentStatus(clr, instStatus);
                                pdata = {
                                    lat: data.result.GPS_ABS_LAT[i],
                                    lon: data.result.GPS_ABS_LONG[i],
                                    etm: data.result.EPOCH_TIME[i],
                                    ch4: data.result.CH4[i]
                                };

                                // only show FOV (swath) for normal_path_color
                                var swath_flag = true;
                                if (clr !== CNSNT.normal_path_color) {
                                    swath_flag = false;
                                }
                                CSTATE.swathPathShowArray.push(swath_flag);

                                if ('WIND_E' in data.result) pdata['windE'] = data.result.WIND_E[i];
                                if ('WIND_N' in data.result) pdata['windN'] = data.result.WIND_N[i];
                                if ('WIND_DIR_SDEV' in data.result) pdata['windDirSdev'] = data.result.WIND_DIR_SDEV[i];
                                if (data.result.GPS_FIT) {
                                    if (data.result.GPS_FIT[i] !== 0) {
                                        updatePath(pdata, clr, data.result.EPOCH_TIME[i], true);
                                    } else {
                                        CSTATE.startNewPath = true;
                                    }
                                } else {
                                    updatePath(pdata, clr, data.result.EPOCH_TIME[i]);
                                }
                            }
                        }
                    }; // processTheData

                    doConvertThenProcess(data, processTheData);
                }
            }
        } else {
            if (TIMER.centerTimer === null) {
                setTimeout(centerTheMapLastTimed, 2000);
            }
        }
        //alert("here");
        statCheck();
        
        if (resultWasReturned === true) {
            CSTATE.datUpdatePeriod = CNSNT.datUpdatePeriod;
            CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriod;
            CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriod;
        } else {
            CSTATE.datUpdatePeriod = CNSNT.datUpdatePeriodSlow;
            CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriodSlow;
            CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriodSlow;
        }
        setGduTimer('dat');

        if (CNSNT.prime_view) {
            if (TIMER.mode === null) {
                setGduTimer('mode');
            }
            if (TIMER.periph === null) {
                setGduTimer('periph');
            }
        }

        if (TIMER.analysis === null) {
            setGduTimer('analysis');
        }
        if (TIMER.peakAndWind === null) {
            setGduTimer('peakAndWind');
        }
        if (TIMER.dnote === null) {
            setGduTimer('dnote');
        }
        if (TIMER.pnote === null) {
            setGduTimer('pnote');
        }
        if (TIMER.anote === null) {
            setGduTimer('anote');
        }
        if (TIMER.swath === null) {
            setGduTimer('swath');
        }
    };
    
    function errorData(xOptions, textStatus) {
        CSTATE.net_abort_count += 1;
        if (CSTATE.net_abort_count >= 4) {
            //alert("HERE in errorData");
            $("#id_modal").html(modalNetWarning());
            $("id_warningCloseBtn").focus();
        }
        $("#errors").html("");
        statCheck();
        setGduTimer('dat');
    }

    switch(CNSNT.prime_view) {
    case false:
        var lmt = CSTATE.getDataLimit;
        if (CSTATE.firstData === true) {
            lmt = 1;
            CSTATE.firstData = false;
        }
        var params = {"alog": CSTATE.alog
                    , "startPos": CSTATE.startPos ? CSTATE.startPos: "null"
                    , "gmtOffset": CNSNT.gmt_offset
                    , 'varList': '["GPS_ABS_LAT","GPS_ABS_LONG","GPS_FIT","CH4","ValveMask", "INST_STATUS", "WIND_N", "WIND_E", "WIND_DIR_SDEV","CAR_SPEED","row"]'        
                    , "limit": lmt
                    , "excludeStart": "true"
                    , "doclist": "true"
                    , "insFilename": "true"
                    , "timeStrings": "true"
                    , "insNextLastPos": "true"
                    , "rtnOnTktError": "1"
                };
        if (!CSTATE.hasOwnProperty("AnzLog")) {
            init_anzlog_rest();
        }
        CSTATE.AnzLog.byPos(params
            // error CB
            , function(err) {
                errorData();
            }
            
            // successCB
            , function(rtn_code, rtnobj) {
                successData(rtnobj);
        });
        
        break;
        
    default:
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        params = {'limit': CSTATE.getDataLimit, 'startPos': CSTATE.startPos, 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset, 
                    'varList': '["GPS_ABS_LAT","GPS_ABS_LONG","GPS_FIT","CH4","ValveMask", "INST_STATUS", "WIND_N", "WIND_E", "WIND_DIR_SDEV","CAR_SPEED"]'};
        call_rest(CNSNT.svcurl, "getData", dtype, params, successData, errorData);
        break;
    }
} // getData

function getMode() {
    var errorMode = function () {
        CSTATE.getting_mode = false;
        //CSTATE.net_abort_count += 1;
        //if (CSTATE.net_abort_count >= 2) {
        //    $("#id_modal").html(modalNetWarning());
        //}
        $("#errors").html("getMode() error");
        setGduTimer('mode');
    };

    var mode;
    if (!CSTATE.getting_mode) {
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        CSTATE.getting_mode = true;
        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "rdDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER']"},
            function (data) {
                CSTATE.net_abort_count = 0;
                if (data.result.value !== undefined) {
                    var mode = data.result.value;
                    setModePane(mode);
                    if (mode === 0) {
                        $("#id_captureBtn").html(P3TXT.switch_to_cptr).attr("onclick","captureSwitch();").removeAttr("disabled");
                        $("#id_surveyOnOffBtn").removeAttr("disabled").html(P3TXT.stop_survey).attr("onclick", "stopSurvey();");
                        $("#id_calibrateBtn").removeAttr("disabled");
                    } else if (mode==1) {
                        $("#id_captureBtn").html(P3TXT.cancl_cptr).attr("onclick", "cancelCapSwitch();").removeAttr("disabled");
                        $("#id_surveyOnOffBtn").attr("disabled", "disabled");
                        $("#id_calibrateBtn").removeAttr("disabled");
                    } else if (mode==2) {
                        $("#id_captureBtn").html(P3TXT.cancl_cptr).attr("onclick", "cancelCapSwitch();").removeAttr("disabled");
                        $("#id_surveyOnOffBtn").attr("disabled", "disabled");
                        $("#id_calibrateBtn").attr("disabled", "disabled");
                    } else if (mode==3) {
                        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "rdDasReg", "args": "['PEAK_DETECT_CNTRL_REMAINING_TRIGGERED_SAMPLES_REGISTER']"},
                            function (data) { 
                                if (data.result.hasOwnProperty('value'))
                                    $("#id_captureBtn").html((0.2*data.result.value).toFixed(0) + P3TXT.cancl_ana_time).attr("onclick", "cancelAnaSwitch();");
                                else     
                                    $("#id_captureBtn").html(P3TXT.cancl_ana).attr("onclick", "cancelAnaSwitch();");
                            }
                        );
                        $("#id_surveyOnOffBtn").attr("disabled", "disabled");
                        $("#id_calibrateBtn").attr("disabled", "disabled");
                    } else if (mode==4) {
                        $("#id_captureBtn").attr("disabled", "disabled");
                        $("#id_surveyOnOffBtn").html(P3TXT.start_survey).attr("onclick","startSurvey();");
                        $("#id_calibrateBtn").attr("disabled", "disabled");
                    } else if (mode==5) {
                        $("#id_captureBtn").attr("disabled", "disabled");
                        $("#id_surveyOnOffBtn").attr("disabled", "disabled");
                        $("#id_calibrateBtn").attr("disabled", "disabled");
                    } else if (mode==6) {
                        $("#id_captureBtn").html(P3TXT.cancl_ref).attr("onclick", "cancelRefSwitch();").removeAttr("disabled");
                        $("#id_surveyOnOffBtn").attr("disabled", "disabled");
                        $("#id_calibrateBtn").attr("disabled", "disabled");
                    } else if (mode==7) {
                        $("#id_captureBtn").html(P3TXT.cancl_ref).attr("onclick", "cancelRefSwitch();").removeAttr("disabled");
                        $("#id_surveyOnOffBtn").attr("disabled", "disabled");
                        $("#id_calibrateBtn").attr("disabled", "disabled");
                    } else if (mode==8) {
                        $("#id_captureBtn").attr("disabled", "disabled");
                        $("#id_surveyOnOffBtn").attr("disabled", "disabled");
                        $("#id_calibrateBtn").attr("disabled", "disabled");
                        injectCal();
                    }
                }
                CSTATE.getting_mode = false;
                setGduTimer('mode');
            }, errorMode);
    }
}

function checkPeriphUpdate() {
    var errorPeriph = function() {
        CSTATE.getting_periph_time = false;
        //CSTATE.net_abort_count += 1;
        //if (CSTATE.net_abort_count >= 2) {
        //    $("#id_modal").html(modalNetWarning());
        //}
        $("#errors").html("checkPeriphUpdate() error");
        setGduTimer('periph');
    };

    if (!CSTATE.getting_periph_time) {
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        CSTATE.getting_periph_time = true;
        call_rest(CNSNT.svcurl, "getLastPeriphUpdate", dtype, {},
            function (data) {
                CSTATE.net_abort_count = 0;
                var gpsPort = CNSNT.gpsPort;
                var wsPort = CNSNT.wsPort;
                if (gpsPort in data.result) {
                    if (data.result[gpsPort] > CNSNT.gpsUpdateTimeout) {
                        CSTATE.lastGpsUpdateStatus = 2;
                    } else {
                        CSTATE.lastGpsUpdateStatus = 1;
                    }
                } else {
                    CSTATE.lastGpsUpdateStatus = 0;
                }
                if (wsPort in data.result) {
                    if (data.result[wsPort] > CNSNT.wsUpdateTimeout) {
                        CSTATE.lastWsUpdateStatus = 2;
                    } else {
                        CSTATE.lastWsUpdateStatus = 1;
                    }
                } else {
                    CSTATE.lastWsUpdateStatus = 0;
                }
                CSTATE.getting_periph_time = false;
                setGduTimer('periph');
            }, errorPeriph);
    }
}

function showAnalysis() {
    function successAnalysis(data) {
        var resultWasReturned, i, result;
        CSTATE.net_abort_count = 0;
        resultWasReturned = false;
        if (data.result) {
            if (data.result.filename) {
                if (CSTATE.lastAnalysisFilename === data.result.filename) {
                    if (data.result.GPS_ABS_LAT) {
                        if (data.result.GPS_ABS_LONG) {
                            resultWasReturned = true;
                        }
                    }
                    CSTATE.analysisDownload = true;
                } else {
                    CSTATE.analysisDownload = false;
                }
            }
        } else {
            if (data && (data.indexOf("ERROR: invalid ticket") !== -1)) {
                statCheck();
                setGduTimer('analysis');
                return;
            }
        }
        if (resultWasReturned === true) {
            if (data.result.CONC) {
                if (CSTATE.clearAnalyses) {
                    CSTATE.clearAnalyses = false;
                } else {
                    var processTheAnalysis = function() {
                        CSTATE.analysisLine = data.result.nextRow;
                        for (i = 0; i < data.result.CONC.length; i += 1) {
                            var analysisCoords = newLatLng(data.result.GPS_ABS_LAT[i], data.result.GPS_ABS_LONG[i]);
                            result = data.result.DELTA[i].toFixed(1) + " +/- " + data.result.UNCERTAINTY[i].toFixed(1);
                            $("#analysis").html(P3TXT.delta + ": " + result);
                            var dcoldata = 0.0;
                            if (data.result.hasOwnProperty("DISPOSITION")) {
                                dcoldata = data.result.DISPOSITION[i];
                            }
                            var analysisMarker = newAnalysisMarker(CSTATE.map, analysisCoords, data.result.DELTA[i], data.result.UNCERTAINTY[i], dcoldata);
                            CSTATE.analysisMarkers[CSTATE.analysisMarkers.length] = analysisMarker;

                            var datadict = CSTATE.analysisNoteDict[data.result.EPOCH_TIME[i]];
                            if (!datadict) {
                                datadict = {};
                            }
                            datadict.lat = data.result.GPS_ABS_LAT[i];
                            datadict.lon = data.result.GPS_ABS_LONG[i];
                            datadict.conc = data.result.CONC[i];
                            datadict.delta = data.result.DELTA[i];
                            datadict.uncertainty = data.result.UNCERTAINTY[i];

                            CSTATE.analysisNoteDict[data.result.EPOCH_TIME[i]] = datadict;
                            attachMarkerListener(analysisMarker, data.result.EPOCH_TIME[i], "analysis", true);
                        }
                    }; //processTheAnalysis

                    doConvertThenProcess(data, processTheAnalysis);

                }
            }
        }
        if (resultWasReturned === true) {
            CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriod;
        } else {
            CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriodSlow;
        }
        setGduTimer('analysis');
    }
    function errorAnalysis() {
        //CSTATE.net_abort_count += 1;
        //if (CSTATE.net_abort_count >= 2) {
        //    $("#id_modal").html(modalNetWarning());
        //}
        $("#errors").html("showAnalysis() error.");
        CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriodSlow;
        setGduTimer('analysis');
    }
    if (!CSTATE.showAbubble) {
        CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriodSlow;
        setGduTimer('analysis');
        return;
    }
    if (CSTATE.ticket !== "WAITING") {
    } else {
        CSTATE.analysisUpdatePeriod = CNSNT.analysisUpdatePeriodSlow;
        setGduTimer('analysis');
    }
    
    switch(CNSNT.prime_view) {
    case false:
        if (CSTATE.alog_analysis === "") {
            CSTATE.alog_analysis = CSTATE.alog.replace(".dat", ".analysis");
        }
        var params = {"alog": CSTATE.alog_analysis
                    , "logtype": "analysis"
                    , "limit": CSTATE.getDataLimit
                    , "startPos": CSTATE.analysisLine
                    , "gmtOffset": CNSNT.gmt_offset
                    , "doclist": "true"
                    , "insFilename": "true"
                    , "timeStrings": "true"
                    , "insNextLastPos": "true"
                    , "rtnOnTktError": "1"
        };
        if (!CSTATE.hasOwnProperty("AnzLog")) {
            init_anzlog_rest();
        }
        CSTATE.AnzLog.byPos(params
            // error CB
            , function(err) {
                errorAnalysis();
            }
            
            // successCB
            , function(rtn_code, rtnobj) {
                successAnalysis(rtnobj);
        });
        break;
        
    default:
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        params = {'startRow': CSTATE.analysisLine, 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset};
        call_rest(CNSNT.svcurl, "getAnalysis", dtype, params, successAnalysis, errorAnalysis);
        break;
    }
} //showAnalysis

function equalProperties(obj1, obj2) {
    var p;
    for (p in obj1) {
        if (obj1.hasOwnProperty(p)) {
            if (obj2.hasOwnProperty(p)) {
                if (obj1[p] !== obj2[p]) return false;
            }
            else return false;
        }
    }
    for (p in obj2) {
        if (obj2.hasOwnProperty(p)) {
            if (obj1.hasOwnProperty(p)) {
                if (obj1[p] !== obj2[p]) return false;
            }
            else return false;
        }
    }
    return true;
}

function refreshFov(errLrtFn, goodLrtFn) {
    gdu_logger("refreshFov:", "debug");
    
    var updateState = function(rtnobj, clear_row_flag) {
        gdu_logger("refreshFov.updateState:", "debug");
        
        if (rtnobj.hasOwnProperty("lrt_parms_hash") 
                        && rtnobj.hasOwnProperty("lrt_start_ts") 
                        && rtnobj.hasOwnProperty("status")) {

            //console.log('new swath status ' + rtnobj.status + ' count: ' + rtnobj.count);
            CSTATE.fov_lrt_parms_hash = rtnobj.lrt_parms_hash;
            CSTATE.fov_lrt_start_ts = rtnobj.lrt_start_ts;
            CSTATE.fov_status = rtnobj.status;
            
            if (rtnobj.hasOwnProperty("count")) {
                CSTATE.fov_count = rtnobj.count;
            } else {
                CSTATE.fov_count = 0;
            }
            
            if (clear_row_flag === true) {
                CSTATE.fov_status = null;                
                CSTATE.fov_lrtrow = 0;
            }
        }
    }; // updateState
    
    // get a new fov LRT document
    // update the CSTATE for the LRT
    var getNewFov = function(fparms, errFn, goodFn) {
        gdu_logger("refreshFov.getNewFov:", "debug");
        
        if (!CSTATE.hasOwnProperty("AnzLog")) {
            init_anzlog_rest();
        }
        CSTATE.AnzLog.makeFov(fparms
            // error callback
            , function(err) {
                gdu_logger("refreshFov.getNewFov: "
                    + "unexpected error in CSTATE.AnzLog.makeFov"
                    , err, "debug");
            
                errFn(err);
            }
            
            // success callback
            , function(stat_code, rtnobj) {
                updateState(rtnobj, true);
                goodFn();
        });
    }; // getNewFov
    
    var refreshFovLrtStatus = function(errFn, goodFn) {
        gdu_logger("refreshFov.refreshFovLrtStatus:", "debug");
        
        var statparams = {'prmsHash': CSTATE.fov_lrt_parms_hash
                        , 'startTs': CSTATE.fov_lrt_start_ts
                        };
        if (!CSTATE.hasOwnProperty("AnzLrt")) {
            init_anzlrt_rest();
        }
        
        CSTATE.AnzLrt.getStatus(statparams
            // error callback
            , function(err) {
                gdu_logger("refreshFov.getNewFov: "
                    + "unexpected error in CSTATE.AnzLog.getStatus"
                    , err, "debug");
            
                errFn(err);
            }
            
            // success callback
            , function(stat_code, rtnobj) {
                updateState(rtnobj);
                goodFn();
        });
    };// checkFovLrtStatus
    
    
    var params = {'nWindow': CNSNT.swathWindow
                    , 'stabClass':CSTATE.stabClass
                    , 'minLeak': CSTATE.minLeak
                    , 'minAmp':CSTATE.fovMinAmp
                    , 'astd_a': CSTATE.astd_a
                    , 'astd_b': CSTATE.astd_b
                    , 'astd_c': CSTATE.astd_c
                    , 'alog': CSTATE.lastDataFilename
                    , 'gmtOffset': CNSNT.gmt_offset
                    , "rtnOnTktError": "1"
                    };

    if (!equalProperties(CSTATE.lastSwathParams,params)) {

        CSTATE.lastSwathParams = {};
        $.extend(CSTATE.lastSwathParams,params);
        
        getNewFov(params
            // errFn
            , function(err) {
                errLrtFn();
            }
            
            // goodFn
            , function() {
                // we have a new FOV LRT, so check the status
                refreshFovLrtStatus(
                    // errFn
                    function(err) {
                        //console.log("errFn from refreshFovLrtStatus");
                        errLrtFn();
                    }
                    
                    // goodFn
                    , function() {
                        //console.log("goodFn from refreshFovLrtStatus");
                        goodLrtFn();
                    });
                
            });
        
    } else {
        
        if ((CSTATE.fov_lrt_parms_hash === null)) {
            // skip because we don't have any lrt to test
            errLrtFn();
        } else {
            if (CSTATE.fov_status < 16) {
                refreshFovLrtStatus(
                    // errFn
                    function(err) {
                        //console.log("EQ errFn from refreshFovLrtStatus");
                        errLrtFn();
                    }
                    
                    // goodFn
                    , function() {
                        //console.log("EQ goodFn from refreshFovLrtStatus");
                        goodLrtFn();
                    });
                
            } else {
                goodLrtFn();
            }
        }
    } 
} //refreshFov

function fetchSwath() {
    gdu_logger("fetchSwath:", "debug");
    
    function successSwath(data) {
        gdu_logger("fetchSwath.successSwath:", "debug");
        gdu_logger("fetchSwath.successSwath: data:", data, "debug");
        
        var resultWasReturned, i;
        resultWasReturned = false;
        CSTATE.lastSwathOutput = {};
        $.extend(CSTATE.lastSwathOutput,data);
        
        if (data.result) {
            if (CNSNT.prime_view === true) {
                if (data.result.filename) {
                    if (CSTATE.lastDataFilename === data.result.filename) {
                    // if (CSTATE.lastSwathFilename === data.result.filename) {
                        resultWasReturned = true;
                    }
                    //CSTATE.lastAnalysisFilename = data.result.filename;
                }
            } else {
                if (data.result.hasOwnProperty("GPS_ABS_LAT")) {
                    resultWasReturned = true;
                }
            }
        } else {
            CSTATE.swathSkipCount = CNSNT.swathMaxSkip; // force call on next pass
            //if (data) {
                setGduTimer('swath');
                return;
            //}
        }
        if (resultWasReturned === true) {
            if (data.result.GPS_ABS_LAT) {
                if (CSTATE.clearSwath) {
                    CSTATE.clearSwath = false;
                } else {
                    var processTheSwath = function() {
                        for (i=0;i<data.result.GPS_ABS_LAT.length;i+=1) {
                            var where = newLatLng(data.result.GPS_ABS_LAT[i],data.result.GPS_ABS_LONG[i]);
                            var deltaLat = data.result.DELTA_LAT[i];
                            var deltaLon = data.result.DELTA_LONG[i];

                            var show_the_swath = true;
                            if (CNSNT.prime_view !== true) {
                                CSTATE.fov_lrtrow = data.result.lrtrow[i];

                                if (CSTATE.fov_lrtrow >= CSTATE.fov_count) {
                                    CSTATE.swathUpdatePeriod = CNSNT.swathUpdatePeriodSlow
                                } else {
                                    CSTATE.swathUpdatePeriod = CNSNT.swathUpdatePeriod
                                }

                                var pthidx = CSTATE.fov_lrtrow + (2*CNSNT.swathWindow) - 1;

                                if ((CSTATE.swathPathShowArray.length >= pthidx)
                                    && (CSTATE.swathPathShowArray[pthidx] !== true)) {

                                    show_the_swath = false;
                                }
                            }

                            if (CSTATE.lastMeasPathLoc && (show_the_swath === true)) {
                                var noLastView = (Math.abs(CSTATE.lastMeasPathDeltaLat) < 1.0e-6) &&
                                    (Math.abs(CSTATE.lastMeasPathDeltaLon) < 1.0e-6);
                                if (!noLastView) {
                                    var noView = (Math.abs(deltaLat) < 1.0e-6) &&
                                        (Math.abs(deltaLon) < 1.0e-6);
                                    if (!noView) {
                                        // Draw the polygon
                                        //console.log("CSTATE.lastMeasPathLoc", CSTATE.lastMeasPathLoc);

                                        var lmlat = getLatFromLoc(CSTATE.lastMeasPathLoc);
                                        var lmlng = getLngFromLoc(CSTATE.lastMeasPathLoc);
                                        var whlat = getLatFromLoc(where);
                                        var whlng = getLngFromLoc(where);


                                        var coords = [
                                            newLatLng(lmlat+CSTATE.lastMeasPathDeltaLat,
                                                lmlng+CSTATE.lastMeasPathDeltaLon),
                                            CSTATE.lastMeasPathLoc,
                                            where,
                                            newLatLng(whlat+deltaLat, whlng+deltaLon)];
                                        CSTATE.swathPolys.push(newPolygonWithoutOutline(CSTATE.map,CNSNT.swath_color,CNSNT.swath_opacity,coords,CSTATE.showSwath));
                                    }
                                }
                            }

                            CSTATE.lastMeasPathLoc = where;
                            CSTATE.lastMeasPathDeltaLat = deltaLat;
                            CSTATE.lastMeasPathDeltaLon = deltaLon;
                        }

                        if (CNSNT.prime_view === true) {
                            CSTATE.swathLine = data.result.nextRow;
                        }
                    }; //processTheSwath

                    doConvertThenProcess(data, processTheSwath);

                }
            }
        }
        setGduTimer('swath');
    } // successSwath
    
    function errorSwath(xOptions, textStatus) {
        gdu_logger("fetchSwath.errorSwath:", "debug");
        gdu_logger("fetchSwath.errorSwath: textStatus:", textStatus, "debug");
        
        CSTATE.swathSkipCount = CNSNT.swathMaxSkip; // force call on next pass
        $("#errors").html("fetchSwath() error.");
        setGduTimer('swath');
    } // errorSwath
    
    function nextFovFromLrt(lmt) {
        gdu_logger("fetchSwath.nextFovFromLrt:", "debug");
        
        if (CSTATE.fov_lrtrow >= CSTATE.fov_count) {
            CSTATE.swathUpdatePeriod = CNSNT.swathUpdatePeriodSlow                                
        } else {
            CSTATE.swathUpdatePeriod = CNSNT.swathUpdatePeriod                                
        }
        
        if ((CSTATE.fov_status >= 16) && (CSTATE.fov_lrtrow >= CSTATE.fov_count)) {
            gdu_logger("fetchSwath.nextFovFromLrt: replay CSTATE.lastSwathOutput", "debug");
            
            //successSwath(CSTATE.lastSwathOutput);
            setGduTimer('swath');
            return;
        }
        
        var lrtparams = {'prmsHash': CSTATE.fov_lrt_parms_hash
                        , 'startTs': CSTATE.fov_lrt_start_ts
                        , 'startRow': CSTATE.fov_lrtrow
                        , 'excludeStart': true
                        , 'excludeLrtId': true
                        , 'doclist': true
                        , 'limit': lmt};
        
        if (!CSTATE.hasOwnProperty("AnzLrt")) {
            init_anzlrt_rest();
        }
        
        gdu_logger("fetchSwath.nextFovFromLrt: CSTATE.AnzLrt.byRowFov(lrtparams)", "debug");
        gdu_logger("fetchSwath.nextFovFromLrt: lrtparams", lrtparams, "debug");
        
        CSTATE.AnzLrt.byRowFov(lrtparams
            // error callback
            , function(err) {
                //console.log('AnzLrt err')
                errorSwath(null, "nextFovFromLrt AnzLrt.byRowFov error");
            }
            
            // success callback
            , function(stat_code, rtnobj) {
                //console.log('AnzLrt success')
                successSwath(rtnobj);
                
        });
    } // nextFovFromLrt()
    

    if (!CSTATE.showSwath) {
        CSTATE.swathSkipCount = CNSNT.swathMaxSkip; // force call on next pass
        setGduTimer('swath');
        return;
    }

    // skip the process if we don't have a startPos for the log
    if (CSTATE.startPos === null) {
        CSTATE.swathSkipCount = CNSNT.swathMaxSkip; // force call on next pass
        setGduTimer('swath');
        return;
        
    } else {
        
        // skip the process if fov is ahead of startPos (fov should trail route)
        //if (CSTATE.fov_lrtrow > CSTATE.startPos) {
        //    CSTATE.swathSkipCount = CNSNT.swathMaxSkip; // force call on next pass
        //    setGduTimer('swath');
        //    return;
        //}
        
        // get the limit (forcing fov to trail the route)
        var lmt = CSTATE.getSwathLimit;
        //var max_lmt = CSTATE.startPos - CSTATE.fov_lrtrow;
        //if (max_lmt < CSTATE.getSwathLimit) {
        //    lmt = max_lmt;
        //}
    }
    
    switch(CNSNT.prime_view) {
    // normal view (prime_view == false) uses AnzLrt:byRow for the data
    // and it uses AnzLog:makeFov to build the data
    case false:

        if (CSTATE.lastDataFilename !== "") {
            refreshFov(
                // error fn
                function() {
                    errorSwath(null, "refreshFov error");
                }
                
                // good fn
                , function() {
                    //console.log('calling nextFovFromLrt limit: ' + lmt + ' start: ' + CSTATE.fov_lrtrow + ' status: ' + CSTATE.fov_status);
                    nextFovFromLrt(lmt);
                });
                
        } else {
            setGduTimer('swath');
        }
        break;
        
        
    // prime view uses AnzLog:makeSwath with analyzer
    default:
        var params = {'startRow': CSTATE.swathLine
                    , 'limit':CSTATE.getSwathLimit
                    , 'nWindow': CNSNT.swathWindow
                    , 'stabClass':CSTATE.stabClass
                    , 'minLeak': CSTATE.minLeak
                    , 'minAmp':CSTATE.fovMinAmp
                    , 'astd_a': CSTATE.astd_a
                    , 'astd_b': CSTATE.astd_b
                    , 'astd_c': CSTATE.astd_c
                    , 'alog': CSTATE.alog
                    , 'gmtOffset': CNSNT.gmt_offset
                    , "rtnOnTktError": "1"
                    };
        
        // Avoid repeatedly calling makeSwath if parameters are unchanged. Even if the parameters
        //  are identical and we get back empty data sets, we should do the call from time-to-time 
        //  in case new data arrive. This frequency is controlled by CNSNT.swathMaxSkip.
        
        if (equalProperties(CSTATE.lastSwathParams,params)) {
            if (CSTATE.swathSkipCount >= CNSNT.swathMaxSkip) {
                // We make the call despite the identical parameters since we
                //  have got too many empty replies
                CSTATE.swathSkipCount = 0;
            } else {
                if (CSTATE.lastSwathOutput.hasOwnProperty("result")) {
                    if (CSTATE.lastSwathOutput.result.hasOwnProperty("GPS_ABS_LAT")) {
                        if (!CSTATE.lastSwathOutput.result.GPS_ABS_LAT.length) CSTATE.swathSkipCount += 1;
                    }
                }
                // Playback from cache
                successSwath(CSTATE.lastSwathOutput);
                return;
            }
        }
    
        // We actually need to make the call. Clear out the lastSwathOutput cache
        //  since the parameters have changed
        CSTATE.lastSwathParams = {};
        $.extend(CSTATE.lastSwathParams,params);
        CSTATE.lastSwathOutput = {};
        
        var dtype = "jsonp";
        call_rest(CNSNT.svcurl, "makeSwath", dtype, params,
                function (json, status, jqXHR) {
                CSTATE.net_abort_count = 0;
                successSwath(json);
            },
            function (xOptions, textStatus) {
                errorSwath(xOptions, textStatus);
            }
        );
        break;
    } // switch(CNSNT.prime_view)
}

function showLeaksAndWind() {
    function successPeaksAndWind(data) {
        var resultWasReturned, i;
        resultWasReturned = false;
        if (data.result) {
            if (data.result.filename) {
                if (CSTATE.lastPeakFilename === data.result.filename) {
                    if (data.result.GPS_ABS_LAT) {
                        if (data.result.GPS_ABS_LONG) {
                            resultWasReturned = true;
                        }
                    }
                }
                //CSTATE.lastPeakFilename = data.result.filename;
                CSTATE.peaksDownload = true;
            } else {
                CSTATE.peaksDownload = false;
            }
        } else {
            if (data && (data.indexOf("ERROR: invalid ticket") !== -1)) {
                statCheck();
                CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriod;
                setGduTimer('peakAndWind');
                return;
            }
        }
        if (resultWasReturned === true) {
            var resetClear = false;
            if (data.result.CH4 && CSTATE.showPbubble && CSTATE.clearLeaks) {
                    CSTATE.clearLeaks = false;
                resetClear = true;
            }
            if (data.result.WIND_DIR_SDEV && CSTATE.showWbubble && CSTATE.clearWind) {
                CSTATE.clearWind = false;
                resetClear = true;
            }
            if (resetClear) {
                CSTATE.peakLine = 1;
            } else {
                var showPeaks = (data.result.CH4 && CSTATE.showPbubble);
                //console.log("showPeaks: " + showPeaks, "CSTATE.minAmp: " + CSTATE.minAmp);
                var showWind = (data.result.WIND_DIR_SDEV && CSTATE.showWbubble);
                if (showPeaks || showWind){
                    var processTheLeaks = function() {
                        for (i = 0; i < data.result.CH4.length; i += 1) {
                            var amp = data.result.AMPLITUDE[i];
                            var peakCoords = newLatLng(data.result.GPS_ABS_LAT[i], data.result.GPS_ABS_LONG[i]);
                            if (showPeaks) {
                                if (amp >= CSTATE.minAmp) {
                                    var peakMarker = newPeakMarker(CSTATE.map, peakCoords, data.result.AMPLITUDE[i], data.result.SIGMA[i], data.result.CH4[i]);
                                    CSTATE.peakMarkers[CSTATE.peakMarkers.length] = peakMarker;

                                    if (CNSNT.turnOnAudio) {
                                        // Play warning sound
                                        var myAudio = document.getElementById("plume");
                                        myAudio.play();
                                    }
                                    var datadict = CSTATE.peakNoteDict[data.result.EPOCH_TIME[i]];
                                    if (!datadict) {
                                        datadict = {};
                                    }
                                    datadict.lat = data.result.GPS_ABS_LAT[i];
                                    datadict.lon = data.result.GPS_ABS_LONG[i];
                                    datadict.ch4 = data.result.CH4[i];
                                    datadict.amp = data.result.AMPLITUDE[i];
                                    datadict.sigma = data.result.SIGMA[i];

                                    CSTATE.peakNoteDict[data.result.EPOCH_TIME[i]] = datadict;
                                    attachMarkerListener(peakMarker, data.result.EPOCH_TIME[i], "peak", true);
                                }
                                else {
                                    var token = newToken(CSTATE.map, peakCoords);
                                    CSTATE.peakMarkers[CSTATE.peakMarkers.length] = token;
                                }
                            }

                            if (showWind && amp>=CSTATE.minAmp) {
                                var windDirection = CNSNT.rtd*Math.atan2(data.result.WIND_E[i],data.result.WIND_N[i]);
                                var windSpeed = Math.sqrt(data.result.WIND_N[i]*data.result.WIND_N[i]+data.result.WIND_E[i]*data.result.WIND_E[i]);
                                var vCar = 0;
                                var windStddev = data.result.WIND_DIR_SDEV[i];
                                if ("CAR_SPEED" in data.result) vCar = data.result.CAR_SPEED[i];
                                windStddev = totSdev(windSpeed,windStddev,vCar);
                                peakCoords = newLatLng(data.result.GPS_ABS_LAT[i], data.result.GPS_ABS_LONG[i]);
                                if (isNaN(windStddev)) {
                                    windStddev = 90;
                                    windDirection = 180;
                                }
                                var windMarker = newWindMarker(CSTATE.map, peakCoords, 50, windDirection, windStddev, data.result.AMPLITUDE[i], data.result.SIGMA[i]);
                                CSTATE.windMarkers[CSTATE.windMarkers.length] = windMarker;
                            }
                        }
                        CSTATE.peakLine = data.result.nextRow;
                    }
                }; //processTheLeaks

                doConvertThenProcess(data, processTheLeaks);
            }
        }
        if (resultWasReturned === true) {
            CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriod;
        } else {
            CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriodSlow;
        }
        setGduTimer('peakAndWind');
    }
    function errorPeakAndWind(text) {
        //CSTATE.net_abort_count += 1;
        //if (CSTATE.net_abort_count >= 2) {
        //    $("#id_modal").html(modalNetWarning());
        //}
        $("#errors").html(text);
        CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriodSlow;
        setGduTimer('peakAndWind');
    }
    
    if ((!CSTATE.showPbubble) && (!CSTATE.showWbubble)) {
        CSTATE.peakAndWindUpdatePeriod = CNSNT.peakAndWindUpdatePeriodSlow;
        setGduTimer('peakAndWind');
        return;
    }
    
    switch(CNSNT.prime_view) {
    case false:
        if (CSTATE.alog_peaks === "") {
            CSTATE.alog_peaks = CSTATE.alog.replace(".dat", ".peaks");
        }
        var params = {"alog": CSTATE.alog_peaks
                    , "logtype": "peaks"
                    , 'postFilter': '{"AMPLITUDE": {"$gte": ' + CSTATE.fovMinAmp + '}}' 
                    , "limit": CSTATE.getDataLimit
                    , "startPos": CSTATE.peakLine
                    , "gmtOffset": CNSNT.gmt_offset
                    , "doclist": "true"
                    , "insFilename": "true"
                    , "timeStrings": "true"
                    , "insNextLastPos": "true"
                    , "rtnOnTktError": "1"
        };
        if (!CSTATE.hasOwnProperty("AnzLog")) {
            init_anzlog_rest();
        }
        CSTATE.AnzLog.byPos(params
            // error CB
            , function(err) {
            errorPeakAndWind("error getting peaks data");
            }
            
            // successCB
            , function(rtn_code, rtnobj) {
                successPeaksAndWind(rtnobj);
        });
        break;
        
    default:
        params = {'startRow': CSTATE.peakLine, 'alog': CSTATE.alog, 'minAmp': CSTATE.fovMinAmp, 'gmtOffset': CNSNT.gmt_offset};
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "getPeaks", dtype, params,
                function (json, status, jqXHR) {
                CSTATE.net_abort_count = 0;
                successPeaksAndWind(json);
            },
            function (jqXHR, ts, et) {
                errorPeakAndWind(jqXHR.responseText);
            }
        );
        break;
    }
    
} //showLeaksAndWind

function getNotes(cat) {
    function successNotes(data, cat) {
        var process_result, resultWasReturned;
        process_result = false;
        resultWasReturned = false;
        
        if (data.result) {
            process_result = true;
            if (cat === "peak") {
                if (CSTATE.clearPeakNote) {
                    CSTATE.clearPeakNote = false;
                    process_result = false;
                }
            } else {
                if (cat === "analysis") {
                    if (CSTATE.clearAnalysisNote) {
                        CSTATE.clearAnalysisNote = false;
                        process_result = false;
                    }
                } else {
                    if (CSTATE.clearDatNote) {
                        CSTATE.clearDatNote = false;
                        process_result = false;
                    }
                }
            }
            if (process_result) {
                if (data.result.EPOCH_TIME) {
                    resultWasReturned = true;
                    dropResultNoteBubbles(data.result, cat);
                }
                if (CNSNT.prime_view) {
                    if (data.result.nextEtm) {
                        if (cat === "peak") {
                            CSTATE.nextPeakEtm = data.result.nextEtm;
                        } else {
                            if (cat === "analysis") {
                                CSTATE.nextAnalysisEtm = data.result.nextEtm;
                            } else {
                                CSTATE.nextDatEtm = data.result.nextEtm;
                            }
                        }
                    }
                } else {
                    var utm = data.result.UPDATE_TIME;
                    if (utm) {
                        var lastUtm = utm.pop();
                        // delete utm;
                        if (cat === "peak") {
                            CSTATE.nextPeakEtm = lastUtm;
                        } else {
                            if (cat === "analysis") {
                                CSTATE.nextAnalysisEtm = lastUtm;
                            } else {
                                CSTATE.nextDatEtm = lastUtm;
                            }
                        }

                    }
                }
            }
        } else {
            resultWasReturned = false;
        }
        if (resultWasReturned === true) {
            CSTATE.noteUpdatePeriod = CNSNT.noteUpdatePeriod;
        } else {
            CSTATE.noteUpdatePeriod = CNSNT.noteUpdatePeriodSlow;
        }
        if (cat === "peak") {
            setGduTimer('pnote');
        } else {
            if (cat === "analysis") {
                setGduTimer('anote');
            } else {
                setGduTimer('dnote');
            }
        }
    }
    function errorDatNotes(text) {
        //CSTATE.net_abort_count += 1;
        //if (CSTATE.net_abort_count >= 2) {
        //    $("#id_modal").html(modalNetWarning());
        //}
        $("#errors").html(text);
        if (cat === "peak") {
            setGduTimer('pnote');
        } else {
            if (cat === "analysis") {
                setGduTimer('anote');
            } else {
                setGduTimer('dnote');
            }
        }
    }

    var params, fname, etm;
    if (cat === "peak") {
        if (!CSTATE.showPnote) {
            setGduTimer('pnote');
            return;
        }
        fname = CSTATE.lastPeakFilename;
        etm = CSTATE.nextPeakEtm;
    } else {
        if (cat === "analysis") {
            if (!CSTATE.showAnote) {
                setGduTimer('anote');
                return;
            }
            fname = CSTATE.lastAnalysisFilename;
            etm = CSTATE.nextAnalysisEtm;
        } else {
            if (!CSTATE.showDnote) {
                setGduTimer('dnote');
                return;
            }
            fname = CSTATE.lastDataFilename;
            etm = CSTATE.nextDatEtm;
        }
    }

    if (CNSNT.resource_AnzLogNote) {
        var ltype = 'dat';
        if (cat === "peak") {
            fname = CSTATE.lastPeakFilename;
            etm = CSTATE.nextPeakEtm;
            ltype = 'peaks';
        } else {
            if (cat === "analysis") {
                fname = CSTATE.lastAnalysisFilename;
                etm = CSTATE.nextAnalysisEtm;
                ltype = 'analysis';
            } else {
                fname = CSTATE.lastDataFilename;
                etm = CSTATE.nextDatEtm;
                ltype = 'dat';
            }
        }

        params = {"alog": fname
                    , "startEtm": etm
                    , "gmtOffset": CNSNT.gmt_offset
                    , "limit": CSTATE.getDataLimit
                    , "ltype": ltype
                    , "doclist": "true"
                    , "insFilename": "true"
                    , "timeStrings": "true"
                    , "byUtm": "true"
                    , "returnLatLng": "true"
                    , "excludeStart": "true"
                    , "rtnOnTktError": "1"
        };
        if (!CSTATE.hasOwnProperty("AnzLogNote")) {
            init_anzlognote_rest();
        }
        CSTATE.AnzLogNote.byEpoch(params
            // error CB
            , function(err) {
            errorDatNotes("error getting peaks data");
            }
            
            // successCB
            , function(rtn_code, rtnobj) {
                successNotes(rtnobj, cat);
        });
    }
    // NOTE: if there is no resource_AnzLogNote, this will STOP the note timers
    // as there is no ELSE logic to restart them. 
    // This is the expected behavior.
}


function attachMarkerListener(marker, etm, cat, bubble) {
    var markerListener = newEventListener(marker, 'click', function () {
        notePane(etm, cat);
    });
    if (cat === "peak") {
        if (bubble === true) {
            CSTATE.peakBblListener[etm] = markerListener;
        } else {
            CSTATE.peakNoteListener[etm] = markerListener;
        }
    } else {
        if (cat === "analysis") {
            if (bubble === true) {
                CSTATE.analysisBblListener[etm] = markerListener;
            } else {
                CSTATE.analysisNoteListener[etm] = markerListener;
            }
        } else {
            CSTATE.datNoteListener[etm] = markerListener;
        }
    }
}

//drop (or update) the note bubble (and add listener if dropping)
//and update the current state dictionary for the note(s) from the result set
function dropResultNoteBubbles(results, cat) {
    var i, ch4, etm, last_etm, ntx, datadict, pathCoords, pathMarker, lat, lon, mkr, utm;
    utm = results.UPDATE_TIME;
    etm = results.EPOCH_TIME;
    ntx = results.NOTE_TXT;
    lat = results.GPS_ABS_LAT;
    lon = results.GPS_ABS_LONG;
    ch4 = results.CH4;
    last_etm = etm;

    for (i = 0; i < etm.length; i += 1) {
        if (cat === 'peak') {
            if (!CSTATE.showPnote) {
                return;
            }
            datadict = CSTATE.peakNoteDict[etm[i]];
        } else {
            if (cat === 'analysis') {
                if (!CSTATE.showAnote) {
                    return;
                }
                datadict = CSTATE.analysisNoteDict[etm[i]];
            } else {
                if (!CSTATE.showDnote) {
                    return;
                }
                datadict = CSTATE.datNoteDict[etm[i]];
            }
        }
        if (!datadict) {
            datadict = {};
        }
        datadict.lat = lat[i];
        datadict.lon = lon[i];
        if (ch4) {
            datadict.ch4 = ch4[i];
        }

        datadict.note = ntx[i];
        datadict.db = true;
        datadict.lock = false;
        if (cat === "peak") {
            mkr = CSTATE.peakNoteMarkers[etm[i]];
        } else {
            if (cat === "analysis") {
                mkr = CSTATE.analysisNoteMarkers[etm[i]];
            } else {
                mkr = CSTATE.datNoteMarkers[etm[i]];
            }
        }
        if (mkr) {
            updateNoteMarkerText(CSTATE.map, mkr, datadict.note, cat);
        } else {
            pathCoords = newLatLng(datadict.lat, datadict.lon);
            pathMarker = newNoteMarker(CSTATE.map, pathCoords, datadict.note, cat);

            if (cat === 'peak') {
                CSTATE.peakNoteMarkers[etm[i]] = pathMarker;
            } else {
                if (cat === 'analysis') {
                    CSTATE.analysisNoteMarkers[etm[i]] = pathMarker;
                } else {
                    CSTATE.datNoteMarkers[etm[i]] = pathMarker;
                }
            }
            attachMarkerListener(pathMarker, etm[i], cat);
        }
        if (cat === 'peak') {
            CSTATE.peakNoteDict[etm[i]] = datadict;
        } else {
            if (cat === 'analysis') {
                CSTATE.analysisNoteDict[etm[i]] = datadict;
            } else {
                CSTATE.datNoteDict[etm[i]] = datadict;
            }
        }
    }
}


function setModePane(mode) {
    if (mode==4) {
        $("#mode").html("<font color='red'>" + modeStrings[mode] + "</font>");
    } else {
        $("#mode").html(modeStrings[mode]);
    }
    CSTATE.current_mode = mode;
}

function captureSwitch() {
    CSTATE.ignoreTimer = true;
    $("#analysis").html("");
    var dtype = "json";
    if (CNSNT.prime_view === true) {
        dtype = "jsonp";
    }
    call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 1]"});
    CSTATE.ignoreTimer = false;
    restoreModChangeDiv();
}

function cancelCapSwitch() {
    if (confirm(P3TXT.cancel_cap_msg)) {
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 0]"});
        restoreModChangeDiv();
    }
}

function cancelRefSwitch() {
    if (confirm(P3TXT.cancel_ref_msg)) {
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 5]"});
        restoreModChangeDiv();
    }
}

function cancelAnaSwitch() {
    if (confirm(P3TXT.cancel_ana_msg)) {
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 5]"});
        restoreModChangeDiv();
    }
}

function primingSwitch() {
    CSTATE.ignoreTimer = true;
    $("#analysis").html("");
    var dtype = "json";
    if (CNSNT.prime_view === true) {
        dtype = "jsonp";
    }
    call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 6]"});
    CSTATE.ignoreTimer = false;
    restoreModChangeDiv();
}

function referenceGas() {
    var dtype = "json";
    if (CNSNT.prime_view === true) {
        dtype = "jsonp";
    }
    call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "interfaceValue", "args": "['PEAK_DETECT_CNTRL_PrimingState']"},
        function (data) {
            if (data.result.value == 6) {
                if (confirm(P3TXT.start_ref_msg)) {
                    setTimeout(primingSwitch, 100);
                }
            }
            else {
                alert("Feature is not available on current analyzer software");
            }
        }
    );
}

function injectCal() {
    captureSwitch();
    setTimeout(callInject, 1000);
}

function callInject() {
    var dtype = "json";
    if (CNSNT.prime_view === true) {
        dtype = "jsonp";
    }
    call_rest(CNSNT.svcurl, "injectCal", dtype, {"valve": 3, "flagValve": 4, "samples": 5});
    restoreModChangeDiv();
}

function startSurvey() {
    var dtype = "json";
    if (CNSNT.prime_view === true) {
        dtype = "jsonp";
    }
    call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 0]"});
    restoreModChangeDiv();
}

function stopSurvey() {
    if (confirm(P3TXT.stop_survey_msg)) {
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 4]"});
        restoreModChangeDiv();
    }
}

function completeSurvey() {
    alert("Complete Survey button pressed");
    restoreModChangeDiv();
}

function initialize_cookienames() {
    COOKIE_NAMES = {
        mapTypeId: COOKIE_PREFIX + '_mapTypeId',
        dnote: COOKIE_PREFIX + '_dnote',
        pnote: COOKIE_PREFIX + '_pnote',
        anote: COOKIE_PREFIX + '_anote',
        pbubble: COOKIE_PREFIX + '_pbubble',
        abubble: COOKIE_PREFIX + '_abubble',
        dbubble: COOKIE_PREFIX + '_dbubble',
        platOutlines: COOKIE_PREFIX + '_platOutlines',
        follow: COOKIE_PREFIX + '_follow',
        zoom: COOKIE_PREFIX + '_zoom',
        center_latitude: COOKIE_PREFIX + '_center_latitude',
        center_longitude: COOKIE_PREFIX + '_center_longitude',
        wbubble: COOKIE_PREFIX + '_wbubble',
        swath: COOKIE_PREFIX + '_swath',
        activePlatName: COOKIE_PREFIX + '_activePlatName',
        dspStabClass: COOKIE_PREFIX + '_dspStabClass',
        dspExportClass: COOKIE_PREFIX + '_dspExportClass',
        weather: COOKIE_PREFIX + '_weather'
    };
}

function initialize_plats() {
    if (!CNSNT.hasOwnProperty("provider")) {
        CNSNT.provider = "google"
    }
    if (!CNSNT.hasOwnProperty("provider_gpsconvert")) {
        CNSNT.provider_gpsconvert = false;
    }

    try {
        var plname, plobj, rect;
        if (PLATOBJS) {
            for (plname in PLATOBJS) {
                plobj = PLATOBJS[plname];
                rect = newRectangle(plobj.minlng, plobj.maxlng, plobj.minlat, plobj.maxlat);
                attachPlatListener(rect, plname);
                plobj.rect = rect;
                plobj.hlite = false;
                plobj.active = false;
                plobj.go = null;
                plobj.go_listener = null;
            }
        }
    } catch( ex) {
        
    }
}

function show_plat_outlines() {
    var plname, plobj, rect;
    if (PLATOBJS) {
        for (plname in PLATOBJS) {
            plobj = PLATOBJS[plname];
            plobj.rect.setMap(CSTATE.map);
        }
    }
}

function hide_plat_outlines() {
    var plname, plobj, rect;
    if (PLATOBJS) {
        for (plname in PLATOBJS) {
            plobj = PLATOBJS[plname];
            switch(CNSNT.provider) {
                case "google":
                    plobj.rect.setMap(null);
                    break;
                case "baidu":
                    break;
            }
            if (plobj.go_listener !== null) {
                removeGoListener(plobj);
            }
        }
    }
}

function initialize(winH, winW) {
    if (init_vars) {
        init_vars();
    }
    if (!CNSNT.hasOwnProperty("provider")) {
        CNSNT.provider = "google";
    }
    if (!CNSNT.hasOwnProperty("provider_gpsconvert")) {
        CNSNT.provider_gpsconvert = false;
    }
    //secure ping (to assure browsers can see secure site)
    $("#id_content_spacer").html('<img src="' + CNSNT.resturl + '/pimg' + '"/>');
    
    //CNSNT.prime_view = true;
    
    initialize_cookienames();
    if (CNSNT.provider === "google") {
        initialize_plats();
    }

    initialize_gdu();
    //get_ticket(initialize_gdu);
}

function showStream() {
    var modalChrome, hdr, body, footer, c1array, c2array;
    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 30%; text-align: right;"');
    c2array.push('style="border-style: none; width: 70%;"');
    c1array.push('<img class="stream-ok" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.stream_ok + '</h4>');
    c1array.push('<img class="stream-warning" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.stream_warning + '</h4>');
    c1array.push('<img class="stream-failed" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.stream_failed + '</h4>');
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 30%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.stream_title + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
}

function showGps() {
    var modalChrome, hdr, body, footer, c1array, c2array;
    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 30%; text-align: right;"');
    c2array.push('style="border-style: none; width: 70%;"');
    c1array.push('<img class="gps-ok" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.gps_ok + '</h4>');
    c1array.push('<img class="gps-warning" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.gps_warning + '</h4>');
    c1array.push('<img class="gps-failed" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.gps_failed + '</h4>');
    c1array.push('<img class="gps-uninstalled" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.gps_uninstalled + '</h4>');
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 30%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.gps_title + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
}

function showWs() {
    var modalChrome, hdr, body, footer, c1array, c2array;
    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 30%; text-align: right;"');
    c2array.push('style="border-style: none; width: 70%;"');
    c1array.push('<img class="ws-ok" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.ws_ok + '</h4>');
    c1array.push('<img class="ws-failed" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.ws_failed + '</h4>');
    c1array.push('<img class="ws-uninstalled" src="' + CNSNT.spacer_gif + '" />');
    c2array.push('<h4>' + P3TXT.ws_uninstalled + '</h4>');
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 30%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.ws_title + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);
}

var bar = ['<div id="id_cavity_p_bar" class="progress progress-danger" style="position:relative; top:9px">' +
           '<div id="id_cavity_p_prog" class="bar" style="width:100%;"><span id="id_cavity_p_val" class="ui-label"><b>?</b></span></div>' +
           '</div>',
           '<div id="id_cavity_t_bar" class="progress progress-danger" style="position:relative; top:9px">' +
           '<div id="id_cavity_t_prog" class="bar" style="width:100%;"><span id="id_cavity_t_val" class="ui-label"><b>?</b></span></div>' +
           '</div>', 
           '<div id="id_wb_t_bar" class="progress progress-danger" style="position:relative; top:9px">' +
          '<div id="id_wb_t_prog" class="bar" style="width:100%;"><span id="id_wb_t_val" class="ui-label"><b>?</b></span></div>' +
          '</div>'];
        
function updateBar(id_sp, id_val, id_prog, id_bar, sp, val) {
    var unit, prog, barClass;
    if (sp !== null) {
        barClass = "progress progress-success";
        if (id_sp ==  '#id_cavity_p_sp') {
            unit = 'Torr';
            if (Math.abs(val-sp) > 5.0) {
                barClass = "progress progress-warning";
            }
            prog = 100.0*Math.exp(-Math.abs(0.05*(val-sp)/5.0));
        } else {
            unit = 'C';
            if (Math.abs(val-sp) > 0.3) {
                barClass = "progress progress-warning";
            }
            prog = 100.0*Math.exp(-Math.abs(0.05*(val-sp)/0.3));
        }
        $(id_sp).html("<h5>" + sp.toFixed(1) + " " + unit + "</h5>");
        $(id_val).html("<b>" + val.toFixed(1) + "</b>");
        $(id_prog).css("width", prog + "%");
        $(id_bar).attr("class", barClass);
    } else {
        $(id_sp).html("<h5></h5>");
        $(id_val).html("<b>?</b>");
        $(id_prog).css("width", "100%");
        $(id_bar).attr("class", "progress progress-danger");
    }    
}

function updateProgress() {
    var cavity_p_val, cavity_p_sp, cavity_t_val, cavity_t_sp, wb_t_val, wb_t_sp;
    if (!CSTATE.getting_warming_status) {
        CSTATE.getting_warming_status = true;
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "getWarmingState", "args": "[]"},
            function (data, ts, jqXHR) {
                if (data.result.value !== undefined) {
                    cavity_p_val = data.result.value['CavityPressure'][0];
                    cavity_p_sp = data.result.value['CavityPressure'][1];
                    cavity_t_val = data.result.value['CavityTemperature'][0];
                    cavity_t_sp = data.result.value['CavityTemperature'][1];
                    wb_t_val = data.result.value['WarmBoxTemperature'][0];
                    wb_t_sp = data.result.value['WarmBoxTemperature'][1];
                    updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", cavity_p_sp, cavity_p_val);
                    updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", cavity_t_sp, cavity_t_val);
                    updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", wb_t_sp, wb_t_val);
                } else {
                    updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", null, 0.0);
                    updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", null, 0.0);
                    updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", null, 0.0);
                }
                CSTATE.getting_warming_status = false;
            },
            function (jqXHR, ts, et) {
                $("#errors").html(jqXHR.responseText);
                updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", null, 0.0);
                updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", null, 0.0);
                updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", null, 0.0);
                CSTATE.getting_warming_status = false;
            }
            );
    }
    if (!CSTATE.end_warming_status){
        TIMER.progress = setTimeout(updateProgress, CNSNT.progressUpdatePeriod);
    }
}
    
function showAnalyzer() {
    var modalChrome, hdr, body, footer, c1array, c2array, c3array;

    c1array = [];
    c2array = [];
    c3array = [];
    c1array.push('style="border-style: none; width: 40%; text-align: right;"');
    c2array.push('style="border-style: none; width: 40%; "');
    c3array.push('style="border-style: none; width: 20%; text-align: left;"');

    c1array.push('<h4>' + P3TXT.cavity_p + '</h4>');
    c2array.push(bar[0]);
    c3array.push('<span id="id_cavity_p_sp"><h5></h5></span>');

    c1array.push('<h4>' + P3TXT.cavity_t + '</h4>');
    c2array.push(bar[1]);
    c3array.push('<span id="id_cavity_t_sp"><h5></h5></span>');

    c1array.push('<h4>' + P3TXT.wb_t + '</h4>');
    c2array.push(bar[2]);
    c3array.push('<span id="id_wb_t_sp"><h5></h5></span>');
    body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array, c3array);

    c1array = [];
    c2array = [];
    c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 30%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.analyzer_title + '</h3>');
    c2array.push(HBTN.modChangeCloseBtn);
    hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    footer = '';
    
    modalChrome = setModalChrome(
        hdr,
        body,
        footer
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_modal_span").css("z-index", 9999);

    if (TIMER.progress === null || TIMER.progress === undefined) {
        CSTATE.end_warming_status = false;
        updateProgress();
    }
}

function setupRadioControlGroup(params)
{
    var result = '';
    result += '<div class="control-group" id="' + params.control_group_id + '">';
    result += '<label class="control-label" for="' + params.control_div_id + '">';
    result += params.label + '</label>';
    result += '<div class="controls">';
    result += '<div id="' + params.control_div_id + '" class="btn-group" data-toggle="buttons-radio">';
    $.each(params.buttons, function (i, v) {
        result += '<button id="' + v.id + '" type="button" class="btn btn-large">' + v.caption + '</button>';
    });
    result += '</div></div></div>';
    return result;
}

function makeWeatherForm(resultFunc, init) {
    /* Makes a weather selection form in the modal box "id_weather". There are currently three questions, where the
     * second question depends on the first
     * 
     * Day (0) or Night (1)
     * If Day:   Weak sunlight (0), moderate sunlight (1) or strong sunlight (2)
     * If Night: <50% cloud cover (0), >50% cloud cover (1)
     * Calm (0), light wind (1) or strong wind (2)
     * 
     * The user selects the appropriate options, and the result is returned as a 3 element array. 
     * e.g. [0,1,2] = Day, moderate sunlight, strong wind
     *      [1,0,1] = Night, <50% cloud cover, light wind
     * 
     * The initial settings of the buttons in the form can be specified using init, which must be a valid 
     *  3-element array
     *  
     * After a successful selection has been made, the function "resultFunc" is called. This function has a
     * single parameter which is the 3-element array of the selections. 
     *  */
    var weatherFormTemplate = [{label: "<h4>" + P3TXT.survey_time + "</h4>",
        control_div_id: "id_day_night", 
        control_group_id: "id_day_night_group",
        buttons: [{id: "id_day", caption: P3TXT.day},
                  {id: "id_night", caption: P3TXT.night}]},
       {label: "<h4>" + P3TXT.sunlight + "</h4>",
        control_div_id: "id_sunlight",
        control_group_id: "id_sunlight_group",
        buttons: [{id: "id_overcast_sunlight", caption: P3TXT.overcast_sunlight },
                  {id: "id_moderate_sunlight", caption: P3TXT.moderate_sunlight },
                  {id: "id_strong_sunlight", caption: P3TXT.strong_sunlight }]},
       {label: "<h4>" + P3TXT.cloud + "</h4>",
        control_div_id: "id_cloud",
        control_group_id: "id_cloud_group",
        buttons: [{id: "id_less50_cloud", caption: P3TXT.less50_cloud },
                  {id: "id_more50_cloud", caption: P3TXT.more50_cloud }]},
       {label: "<h4>Wind</h4>",
        control_div_id: "id_wind",
        control_group_id: "id_wind_group",
        buttons: [{id: "id_calm_wind", caption: P3TXT.calm_wind },
                  {id: "id_light_wind", caption: P3TXT.light_wind },
                  {id: "id_strong_wind", caption: P3TXT.strong_wind }]}];                              

    function addError(field_id, message) {
        var id = "#" + field_id;
        if ($(id).next('.help-inline').length === 0) {
            $(id).after('<span class="help-inline">' + message + '</span>');
            $(id).parents("div .control-group").addClass("error");
        }
        $(id).on('focus keypress click', function () {
            $(this).next('.help-inline').fadeOut("fast", function () {
                $(this).remove();
            });
            $(this).parents('.control-group').removeClass('error');
        });
    }
    
    function getSelected(field_id) {
        var selection = [];
        var id = "#" + field_id;
        $(id).find("button").each(function (i) {
            if ($(this).hasClass("active")) selection.push(i);
        });
        if (selection.length === 0) {
            addError(field_id,P3TXT.choose);
        }
        return selection;
    }
    
    var modalChrome, header, body, footer, c1array, c2array;
    c1array = []; c2array = [];
    c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    c1array.push('<h3>' + P3TXT.select_weather + '</h3>');
    c2array.push(HBTN.weatherFormOkBtn);
    header = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    body = '<form id="id_weather_form" class="form-horizontal"><fieldset>';
    $.each(weatherFormTemplate, function (i, v) {
        body += setupRadioControlGroup(v);
    });
    body += '</fieldset></form>';
    footer = '';

    modalChrome = '<div class="modal-header">' + header + '</div>';
    modalChrome += '<div class="modal-body">' + body + '</div>';
    modalChrome += '<div class="modal-footer">' + footer +'</div>';
    
    $("#id_weather").html(modalChrome);
    $("#id_weather").modal({show: true, backdrop: "static", keyboard: false});
    
    if (undefined !== init) {
        $("#"+weatherFormTemplate[0].buttons[init[0]].id).button("toggle");
        switch (init[0]) {
        case 0:
            $("#"+weatherFormTemplate[1].buttons[init[1]].id).button("toggle");
            $("#id_sunlight_group").removeClass("hide");
            $("#id_cloud_group").addClass("hide");
            break;
        case 1:
            $("#"+weatherFormTemplate[2].buttons[init[1]].id).button("toggle");
            $("#id_sunlight_group").addClass("hide");
            $("#id_cloud_group").removeClass("hide");        
            break;
        }
        $("#"+weatherFormTemplate[3].buttons[init[2]].id).button("toggle");        
    }
    
    $("#id_day").on("click", function (e) {
        $("#id_sunlight_group").removeClass("hide");
        $("#id_cloud_group").addClass("hide");
    });
    $("#id_night").on("click", function (e) {
        $("#id_sunlight_group").addClass("hide");
        $("#id_cloud_group").removeClass("hide");        
    });
    $("#id_weatherFormOkBtn").on("click", function (e) {
        var c, s, result = [];
        var dn = getSelected("id_day_night");
        var w  = getSelected("id_wind");
        
        if (dn.length > 0) {
            result.push(dn[0]);
            if (dn[0] === 0) { // Day selected
                s = getSelected("id_sunlight");
                if (s.length > 0) result.push(s[0]);
            }
            else {  // Night selected
                c = getSelected("id_cloud");
                if (c.length > 0) result.push(c[0]);
            }
        }
        if (w.length > 0) result.push(w[0]);

        if (result.length === 3) {
            $("#id_weather").modal("hide").html("");            
            if (undefined !== resultFunc) resultFunc(result);
        }
    });
}
