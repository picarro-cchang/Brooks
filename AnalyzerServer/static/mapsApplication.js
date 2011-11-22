var minAmp = 0.1;
var svcurl = "rest";
var alog = "";
var center_longitude = -121.98432;
var center_latitude = 37.39604; 
var use_callback = true;
var log_selection_options = [];

// Normal js vars and functions
var net_abort_count = 0;
var follow = true;
var normal_path_color = "#0000FF";
var analyze_path_color = "#000000";

var resize_map_inprocess = false;
var resize_map_timer;
var current_mapTypeId;
var current_zoom;
var current_mode = 0;

var gglOptions;
var map;
var lastwhere;
var lastanastat;
var lastgpsstat;
var lastFit;
var lastInst;
var lastTimestring = '';
var lastDataFilename = "";
var lastPeakFilename = "";
var lastAnalysisFilename = "";
var dte = new Date();
var laststreamtime = dte.getTime();
var streamwarning = (1000 * 10);
var streamerror = (1000 * 30);
var streamdiff = 0;
var startTime;
var trange = 0;
var marker = null;
var peakMarkers = new Array();
var analysisMarkers = new Array();
var path = null;
var ignoreTimer = false;
var ignoreRequests = false;
var timer1;
var counter = 0;
var leakLine = 1;
var analysisLine = 1;
var startPos = null;
var gmt_offset = get_time_zone_offset();
var conc_array = new Array();

var methaneHistory = new Array();
var histMax = 200;

function setCookie(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    document.cookie = name+"="+value+expires+"; path=/";
};

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
};

function deleteCookie(name) {
    setCookie(name,"",-1);
};

function setModalChrome(hdr, msg, click) {
    var modalChrome = "";
    modalChrome = '<div class="modal" style="position: relative; top: auto; left: auto; margin: 0 auto; z-index: 1">'
    modalChrome += '<div class="modal-header">'
    modalChrome +='<h3>' + hdr + '</h3>'
    modalChrome +='</div>'    
    modalChrome +='<div class="modal-body">'    
    modalChrome += msg      
    modalChrome +='</div>'    
    modalChrome +='<div class="modal-footer">'    
    modalChrome +=click      
    modalChrome +='</div>'    
    modalChrome +='</div>'  
    return modalChrome
};

var modalNetWarning = setModalChrome('<h3>Connection Warning</h3>', 
		'<p><h3>There is a problem with the network connection. Please verify connectivity.</h3></p>',
		'<button id="id_warningCloseBtn" onclick="restoreModalDiv();" class="btn primary large">Close</button>'
);

var primeControlsBtn = '<li><div><button id="id_primeControlsBtn" type="button" onclick="primeControls();" class="btn primary large">Analyzer Controls</button></div></li>';
var restartBtn = '<div><button id="id_restartBtn" type="button" onclick="restart_datalog();" class="btn primary large">Restart Log</button></div>';
var captureBtn = '<div><button id="id_captureBtn" type="button" onclick="captureSwitch();" class="btn primary large">Switch to Capture Mode</button></div>';
var cancelCapBtn = '<div><button id="id_cancelCapBtn" type="button" onclick="cancelCapSwitch();" class="btn primary large">Cancel Capture</button></div>';
var calibrateBtn = '<div><button id="id_calibrateBtn" type="button" onclick="injectCal();" class="btn primary large">Calibrate</button></div>';
var shutdownBtn = '<div><button id="id_shutdownBtn" type="button" onclick="shutdown_analyzer();" class="btn primary large">Shutdown Analyzer</button></div>';

function primeControls() {
	var capOrCan = "";
    for (var i=0;i<modeBtn[current_mode].length;i++) {
        capOrCan += modeBtn[current_mode][i]+ "<br/>";
    }
	var primeControlBtns = setModalChrome('<h3>Analyzer Controls</h3>',
			restartBtn + "<br/>" +
			capOrCan  +
            calibrateBtn +
			"<br/><br/>" + shutdownBtn + "<br/>",
			'<button onclick="restoreModChangeDiv();" class="btn primary large">Close</button>'
	);
	$("#id_mod_change").html(primeControlBtns);
	$("#id_restartBtn").focus();
};

