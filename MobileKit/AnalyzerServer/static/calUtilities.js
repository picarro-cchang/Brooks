var CSTATE = {};
CSTATE.getDataLimit = 50;
CSTATE.startPos = 1;
CSTATE.carSpeed = [];
CSTATE.windLat = [];
CSTATE.windLon = [];
CSTATE.collecting = false;
CSTATE.speedFactor = 0;
CSTATE.latFactor = 0;
CSTATE.rotation = 0;
CSTATE.maxLatSpeed = 1;
CSTATE.applyFilter = false;

var CNSNT = {};
CNSNT.svcurl = '/rest';

$(function () {
    resize_page();
    setTimeout(processNext, 1000);
});

function cross(ctx, x, y, radius, shadow) {
    var size = radius * Math.sqrt(Math.PI) / 2;
    ctx.moveTo(x - size, y - size);
    ctx.lineTo(x + size, y + size);
    ctx.moveTo(x - size, y + size);
    ctx.lineTo(x + size, y - size);
}

function replot() {
    var i, wlon = [], wlat = [], wlonFilt = [], wlatFilt = [];
    var options = {
        xaxes: [{axisLabel: 'Vehicle speed (m/s)'}],
        yaxes: [{position: 'left', axisLabel: 'Apparent wind speed (m/s)'}],
        lines: { show: false },
        points: { show: true },
        shadowSize: 0,
        colors: ["#ff0000", "#c0c0c0", "#0000ff", "#c0c0c0", "#ff0000", "#0000ff"]
    };
    for (i=0; i<CSTATE.carSpeed.length; i++) {
        if (!CSTATE.applyFilter || (Math.abs(CSTATE.windLat[i]) <= CSTATE.maxLatSpeed)) {
            wlon.push([CSTATE.carSpeed[i], CSTATE.windLon[i]]);
            wlat.push([CSTATE.carSpeed[i], CSTATE.windLat[i]]);
        }
        else {
            wlonFilt.push([CSTATE.carSpeed[i], CSTATE.windLon[i]]);
            wlatFilt.push([CSTATE.carSpeed[i], CSTATE.windLat[i]]);
        }
    }
    maxSpeed = 20.0;
    bfLon = [[0.0,0.0],[maxSpeed,maxSpeed/CSTATE.speedFactor]];
    bfLat = [[0.0,0.0],[maxSpeed,maxSpeed/CSTATE.latFactor]];
    $.plot($("#placeholder"), [
        {data: wlon, points: {symbol:"circle"}}, {data: wlonFilt, points: {symbol:"circle"}},
        {data: wlat, points: {symbol:cross}}, {data: wlatFilt, points: {symbol:cross}},
        {data:bfLon, lines:{show:true}, points:{show:false}},
        {data:bfLat, lines:{show:true}, points:{show:false}}
        ], options);
}

// Button handlers

function startClick() {
    $("#id_start_button").toggleClass("active");
    if ($("#id_start_button").hasClass("active")) {
        $("#id_start_button").html("Stop");
        CSTATE.collecting = true;
    }
    else {
        $("#id_start_button").html("Start");
        CSTATE.collecting = false;
    }
}

function clearClick() {
    CSTATE.carSpeed = [];
    CSTATE.windLat = [];
    CSTATE.windLon = [];
}

function startNewLogClick() {
    var dtype = "jsonp";
    if (CSTATE.collecting) startClick();
    call_rest(CNSNT.svcurl, "restartDatalog", dtype, {weatherCode:0});
    CSTATE.carSpeed = [];
    CSTATE.windLat = [];
    CSTATE.windLon = [];
    CSTATE.startPos = 1;
}

function applyFilterClick() {
    CSTATE.applyFilter = $("#id_apply_filter").prop('checked');
}

function initialize(winH, winW) {
    CSTATE.winH = winH;
    CSTATE.winW = winW;
    console.log("initialize called with " + winH + " " + winW);
}

