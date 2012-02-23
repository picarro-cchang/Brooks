//default (eng) values for dsp.  Override this 
//for each language specific labels
var TXT = {
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
        anz_cntls: 'Analyzer Controls',
        restart_log: 'Restart Log',
        switch_to_cptr: 'Switch to Capture Mode',
        cancl_cptr: 'Cancel Capture',
        calibrate: 'Calibrate',
        shutdown: 'Shutdown Analyzer',
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
        prime_conf_msg: 'Do you want to switch to Prime View Mode? \n\nWhen the browser is in Prime View Mode, you will have control of the Analyzer.',
        change_min_amp: 'Change Minimum Amplitude',
        restart_datalog_msg: 'Close current data log and open a new one?',
        shutdown_anz_msg: 'Do you want to shut down the Analyzer? \n\nWhen the analyzer is shutdown it can take 30 to 45 minutes warm up.',
        cancel_cap_msg: 'Cancel capture and return to survey mode?',
        show_controls: 'Show Controls',
        show_dnote: 'Show route annotations',
        show_pnote: 'Show peak annotations',
        show_anote: 'Show analysis annotations',
        click_show_cntls: 'Click to show controls',
        controls: 'Controls',
        dnote: 'Route annotation',
        anote: 'Analysis annotation',
        pnote: 'Peak annotation',
        show_notes: 'Show user annotations on map',
        abubble: 'Analysis markers',
        pbubble: 'Peak markers',
        wbubble: 'Wind markers',
        swath: 'Swath',
        show_markers: 'Show system markers on map',
        show_txt: 'Show',
        hide_txt: 'Hide'
    };

//Html button
var HBTN = {
        exptLogBtn: '<div><button id="id_exptLogBtn" type="button" onclick="exportLog();" class="btn primary large">' + TXT.download_concs + '</button></div>',
        exptPeakBtn: '<div><button id="id_exptPeakBtn" type="button" onclick="exportPeaks();" class="btn primary large">' + TXT.download_peaks + '</button></div>',
        restartBtn: '<div><button id="id_restartBtn" type="button" onclick="restart_datalog();" class="btn primary large">' + TXT.restart_log + '</button></div>',
        captureBtn: '<div><button id="id_captureBtn" type="button" onclick="captureSwitch();" class="btn primary large">' + TXT.switch_to_cptr + '</button></div>',
        cancelCapBtn: '<div><button id="id_cancelCapBtn" type="button" onclick="cancelCapSwitch();" class="btn primary large">' + TXT.cancl_cptr + '</button></div>',
        calibrateBtn: '<div><button id="id_calibrateBtn" type="button" onclick="injectCal();" class="btn primary large">' + TXT.calibrate + '</button></div>',
        shutdownBtn: '<div><button id="id_shutdownBtn" type="button" onclick="shutdown_analyzer();" class="btn red large">' + TXT.shutdown + '</button></div>',
        downloadBtn: '<div><button id="id_downloadBtn" type="button" onclick="exportControls();" class="btn primary large">' + TXT.download_files + '</button></div>',
        analyzerCntlBtn: '<div><button id="id_analyzerCntlBtn" type="button" onclick="primeControls();" class="btn primary large">' + TXT.anz_cntls + '</button></div>',
        warningCloseBtn: '<div><button id="id_warningCloseBtn" onclick="restoreModalDiv();" class="btn primary large">' + TXT.close + '</button></div>',
        modChangeCloseBtn: '<div><button id="id_modChangeCloseBtn" onclick="restoreModChangeDiv();" class="btn primary large">' + TXT.close + '</button></div>',
        switchLogBtn: '<div><button id="id_switchLogBtn" onclick="switchLog();" class="btn primary large">' + TXT.select_log + '</button></div>',
        switchToPrimeBtn: '<div><button id="id_switchToPrimeBtn" onclick="switchToPrime();" class="btn primary large">' + TXT.switch_to_prime + '</button></div>',
        cancelModalBtn: '<div><button id="id_cancelModalBtn" onclick="restoreModChangeDiv();" class="btn primary large">' + TXT.cancel + '</button></div>',
        changeMinAmpCancelBtn: '<div><button id="id_changeMinAmpCancelBtn" onclick="changeMinAmpVal(false);" class="btn primary large">' + TXT.cancel + '</button></div>',
        changeMinAmpOkBtn: '<div><button id="id_changeMinAmpOkBtn" onclick="changeMinAmpVal(true);" class="btn primary large">' + TXT.ok + '</button></div>',
        changeMinAmpOkHidBtn: '<div style="display: hidden;"><button id="id_changeMinAmpOkHidBtn" onclick="changeMinAmpVal(true);"/></div>'
    };


// List of Html buttons (<li>....</li><li>....</li>...)
var LBTNS = {
        downloadBtns: '<li>' + HBTN.downloadBtn + '</li>',
        analyzerCntlBtns: '<li>' + HBTN.analyzerCntlBtn + '</li>',
        exptBtns: '<li>' + HBTN.exptLogBtn + '</li><br/><li>' + HBTN.exptPeakBtn + '</li>'
    };

// Fixed HTML pane
var HPANE = {
        modalNetWarning: setModalChrome('<h3>' + TXT.conn_warning_hdr + '</h3>',
                '<p><h3>' + TXT.conn_warning_txt + '</h3></p>',
                HBTN.warningCloseBtn
                )
    };

//Constant Values
var CNSNT = {
        // initial "|" is expected with no trailing "|"
        peak_bbl_clr: "|40FFFF|000000",
        analysis_bbl_clr: "|FF8080|000000",
        path_bbl_clr: "|FFFF90|000000",

        // trailing "|" is expected
        peak_bbl_tail: "bb|", // tail bottom left
        analysis_bbl_tail: "bb|",  // tail bottom left
        path_bbl_tail: "bbtl|", // tail top left

        peak_bbl_anchor: newPoint(0, 42), //d_bubble_text_small is 42px high 
        analysis_bbl_anchor: newPoint(0, 42), //d_bubble_text_small is 42px high
        path_bbl_anchor: newPoint(0, 0),

        peak_bbl_origin: newPoint(0, 0),
        analysis_bbl_origin: newPoint(0, 0),
        path_bbl_origin: newPoint(0, 0),

        normal_path_color: "#0000FF",
        analyze_path_color: "#000000",
        streamwarning:  (1000 * 10),
        streamerror:  (1000 * 30),

        histMax: 200,
        datUpdatePeriod: 500,
        peakUpdatePeriod: 500,
        analysisUpdatePeriod: 500,
        windUpdatePeriod: 500,
        noteUpdatePeriod: 1500,
        hmargin: 25,
        vmargin: 0,

        peakNoteList: ['amp', 'ch4', 'sigma', 'lat', 'lon'],
        analysisNoteList: ['conc', 'delta', 'uncertainty', 'lat', 'lon'],
        datNoteList: ['ch4', 'lat', 'lon'],

        gmt_offset: get_time_zone_offset(),

        svcurl: "/rest",
        callbacktest_url: "",
        annotation_url: undefined,

        prime_view: true,
        log_sel_opts: [],
        analyzer_name: "",
        user_id: "",

        mapControl: undefined,
        mapControlDiv: undefined,

        earthRadius: 6378100,
        swath_color: "#0000CC", 
        swath_opacity: 0.3,
        
        dtr : Math.PI/180.0,    // Degrees to radians
        rtd : 180.0/Math.PI,    // Radians to degrees
        
        cookie_duration: 14
    };