function restoreModChangeDiv() {
	$("#id_mod_change").html("");
};

var saved_html = "";
function restoreModalDiv() {
    $("#id_modal").html("");
    net_abort_count = 0;
};

function changeMinAmpVal(reqbool) {
    ignoreTimer = true;
    if (reqbool) {
        changeMinAmp();
    }
    $("#id_mod_change").html("");
    ignoreTimer = false;
};

function requestMinAmpChange() {
    var modalChangeMinAmp = setModalChrome('<h3>Change Minimum Amplitude</h3>',
            '<div><input type="text" id="id_amplitude" value="' + minAmp + '"/></div>',
			'<div><button onclick="changeMinAmpVal(false);" class="btn primary large">Cancel</button></div>' +
			'<div><button onclick="changeMinAmpVal(true);" class="btn primary large">OK</button></div>'
    );

    $("#id_mod_change").html(modalChangeMinAmp);
    $("#id_amplitude").focus();
};

function colorPathFromValveMask(value) {
    var value_float = parseFloat(value);
    var value_int = parseInt(value);
    var clr = normal_path_color;
    if (value_float != value_int) {
        clr = normal_path_color;
    } else {
        var value_binstr = value_int.toString(2);
        var value_lastbits = value_binstr.substring(value_binstr.length-1, value_binstr.length);
        if (value_lastbits == "1") {
            clr = analyze_path_color;
        } else {
            clr = normal_path_color;
        }
    }
    // when path color needs to change, we instatiate a new path
    // this is because strokeColor changes the entire Polyline, not just
    // new points
    if (clr != path.strokeColor) {
        path = new google.maps.Polyline(
                {   path:new google.maps.MVCArray(),
                    strokeColor: clr,
                    strokeOpactity:1.0,
                    strokeWeight:2  });
        path.setMap(map);
    }
};

function initialize_gdu(winH, winW) {
    pge_wdth = $('#id_topbar').width();
    $('#map_canvas').css('height', winH-200);
   	$('#map_canvas').css('width', pge_wdth);
    initialize_btns();

    if (use_callback) {
    	current_mapTypeId = google.maps.MapTypeId.ROADMAP;
    } else {
    	current_mapTypeId = google.maps.MapTypeId.SATELLITE;
    }

    
    var followCookie = getCookie("pcubed_follow");
    if (followCookie) follow = parseInt(followCookie);
    if (follow) $("#id_follow").attr("checked","checked")
    else $("#id_follow").removeAttr("checked")

    var minAmpCookie = getCookie("pcubed_minAmp");
    if (minAmpCookie) minAmp = parseFloat(minAmpCookie);
    $("#id_amplitude_btn").html(minAmp);

    var current_zoom = getCookie("pcubed_zoom");
    if (current_zoom) {
        current_zoom = parseInt(current_zoom)
    } else {
        current_zoom = 14
    }

    var latCookie = getCookie("pcubed_center_latitude");
    if (latCookie) center_latitude = parseFloat(latCookie);

    var lonCookie = getCookie("pcubed_center_longitude");
    if (lonCookie) center_longitude = parseFloat(lonCookie);
 
    var latlng = new google.maps.LatLng(center_latitude,center_longitude);
    var myOptions = {
      zoom: current_zoom,
      center: latlng,
      mapTypeId: current_mapTypeId
    };
    gglOptions = myOptions;
    
    initialize_map();
    timer1 = setTimeout(onTimer,1000);    
};

function initialize_btns() {
    $('#cancel').hide();

    if (use_callback) {
    	$("#id_primeControlButton_span").html(primeControlsBtn);
    } else {
    	$("#id_primeControlButton_span").html("");
        $("#id_exportButton_span").html("");
        var type = $("#id_selectLogBtn").html();
        if (type == "Live") {
            $("#id_exportButton_span").html("");
        } else {
            $("#id_exportButton_span").html(exportControlsBtn);
        }
    }
};

