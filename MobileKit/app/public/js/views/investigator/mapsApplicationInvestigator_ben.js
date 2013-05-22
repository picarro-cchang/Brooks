var mapmaster = mapmaster || {};

var CNSNT = mapmaster.CNSNT;
var TXT = mapmaster.TXT;
var CSTATE = mapmaster.CSTATE;
var HBTN = mapmaster.HBTN;
var LBTNS = mapmaster.LBTNS;
var COOKIE_NAMES = mapmaster.COOKIE_NAMES;

var TIMER = {
        prime: null,
        resize: null,
        data: null, // timer for getData
        analysis: null, // timer for showAnalysis (getAnalysis)
        progress: null, //timer for updateProgress
        mode: null, // timer for getMode
        periph: null, // timer for checkPeriphUpdate
    };

var modeStrings = {0: TXT.survey_mode, 1: TXT.capture_mode, 2: TXT.capture_mode, 3: TXT.analyzing_mode, 4: TXT.inactive_mode,
                   5: TXT.cancelling_mode, 6: TXT.priming_mode, 7: TXT.purging_mode, 8: TXT.injection_pending_mode };


function newLatLng(lat, lng) {
    return new L.LatLng(lat, lng);
}

function timeStringFromEtm(etm) {
    var gmtoffset_mil, etm_mil, tmil, tdate, tstring;
    etm_mil = (etm * 1000);
    tdate = new Date(etm_mil);
    //tstring = tdate.toLocaleDateString() + " " + tdate.toLocaleTimeString();
    tstring = tdate.toString().substring(0,24);
    return tstring;
}

var MapControl2 = L.Control.extend({
    options: {
        position: 'topright'
    },
    onAdd: function (map) {
        var container = L.DomUtil.create('div','mapControl2class');
        container.style.paddingLeft = '4px';
        container.style.paddingRight = '4px';
        container.style.backgroundColor = 'white';
        container.style.borderStyle = 'solid';
        container.style.borderWidth = '2px';
        container.style.cursor = 'pointer';
        container.style.textAlign = 'center';
        container.title = TXT.click_show_cntls;
        container.innerHTML = TXT.map_controls  + "<br/>" + CSTATE.minAmp + "&nbsp; &nbsp;" + CSTATE.stabClass;
        // L.DomEvent.on(container, 'click', modalPaneMapControls);
        this._container = container;
        return container;
    },
    changeControlText: function(newText) {
        this._container.innerHTML = newText;
    }
});

var MapConcPlot2 = L.Control.extend({
    options: {
        position: 'bottomleft'
    },
    onAdd: function (map) {
        var container = L.DomUtil.create('div','concPlot2class');
        container.style.paddingLeft = '4px';
        container.style.paddingRight = '4px';
        container.style.backgroundColor = 'white';
        container.style.borderStyle = 'solid';
        container.style.borderWidth = '2px';
        container.innerHTML = '<div id="concPlot2" style="width:160px;height:90px;"></div>';
        return container;
    }
});