// Current State
var CSTATE = {
        net_abort_count: 0,
        follow: true,
        prime_available: false,
        prime_test_count: 0,
        green_on: false,

        resize_map_inprocess: false,
        current_mode: 0,
        getting_mode: false,

        current_zoom: undefined,
        current_mapTypeId: undefined,

        center_lon: -121.98432,
        center_lat: 37.39604,

        minAmp: 0.1,
        alog: "",

        showDnote: true,
        showPnote: true,
        showAnote: true,
        showPbubble: true,
        showAbubble: true,
        showWbubble: true,
        showSwath: false,

        lastwhere: '',
        lastFit: '',
        lastInst: '',
        lastTimestring: '',
        lastDataFilename: '',
        lastPeakFilename: '',
        lastAnalysisFilename: '',
        laststreamtime: new Date().getTime(),

        counter: 0,
        leakLine: 1,
        clearLeaks: false,
        analysisLine: 1,
        clearAnalyses: false,
        windLine: 1,
        clearWind: false,
        startNewPath: true,
        nextAnalysisEtm: 0.0,
        nextPeakEtm: 0.0,
        nextDatEtm: 0.0,
        nextAnalysisUtm: 0.0,
        nextPeakUtm: 0.0,
        nextDatUtm: 0.0,
        startPos: null,

        ignoreTimer: false,
        ignoreRequests: false,

        path: null,
        map: undefined,
        marker: null,
        gglOptions: null,
        peakMarkers: {},
        analysisMarkers: {},
        windMarkers: {},
        methaneHistory: [],

        peakNoteMarkers: {},
        peakNoteDict: {},
        peakNoteListener: {},
        peakBblListener: {},

        analysisNoteMarkers: {},
        analysisNoteDict: {},
        analysisNoteListener: {},
        analysisBblListener: {},

        datNoteMarkers: {},
        datNoteDict: {},
        datNoteListener: {},

        // the following help specify the polygon which represents
        //  the effective map area associated with the path
        swathPolys : [],
        lastMeasPathLoc: null,
        lastMeasPathDeltaLat: null,
        lastMeasPathDeltaLon: null,
        
        pobj: [],

        noteSortSel: undefined,
    };

var TIMER = {
        prime: null,
        resize: null,
        data: null, // timer for getData
        dnote: null, // timer for getDatNotes
        peak: null, // timer for showLeaks (getPeaks)
        pnote: null, // timer for getPeakNotes
        analysis: null, // timer for showAnalysis (getAnalysis)
        anote: null, // timer for getAnalysisNotes
        wind: null, // timer for showWind (getPeaks)
    };

var modeStrings = {0: TXT.survey_mode, 1: TXT.capture_mode, 2: TXT.capture_mode, 3: TXT.analyzing_mode};
var modeBtn = {0: [HBTN.captureBtn],  1: [HBTN.cancelCapBtn], 2: [HBTN.cancelCapBtn], 3: []};

function newMap(canvas) {
    return new google.maps.Map(canvas, CSTATE.gglOptions);
    // return new Microsoft.Maps.Map(canvas, CSTATE.bingOptions); 
}
function newLatLng(lat, lng) {
    return new google.maps.LatLng(lat, lng);
    // return new Microsoft.Maps.Location(lat, lng);
}

function newPolyline(map, clr) {
    var pl = new google.maps.Polyline(
        {path: new google.maps.MVCArray(),
            strokeColor: clr,
            strokeOpactity: 1.0,
            strokeWeight: 2}
    );
    pl.setMap(map);
    return pl;

    // var pl = new Microsoft.Maps.Polyline([], {strokeColor: clr, strokeThickness: 2, });
    // map.entities.push(pl);
    // return pl;
}

function newPolygonWithoutOutline(map, clr, opacity, vertices, visible) {
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
}

function pushToPath(path, where) {
    path.getPath().push(where);
    // var locs = path.getLocations();
    // locs.push(where);
    // path.setLocations();
}

function newPoint(x, y) {
    return new google.maps.Point(x, y);
    // return new Microsoft.Maps.Point(x, y);
}

function newAnzLocationMarker(map) {
    var mk = new google.maps.Marker({position: map.getCenter(), visible: false});
    mk.setMap(map);
    return mk;
    // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null); 
    // map.entities.push(mk);
    // return mk;
}

function newPeakMarker(map, latLng, amp, sigma, ch4) {
    var size, fontsize, mk;
    size = Math.pow(amp, 1.0 / 4.0);
    fontsize = 20.0 * Math.pow(amp, 1.0 / 4.0);
    mk = new google.maps.Marker({position: latLng,
        title: TXT.amp + ": " + amp.toFixed(2) + " " + TXT.sigma + ": " + sigma.toFixed(1),
        icon: "http://chart.apis.google.com/chart?chst=d_map_spin&chld=" + size + "|0|40FFFF|" + fontsize + "|b|" + ch4.toFixed(1)
        });
    mk.setMap(map);
    mk.setMap(map);
    return mk;
    // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null); 
    // map.entities.push(mk);
    // return mk;
}

function newWindMarker(map, latLng, speed, dir, dirSdev) {
    var wr, wedge;
    wedge = makeWindWedge(20.0*speed,dir,2*dirSdev);
    wr = new google.maps.Marker({position: latLng, icon: new google.maps.MarkerImage(wedge.url,null,null,newPoint(wedge.radius,wedge.radius)),zIndex:0});
    wr.setMap(map);
    return wr;
}

function newAnalysisMarker(map, latLng, delta, uncertainty) {
    var result, mk;
    result = delta.toFixed(1) + " +/- " + uncertainty.toFixed(1);
    result = result.replace("+", "%2B").replace(" ", "+");
    mk = new google.maps.Marker({position: latLng,
        icon: new google.maps.MarkerImage(
            "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=bbtl|" + result + CNSNT.analysis_bbl_clr,
            null,
            null,
            newPoint(0, 0)
        )}
        );
    mk.setMap(map);
    return mk;
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
    mkrUrlFrag = "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=" + mkrBbl + pathTxt + mkrClr;
    micon = new google.maps.MarkerImage(
        mkrUrlFrag,
        null,
        mkrOrigin,
        mkrAnchor
    );
    mkr.setIcon(micon);
}

function removeListener(handle) {
    google.maps.event.removeListener(handle);
}

function clearPeakMarkerArray() {
    var i, ky;
    CSTATE.peakNoteDict = {};
    for (i = 0; i < CSTATE.peakMarkers.length; i += 1) {
        CSTATE.peakMarkers[i].setMap(null);
    }
    for (ky in CSTATE.peakBblListener) {
        removeListener(CSTATE.peakBblListener[ky]);
    }
    CSTATE.peakMarkers = [];
    CSTATE.peakBblListener = {};
    CSTATE.leakLine = 1;
    CSTATE.clearLeaks = true;
}

function clearAnalysisMarkerArray() {
    var i, ky;
    CSTATE.analysisNoteDict = {};
    for (i = 0; i < CSTATE.analysisMarkers.length; i += 1) {
        CSTATE.analysisMarkers[i].setMap(null);
    }
    for (ky in CSTATE.analysisBblListener) {
        removeListener(CSTATE.analysisBblListener[ky]);
    }
    CSTATE.analysisMarkers = [];
    CSTATE.analysisBblListener = {};
    CSTATE.analysisLine = 1;
    CSTATE.clearAnalyses = true;
}

function clearWindMarkerArray() {
    var i;
    for (i = 0; i < CSTATE.windMarkers.length; i += 1) {
        CSTATE.windMarkers[i].setMap(null);
    }
    CSTATE.windMarkers = [];
    CSTATE.windLine = 1;
    CSTATE.clearWind = true;
}

function clearDatNoteMarkers(emptyTheDict) {
    var ky;
    for (ky in CSTATE.datNoteMarkers) {
        CSTATE.datNoteMarkers[ky].setMap(null);
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
    for (ky in CSTATE.analysisNoteMarkers) {
        CSTATE.analysisNoteMarkers[ky].setMap(null);
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
    for (ky in CSTATE.peakNoteMarkers) {
        CSTATE.peakNoteMarkers[ky].setMap(null);
    }
    for (ky in CSTATE.peakNoteListener) {
        removeListener(CSTATE.peakNoteListener[ky]);
    }
    CSTATE.peakNoteMarkers = {};
    CSTATE.peakNoteListener = {};
    CSTATE.nextPeakEtm = 0.0;
    CSTATE.nextPeakUtm = 0.0;
}

function showSwath() {
    var i;
    for (i=0;i<CSTATE.swathPolys.length;i++) CSTATE.swathPolys[i].setVisible(true);
}

function hideSwath() {
    var i;
    for (i=0;i<CSTATE.swathPolys.length;i++) CSTATE.swathPolys[i].setVisible(false);
}

function resetLeakPosition() {
    clearPeakMarkerArray();
    clearAnalysisMarkerArray();
    clearWindMarkerArray();
}

function timeStringFromEtm(etm) {
    var gmtoffset_mil, etm_mil, tmil, tdate, tstring;
    etm_mil = (etm * 1000);
    tdate = new Date(etm_mil);
    tstring = tdate.toLocaleDateString() + " " + tdate.toLocaleTimeString();
    return tstring;
}

function setCookie(name, value, days) {
    var date, expires;

    if (days) {
        date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires = " + date.toGMTString();
    } else {
        expires = "";
    }
    document.cookie = name + "=" + value + expires + "; path=/";
}

function getCookie(name) {
    var nameEQ, ca, i, c;

    nameEQ = name + "=";
    ca = document.cookie.split(';');
    for (i = 0; i < ca.length; i += 1) {
        c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1, c.length);
        }
        if (c.indexOf(nameEQ) === 0) {
            return c.substring(nameEQ.length, c.length);
        }
    }
    return null;
}