function initialize_map() {
    map = new google.maps.Map(document.getElementById("map_canvas"),gglOptions);
    google.maps.event.addListener(map, 'center_changed', function() {
        var where = map.getCenter();
        center_latitude = where.lat();
        center_longitude = where.lng();
        setCookie("pcubed_center_latitude",center_latitude,7);
        setCookie("pcubed_center_longitude",center_longitude,7);
        $("#center_latitude").val(where.lat())
        $("#center_longitude").val(where.lng())
    });
    google.maps.event.addListener(map, 'zoom_changed', function() {
        var new_zoom = map.getZoom();
        setCookie("pcubed_zoom", new_zoom, 7);
    });
    path = new google.maps.Polyline(
        {   path:new google.maps.MVCArray(),
            strokeColor: normal_path_color,
            strokeOpactity:1.0,
            strokeWeight:2  });
    path.setMap(map);
};

function resize_map() {
    pge_wdth = $('#id_topbar').width();
    hgth_top = $('#id_topbar').height() + $('#id_feedback').height() + $('#id_content_title').height();
    lpge_wdth = $('#id_sidebar').width();
    
    new_width = pge_wdth - margin;
    new_height = winH - hgth_top - margin - 40;
    new_top = hgth_top + margin;
    
	$("#id_modal_span").css('position', 'absolute');
	$("#id_modal_span").css('top', hgth_top);
    if (new_width < 640) {
        new_top = new_top + 30;
        new_height = new_height - 30;
		$("#id_modal_span").css('left', margin + 5);
	} else {
		$("#id_modal_span").css('left', lpge_wdth + margin + 5);
    }
    
    $('#map_canvas').css('position', 'absolute');
    $('#map_canvas').css('left', lpge_wdth + margin + 5);
    $('#map_canvas').css('top', new_top);
    $('#map_canvas').css('height', new_height);
    $('#map_canvas').css('width', new_width);
    
    cen = map.getCenter();
    google.maps.event.trigger(map, 'resize')
    map.setCenter(cen);
    
    resize_map_inprocess = false;
};

function resize_page() {
    if (!resize_map_inprocess) {
        resize_map_inprocess = true;
		resize_map_timer = setTimeout(resize_map,25);
    }
};

function restart_datalog() {
    if (confirm("Close current data log and open a new one?")) {
        call_rest("restartDatalog",{});
		restoreModChangeDiv();
    }
};

function shutdown_analyzer() {
    if (confirm("Do you want to shut down the Analyzer? \n\nWhen the analyzer is shutdown it can take 30 to 45 minutes warm up.")) {
        call_rest("shutdownAnalyzer",{});	
		restoreModChangeDiv();
    }
};

function get_time_zone_offset( ) {
    var current_date = new Date( );
    var gmt_offset = current_date.getTimezoneOffset( ) / 60;
    $('#gmt_offset').val(gmt_offset);
    rtn_offset = $('#gmt_offset').val()
    // alert(rtn_offset)
    return gmt_offset;
};


function call_rest(method,params,success_callback,error_callback) {
jQuery.ajax( {contentType:"application/json",
              data:$.param(params),
              dataType:"jsonp",
              url:"/rest/" + method,
              type:"get",
              timeout: 5000,
              success: success_callback,
              error: error_callback} );
}

/*
function call_rest(method,params,success_callback,error_callback) {
	var dtype = "json";
	if (use_callback) {dtype = "jsonp";}
	
	if (svcurl == "") {svcurl = "p3.picarro.com/pcubed/rest";}
	// var url = 'http://' + svcurl + '/' + method
    var url = "/rest/" + method;
	jQuery.ajax({contentType:"application/json",
        data: $.param(params),
        dataType: dtype,
        url: url,
        type: "get",
        timeout: 5000,
        ssuccess: success_callback,
        error: error_callback})
};
*/

function changeFollow() {
    var cval = $("#id_follow").attr("checked");
    if (cval == "checked") {
        if (lastwhere && map) map.setCenter(lastwhere);
        follow = true;
    } else {
        follow = false;
    }
    setCookie("pcubed_follow",(follow)? "1":"0",7);
};