function newMap2() {
    // create a map in the "map" div, set the view to a given place and zoom
    if (!CSTATE.map2) {
        CSTATE.map2 = L.map('map2_canvas',{
            inertia:true,
            inertiaDeceleration:1000,
            attributionControl:false
        }).setView([CSTATE.center_lat,CSTATE.center_lon], CSTATE.current_zoom);

        var mapquestUrl = 'http://{s}.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png',
        subDomains = ['otile1','otile2','otile3','otile4'],
        mapquestAttrib = '<a href="http://open.mapquest.co.uk" target="_blank">MapQuest</a>, <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>.'
        var mapquest = new L.TileLayer(mapquestUrl, {maxZoom: 19, attribution: mapquestAttrib, subdomains: subDomains});
        mapquest.addTo(CSTATE.map2);

        // /*
        // L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        //     attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        // }).addTo(CSTATE.map2);
        // */
        // L.control.scale().addTo(CSTATE.map2);
        // CSTATE.map2.addControl(new MapConcPlot2());
        // CNSNT.mapControl = new MapControl2();
        // CSTATE.map2.addControl(CNSNT.mapControl);
        // CSTATE.map2.on('zoomend', function() {
        //     CSTATE.current_zoom = CSTATE.map2.getZoom();
        //     setCookie(COOKIE_NAMES.zoom, CSTATE.current_zoom, CNSNT.cookie_duration);
        // });
        // CSTATE.map2.on('moveend', function() {
        //     var where = CSTATE.map2.getCenter();
        //     CSTATE.center_lat = where.lat;
        //     CSTATE.center_lon = where.lng;
        //     setCookie(COOKIE_NAMES.center_latitude, CSTATE.center_lat, CNSNT.cookie_duration);
        //     setCookie(COOKIE_NAMES.center_longitude, CSTATE.center_lon, CNSNT.cookie_duration);
        // });

        var greenIcon = L.icon({
            iconUrl: '/static/images/crosshair.png',
            shadowUrl: '/static/images/crosshair.png',

            iconSize:     [65, 65], // size of the icon
            shadowSize:   [0, 0], // size of the shadow
            iconAnchor:   [32, 32], // point of the icon which will correspond to marker's location
            shadowAnchor: [0, 0],  // the same for the shadow
            popupAnchor:  [0, 0] // point from which the popup should open relative to the iconAnchor
        });
        CSTATE.carMarker = L.marker([CSTATE.center_lat,CSTATE.center_lon], {icon: greenIcon}).addTo(CSTATE.map2);
    }
    else {
        // CSTATE.concMarkerLayer.clearLayers();
        // CSTATE.windRayLayer.clearLayers();
        // CSTATE.analysisMarkerLayer.clearLayers();
        // CSTATE.layerControl.removeFrom(CSTATE.map2);
    }
    // CSTATE.concMarkerLayer = L.layerGroup([]).addTo(CSTATE.map2);
    // CSTATE.windRayLayer = L.layerGroup([]).addTo(CSTATE.map2);
    // CSTATE.analysisMarkerLayer = L.layerGroup([]).addTo(CSTATE.map2);
    // CSTATE.layerControl = L.control.layers(null,{"Concentration":CSTATE.concMarkerLayer, "Wind Direction":CSTATE.windRayLayer });
    // CSTATE.layerControl.addTo(CSTATE.map2);
}

function initialize_map() {
    var where, mapListener;

    CSTATE.concMarkerOffset = null;
    newMap2();

    CSTATE.prevInferredStabClass = null;

    CSTATE.firstData = true;

    $('.leaflet-bottom.leaflet-left').hide()
    $('.leaflet-top.leaflet-right2').hide()

    // draw_legend();
}

function resize_map() {
    $('#pageContent').css({height:$('#pageFooter').offset().top - $('#pageFooter').height() + 60})

    $('#legend-controls').css({height:$('#map2_flot').offset().top - 110})

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
        if (TIMER) {
            TIMER.resize = setTimeout(resize_map, 25);
        }
    }
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



function initialize_gdu(winH, winW) {
    log("init gdu")
    var mapTypeCookie, current_zoom, followCookie, overlayCookie, minAmpCookie, latCookie,new_height;
    var abubbleCookie, windRayCookie;

    // initialize_btns();
    resize_map();

    if (CNSNT.prime_view) {
        // CSTATE.current_mapTypeId = google.maps.MapTypeId.ROADMAP;
    } else {
        // CSTATE.current_mapTypeId = google.maps.MapTypeId.ROADMAP;
        mapTypeCookie = getCookie(COOKIE_NAMES.mapTypeId);
        if (mapTypeCookie) {
            CSTATE.current_mapTypeId = mapTypeCookie;
        }
    }

    abubbleCookie = getCookie(COOKIE_NAMES.abubble);
    if (abubbleCookie) {
        CSTATE.showAbubble = parseInt(abubbleCookie, 2);
    }

    /*
    windRayCookie = getCookie(COOKIE_NAMES.windRay);
    if (windRayCookie) {
        var value = parseInt(windRayCookie, 2);
        CSTATE.showWindRay = !(value === 0);
    }
    */

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
        $("#id_follow").attr("class","follow-checked").attr("data-checked",'false')
    } else {
        $("#id_follow").attr("class","follow").attr("data-checked",'true')
    }

    overlayCookie = getCookie("pcubed_overlay");
    if (overlayCookie) {
        CSTATE.overlay = parseInt(overlayCookie, 2);
    }
    if (CSTATE.overlay) {
        $("#id_overlay").attr("class","overlay-checked").attr("data-checked",'false')
    } else {
        $("#id_overlay").attr("class","overlay").attr("data-checked",'true')
    }

    minAmpCookie = getCookie("pcubed_minAmp");
    if (minAmpCookie) {
        CSTATE.minAmp = parseFloat(minAmpCookie);
    }
    $("#id_amplitude_btn").html(CSTATE.minAmp);

    peakThresholdCookie = getCookie("pcubed_peakThreshold");
    if (peakThresholdCookie) {
        CSTATE.peakThreshold = parseFloat(peakThresholdCookie);
    }

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
    /*
    CSTATE.gglOptions = {
        zoom: CSTATE.current_zoom,
        center: latlng,
        mapTypeId: CSTATE.current_mapTypeId,
        rotateControl: false,
        scaleControl: true,
        zoomControl: true,
        zoomControlOptions: {style: google.maps.ZoomControlStyle.SMALL}
    };
    */

    initialize_map();
    TIMER.data = setTimeout(datTimer, 1000);
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