function deleteCookie(name) {
    setCookie(name, "", -1);
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
    controlUI.title = TXT.click_show_cntls;
    controlDiv.appendChild(controlUI);

    // Set CSS for the control interior.
    controlText = document.createElement('DIV');
    controlText.style.fontFamily = 'Arial,sans-serif';
    controlText.style.fontSize = '12px';
    controlText.style.paddingLeft = '4px';
    controlText.style.paddingRight = '4px';
    controlText.innerHTML = TXT.controls;
    controlUI.appendChild(controlText);

    google.maps.event.addDomListener(controlUI, 'click', function () {
        controlPane();
    });
}

function initialize_map() {
    var where;

    CSTATE.map = newMap(document.getElementById("map_canvas"));

    CNSNT.mapControlDiv = document.createElement('DIV');
    CNSNT.mapControl = new MapControl(CNSNT.mapControlDiv, CSTATE.map);

    CNSNT.mapControlDiv.index = 1;
    CSTATE.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(CNSNT.mapControlDiv);

    google.maps.event.addListener(CSTATE.map, 'center_changed', function () {
        where = CSTATE.map.getCenter();
        CSTATE.center_lat = where.lat();
        CSTATE.center_lon = where.lng();
        setCookie("pcubed_center_latitude", CSTATE.center_lat, CNSNT.cookie_duration);
        setCookie("pcubed_center_longitude", CSTATE.center_lon, CNSNT.cookie_duration);
        $("#center_latitude").val(where.lat());
        $("#center_longitude").val(where.lng());
    });
    google.maps.event.addListener(CSTATE.map, 'zoom_changed', function () {
        CSTATE.current_zoom = CSTATE.map.getZoom();
        setCookie("pcubed_zoom", CSTATE.current_zoom, CNSNT.cookie_duration);
    });
    google.maps.event.addListener(CSTATE.map, 'maptypeid_changed', function () {
        CSTATE.current_mapTypeId = CSTATE.map.getMapTypeId();
        setCookie("pcubed_mapTypeId", CSTATE.current_mapTypeId, CNSNT.cookie_duration);
    });
    CSTATE.path = newPolyline(CSTATE.map, CNSNT.normal_path_color);
    CSTATE.swathPolys = []
    CSTATE.lastMeasPathLoc = null;
    CSTATE.lastMeasPathDeltaLat = null;
    CSTATE.lastMeasPathDeltaLon = null;

    google.maps.event.addListener(CSTATE.path, 'click', function (event) {
        var newhash, closepobjs, i, pobj;
        newhash = encodeGeoHash(event.latLng.lat(), event.latLng.lng());
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

    if (CSTATE.marker) {
        CSTATE.marker.setMap(null);
    }
    CSTATE.marker = newAnzLocationMarker(CSTATE.map);
    
    // Hardwire PG&E plats for display
    var bounds, overlay;
    bounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(37.9181,-122.0662),
        new google.maps.LatLng(37.9275,-122.0584));
    overlay = new google.maps.GroundOverlay("static/45C16.jpg",bounds)
    overlay.setMap(CSTATE.map);
    bounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(37.8901,-122.1272),
        new google.maps.LatLng(37.8995,-122.1197));
    overlay = new google.maps.GroundOverlay("static/45F08.jpg",bounds)
    overlay.setMap(CSTATE.map);
};

function resize_map() {
    var pge_wdth, hgth_top, lpge_wdth, new_width, new_height, new_top, cen;
    pge_wdth = $('#id_topbar').width();
    hgth_top = $('#id_topbar').height() + $('#id_feedback').height() + $('#id_content_title').height();
    lpge_wdth = $('#id_sidebar').width();

    new_width = pge_wdth - CNSNT.hmargin;
    new_height = winH - hgth_top - CNSNT.hmargin - 40;
    new_top = hgth_top + CNSNT.vmargin;

    $("#id_modal_span").css('position', 'absolute');
    $("#id_modal_span").css('top', hgth_top);
    if (new_width < 640) {
        new_top = new_top + 30;
        new_height = new_height - 30;
        $("#id_modal_span").css('left', CNSNT.hmargin);
    } else {
        $("#id_modal_span").css('left', lpge_wdth + CNSNT.hmargin);
    }

    $("#id_side_modal_span").css('position', 'absolute');
    $("#id_side_modal_span").css('top', hgth_top);
    new_top = new_top + 30;
    new_height = new_height - 30;
    $("#id_side_modal_span").css('left', CNSNT.hmargin);

    $('#map_canvas').css('position', 'absolute');
    $('#map_canvas').css('left', lpge_wdth + CNSNT.hmargin);
    $('#map_canvas').css('top', new_top);
    $('#map_canvas').css('height', new_height);
    $('#map_canvas').css('width', new_width);
    $('#id_feedback').css('width', new_width);

    if (CSTATE.map) {
        cen = CSTATE.map.getCenter();
        google.maps.event.trigger(CSTATE.map, 'resize');
        CSTATE.map.setCenter(cen);
    }

    CSTATE.resize_map_inprocess = false;
}

function resize_page() {
    if (!CSTATE.resize_map_inprocess) {
        CSTATE.resize_map_inprocess = true;
        TIMER.resize = setTimeout(resize_map, 25);
    }
}



function setModalChrome(hdr, msg, click) {
    var modalChrome = "";

    modalChrome = '<div class="modal" style="position: relative; top: auto; left: auto; margin: 0 auto; z-index: 1">';
    modalChrome += '<div class="modal-header">';
    modalChrome += '<h3>' + hdr + '</h3>';
    modalChrome += '</div>';
    modalChrome += '<div class="modal-body">';
    modalChrome += msg;
    modalChrome += '</div>';
    modalChrome += '<div class="modal-footer">';
    modalChrome += click;
    modalChrome += '</div>';
    modalChrome += '</div>';

    return modalChrome;
}

function primeControls() {
    var capOrCan, i, modalChrome;

    capOrCan = "";
    for (i = 0; i < modeBtn[CSTATE.current_mode].length; i += 1) {
        capOrCan += modeBtn[CSTATE.current_mode][i] + "<br/>";
    }

    modalChrome = setModalChrome('<h3>' + TXT.anz_cntls + '</h3>',
        HBTN.restartBtn + "<br/>" +
        capOrCan +
        HBTN.calibrateBtn +
        "<br/><br/><br/>" + HBTN.shutdownBtn + "<br/>",
        HBTN.modChangeCloseBtn
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_restartBtn").focus();
}

function exportControls() {
    var modalChrome, exportBtns;
    exportBtns = '<ul class="inputs-list">' + LBTNS.exptBtns + '</ul><br/>';

    modalChrome = setModalChrome('<h3>' + TXT.download_files + '</h3>',
        exportBtns,
        HBTN.modChangeCloseBtn
        );

    $("#id_mod_change").html(modalChrome);
    $("#id_restartBtn").focus();
}

function exportLog() {
    var url = CNSNT.svcurl + '/sendLog?alog=' + CSTATE.alog;

    window.location = url;
}

function exportPeaks() {
    var apath, url;

    apath = CSTATE.alog.replace(".dat", ".peaks");
    url = CNSNT.svcurl + '/sendLog?alog=' + apath;

    window.location = url;
}

function selectLog() {
    var options, i, len, row, selected, opendiv, closediv, btns, modalChangeMinAmp;

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

    opendiv = "<div>";
    closediv = "</div>";
    btns = "";

    if (CSTATE.prime_available) {
        btns = '&nbsp;&nbsp;' + HBTN.switchLogBtn +
            '&nbsp;&nbsp;' + HBTN.switchToPrimeBtn;
    } else {
        btns = '&nbsp;&nbsp;' + HBTN.switchLogBtn;
    }

    modalChangeMinAmp = setModalChrome('<h3>' + TXT.select_log + '</h3>',
        opendiv +
        '<select id="id_selectLog" class="large">' + options + '</select>' +
        btns +
        closediv,
        HBTN.cancelModalBtn
        );

    $("#id_mod_change").html(modalChangeMinAmp);
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
        CSTATE.startPos = null;
        resetLeakPosition();
        clearPeakNoteMarkers();
        clearAnalysisNoteMarkers();
        clearDatNoteMarkers(true);

        $("#id_selectLogBtn").html(newtitle);
        if (CNSNT.prime_view) {
            $("#concentrationSparkline").html("Loading..");
        } else {
            $('#concentrationSparkline').html("");
        }
        if (newtitle === "Live") {
            $("#id_exportButton_span").html("");
        } else {
            $("#id_exportButton_span").html(LBTNS.downloadBtns + '<br/>');
        }
    }
    $("#id_mod_change").html("");
}