function changeMinAmp() {
    minAmp = $("#id_amplitude").val();
    try {
        minAmpFloat = parseFloat(minAmp)
        if (isNaN(minAmpFloat)) {
            minAmpFloat = 0.1
        }
        minAmp = minAmpFloat
    } catch(err) {
        minAmp = 0.1
    }
    $("#id_amplitude_btn").html(minAmp);
    setCookie("pcubed_minAmp",minAmp,7);
    leakLine = 1;
    for(var i=0,len=peakMarkers.length; value=peakMarkers[i], i<len; i++) {
        var mkr = peakMarkers[i];
        mkr.setMap(null);
    }
    peakMarkers = new Array();
};

function onTimer() {
    if (ignoreTimer) timer1 = setTimeout(onTimer,1000);
    if (use_callback) {
    	getMode();
    } else {
        getData();
    }
};

function statCheck() {
    dte = new Date();
    var curtime = dte.getTime();
    streamdiff = curtime - laststreamtime;
    if (streamdiff > streamerror) { 
        $("#id_stream_stat").html("<font color='red'><strike>Stream</strike></font>");
        $("#id_gps_stat").html("<font color='red'><strike>GPS</strike></font>");
        $("#id_analyzer_stat").html("<font color='red'><strike>Analyzer</strike></font>");
    } else {
        if (streamdiff > streamwarning) { 
            $("#id_stream_stat").html("Stream Warning");
        } else {
            $("#id_stream_stat").html("Stream OK");
			if (lastFit) {
				if (lastFit == 0) {
                $("#id_gps_stat").html("<font color='red'><strike>GPS</strike></font>");
            } else {
                $("#id_gps_stat").html("GPS OK");
            }      
			} else {
				$("#id_gps_stat").html("<font color='red'><strike>GPS</strike></font>");
			}
			
            if (lastInst != 963) {
                $("#id_analyzer_stat").html("<font color='red'><strike>Analyzer</strike></font>");
            } else {
                $("#id_analyzer_stat").html("Analyzer OK");
            }
        };
    };        
};

function successData(data) {
    restoreModalDiv();
    var resultWasReturned = false;
    counter += 1;
    $("#counter").html("<h4>" + "Counter: " + counter + "</h4>");
    if (data.result) {
        if ("filename" in data.result) {
            if (lastDataFilename == data.result["filename"]) {
                resultWasReturned = true;
            } else {
                initialize_map();
                startPos = null;
            }
            lastDataFilename = data.result["filename"]
        }
    }
    if (resultWasReturned) {
        if ("lastPos" in data.result) {
            startPos = data.result["lastPos"];
        }
        if ("timeStrings" in data.result) {
            var timeStrings = data.result["timeStrings"];
            if (timeStrings.length>0) {
                var newTimestring = timeStrings[timeStrings.length-1];
                if (lastTimestring != newTimestring) {
                    dte = new Date();
                    laststreamtime = dte.getTime();
                    $("#placeholder").html("<h4>" + newTimestring + "</h4>");
                    lastTimestring = newTimestring;
                }
            }
            if ("GPS_FIT" in data.result) {
                if (data.result["GPS_FIT"].length>0) {
                    var newFit = data.result["GPS_FIT"][data.result["GPS_FIT"].length-1];
                    if (lastFit != newFit) {
                        lastFit = newFit;
                    }
                }
            }
            if ("INST_STATUS" in data.result) {
                if (data.result["INST_STATUS"].length>0) {
                    var newInst = data.result["INST_STATUS"][data.result["INST_STATUS"].length-1];
                    if (lastInst != newInst) {
                        lastInst = newInst;
                    }
                }
            }
            lat = data.result["GPS_ABS_LAT"];
            lon = data.result["GPS_ABS_LONG"];
            fit = data.result["GPS_FIT"]
            ch4 = data.result["CH4"];
            vmask = data.result["ValveMask"];

            n = ch4.length;
            if (n>0) {
                where = new google.maps.LatLng(lat[n-1],lon[n-1]);
                if (marker) marker.setMap(null);
                if (fit) {
                    if (fit[n-1] != 0) {
                        lastwhere = where;
                        marker = new google.maps.Marker({position:where});
                        if (follow) map.setCenter(where);
                        marker.setMap(map);
                    }
                } else {
                    lastwhere = where;
                    marker = new google.maps.Marker({position:where});
                    if (follow) map.setCenter(where);
                    marker.setMap(map);
                }
                if (n>1) {
                    ch4.shift()
                    n = n-1
                    methaneHistory = methaneHistory.concat(ch4);
                    if (methaneHistory.length >= histMax) methaneHistory.splice(0,methaneHistory.length-histMax);
                    $('#concentrationSparkline').sparkline(methaneHistory,{"chartRangeMin":1.8, "width":"180px", "height":"50px"});
                    $("#concData").html("<h4>" + "Current concentration " + ch4[n-1].toFixed(3) + " ppm" + "</h4>"); 
                    pathCoords = path.getPath();
                    for (i=1;i<n;i++) {
                        if (vmask) {
                            colorPathFromValveMask(vmask[i]);
                        }
                        if (fit) {
                            if (fit[i] != 0) {
                                pathCoords.push(new google.maps.LatLng(lat[i],lon[i]));
                                conc_array.push(ch4[i]);
                            }
                        } else {
                            pathCoords.push(new google.maps.LatLng(lat[i],lon[i]));
                            conc_array.push(ch4[i]);
                        }
                    }
                }
            }
        }
    }
    statCheck();
    showLeaks();
};