function insertTicket(uri) {
    var nuri
    // sometimes HLL programs try to be "helpful" and convert the < and > strings
    // into &lt; and &gt; tokens.  So we have to beware.
    nuri = uri.replace("&lt;TICKET&gt;", CSTATE.ticket);
    return nuri.replace("<TICKET>", CSTATE.ticket);
}


function _changeStabClass(value) {
    var isc = "";
    if (value !== CSTATE.stabClass || ((value === "*") && (CSTATE.inferredStabClass != CSTATE.prevInferredStabClass))) {
        CSTATE.stabClass = value;
        CSTATE.prevInferredStabClass = CSTATE.inferredStabClass;
        setCookie(COOKIE_NAMES.dspStabClass, CSTATE.stabClass, CNSNT.cookie_duration);
        if (value === "*") isc = CSTATE.inferredStabClass;
        CNSNT.mapControl.changeControlText(TXT.map_controls  + "<br/>" + CSTATE.minAmp + "&nbsp; &nbsp;" + isc + CSTATE.stabClass);
    }
}


function setGduTimer(tcat) {
    // log('gdu timer', tcat)
    if (tcat === "fast") {
        TIMER.data = setTimeout(datTimer, CNSNT.fastUpdatePeriod);
        return;
    }    
    if (tcat === "dat") {
        TIMER.data = setTimeout(datTimer, CNSNT.datUpdatePeriod);
        return;
    }    
    if (tcat === "longDat") {
        TIMER.data = setTimeout(datTimer, CNSNT.longDatUpdatePeriod);
        return;
    }
    if (tcat === "peakAndWind") {
        TIMER.peakAndWind = setTimeout(peakAndWindTimer, CNSNT.peakAndWindUpdatePeriod);
        return;
    }
    // if (tcat === "mode") {
    //     TIMER.mode = setTimeout(modeTimer, CNSNT.modeUpdatePeriod);
    //     return;
    // }
    return;
}

function datTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('dat');
        return;
    }
    mapmaster.Controller.getData();
}