function switchToPrime() {
    var baseurl, url;

    if (confirm(TXT.prime_conf_msg)) {
        baseurl = CNSNT.svcurl.replace("rest", "gduprime");
        url = baseurl + '/' + CNSNT.analyzer_name;
        window.location = url;
        restoreModChangeDiv();
    }
}

function testPrime() {
    var params, url;

    if (CSTATE.prime_test_count >= 10) {
        TIMER.prime = null;
    } else {
        if (CNSNT.prime_view) {
            TIMER.prime = null;
        } else {
            params = {'startPos': 'null', 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset};
            url = CNSNT.callbacktest_url + '/' + 'getData';

            $.ajax({contentType: "application/json",
                data: $.param(params),
                dataType: "jsonp",
                url: url,
                type: "get",
                timeout: 60000,
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
    $("#id_mod_change").html("");
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
    CSTATE.ignoreTimer = false;
}

function showDnoteCb() {
    var btxt;

    if (CSTATE.showDnote === false) {
        CSTATE.showDnote = true;
    } else {
        CSTATE.showDnote = false;
        clearDatNoteMarkers(false);
    }
    setCookie("pcubed_dnote", (CSTATE.showDnote) ? "1" : "0", CNSNT.cookie_duration);

    btxt = TXT.show_txt;
    if (CSTATE.showDnote) {
        btxt = TXT.hide_txt;
    }
    btxt += " " + TXT.dnote;
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
    setCookie("pcubed_pnote", (CSTATE.showPnote) ? "1" : "0", CNSNT.cookie_duration);

    btxt = TXT.show_txt;
    if (CSTATE.showPnote) {
        btxt = TXT.hide_txt;
    }
    btxt += " " + TXT.pnote;
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
    setCookie("pcubed_anote", (CSTATE.showAnote) ? "1" : "0", CNSNT.cookie_duration);

    btxt = TXT.show_txt;
    if (CSTATE.showAnote) {
        btxt = TXT.hide_txt;
    }
    btxt += " " + TXT.anote;
    $('#id_showAnoteCb').html(btxt);
}

function showPbubbleCb() {
    var btxt;

    if (CSTATE.showPbubble === false) {
        CSTATE.showPbubble = true;
    } else {
        CSTATE.showPbubble = false;
        clearPeakMarkerArray();
    }
    setCookie("pcubed_pbubble", (CSTATE.showPbubble) ? "1" : "0", CNSNT.cookie_duration);

    btxt = TXT.show_txt;
    if (CSTATE.showPbubble) {
        btxt = TXT.hide_txt;
    }
    btxt += " " + TXT.pbubble;
    $('#id_showPbubbleCb').html(btxt);
}

function showAbubbleCb() {
    var btxt;

    if (CSTATE.showAbubble === false) {
        CSTATE.showAbubble = true;
    } else {
        CSTATE.showAbubble = false;
        clearAnalysisMarkerArray();
    }
    setCookie("pcubed_abubble", (CSTATE.showAbubble) ? "1" : "0", CNSNT.cookie_duration);

    btxt = TXT.show_txt;
    if (CSTATE.showAbubble) {
        btxt = TXT.hide_txt;
    }
    btxt += " " + TXT.abubble;
    $('#id_showAbubbleCb').html(btxt);
}

function showWbubbleCb() {
    var btxt;

    if (CSTATE.showWbubble === false) {
        CSTATE.showWbubble = true;
    } else {
        CSTATE.showWbubble = false;
        clearWindMarkerArray();
    }
    setCookie("pcubed_wbubble", (CSTATE.showWbubble) ? "1" : "0", CNSNT.cookie_duration);

    btxt = TXT.show_txt;
    if (CSTATE.showWbubble) {
        btxt = TXT.hide_txt;
    }
    btxt += " " + TXT.wbubble;
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
    setCookie("pcubed_swath", (CSTATE.showSwath) ? "1" : "0", CNSNT.cookie_duration);

    btxt = TXT.show_txt;
    if (CSTATE.showSwath) {
        btxt = TXT.hide_txt;
    }
    btxt += " " + TXT.swath;
    $('#id_showSwathCb').html(btxt);
}

function requestMinAmpChange() {
    var modalChangeMinAmp;
    modalChangeMinAmp = setModalChrome('<h3>' + TXT.change_min_amp + '</h3>',
        '<div><input type="text" id="id_amplitude" value="' + CSTATE.minAmp + '"/></div>',
        HBTN.changeMinAmpOkHidBtn +
        HBTN.changeMinAmpCancelBtn +
        HBTN.changeMinAmpOkBtn
        );

    $("#id_mod_change").html(modalChangeMinAmp);
    $("#id_amplitude").focus();
}

function updateNote(cat, fnm, etm, note, type) {
    var method, docrow;

    //alert("updateNote: " + fnm + "\n" + etm + "\n" + note + "\n" + type);
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
    if (cat === 'peak') {
        CSTATE.peakNoteDict[etm] = datadict;
    } else {
        if (cat === 'analysis') {
            CSTATE.analysisNoteDict[etm] = datadict;
        } else {
            CSTATE.datNoteDict[etm] = datadict;
        }
    }
    docrow = {"FILENAME": fnm,
            "EPOCH_TIME": etm,
            "NOTE_TXT": note};

    if (type === 'add') {
        method = 'gdu/dataNoteAdd';
        docrow.INSERT_USER = CNSNT.user_id;
    } else {
        method = 'gdu/dataNoteUpdate';
        docrow.UPDATE_USER = CNSNT.user_id;
    }
    post_rest(CNSNT.annotation_url,
        method,
        docrow,
        function (json, status, jqXHR, cat) {
            var datadict;
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
        },
        function (jqXHR, ts, et, cat) {
            var datadict;
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
        }
        );
}

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
    var k, kk, options, lst, selected, dsp, noteSel, logseldiv, modalPinNote, hdr, body, buttons, proplist, vlu, datadict, currnote, catstr;

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
    for (i = 0; i < CSTATE.noteSortSel.length; i += 1) {
        selected = "";
        if (CSTATE.noteSortSel[i].cat === cat && CSTATE.noteSortSel[i].etm === etm.toString()) {
            selected = ' selected="selected" ';
        }
        dsp = TXT[CSTATE.noteSortSel[i].cat] + ": " + CSTATE.noteSortSel[i].timeStrings;
        options += '<option value="' + CSTATE.noteSortSel[i].cat + ":" + CSTATE.noteSortSel[i].etm + '"' + selected + '>' + dsp + '</option>';
    }
    logseldiv = "";
    k = 'note_list';
    vlu = '<select onchange="notePaneSwitch(this)">';
    vlu += options;
    vlu += '</select>';
    logseldiv += '<div class="clearfix">';
    logseldiv += '<label for="id_' + k + '">' + TXT[k]  +  '</label>';
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

    hdr = '<h3>' + TXT[cat]  +  ':&nbsp;' + timeStringFromEtm(etm) + '</h3>';
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
            proplist += '<label for="id_' + k + '">' + TXT[k]  +  '</label>';
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
        proplist += '<label for="id_note">' + TXT.note + '</label>';
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
    buttons += '<div><button onclick="noteUpdate(false, ' + etm + ',' + catstr + ');" class="btn primary large">' + TXT.close + '</button></div>';

    if (CNSNT.annotation_url) {
        buttons += '<div><button onclick="noteUpdate(true, ' + etm + ', ' + catstr + ');" class="btn primary large">' + TXT.save_note + '</button></div>';
    }

    modalPinNote = setModalChrome(hdr, body, buttons);

    $("#id_smodal").html(modalPinNote);
    $("#id_note").focus();
}

function controlPane() {
    var modalChangeMinAmp, showDnoteCntl, showPnoteCntl, showAbubbleCntl, showPbubbleCntl, showAnoteCntl, showWbubbleCntl, showSwathCntl;
    var dchkd, pchkd, achkd, pbchkd, abchkd, wbchkd, swchkd, body;

    dchkd = TXT.show_txt;
    if (CSTATE.showDnote) {
        dchkd = TXT.hide_txt;
    }
    dchkd += " " + TXT.dnote;
    
    pchkd = TXT.show_txt;
    if (CSTATE.showPnote) {
        pchkd = TXT.hide_txt;
    }
    pchkd += " " + TXT.pnote;
    
    achkd = TXT.show_txt;
    if (CSTATE.showAnote) {
        achkd = TXT.hide_txt;
    }
    achkd += " " + TXT.anote;
    
    pbchkd = TXT.show_txt;
    if (CSTATE.showPbubble) {
        pbchkd = TXT.hide_txt;
    }
    pbchkd += " " + TXT.pbubble;
    
    abchkd = TXT.show_txt;
    if (CSTATE.showAbubble) {
        abchkd = TXT.hide_txt;
    }
    abchkd += " " + TXT.abubble;
    
    wbchkd = TXT.show_txt;
    if (CSTATE.showWbubble) {
        wbchkd = TXT.hide_txt;
    }
    wbchkd += " " + TXT.wbubble;

    swchkd = TXT.show_txt;
    if (CSTATE.showSwath) {
        swchkd = TXT.hide_txt;
    }
    swchkd += " " + TXT.swath;
    
    showDnoteCntl = '<div><button id="id_showDnoteCb" type="button" onclick="showDnoteCb();" class="btn large">' + dchkd + '</button></div>',
    showPnoteCntl = '<div><button id="id_showPnoteCb" type="button" onclick="showPnoteCb();" class="btn large">' + pchkd + '</button></div>',
    showAnoteCntl = '<div><button id="id_showAnoteCb" type="button" onclick="showAnoteCb();" class="btn large">' + achkd + '</button></div>',

    showPbubbleCntl = '<div><button id="id_showPbubbleCb" type="button" onclick="showPbubbleCb();" class="btn large">' + pbchkd + '</button></div>',
    showAbubbleCntl = '<div><button id="id_showAbubbleCb" type="button" onclick="showAbubbleCb();" class="btn large">' + abchkd + '</button></div>',
    showWbubbleCntl = '<div><button id="id_showWbubbleCb" type="button" onclick="showWbubbleCb();" class="btn large">' + wbchkd + '</button></div>',
    showSwathCntl   = '<div><button id="id_showSwathCb"   type="button" onclick="showSwathCb();"   class="btn large">' + swchkd + '</button></div>',

    //showDnoteCntl ='<label><h3><input type="checkbox" id="id_showDnoteCb" onclick="showDnoteCb();" ' + dchkd + '/><span>' + TXT.dnote + '</span></h3></label>';
    //showPnoteCntl ='<label><h3><input type="checkbox" id="id_showPnoteCb" onclick="showPnoteCb();" ' + pchkd + '/><span>' + TXT.pnote + '</span></h3></label>';
    //showAnoteCntl ='<label><h3><input type="checkbox" id="id_showAnoteCb" onclick="showAnoteCb();" ' + achkd + '/><span>' + TXT.anote + '</span></h3></label>';

    //showPbubbleCntl ='<label><h3><input type="checkbox" id="id_showPbubbleCb" onclick="showPbubbleCb();" ' + pbchkd + '/><span>' + TXT.pbubble + '</span></h3></label>';
    //showAbubbleCntl ='<label><h3><input type="checkbox" id="id_showAbubbleCb" onclick="showAbubbleCb();" ' + abchkd + '/><span>' + TXT.abubble + '</span></h3></label>';

    body = "";
    if (CNSNT.annotation_url) {
        body += '<div class="clearfix">';
        body += '<label>' + TXT.show_notes + '</label>';
        body += '<div class="input">';
        body += '<ul class="inputs-list">';
        body += '<li>' + showDnoteCntl + '</li>';
        body += '<li>' + showPnoteCntl + '</li>';
        body += '<li>' + showAnoteCntl + '</li>';
        body += '</ul>';
        body += '</div>';
        body += '</div>';
    }

    body += '<div class="clearfix">';
    body += '<label>' + TXT.show_markers + '</label>';
    body += '<div class="input">';
    body += '<ul class="inputs-list">';
    body += '<li>' + showPbubbleCntl + '</li>';
    body += '<li>' + showAbubbleCntl + '</li>';
    body += '<li>' + showWbubbleCntl + '</li>';
    // body += '<li>' + showSwathCntl + '</li>';
    body += '</ul>';
    body += '</div>';
    body += '</div>';

    modalChangeMinAmp = setModalChrome('<h3>' + TXT.show_controls + '</h3>',
        body,
        HBTN.modChangeCloseBtn
        );

    $("#id_mod_change").html(modalChangeMinAmp);
    $("#id_showDnoteCb").focus();
}

function colorPathFromValveMask(value) {
    var value_float, value_int, clr, value_binstr, value_lastbits;
    value_float = parseFloat(value);
    value_int = Math.round(value_float);
    clr = CNSNT.normal_path_color;
    if (Math.abs(value_float - value_int) > 1e-4) {
        clr = CNSNT.normal_path_color;
    } else {
        value_binstr = value_int.toString(2);
        value_lastbits = value_binstr.substring(value_binstr.length - 1, value_binstr.length);
        if (value_lastbits === "1") {
            clr = CNSNT.analyze_path_color;
        } else {
            clr = CNSNT.normal_path_color;
        }
    }
    return clr;
}

function widthFunc(windspeed,windDirSdev) {
    var v0 = 5; // 5m/s gives maximum width
    var w0 = 100;   // Maximum width is 100m
    return w0*Math.exp(1.0)*(windspeed/v0)*Math.exp(-windspeed/v0);
}

function updatePath(pdata, clr, etm) {
    var where, lastPoint, pathLen, npdata;
    lastPoint = null;
    where = newLatLng(pdata.lat, pdata.lon);
    
    if (clr === CNSNT.analyze_path_color) {
        $("#analysis").html("");
    }
    // when path color needs to change, we instatiate a new path
    // this is because strokeColor changes the entire Polyline, not just
    // new points
    if (CSTATE.startNewPath || clr !== CSTATE.path.strokeColor) {
        pathLen = CSTATE.path.getPath().getLength();
        if (pathLen > 0) {
            lastPoint = CSTATE.path.getPath().getAt(pathLen - 1);
        }
        CSTATE.path = newPolyline(CSTATE.map, clr);

        google.maps.event.addListener(CSTATE.path, 'click', function (event) {
            var newhash, closepobjs, i, pobj;
            newhash = encodeGeoHash(event.latLng.lat(), event.latLng.lng());
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

        if (lastPoint && !CSTATE.startNewPath) {
            pushToPath(CSTATE.path, lastPoint);
        }
    }
    pushToPath(CSTATE.path, where);

    if ('windN' in pdata) { 
        if (clr === CNSNT.normal_path_color) {
            var dir = Math.atan2(pdata.windE,pdata.windN);
            var windspeed = Math.sqrt(pdata.windN*pdata.windN + pdata.windE*pdata.windE);
            var width = widthFunc(windspeed,pdata.windDirSdev); // Width of band in meters in direction of mean wind
            var deltaLat = CNSNT.rtd*width*Math.cos(dir)/CNSNT.earthRadius;
            var deltaLon = CNSNT.rtd*width*Math.sin(dir)/(CNSNT.earthRadius*Math.cos(where.lat()*CNSNT.dtr));
            
            if (CSTATE.lastMeasPathLoc) {
                if (!CSTATE.startNewPath) {
                    // Draw the polygon
                    var coords = [newLatLng(CSTATE.lastMeasPathLoc.lat()+CSTATE.lastMeasPathDeltaLat,CSTATE.lastMeasPathLoc.lng()+CSTATE.lastMeasPathDeltaLon),
                        CSTATE.lastMeasPathLoc,
                        where,
                        newLatLng(where.lat()+deltaLat, where.lng()+deltaLon)];
                    CSTATE.swathPolys.push(newPolygonWithoutOutline(CSTATE.map,CNSNT.swath_color,CNSNT.swath_opacity,coords,CSTATE.showSwath));
                }    
            }
            CSTATE.lastMeasPathLoc = where;
            CSTATE.lastMeasPathDeltaLat = deltaLat;
            CSTATE.lastMeasPathDeltaLon = deltaLon;
        }
        else {
            CSTATE.lastMeasPathLoc = null;
            CSTATE.lastMeasPathDeltaLat = null;
            CSTATE.lastMeasPathDeltaLon = null;
        }
    }
    CSTATE.startNewPath = false;
    npdata = pdata;
    npdata.geohash = encodeGeoHash(where.lat(), where.lng());
    CSTATE.pathGeoObjs.push(npdata);
}

/*
function makeWindRose(radius,meanBearing,shaftLength,halfWidth) {
    var wMin = meanBearing - halfWidth;
    var height = 2*radius;
    $("#windRose").sparkline([2*halfWidth,360-2*halfWidth],{"type":"pie","height":height+"px","offset":-90+wMin,"sliceColors":["#ffff00","#cccccc"]});
};
*/

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
    context.fillStyle = "#cccccc"
    context.fill();
    context.beginPath();
    context.moveTo(centerX,centerY);
    context.arc(centerX,centerY,radius,1.5*Math.PI+wMin,1.5*Math.PI+wMax,false);
    context.lineTo(centerX,centerY);
    context.fillStyle = "#ffff00"
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
};

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
    context.fillStyle = "#ffff00"
    context.fill();
    context.lineWidth = 1;
    context.strokeStyle = "black";
    context.stroke();
    return {radius:radius,url:canvas.toDataURL("image/png")};
};

function getNearest(currentHash, maxNeighbors) {
    var matching, accuracy, matchCount, i, tmp;
    matching = {};
    accuracy = 12;
    matchCount = 0;
    while (matchCount < maxNeighbors && accuracy > 0) {
        cmpHash = currentHash.substring(0, accuracy);
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
    var mapTypeCookie, current_zoom, followCookie, minAmpCookie, latCookie, dnoteCookie, pnoteCookie, anoteCookie;
    var abubbleCookie, pbubbleCookie, wbubbleCookie, swathCookie;
    pge_wdth = $('#id_topbar').width();
    $('#map_canvas').css('height', winH - 200);
    $('#map_canvas').css('width', pge_wdth);
    initialize_btns();

    if (CNSNT.prime_view) {
        CSTATE.current_mapTypeId = google.maps.MapTypeId.ROADMAP;
    } else {
        CSTATE.current_mapTypeId = google.maps.MapTypeId.ROADMAP;
        mapTypeCookie = getCookie("pcubed_mapTypeId");
        if (mapTypeCookie) {
            CSTATE.current_mapTypeId = mapTypeCookie;
        }
    }

    dnoteCookie = getCookie("pcubed_dnote");
    if (dnoteCookie) {
        CSTATE.showDnote = parseInt(dnoteCookie, 2);
    }

    pnoteCookie = getCookie("pcubed_pnote");
    if (pnoteCookie) {
        CSTATE.showPnote = parseInt(pnoteCookie, 2);
    }

    anoteCookie = getCookie("pcubed_anote");
    if (anoteCookie) {
        CSTATE.showAnote = parseInt(anoteCookie, 2);
    }

    pbubbleCookie = getCookie("pcubed_pbubble");
    if (pbubbleCookie) {
        CSTATE.showPbubble = parseInt(pbubbleCookie, 2);
    }

    abubbleCookie = getCookie("pcubed_abubble");
    if (abubbleCookie) {
        CSTATE.showAbubble = parseInt(abubbleCookie, 2);
    }

    wbubbleCookie = getCookie("pcubed_wbubble");
    if (wbubbleCookie) {
        CSTATE.showWbubble = parseInt(wbubbleCookie, 2);
    }
    
    swathCookie = getCookie("pcubed_swath");
    if (swathCookie) {
        var value = parseInt(swathCookie, 2);
        CSTATE.showSwath = !(value === 0);
    }

    followCookie = getCookie("pcubed_follow");
    if (followCookie) {
        CSTATE.follow = parseInt(followCookie, 2);
    }
    if (CSTATE.follow) {
        $("#id_follow").attr("checked", "checked");
    } else {
        $("#id_follow").removeAttr("checked");
    }

    minAmpCookie = getCookie("pcubed_minAmp");
    if (minAmpCookie) {
        CSTATE.minAmp = parseFloat(minAmpCookie);
    }
    $("#id_amplitude_btn").html(CSTATE.minAmp);

    current_zoom = getCookie("pcubed_zoom");
    if (current_zoom) {
        CSTATE.current_zoom = parseInt(current_zoom, 10);
    } else {
        CSTATE.current_zoom = 14;
    }

    latCookie = getCookie("pcubed_center_latitude");
    if (latCookie) {
        CSTATE.center_lat = parseFloat(latCookie);
    }

    lonCookie = getCookie("pcubed_center_longitude");
    if (lonCookie) {
        CSTATE.center_lon = parseFloat(lonCookie);
    }

    latlng = newLatLng(CSTATE.center_lat, CSTATE.center_lon);
    CSTATE.gglOptions = {
        zoom: CSTATE.current_zoom,
        center: latlng,
        mapTypeId: CSTATE.current_mapTypeId,
        rotateControl: false,
        scaleControl: true,
        zoomControl: true,
        zoomControlOptions: {style: google.maps.ZoomControlStyle.SMALL}
    };

    initialize_map();
    TIMER.data = setTimeout(datTimer, 1000);
}

function initialize_btns() {
    var type;
    $('#cancel').hide();

    if (CNSNT.prime_view) {
        $("#id_primeControlButton_span").html(LBTNS.analyzerCntlBtns);
    } else {
        testPrime();
        $("#id_primeControlButton_span").html("");
        $("#id_exportButton_span").html("");
        type = $("#id_selectLogBtn").html();
        if (type === "Live") {
            $("#id_exportButton_span").html("");
        } else {
            $("#id_exportButton_span").html(LBTNS.downloadBtns + '<br/>');
        }
    }
}

function restart_datalog() {
    if (confirm(TXT.restart_datalog_msg)) {
        call_rest(CNSNT.svcurl, "restartDatalog", {});
        restoreModChangeDiv();
    }
}

function shutdown_analyzer() {
    if (confirm(TXT.shutdown_anz_msg)) {
        call_rest(CNSNT.svcurl, "shutdownAnalyzer", {});
        restoreModChangeDiv();
    }
}

function get_time_zone_offset() {
    var current_date, gmt_offset;
    current_date = new Date();
    gmt_offset = current_date.getTimezoneOffset() / 60;
    $('#gmt_offset').val(gmt_offset);
    rtn_offset = $('#gmt_offset').val();
    // alert(rtn_offset)
    return gmt_offset;
}

function call_rest(call_url, method, params, success_callback, error_callback) {
    var dtype, url;
    dtype = "json";
    if (CNSNT.prime_view) {
        dtype = "jsonp";
    }
    url = call_url + '/' + method;
    $.ajax({contentType: "application/json",
        data: $.param(params),
        dataType: dtype,
        url: url,
        type: "get",
        timeout: 60000,
        success: success_callback,
        error: error_callback
        });
}

function post_rest(call_url, method, params, success_callback, error_callback) {
    var dtype, url;
    dtype = "json";
    if (CNSNT.prime_view) {
        dtype = "jsonp";
    }
    url = call_url + '/' + method;
    $.ajax({contentType: "application/json",
        data: $.param(params),
        dataType: dtype,
        url: url,
        type: "get",
        timeout: 60000,
        success: success_callback,
        error: error_callback
        });
}

function changeFollow() {
    var cval = $("#id_follow").attr("checked");
    if (cval === "checked") {
        if (CSTATE.lastwhere && CSTATE.map) {
            CSTATE.map.setCenter(CSTATE.lastwhere);
        }
        CSTATE.follow = true;
    } else {
        CSTATE.follow = false;
    }
    setCookie("pcubed_follow", (CSTATE.follow) ? "1" : "0", CNSNT.cookie_duration);
}

function changeMinAmp() {
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
    $("#id_amplitude_btn").html(CSTATE.minAmp);
    setCookie("pcubed_minAmp", CSTATE.minAmp, CNSNT.cookie_duration);
    resetLeakPosition();
}

function setGduTimer(tcat) {
    if (tcat === "dat") {
        TIMER.data = setTimeout(datTimer, CNSNT.datUpdatePeriod);
        return;
    }
    if (tcat === "peak") {
        TIMER.peak = setTimeout(peakTimer, CNSNT.peakUpdatePeriod);
        return;
    }
    if (tcat === "analysis") {
        TIMER.analysis = setTimeout(analysisTimer, CNSNT.analysisUpdatePeriod);
        return;
    }
    if (tcat === "wind") {
        TIMER.wind = setTimeout(windTimer, CNSNT.windUpdatePeriod);
        return;
    }
    if (tcat === "dnote") {
        TIMER.dnote = setTimeout(dnoteTimer, CNSNT.noteUpdatePeriod);
        return;
    }
    if (tcat === "pnote") {
        TIMER.pnote = setTimeout(pnoteTimer, CNSNT.noteUpdatePeriod);
        return;
    }
    if (tcat === "anote") {
        TIMER.anote = setTimeout(anoteTimer, CNSNT.noteUpdatePeriod);
        return;
    }
}

function datTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('dat');
        return;
    }
    if (CNSNT.prime_view) {
        getMode();
    } else {
        getData();
    }
}

function peakTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('peak');
        return;
    }
    showLeaks();
}

function windTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('wind');
        return;
    }
    showWind();
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

function statCheck() {
    var dte, curtime, streamdiff;
    dte = new Date();
    curtime = dte.getTime();
    streamdiff = curtime - CSTATE.laststreamtime;
    if (streamdiff > CNSNT.streamerror) {
        $("#id_stream_stat").html("<font color='red'><strike>Stream</strike></font>");
        $("#id_gps_stat").html("<font color='red'><strike>GPS</strike></font>");
        $("#id_analyzer_stat").html("<font color='red'><strike>Analyzer</strike></font>");
    } else {
        if (streamdiff > CNSNT.streamwarning) {
            $("#id_stream_stat").html("Stream Warning");
        } else {
            $("#id_stream_stat").html("Stream OK");
            if (CSTATE.lastFit === 0) {
                $("#id_gps_stat").html("<font color='red'><strike>GPS</strike></font>");
            } else {
                $("#id_gps_stat").html("GPS OK");
            }

            if (CSTATE.lastInst !== 963) {
                $("#id_analyzer_stat").html("<font color='red'><strike>Analyzer</strike></font>");
            } else {
                $("#id_analyzer_stat").html("Analyzer OK");
            }
        }
    }
}

function getData() {
    //if (startPos) {startPosStr = startPos;} else {startPosStr = 'null';};
    var params = {'startPos': CSTATE.startPos, 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset, 
        'varList': '["GPS_ABS_LAT","GPS_ABS_LONG","GPS_FIT","CH4","ValveMask", "INST_STATUS", "WIND_N", "WIND_E", "WIND_DIR_SDEV"]'};
    call_rest(CNSNT.svcurl, "getData", params,
            function (json, status, jqXHR) {
            CSTATE.net_abort_count = 0;
            successData(json);
        },
        function (jqXHR, ts, et) {
            errorData(jqXHR.responseText);
        }
        );
}