function successPeaks(data) {
    var i;
    var resultWasReturned = false;
    if (data.result) {
        if ("filename" in data.result) {
            if (lastPeakFilename == data.result["filename"]) {
                resultWasReturned = true;
            } else {
                leakLine = 1;
                for(var i=0,len=peakMarkers.length; value=peakMarkers[i], i<len; i++) {
                    var mkr = peakMarkers[i];
                    mkr.setMap(null);
                }
                peakMarkers = new Array();
            }
            lastPeakFilename = data.result["filename"]
        }
    }
    if (resultWasReturned) {
        if ("ch4" in data.result) {
            lat = data.result["lat"];
            lon = data.result["long"];
            ch4 = data.result["ch4"];
            amp = data.result["amp"];
            sigma = data.result["sigma"];
            leakLine = data.result["nextRow"];
            for (i=0;i<ch4.length;i++) {
                peakCoords = new google.maps.LatLng(lat[i],lon[i]);
                size = Math.pow(amp[i],1.0/4.0)
                fontsize = 20.0*Math.pow(amp[i],1.0/4.0)
                peakMarker = new google.maps.Marker({position:peakCoords,title:"Amp: "+amp[i].toFixed(2)+" HalfWidth: "+sigma[i].toFixed(1),
                                                     icon:"http://chart.apis.google.com/chart?chst=d_map_spin&chld="+size+"|0|40FFFF|"+fontsize+"|b|" + ch4[i].toFixed(1)});
                peakMarker.setMap(map);
                peakMarkers[peakMarkers.length] = peakMarker;
            }
        }
    }
    showAnalysis();
};

function successAnalysis(data) {
    var i;
    var resultWasReturned = false;
    if (data.result) {
        if ("filename" in data.result) {
            if (lastAnalysisFilename == data.result["filename"]) {
                resultWasReturned = true;
            } else {
                analysisLine = 1;
                for(var i=0,len=analysisMarkers.length; value=analysisMarkers[i], i<len; i++) {
                    var mkr = analysisMarkers[i];
                    mkr.setMap(null);
                }
                analysisMarkers = new Array();
            }
            lastAnalysisFilename = data.result["filename"]
        }
    }
    if (resultWasReturned) {
        if ("conc" in data.result) {
            lat = data.result["lat"];
            lon = data.result["long"];
            conc = data.result["conc"];
            delta = data.result["delta"];
            uncertainty = data.result["uncertainty"];
            analysisLine = data.result["nextRow"];
            for (i=0;i<conc.length;i++) {
                analysisCoords = new google.maps.LatLng(lat[i],lon[i]);
                var result = delta[i].toFixed(1)+" +/- "+uncertainty[i].toFixed(1);
                $("#analysis").html("Delta: " + result);
                result = result.replace("+","%2B").replace(" ","+");
                analysisMarker = new google.maps.Marker({position:analysisCoords,
                icon:new google.maps.MarkerImage(
                    "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=bbtl|"+result+"|FF8080|000000",
                    null, null, new google.maps.Point(0, 0))});
                analysisMarker.setMap(map);
                analysisMarkers[analysisMarkers.length] = analysisMarker;
            }
        }
    }
    timer1 = setTimeout(onTimer,1000);                        
};