function resize_page() {
    CSTATE.winH = window.innerHeight;
    CSTATE.winW = window.innerWidth;
    var pge_wdth, hgth_top, lpge_wdth, new_width, new_height, new_top, cen;
    pge_wdth = $('#id_topbar').width() - ($('#id_sidebar').width() + 20);
    hgth_top = $('#id_topbar').height() + $('#id_feedback').height();

    if ($('#id_sidebar')) {
        lpge_wdth = $('#id_sidebar').width();
    } else {
        lpge_wdth = 0;
    }
    new_width = pge_wdth - 30;
    new_height = CSTATE.winH - hgth_top - 40;
    new_top = hgth_top;

    console.log('pge_wdth: ' + pge_wdth + ' hgth_top: ' + hgth_top + ' lpge_wdth: ' + lpge_wdth);
    console.log('new_height: ' + new_height + ' new_top: ' + new_top);
            
    $("#placeholder").width(new_width).height(new_height);
    replot();
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

function processNext() {
    getData();
}

function getData() {
    var dtype = "jsonp";
    var params = {'limit': CSTATE.getDataLimit, 'startPos': CSTATE.startPos,
                'varList': '["WS_WIND_LAT", "WS_WIND_LON", "CAR_SPEED"]'};
    call_rest(CNSNT.svcurl, "getData", dtype, params, successData, errorData);
    function successData(data) {
        if (data.result.hasOwnProperty('CAR_SPEED')) {
                if (CSTATE.collecting) {
                data.result.CAR_SPEED.forEach(function (x) {
                    CSTATE.carSpeed.push(x);
                });
                data.result.WS_WIND_LON.forEach(function (x) {
                    CSTATE.windLon.push(x);
                });
                data.result.WS_WIND_LAT.forEach(function (x) {
                    CSTATE.windLat.push(x);
                });
                CSTATE.startPos = data.result.lastPos + 1;
                console.log('Success! ' + CSTATE.startPos + ' ' + CSTATE.carSpeed.length);
            }
        }
        else console.log('No data arrived');
        processData();
        setTimeout(processNext, 1000);
    }
    function errorData(xOptions, textStatus) {
        console.log('Error: ' + textStatus + ' xOptions: ' + JSON.stringify(xOptions));
        setTimeout(processNext, 1000);
    }
}

function processData() {
    // Calculate regression line which passes through origin and take reciprocal of slope
    var i, sumSpeedSq=0, sumSpeedWlon=0, sumSpeedWlat=0;
    var sumSpeedSqFilt=0, sumSpeedWlonFilt=0;

    for (i=0; i<CSTATE.carSpeed.length; i++) {
        var cs = CSTATE.carSpeed[i];
        var wlon = CSTATE.windLon[i];
        var wlat = CSTATE.windLat[i];

        if (! (isNaN(cs) || isNaN(wlon) || isNaN(wlat))) {
            if (cs > 2.0 && cs < 20.0) {
                sumSpeedSq += cs*cs;
                sumSpeedWlon += cs*wlon;
                sumSpeedWlat += cs*wlat;
                if (!CSTATE.applyFilter || (Math.abs(wlat) <= CSTATE.maxLatSpeed)) {
                    sumSpeedSqFilt += cs*cs;
                    sumSpeedWlonFilt += cs*wlon;
                }
            }
        }
    }
    CSTATE.speedFactor = sumSpeedSqFilt/(sumSpeedWlonFilt + 1.0e-6);
    CSTATE.latFactor   = sumSpeedSq/(sumSpeedWlat + 1.0e-6);
    CSTATE.rotation = Math.atan2(sumSpeedWlat, sumSpeedWlon) * 180.0/Math.PI;
    $("#id_speed_factor").val(CSTATE.speedFactor.toFixed(3));
    $("#id_rotation").val(CSTATE.rotation.toFixed(1));
    replot();
}