function getMode() {
    var mode;
    if (!CSTATE.getting_mode) {
        CSTATE.getting_mode = true;
        call_rest(CNSNT.svcurl, "driverRpc", {"func": "rdDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER']"},
                function (data, ts, jqXHR) {
                if (data.result.value !== undefined) {
                    var mode = data.result.value;
                    setModePane(mode);
                }
                CSTATE.getting_mode = false;
            },
            function (jqXHR, ts, et) {
                $("#errors").html(jqXHR.responseText);
                CSTATE.getting_mode = false;
            }
            );
    }
    getData();
}

function showLeaks() {
    var params = {'startRow': CSTATE.leakLine, 'alog': CSTATE.alog, 'minAmp': CSTATE.minAmp, 'gmtOffset': CNSNT.gmt_offset};
    if (!CSTATE.showPbubble) {
        setGduTimer('peak');
        return;
    }
    call_rest(CNSNT.svcurl, "getPeaks", params,
            function (json, status, jqXHR) {
            CSTATE.net_abort_count = 0;
            successPeaks(json);
        },
        function (jqXHR, ts, et) {
            errorPeaks(jqXHR.responseText);
        }
        );
}

function showAnalysis() {
    var params = {'startRow': CSTATE.analysisLine, 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset};
    if (!CSTATE.showAbubble) {
        setGduTimer('analysis');
        return;
    }
    call_rest(CNSNT.svcurl, "getAnalysis", params,
            function (json, status, jqXHR) {
            CSTATE.net_abort_count = 0;
            successAnalysis(json);
        },
        function (jqXHR, ts, et) {
            errorAnalysis(jqXHR.responseText);
        }
        );
}