function statCheck() {
    // log('stat check')
    return;
    var dte, curtime, streamdiff;
    var good = CNSNT.INSTMGR_STATUS_READY | CNSNT.INSTMGR_STATUS_MEAS_ACTIVE |
               CNSNT.INSTMGR_STATUS_GAS_FLOWING | CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED |
               CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED | CNSNT.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED;

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


function completeSurvey() {
    alert("Complete Survey button pressed");
    restoreModChangeDiv();
}

function initialize_cookienames() {
    COOKIE_NAMES = {
        mapTypeId: COOKIE_PREFIX + '_mapTypeId',
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
}



    // var calcGroups = function(avg, sd){
    //     if(!mapSVGInit){
    //         initMap();
    //     }

    //     var timeTrack = 0;
    //     var timeStart = path_data[0].etm;
    //     var bins = [[]];
    //     var threshold = avg + sd*2;

    //     var queue_copy = path_data.slice(0)

    //     if(queue_copy.length < temp_render_count){
    //         max = queue_copy.length - 1;
    //     }else{          
    //         max = temp_render_count;
    //     }

    //     for(var i = 0 ; i < max ; i++){
    //         if(queue_copy[i].pdata.ch4 >= threshold){
    //             if(timeTrack > 50){
    //                 timeTrack = 0;
    //                 timeStart = queue_copy[i].etm;
    //                 if(bins[0].length < 4){
    //                     bins[0] = [];
    //                 }else{
    //                     bins.unshift([]);
    //                 }                   
    //             }   
    //             bins[0].push({
    //                 pdata:{
    //                     ch4:queue_copy[i].pdata.ch4,
    //                     lon:queue_copy[i].pdata.lon,
    //                     lat:queue_copy[i].pdata.lat,
    //                     windE:queue_copy[i].pdata.windE,
    //                     windN:queue_copy[i].pdata.windN,
    //                     windDirSdev:queue_copy[i].pdata.windDirSdev
    //                 }
    //             })
    //         }else{
    //             timeTrack = queue_copy[i].pdata.etm - timeStart;
    //         }
    //     }           

    //     var lineScale = 1/1000;

    //     var binLen = bins.length;

    //     var sites = [];


    //     for(var b = 1 ; b < binLen ; b++){
    //         var myBin = bins[b];
    //         var min = 10000;
    //         var max = 0;
    //         var latTotal = 0;
    //         var lonTotal = 0;
    //         var ch4Total = 0;
    //         var avgCount = 0;
    //         var weightedCount = 0;
    //         var quantize = d3.scale.quantile().domain([avg + sd*2, 3]).range(d3.range(100));
    //         for(var c = 0 ; c < myBin.length ; c++){
    //             if(myBin[c].pdata.lat && myBin[c].pdata.lon){                   
    //                 // log(myBin[c].pdata.lat,myBin[c].pdata.lon)
    //                 var latlng = new L.LatLng(myBin[c].pdata.lat,myBin[c].pdata.lon)
    //                 var bearingRad = Math.atan2(myBin[c].pdata.windE,myBin[c].pdata.windN)

    //                 var rayLength = myBin[c].pdata.windDirSdev/10;
    //                 var endLon = -1 * rayLength*Math.cos(bearingRad) * lineScale;
    //                 var endLat = rayLength*Math.sin(bearingRad) * lineScale;
    //                 if(bearingRad){
    //                     myBin[c].pdata.lat += endLat;
    //                     myBin[c].pdata.lon += endLon;

    //                     if(myBin[c].pdata.ch4 < min) min = myBin[c].pdata.ch4;
    //                     if(myBin[c].pdata.ch4 > max) max = myBin[c].pdata.ch4;

    //                     avgCount ++;
    //                     weightedCount += quantize(myBin[c].pdata.ch4);
    //                     latTotal += myBin[c].pdata.lat * quantize(myBin[c].pdata.ch4);
    //                     lonTotal += myBin[c].pdata.lon * quantize(myBin[c].pdata.ch4);
    //                     ch4Total += myBin[c].pdata.ch4// * quantize(myBin[c].pdata.ch4)/100;
    //                     // log('ch41', quantize(myBin[c].pdata.ch4))
    //                 }else{
    //                     // bin[c].pdata.ch4 = 0;
    //                     log('no bearing')
    //                 }
    //             }               
    //         }

    //         if(latTotal && lonTotal && ch4Total){
    //             sites.push({
    //                 pdata:{
    //                     lat:latTotal/weightedCount,
    //                     lon:lonTotal/weightedCount,
    //                     ch4:ch4Total/avgCount
    //                 }
    //             })
    //         }
    //     }

    //     geodata = {
    //         "type": "FeatureCollection",
    //         "features": []
    //     };

    //     var greenIcon = L.icon({
    //         iconUrl: '/static/images/biohazard-64.png',
    //         shadowUrl: '/static/images/biohazard-64.png',

    //         iconSize:     [65, 65], // size of the icon
    //         shadowSize:   [0, 0], // size of the shadow
    //         iconAnchor:   [32, 32], // point of the icon which will correspond to marker's location
    //         shadowAnchor: [0, 0],  // the same for the shadow
    //         popupAnchor:  [0, 0] // point from which the popup should open relative to the iconAnchor
    //     });

    //     for(var i = 0 ; i < sites.length ; i++){
    //         geodata.features.push({
    //             "type": "Feature",
    //             "geometry": {
    //                 "type": "circle",
    //                 "coordinates": [ sites[i].pdata.lon,sites[i].pdata.lat ]
    //             },
    //             "properties": {
    //                 "type": "circle",
    //                 "size":sites[i].pdata.ch4 * 1.5
    //             }
    //         })  
    //         L.marker([sites[i].pdata.lat, sites[i].pdata.lon], {icon: greenIcon}).addTo(CSTATE.map2);
    //     }

    //     return;

    //     geodata.features.forEach(function(d) {
    //         d.LatLng = new L.LatLng(d.geometry.coordinates[1],d.geometry.coordinates[0])
    //     })

    //     // $('circle').remove();


    //     var feature = mapG.selectAll("circle")
    //       .data(geodata.features)
    //       .enter().append("circle").attr("r", function (d) {            
    //         return calcSVGsize(d.properties.size) 
    //       }).attr('opacity',function(d){
    //         if(d.properties.size > map_threshold){
    //             return .8;
    //         }else{
    //             return .5;
    //         }
    //       }).attr("class", function(d) { return "q" + quantize(d.properties.size) + "-9"; });

    //     CSTATE.map2.on("viewreset", redrawSVG);

    //     redrawSVG();

    // }