function errorData(text) {
    net_abort_count += 1;
    if (net_abort_count >= 2) {
        $("#id_modal").html(modalNetWarning);
        $("id_warningCloseBtn").focus();
    }
    $("#errors").html(text);
    statCheck();
    showLeaks();
};

function errorPeaks(text) {
    net_abort_count += 1;
    if (net_abort_count >= 2) {
        $("#id_modal").html(modalNetWarning);
    }
    $("#errors").html(text); 
    showAnalysis();
};

function errorAnalysis(text) {
    net_abort_count += 1;
    if (net_abort_count >= 2) {
        $("#id_modal").html(modalNetWarning);
    }
    $("#errors").html(text); 
    timer1 = setTimeout(onTimer,1000);                        
};

var modeStrings = {0:"Survey Mode", 1:"Capture Mode", 2:"Capture Mode", 3:"Analyzing Peak"};
var modeBtn =     {0:[captureBtn],  1:[cancelCapBtn], 2:[cancelCapBtn], 3:[]};

function setModePane(mode) {
    var i;
    $("#mode").html(modeStrings[mode]);
    current_mode = mode;
};

function captureSwitch() {
    ignoreTimer = true;
    $("#analysis").html("");
    $("#id_mode_pane").html(modeStrings[1]);
    call_rest("driverRpc",{"func":"wrDasReg","args":"['PEAK_DETECT_CNTRL_STATE_REGISTER',1]"});
    ignoreTimer = false;
	restoreModChangeDiv();
};

function cancelCapSwitch() {
    if (confirm("Cancel capture and return to survey mode?")) {
        call_rest("driverRpc",{"func":"wrDasReg","args":"['PEAK_DETECT_CNTRL_STATE_REGISTER',0]"});
		restoreModChangeDiv();
    }
};

function injectCal() {
    call_rest("injectCal",{"valve":3,"samples":1});
    alert("Calibration pulse injected");
    restoreModChangeDiv();
};

function getMode() {
    call_rest("driverRpc",{"func":"rdDasReg","args":"['PEAK_DETECT_CNTRL_STATE_REGISTER']"},
        function(data,ts,jqXHR) {
            if ("value" in data.result) {
                var mode = data.result["value"];
                setModePane(mode);
            }
            getData();
        },
        function(jqXHR,ts,et) {  
            $("#errors").html(jqXHR.responseText); 
            getData();
        }
    );
};

function getData() {
    var params = {'startPos': startPos, 'alog': alog, 'gmtOffset': gmt_offset};
    call_rest("getData", params, 
        function(json, status, jqXHR) { 
            net_abort_count = 0;
            successData(json);
        },
        function(jqXHR,ts,et) {  
            errorData(jqXHR.responseText); 
        }
    );
}                

function showLeaks() {
    var params = {'startRow': leakLine, 'alog': alog, 'minAmp': minAmp, 'gmtOffset': gmt_offset};
    call_rest("getPeaks", params, 
        function(json, status, jqXHR) { 
            net_abort_count = 0;
            successPeaks(json);
        },
        function(jqXHR,ts,et) {  
            errorPeaks(jqXHR.responseText); 
        }
    );
} 

function showAnalysis() {
    var params = {'startRow': analysisLine, 'alog': alog, 'gmtOffset': gmt_offset};
    call_rest("getAnalysis", params, 
        function(json, status, jqXHR) { 
            net_abort_count = 0;
            successAnalysis(json);
        },
        function(jqXHR,ts,et) {  
            errorAnalysis(jqXHR.responseText); 
        }
    );
} 

function initialize(winH,winW)
{ 
    initialize_gdu(winH,winW);
};