function showWind() {
    var params = {'startRow': CSTATE.windLine, 'alog': CSTATE.alog, 'minAmp': CSTATE.minAmp, 'gmtOffset': CNSNT.gmt_offset};
    if (!CSTATE.showWbubble) {
        setGduTimer('wind');
        return;
    }
    call_rest(CNSNT.svcurl, "getPeaks", params,
            function (json, status, jqXHR) {
            CSTATE.net_abort_count = 0;
            successWind(json);
        },
        function (jqXHR, ts, et) {
            errorWind(jqXHR.responseText);
        }
        );
}

function getNotes(cat) {
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
    params = {'startEtm': etm, 'alog': fname, 'gmtOffset': CNSNT.gmt_offset, 'returnLatLng': 'true', 'byUtm': 'true'};
    if (CNSNT.annotation_url) {
        call_rest(CNSNT.annotation_url, "gdu/getNotes", params,
                function (json, status, jqXHR) {
                CSTATE.net_abort_count = 0;
                successNotes(json, cat);
            },
            function (jqXHR, ts, et) {
                errorDatNotes(jqXHR.responseText);
            }
            );
    }
    // NOTE: if there is no annotation_url, this will STOP the note timers
    // as there is no ELSE logic to restart them. 
    // This is the expected behavior.
}

function successData(data) {
    var resultWasReturned, newTimestring, newFit, newInst, i, clr, pdata;
    restoreModalDiv();
    resultWasReturned = false;
    CSTATE.counter += 1;
    if (CSTATE.green_on) {
        $("#id_data_alert").css('background-color', 'green');
        CSTATE.green_on = false;
    } else {
        $("#id_data_alert").css('background-color', 'white');
        CSTATE.green_on = true;
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
            }
            CSTATE.lastDataFilename = data.result.filename;
            CSTATE.lastPeakFilename = CSTATE.lastDataFilename.replace(".dat", ".peaks");
            CSTATE.lastAnalysisFilename = CSTATE.lastDataFilename.replace(".dat", ".analysis");
        }
    }
    if (resultWasReturned) {
        if (data.result.lastPos) {
            CSTATE.startPos = data.result.lastPos;
        }
        if (data.result.EPOCH_TIME) {
            if (data.result.EPOCH_TIME.length > 0) {
                newTimestring = timeStringFromEtm(data.result.EPOCH_TIME[data.result.EPOCH_TIME.length - 1]);
                if (CSTATE.lastTimestring !== newTimestring) {
                    dte = new Date();
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
                    if (CSTATE.lastInst !== newInst) {
                        CSTATE.lastInst = newInst;
                    }
                }
            }

            n = data.result.CH4.length;
            if (n > 0) {
                where = newLatLng(data.result.GPS_ABS_LAT[n - 1], data.result.GPS_ABS_LONG[n - 1]);
                if (data.result.GPS_FIT) {
                    if (data.result.GPS_FIT[n - 1] !== 0) {
                        CSTATE.lastwhere = where;
                        CSTATE.marker.setPosition(where);
                        CSTATE.marker.setVisible(true);
                        if (CSTATE.follow) {
                            CSTATE.map.setCenter(where);
                        }
                    } else {
                        CSTATE.marker.setVisible(false);
                    }
                } else {
                    CSTATE.lastwhere = where;
                    if (CSTATE.follow) {
                        CSTATE.map.setCenter(where);
                    }
                    CSTATE.marker.setPosition(where);
                    CSTATE.marker.setVisible(true);
                    CSTATE.marker.setZIndex(9999999);
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
                            var direction = CNSNT.rtd*Math.atan2(data.result.WIND_E[n-1],data.result.WIND_N[n-1]);
                            var stddev = data.result.WIND_DIR_SDEV[n-1];
                            if (stddev>90.0) stddev = 90.0;
                            makeWindRose(70,30,direction,2*stddev,5.0*speed,15.0,60.0);
                        }
                    } else {
                        $('#concentrationSparkline').html("");
                    }
                    $("#concData").html("<h4>" + "Current concentration " + data.result.CH4[n - 1].toFixed(3) + " ppm" + "</h4>");
                    for (i = 1; i < n; i += 1) {
                        clr = data.result.ValveMask ? colorPathFromValveMask(data.result.ValveMask[i]) : CNSNT.normal_path_color;
                        pdata = {
                            lat: data.result.GPS_ABS_LAT[i],
                            lon: data.result.GPS_ABS_LONG[i],
                            etm: data.result.EPOCH_TIME[i],
                            ch4: data.result.CH4[i]
                        };
                        if ('WIND_E' in data.result) pdata['windE'] = data.result.WIND_E[i];
                        if ('WIND_N' in data.result) pdata['windN'] = data.result.WIND_N[i];
                        if ('WIND_DIR_SDEV' in data.result) pdata['windDirSdev'] = data.result.WIND_DIR_SDEV[i];
                        if (data.result.GPS_FIT) {
                            if (data.result.GPS_FIT[i] !== 0) {
                                updatePath(pdata, clr, data.result.EPOCH_TIME[i]);
                            } else {
                                CSTATE.startNewPath = true;
                            }
                        } else {
                            updatePath(pdata, clr, data.result.EPOCH_TIME[i]);
                        }
                    }
                }
            }
        }
    }
    statCheck();
    setGduTimer('dat');
    if (TIMER.peak === null) {
        setGduTimer('peak');
    }
    if (TIMER.analysis === null) {
        setGduTimer('analysis');
    }
    if (TIMER.wind === null) {
        setGduTimer('wind');
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
}

function successPeaks(data) {
    var resultWasReturned, i;
    resultWasReturned = false;
    if (data.result) {
        if (data.result.filename) {
            if (CSTATE.lastPeakFilename === data.result.filename) {
                resultWasReturned = true;
            }
            //CSTATE.lastPeakFilename = data.result.filename;
        }
    }
    if (resultWasReturned) {
        if (data.result.CH4) {
            if (CSTATE.clearLeaks) {
                CSTATE.clearLeaks = false;
            }
            else {
                CSTATE.leakLine = data.result.nextRow;
                for (i = 0; i < data.result.CH4.length; i += 1) {
                    peakCoords = newLatLng(data.result.GPS_ABS_LAT[i], data.result.GPS_ABS_LONG[i]);
                    peakMarker = newPeakMarker(CSTATE.map, peakCoords, data.result.AMPLITUDE[i], data.result.SIGMA[i], data.result.CH4[i]);
                    CSTATE.peakMarkers[CSTATE.peakMarkers.length] = peakMarker;

                    datadict = CSTATE.peakNoteDict[data.result.EPOCH_TIME[i]];
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
            }
        }
    }
    setGduTimer('peak');
}

function successWind(data) {
    var resultWasReturned, i;
    resultWasReturned = false;
    if (data.result) {
        if (data.result.filename) {
            if (CSTATE.lastPeakFilename === data.result.filename) {
                resultWasReturned = true;
            }
            //CSTATE.lastPeakFilename = data.result.filename;
        }
    }
    if (resultWasReturned) {
        if (data.result.WIND_DIR_SDEV) {
            if (CSTATE.clearWind) {
                CSTATE.clearWind = false;
            }
            else {
                CSTATE.windLine = data.result.nextRow;
                for (i = 0; i < data.result.WIND_DIR_SDEV.length; i += 1) {
                    var windDirection = CNSNT.rtd*Math.atan2(data.result.WIND_E[i],data.result.WIND_N[i]);
                    var windSpeed = Math.sqrt(data.result.WIND_N[i]*data.result.WIND_N[i]+data.result.WIND_E[i]*data.result.WIND_E[i]);
                    peakCoords = newLatLng(data.result.GPS_ABS_LAT[i], data.result.GPS_ABS_LONG[i]);
                    windMarker = newWindMarker(CSTATE.map, peakCoords, windSpeed, windDirection, data.result.WIND_DIR_SDEV[i]);
                    CSTATE.windMarkers[CSTATE.windMarkers.length] = windMarker;
                    /*
                    datadict = CSTATE.peakNoteDict[data.result.EPOCH_TIME[i]];
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
                    */
                }
            }
        }
    }
    setGduTimer('wind');
}

function attachMarkerListener(marker, etm, cat, bubble) {
    var markerListener = new google.maps.event.addListener(marker, 'click', function () {
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

function successAnalysis(data) {
    var resultWasReturned, i, result;
    resultWasReturned = false;
    if (data.result) {
        if (data.result.filename) {
            if (CSTATE.lastAnalysisFilename === data.result.filename) {
                resultWasReturned = true;
            }
            //CSTATE.lastAnalysisFilename = data.result.filename;
        }
    }
    if (resultWasReturned) {
        if (data.result.CONC) {
            if (CSTATE.clearAnalyses) {
                CSTATE.clearAnalyses = false;
            }
            else {
                CSTATE.analysisLine = data.result.nextRow;
                for (i = 0; i < data.result.CONC.length; i += 1) {
                    analysisCoords = newLatLng(data.result.GPS_ABS_LAT[i], data.result.GPS_ABS_LONG[i]);
                    result = data.result.DELTA[i].toFixed(1) + " +/- " + data.result.UNCERTAINTY[i].toFixed(1);
                    $("#analysis").html(TXT.delta + ": " + result);
                    analysisMarker = newAnalysisMarker(CSTATE.map, analysisCoords, data.result.DELTA[i], data.result.UNCERTAINTY[i]);
                    CSTATE.analysisMarkers[CSTATE.analysisMarkers.length] = analysisMarker;

                    datadict = CSTATE.analysisNoteDict[data.result.EPOCH_TIME[i]];
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
            }
        }
    }
    setGduTimer('analysis');
}

//drop (or update) the note bubble (and add listener if dropping)
//and update the current state dictionary for the note(s) from the result set
function dropResultNoteBubbles(results, cat) {
    var i, etm, ntx, datadict, pathCoords, pathMarker, mkr;
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

function successNotes(data, cat) {
    if (data.result) {
        if (data.result.EPOCH_TIME) {
            dropResultNoteBubbles(data.result, cat);
        }
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

function errorData(text) {
    CSTATE.net_abort_count += 1;
    if (CSTATE.net_abort_count >= 2) {
        $("#id_modal").html(HPANE.modalNetWarning);
        $("id_warningCloseBtn").focus();
    }
    $("#errors").html(text);
    statCheck();
    setGduTimer('dat');
}

function errorPeaks(text) {
    CSTATE.net_abort_count += 1;
    if (CSTATE.net_abort_count >= 2) {
        $("#id_modal").html(HPANE.modalNetWarning);
    }
    $("#errors").html(text);
    setGduTimer('peak');
}

function errorAnalysis(text) {
    CSTATE.net_abort_count += 1;
    if (CSTATE.net_abort_count >= 2) {
        $("#id_modal").html(HPANE.modalNetWarning);
    }
    $("#errors").html(text);
    setGduTimer('analysis');
}

function errorWind(text) {
    CSTATE.net_abort_count += 1;
    if (CSTATE.net_abort_count >= 2) {
        $("#id_modal").html(HPANE.modalNetWarning);
    }
    $("#errors").html(text);
    setGduTimer('wind');
}

function errorPeakNotes(text) {
    CSTATE.net_abort_count += 1;
    if (CSTATE.net_abort_count >= 2) {
        $("#id_modal").html(HPANE.modalNetWarning);
    }
    $("#errors").html(text);
    setGduTimer('pnote');
}

function errorAnalysisNotes(text) {
    CSTATE.net_abort_count += 1;
    if (CSTATE.net_abort_count >= 2) {
        $("#id_modal").html(HPANE.modalNetWarning);
    }
    $("#errors").html(text);
    setGduTimer('anote');
}

function errorDatNotes(text) {
    CSTATE.net_abort_count += 1;
    if (CSTATE.net_abort_count >= 2) {
        $("#id_modal").html(HPANE.modalNetWarning);
    }
    $("#errors").html(text);
    setGduTimer('dnote');
}

function setModePane(mode) {
    $("#mode").html(modeStrings[mode]);
    CSTATE.current_mode = mode;
}

function captureSwitch() {
    CSTATE.ignoreTimer = true;
    $("#analysis").html("");
    $("#id_mode_pane").html(modeStrings[1]);
    call_rest(CNSNT.svcurl, "driverRpc", {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 1]"});
    CSTATE.ignoreTimer = false;
    restoreModChangeDiv();
}

function cancelCapSwitch() {
    if (confirm(TXT.cancel_cap_msg)) {
        call_rest(CNSNT.svcurl, "driverRpc", {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 0]"});
        restoreModChangeDiv();
    }
}

function injectCal() {
    call_rest(CNSNT.svcurl, "injectCal", {"valve": 3, "samples": 1});
    alert("Calibration pulse injected");
    restoreModChangeDiv();
}

function initialize(winH, winW) {
    if (init_vars) {
        init_vars();
    }
    initialize_gdu(winH, winW);
}
