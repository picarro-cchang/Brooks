var mapmaster = mapmaster || {};

var CNSNT = mapmaster.CNSNT;
var TXT = mapmaster.TXT;
var CSTATE = mapmaster.CSTATE;
var HBTN = mapmaster.HBTN;
var LBTNS = mapmaster.LBTNS;
var COOKIE_NAMES = mapmaster.COOKIE_NAMES;

// Extensions to leaflet.js to support polygon markers

// L.PolygonMarker = L.Polygon.extend({
//     initialize: function (latlng, vertices, options) {
//         this._latlng = latlng;
//         this._vertices = this._convertPoints(vertices);
//         L.Polygon.prototype.initialize.call(this, [], options);
//         if (!L.Util.isArray(latlng) || typeof latlng[0] === 'number') {
//             this._latlng = L.latLng(latlng);
//         }
//     },
//     projectLatlngs: function () {
//         var anchor = this._map.latLngToLayerPoint(this._latlng);
//         this._originalPoints = [];
//         for (var i = 0; i < this._vertices.length; i++) {
//             this._originalPoints[i] = anchor.add(this._vertices[i]);
//         }
//         this._holePoints = [];
//         this._holes = [];
//     },
//     _convertPoints: function (points) {
//         var i, len;
//         for (i = 0, len = points.length; i < len; i++) {
//             if (L.Util.isArray(points[i]) && typeof points[i][0] !== 'number') {
//                 return;
//             }
//             points[i] = L.point(points[i][0],points[i][1]);
//         }
//         return points;
//     }
// });

// L.polygonMarker = function (latlng, vertices, options) {
//     return new L.PolygonMarker(latlng, vertices, options);
// };

//default (eng) values for dsp.  Override this
//for each language specific labels
// var COOKIE_PREFIX = "p3gdu";
// var COOKIE_NAMES = {};


var TIMER = {
        prime: null,
        resize: null,
        data: null, // timer for getData
        analysis: null, // timer for showAnalysis (getAnalysis)
        anote: null, // timer for getAnalysisNotes
        progress: null, //timer for updateProgress
        mode: null, // timer for getMode
        periph: null, // timer for checkPeriphUpdate
    };

var modeStrings = {0: TXT.survey_mode, 1: TXT.capture_mode, 2: TXT.capture_mode, 3: TXT.analyzing_mode, 4: TXT.inactive_mode,
                   5: TXT.cancelling_mode, 6: TXT.priming_mode, 7: TXT.purging_mode, 8: TXT.injection_pending_mode };



// function newMap(canvas) {
//     return new google.maps.Map(canvas, CSTATE.gglOptions);
//     // return new Microsoft.Maps.Map(canvas, CSTATE.bingOptions);
// }

function newLatLng(lat, lng) {
    return new L.LatLng(lat, lng);
}

// function newPolyline(map, clr) {
//     var pl = new google.maps.Polyline(
//         {path: new google.maps.MVCArray(),
//             strokeColor: clr,
//             strokeOpactity: 1.0,
//             strokeWeight: 2}
//     );
//     pl.setMap(map);
//     return pl;

//     // var pl = new Microsoft.Maps.Polyline([], {strokeColor: clr, strokeThickness: 2, });
//     // map.entities.push(pl);
//     // return pl;
// }

// function newPolygonWithoutOutline(map, clr, opacity, vertices, visible) {
//     var poly = new google.maps.Polygon(
//         {   paths: vertices,
//             strokeColor: "#000000",
//             strokeOpacity: 0.0,
//             strokeWeight: 0,
//             fillColor: clr,
//             visible: visible,
//             fillOpacity: opacity}
//     );
//     poly.setMap(map);
//     return poly;
// }

// function pushToPath(path, where) {
//     path.getPath().push(where);
//     // var locs = path.getLocations();
//     // locs.push(where);
//     // path.setLocations();
// }

// function newPoint(x, y) {
//     return new google.maps.Point(x, y);
//     // return new Microsoft.Maps.Point(x, y);
// }

// function newAnzLocationMarker(map) {
//     var mk = new google.maps.Marker({position: map.getCenter(), visible: false});
//     mk.setMap(map);
//     return mk;
//     // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null);
//     // map.entities.push(mk);
//     // return mk;
// }

// function concMarkerSize(ch4, scale, offset) {
//     var size = Math.max(1,Math.round(scale*Math.pow(Math.max(0.0,ch4-offset),0.5)));
//     return size;
// }

// function newConcMarker(map, latLng, size, color) {
//     mk = new google.maps.Marker({position: latLng, icon: new google.maps.MarkerImage(makeCircle(size,color), null, null, newPoint(0.5*size, 0.5*size))});
//     mk.setMap(map);
//     return mk;
// }

// function newWindRay(map, latLng, bearing, rayLength) {
//     // mk = new google.maps.Marker({position: latLng, zIndex: google.maps.MAX_ZINDEX+100, icon: new google.maps.MarkerImage(makeRay(bearing,rayLength),
//     //         null, null, newPoint(rayLength,rayLength))});
//     mk = new google.maps.Marker({position: latLng, icon: new google.maps.MarkerImage(makeRay(bearing,rayLength),
//             null, null, newPoint(rayLength,rayLength))});
//     mk.setMap(map);
//     return mk;
// }

// function newPeakMarker(map, latLng, amp, sigma, ch4) {
//     var size, fontsize, mk;
//     size = Math.max(0.75,0.25*Math.round(4.0*Math.pow(amp, 1.0 / 3.0)));
//     fontsize = 20.0 * size;
//     mk = new google.maps.Marker({position: latLng,
//         title: TXT.amp + ": " + amp.toFixed(2) + " " + TXT.sigma + ": " + sigma.toFixed(1),
//         icon: makeMarker(size,"rgba(64,255,255,255)","black",ch4.toFixed(1),"bold "+ fontsize +"px sans-serif","black")
//         });
//     mk.setMap(map);
//     return mk;
//     // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null);
//     // map.entities.push(mk);
//     // return mk;
// }

// function newWindMarker(map, latLng, radius, dir, dirSdev) {
//     var wr, wedge;
//     wedge = makeWindWedge(radius,dir,2*dirSdev);
//     wr = new google.maps.Marker({position: latLng, icon: new google.maps.MarkerImage(wedge.url,null,null,newPoint(wedge.radius,wedge.radius)),zIndex:0});
//     wr.setMap(map);
//     return wr;
// }

// function newAnalysisMarker(map, latLng, delta, uncertainty) {
//     var result, mk;
//     result = delta.toFixed(1) + " +/- " + uncertainty.toFixed(1);
//     result = result.replace("+", "%2B").replace(" ", "+");
//     mk = new google.maps.Marker({position: latLng,
//         icon: new google.maps.MarkerImage(
//             "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=bbtl|" + result + CNSNT.analysis_bbl_clr,
//             null,
//             null,
//             newPoint(0, 0)
//         )}
//         );
//     mk.setMap(map);
//     return mk;
//     // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null);
//     // map.entities.push(mk);
//     // return mk;
// }

function newNoteMarker(map, latLng, text, cat) {
    log('newNoteMarker')
    // var mk, pathTxt, mkrUrlFrag, mkrClr, mkrBbl, mkrOrigin, mkrAnchor;
    // pathTxt = (text.length <= 20) ? text : text.substring(0, 20) + " ...";
    // if (cat === "peak") {
    //     mkrClr = CNSNT.peak_bbl_clr;
    //     mkrBbl = CNSNT.peak_bbl_tail;
    //     mkrOrigin = CNSNT.peak_bbl_origin;
    //     mkrAnchor = CNSNT.peak_bbl_anchor;
    // } else {
    //     if (cat === "analysis") {
    //         mkrClr = CNSNT.analysis_bbl_clr;
    //         mkrBbl = CNSNT.analysis_bbl_tail;
    //         mkrOrigin = CNSNT.analysis_bbl_origin;
    //         mkrAnchor = CNSNT.analysis_bbl_anchor;
    //     } else {
    //         mkrClr = CNSNT.path_bbl_clr;
    //         mkrBbl = CNSNT.path_bbl_tail;
    //         mkrOrigin = CNSNT.path_bbl_origin;
    //         mkrAnchor = CNSNT.path_bbl_anchor;
    //     }
    // }
    // mkrUrlFrag = "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=" + mkrBbl + pathTxt + mkrClr;
    // mk = new google.maps.Marker({position: latLng,
    //     icon: new google.maps.MarkerImage(
    //         mkrUrlFrag,
    //         null,
    //         mkrOrigin,
    //         mkrAnchor
    //     )}
    //     );
    // mk.setMap(map);
    // return mk;
    // var mk = new Microsoft.Maps.Pushpin(map.getCenter(), null);
    // map.entities.push(mk);
    // return mk;
}

function updateNoteMarkerText(map, mkr, text, cat) {
    log('updateNoteMarkerText')
    // var pathTxt, mkrUrlFrag, mkrClr, mkrBbl, mkrOrigin, mkrAnchor, micon;
    // pathTxt = (text.length <= 20) ? text : text.substring(0, 20) + " ...";
    // if (cat === "peak") {
    //     mkrClr = CNSNT.peak_bbl_clr;
    //     mkrBbl = CNSNT.peak_bbl_tail;
    //     mkrOrigin = CNSNT.peak_bbl_origin;
    //     mkrAnchor = CNSNT.peak_bbl_anchor;
    // } else {
    //     if (cat === "analysis") {
    //         mkrClr = CNSNT.analysis_bbl_clr;
    //         mkrBbl = CNSNT.analysis_bbl_tail;
    //         mkrOrigin = CNSNT.analysis_bbl_origin;
    //         mkrAnchor = CNSNT.analysis_bbl_anchor;
    //     } else {
    //         mkrClr = CNSNT.path_bbl_clr;
    //         mkrBbl = CNSNT.path_bbl_tail;
    //         mkrOrigin = CNSNT.path_bbl_origin;
    //         mkrAnchor = CNSNT.path_bbl_anchor;
    //     }
    // }
    // mkrUrlFrag = "http://chart.googleapis.com/chart?chst=d_bubble_text_small&chld=" + mkrBbl + pathTxt + mkrClr;
    // micon = new google.maps.MarkerImage(
    //     mkrUrlFrag,
    //     null,
    //     mkrOrigin,
    //     mkrAnchor
    // );
    // mkr.setIcon(micon);
}

function removeListener(handle) {
    log('removeListener')
    // google.maps.event.removeListener(handle);
}

function repaintData() {
    log('repaintData')
    // CSTATE.ignoreTimer = true;
    // clearConcMarkerArray();
    // clearWindRayMarkerArray();
    // clearAnalysisMarkerArray();
    // CSTATE.clearConcMarkers = true;
    // CSTATE.ignoreTimer = false;
    // draw_legend();
}

function onPeakThresholdChange() {
    log('onPeakThresholdChange')
    // var i;
    // draw_legend();
    // repaintData();
    /*
    for (i in CSTATE.markerByPos) {
        var mk = CSTATE.markerByPos[i];
        var color = mk.myProperties.conc < CSTATE.peakThreshold ? CNSNT.concMarkerBelowThresholdColor : CNSNT.concMarkerAboveThresholdColor;
        var size = mk.myProperties.size;
        if (color != mk.myProperties.color) {
            mk.setIcon(new google.maps.MarkerImage(makeCircle(size,color), null, null, newPoint(0.5*size, 0.5*size)));
            mk.myProperties.color = color;
        }
    }
    */
}

function attachConcMarkerListener(concMarker) {
    log('attachConcMarkerListener')
    // var concMarkerListener;
    // concMarkerListener = new google.maps.event.addListener(concMarker, 'mouseover', function() {
    //     var i, pos = concMarker.myProperties.pos;
    //     CSTATE.concPlotNotFollowing = [];
    //     for (i=pos-100; i<pos+100; i++) {
    //         if (i in CSTATE.markerByPos) {
    //             CSTATE.concPlotNotFollowing.push([i,CSTATE.markerByPos[i].myProperties.conc]);
    //         }
    //     }
    //     if (!CSTATE.follow) {
    //         $.plot($("#concPlot2"), [ {data: CSTATE.concPlotNotFollowing, lines: {show: true}, color:"#f00" } ], {xaxis: {ticks:5}} );
    //     }
    // });
    // CSTATE.concMarkerListener[concMarkerListener] = concMarkerListener;
}

function clearConcMarkerArray() {
    log('clearConcMarkerArray')
    // var i, ky;
    // CSTATE.concMarkerLayer.clearLayers();
    // for (i in CSTATE.markerByPos) {
    //     CSTATE.markerByPos[i].setMap(null);
    // }
    // for (i in CSTATE.concMarkerListener) {
    //     removeListener(CSTATE.concMarkerListener[ky]);
    // }
    // CSTATE.markerByPos = {};
}

function clearWindRayMarkerArray() {
    log('clearWindRayMarkerArray')
    // var i;
    // CSTATE.windRayLayer.clearLayers();
    // for (i in CSTATE.windRayByPos) {
    //     CSTATE.windRayByPos[i].setMap(null);
    // }
    // CSTATE.windRayByPos = {};
}

// function clearAnalysisMarkerArray() {
//     log('clearAnalysisMarkerArray')
//     // var i, ky;
//     // CSTATE.analysisMarkerLayer.clearLayers();
//     // CSTATE.clearAnalyses = true;
//     // CSTATE.analysisNoteDict = {};
//     // for (i = 0; i < CSTATE.analysisMarkers.length; i += 1) {
//     //     CSTATE.analysisMarkers[i].setMap(null);
//     // }
//     // for (ky in CSTATE.analysisBblListener) {
//     //     removeListener(CSTATE.analysisBblListener[ky]);
//     // }
//     // CSTATE.analysisMarkers = [];
//     // CSTATE.analysisBblListener = {};
//     // CSTATE.analysisLine = 1;
// }

function clearAnalysisNoteMarkers() {
    log("clearAnalysisNoteMarkers")
    // var ky;
    // CSTATE.clearAnalysisNote = true;
    // for (ky in CSTATE.analysisNoteMarkers) {
    //     CSTATE.analysisNoteMarkers[ky].setMap(null);
    // }
    // for (ky in CSTATE.analysisNoteListener) {
    //     removeListener(CSTATE.analysisNoteListener[ky]);
    // }
    // CSTATE.analysisNoteMarkers = {};
    // CSTATE.analysisNoteListener = {};
    // CSTATE.nextAnalysisEtm = 0.0;
    // CSTATE.nextAnalysisUtm = 0.0;
}

// function clearMapListener() {
//     for (ky in CSTATE.mapListener) {
//         removeListener(CSTATE.mapListener[ky]);
//     }
//     CSTATE.mapListener = {};
// }

// function clearPathListener() {
//     for (ky in CSTATE.pathListener) {
//         removeListener(CSTATE.pathListener[ky]);
//     }
//     CSTATE.pathListener = {};
// }

// function showWindRay() {
//     var i;
//     for (i in CSTATE.windRayByPos) CSTATE.windRayByPos[i].setVisible(true);
// }

// function hideWindRay() {
//     var i;
//     for (i in CSTATE.windRayByPos) CSTATE.windRayByPos[i].setVisible(false);
// }

function single_quote(txt) {
    return "'" + txt + "'";
}

function double_quote(txt) {
    return '"' + txt + '"';
}

// function resetLeakPosition() {
//     clearAnalysisMarkerArray();
// }

function timeStringFromEtm(etm) {
    var gmtoffset_mil, etm_mil, tmil, tdate, tstring;
    etm_mil = (etm * 1000);
    tdate = new Date(etm_mil);
    //tstring = tdate.toLocaleDateString() + " " + tdate.toLocaleTimeString();
    tstring = tdate.toString().substring(0,24);
    return tstring;
}

function MapConcPlot(div, map) {
    var controlUI, controlText;

    // Set CSS styles for the DIV containing the control
    // Setting padding to 5 px will offset the control
    // from the edge of the map.
    div.style.padding = '5px';

    // Set CSS for the control border.
    controlUI = document.createElement('DIV');
    controlUI.style.backgroundColor = 'white';
    controlUI.style.borderStyle = 'solid';
    controlUI.style.borderWidth = '2px';
    controlUI.style.cursor = 'pointer';
    controlUI.style.textAlign = 'center';
    controlUI.title = TXT.click_show_cntls;
    div.appendChild(controlUI);

    // Set CSS for the control interior.
    controlText = document.createElement('DIV');
    controlText.style.fontFamily = 'Arial,sans-serif';
    controlText.style.fontSize = '12px';
    controlText.style.paddingLeft = '4px';
    controlText.style.paddingRight = '4px';
    controlText.innerHTML = '<div id="concPlot" style="width:160px;height:90px;"></div>';

    controlUI.appendChild(controlText);
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
    controlText.innerHTML = TXT.map_controls  + "<br/>" + CSTATE.minAmp + "&nbsp; &nbsp;" + CSTATE.stabClass;
    controlUI.appendChild(controlText);

    google.maps.event.addDomListener(controlUI, 'click', function () {
        modalPaneMapControls();
    });

    this.changeControlText = function(newText) {
        controlText.innerHTML = newText;
    }
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
        L.DomEvent.on(container, 'click', modalPaneMapControls);
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
        CSTATE.map2 = L.map('map2_canvas').setView([CSTATE.center_lat,CSTATE.center_lon], CSTATE.current_zoom);

        var mapquestUrl = 'http://{s}.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png',
        subDomains = ['otile1','otile2','otile3','otile4'],
        mapquestAttrib = '<a href="http://open.mapquest.co.uk" target="_blank">MapQuest</a>, <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>.'
        var mapquest = new L.TileLayer(mapquestUrl, {maxZoom: 20, attribution: mapquestAttrib, subdomains: subDomains});
        mapquest.addTo(CSTATE.map2);

        /*
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(CSTATE.map2);
        */
        L.control.scale().addTo(CSTATE.map2);
        CSTATE.map2.addControl(new MapConcPlot2());
        CNSNT.mapControl = new MapControl2();
        CSTATE.map2.addControl(CNSNT.mapControl);
        CSTATE.map2.on('zoomend', function() {
            CSTATE.current_zoom = CSTATE.map2.getZoom();
            setCookie(COOKIE_NAMES.zoom, CSTATE.current_zoom, CNSNT.cookie_duration);
        });
        CSTATE.map2.on('moveend', function() {
            var where = CSTATE.map2.getCenter();
            CSTATE.center_lat = where.lat;
            CSTATE.center_lon = where.lng;
            setCookie(COOKIE_NAMES.center_latitude, CSTATE.center_lat, CNSNT.cookie_duration);
            setCookie(COOKIE_NAMES.center_longitude, CSTATE.center_lon, CNSNT.cookie_duration);
        });
        CSTATE.carMarker = L.marker([CSTATE.center_lat,CSTATE.center_lon]).addTo(CSTATE.map2);
    }
    else {
        CSTATE.concMarkerLayer.clearLayers();
        CSTATE.windRayLayer.clearLayers();
        CSTATE.analysisMarkerLayer.clearLayers();
        CSTATE.layerControl.removeFrom(CSTATE.map2);
    }
    CSTATE.concMarkerLayer = L.layerGroup([]).addTo(CSTATE.map2);
    CSTATE.windRayLayer = L.layerGroup([]).addTo(CSTATE.map2);
    CSTATE.analysisMarkerLayer = L.layerGroup([]).addTo(CSTATE.map2);
    CSTATE.layerControl = L.control.layers(null,{"Concentration":CSTATE.concMarkerLayer, "Wind Direction":CSTATE.windRayLayer });
    CSTATE.layerControl.addTo(CSTATE.map2);
}

function initialize_map() {
    var where, mapListener;

    CSTATE.concMarkerOffset = null;
    newMap2();

    CSTATE.prevInferredStabClass = null;

    CSTATE.firstData = true;

    draw_legend();
}

function resize_map() {
    var pge_wdth, hgth_top, lpge_wdth, new_width, new_height, new_top, cen;
    pge_wdth = $('#id_topbar').width();
    hgth_top = $('#id_topbar').height() + $('#id_feedback').height() + $('#id_content_title').height();


    if ($('#id_sidebar')) {
        lpge_wdth = $('#id_sidebar').width();
    } else {
        lpge_wdth = 0;
    }
    new_width = pge_wdth - CNSNT.hmargin;

    // !!!!
    new_width = '1000px';


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
/*
    $('#map_canvas').css('position', 'absolute');
    $('#map_canvas').css('left', lpge_wdth + CNSNT.hmargin);
    $('#map_canvas').css('top', new_top);
    $('#map_canvas').css('height', new_height);
    $('#map_canvas').css('width', new_width/2);
    $('#map_canvas').css('border', '2px solid red');
*/
    $('#map2_canvas').css('position', 'absolute');
    $('#map2_canvas').css('left', lpge_wdth + CNSNT.hmargin);
    $('#map2_canvas').css('top', new_top);
    $('#map2_canvas').css('height', new_height);
    $('#map2_canvas').css('width', new_width);
    $('#map2_canvas').css('border', '2px solid green');

    $('#id_feedback').css('width', new_width);
    $('#id_below_map').css('position', 'absolute');
    $('#id_below_map').css('left', lpge_wdth + CNSNT.hmargin);
    $('#id_below_map').css('top', new_top + new_height);
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


// function doExport(log) {
//     var exptlog = "export:" + log;
//     get_ticket(null, exptlog);
//     //url = CNSNT.svcurl + blah;
// }

// function exportLog() {
//     var url = CNSNT.svcurl + '/sendLog?alog=' + CSTATE.alog;

//     $('#id_exptLogBtn').html(TXT.working + "...");
//     $('#id_exptLogBtn').redraw;

//     doExport(CSTATE.alog);
// }

// function exportPeaks() {
//     var apath, url;

//     $('#id_exptPeakBtn').html(TXT.working + "...");
//     $('#id_exptPeakBtn').redraw;

//     apath = CSTATE.alog.replace(".dat", ".peaks");
//     doExport(apath);
// }

// function exportAnalysis() {
//     var apath, url;

//     $('#id_exptAnalysisBtn').html(TXT.working + "...");
//     $('#id_exptAnalysisBtn').redraw;

//     apath = CSTATE.alog.replace(".dat", ".analysis");
//     doExport(apath);
// }

// function exportNotes() {
//     var apath, url;

//     $('#id_exptNoteBtn').html(TXT.working + "...");
//     $('#id_exptNoteBtn').redraw;

//     apath = CSTATE.alog.replace(".dat", ".notes");
//     doExport(apath);
// }

function modalPaneSelectLog() {
    // var options, i, len, row, selected, opendiv, closediv, btns, modalChangeMinAmp, hdr, body, footer, c1array, c2array;
    // options = "";

    // len = CNSNT.log_sel_opts.length;
    // for (i = 0; i < len; i += 1) {
    //     row = CNSNT.log_sel_opts[i];
    //     selected = "";
    //     if (CSTATE.alog === row[0]) {
    //         selected = ' selected="selected" ';
    //     }
    //     options += '<option value="' + row[0] + '"' + selected + '>' + row[1] + '</option>';
    // }

    // c1array = [];
    // c2array = [];

    // c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    // c2array.push('style="border-style: none; width: 50%;"');

    // c1array.push('<select id="id_selectLog" class="large" style="width: 100%;">' + options + '</select>');
    // c2array.push(HBTN.switchLogBtn);

    // if (CSTATE.prime_available) {
    //     c1array.push("");
    //     c2array.push("");
    //     c1array.push('');
    //     c2array.push(HBTN.switchToPrimeBtn);
    // }
    // body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

    // c1array = [];
    // c2array = [];
    // c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    // c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    // c1array.push('<h3>' + TXT.select_log + '</h3>');
    // c2array.push(HBTN.modChangeCloseBtn);
    // hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    // footer = '';

    // modalChangeMinAmp = setModalChrome(
    //     hdr,
    //     body,
    //     footer
    //     );

    // $("#id_mod_change").html(modalChangeMinAmp);
    // $("#id_amplitude").focus();
}

function switchLog() {
    // var newlog, newtitle, i, len, row, selected;

    // newlog = $("#id_selectLog").val();
    // newtitle = "";

    // len = CNSNT.log_sel_opts.length;
    // for (i = 0; i < len; i += 1) {
    //     row = CNSNT.log_sel_opts[i];
    //     selected = "";
    //     if (newlog === row[0]) {
    //         newtitle = row[1];
    //     }
    // }

    // if (newlog !== CSTATE.alog) {
    //     initialize_map();
    //     CSTATE.alog = newlog;
    //     CSTATE.alog_peaks = CSTATE.alog.replace(".dat", ".peaks");
    //     CSTATE.alog_analysis = CSTATE.alog.replace(".dat", ".analysis");
    //     CSTATE.startPos = null;
    //     resetLeakPosition();
    //     clearAnalysisNoteMarkers();

    //     $("#id_selectLogBtn").html(newtitle);
    //     if (CNSNT.prime_view) {
    //         // $("#concentrationSparkline").html("Loading..");
    //         $("#id_exportButton_span").html("");
    //         $("#id_selectAnalyzerBtn").css("display", "none");
    //         $("#id_selectAnalyzerBtn").css("visibility", "hidden");
    //     } else {
    //         // $('#concentrationSparkline').html("");
    //         if (newtitle === "Live") {
    //             $("#id_exportButton_span").html("");
    //         } else {
    //             $("#id_exportButton_span").html(LBTNS.downloadBtns + '<br/>');
    //         }
    //     }
    // }
    // $("#id_mod_change").html("");
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

// function testPrime() {
//     var params, url;

//     if (CSTATE.prime_test_count >= 10) {
//         TIMER.prime = null;
//     } else {
//         if (CNSNT.prime_view) {
//             TIMER.prime = null;
//         } else {
//             params = {'startPos': 'null', 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset};
//             url = CNSNT.callbacktest_url + '/' + 'getData';

//             $.ajax({contentType: "application/json",
//                 data: $.param(params),
//                 dataType: "jsonp",
//                 url: url,
//                 type: "get",
//                 timeout: CNSNT.callbacktest_timeout,
//                 success: function () {
//                     CSTATE.prime_available = true;
//                     TIMER.prime = null;
//                 },
//                 error: function () {
//                     CSTATE.prime_available = false;
//                     TIMER.prime = setTimeout(primeTimer, 10000);
//                 }
//                 });
//         }
//     }
// }

// function primeTimer() {
//     testPrime();
//     CSTATE.prime_test_count += 1;
// }

// function restoreModChangeDiv() {
//     if (TIMER.progress !== null) {
//         clearTimeout(TIMER.progress);
//         TIMER.progress = null;
//         CSTATE.end_warming_status = true;
//     }
//     $("#id_mod_change").html("");
// }

function restoreModalDiv() {
    $("#id_modal").html("");
    CSTATE.net_abort_count = 0;GPS_FIT
}

// function changeMinAmpVal(reqbool) {
//     CSTATE.ignoreTimer = true;
//     if (reqbool) {
//         changeMinAmp();
//     }
//     $("#id_mod_change").html("");
//     CSTATE.ignoreTimer = false;
// }

// function changeStabClassVal(reqbool) {
//     CSTATE.ignoreTimer = true;
//     if (reqbool) {
//         changeStabClass();
//     }
//     $("#id_mod_change").html("");
//     CSTATE.ignoreTimer = false;
// }

// function changePeakThresholdVal(reqbool) {
//     CSTATE.ignoreTimer = true;
//     if (reqbool) {
//         changePeakThreshold();
//     }
//     $("#id_mod_change").html("");
//     CSTATE.ignoreTimer = false;
// }


// function copyCliboard() {
//     $("#id_mod_change").html("");
// }

// function workingBtnPassThrough(btnBase) {
//     $('#id_' + btnBase).html(TXT.working + "...");
//     $('#id_' + btnBase).redraw;
//     setTimeout(btnBase + '()', 2);
// }

// function showAnoteCb() {
//     var btxt;

//     if (CSTATE.showAnote === false) {
//         CSTATE.showAnote = true;
//     } else {
//         CSTATE.showAnote = false;
//         clearAnalysisNoteMarkers();
//     }
//     setCookie(COOKIE_NAMES.anote, (CSTATE.showAnote) ? "1" : "0", CNSNT.cookie_duration);

//     btxt = TXT.show_txt;
//     if (CSTATE.showAnote) {
//         btxt = TXT.hide_txt;
//     }
//     btxt += " " + TXT.anote;
//     $('#id_showAnoteCb').html(btxt);
// }

// function showAbubbleCb() {
//     var btxt;

//     if (CSTATE.showAbubble === false) {
//         CSTATE.showAbubble = true;
//     } else {
//         CSTATE.showAbubble = false;
//         clearAnalysisMarkerArray();
//     }
//     setCookie(COOKIE_NAMES.abubble, (CSTATE.showAbubble) ? "1" : "0", CNSNT.cookie_duration);

//     btxt = TXT.show_txt;
//     if (CSTATE.showAbubble) {
//         btxt = TXT.hide_txt;
//     }
//     btxt += " " + TXT.abubble;
//     $('#id_showAbubbleCb').html(btxt);
// }

// function showWindRayCb() {
//     var btxt;

//     if (CSTATE.showWindRay === false) {
//         CSTATE.showWindRay = true;
//         showWindRay();
//     } else {
//         CSTATE.showWindRay = false;
//         hideWindRay();
//     }
//     setCookie(COOKIE_NAMES.windRay, (CSTATE.showWindRay) ? "1" : "0", CNSNT.cookie_duration);

//     btxt = TXT.show_txt;
//     if (CSTATE.showWindRay) {
//         btxt = TXT.hide_txt;
//     }
//     btxt += " " + TXT.windRay;
//     $('#id_showWindRayCb').html(btxt);
// }

// function requestMinAmpChange() {
//     var modalChrome, hdr, body, footer, c1array, c2array;
//     var textinput;

//     textinput = '<div><input type="text" id="id_amplitude" style="width:90%; height:25px; font-size:20px; text-align:center;" value="' + CSTATE.minAmp + '"/></div>';

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 50%;"');
//     c1array.push(textinput);
//     c2array.push(HBTN.changeMinAmpOkBtn);
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push('<h3>' + TXT.change_min_amp + '</h3>');
//     c2array.push(HBTN.changeMinAmpCancelBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
//     $("#id_amplitude").focus();
// }

// function requestStabClassChange() {
//     var modalChrome, hdr, body, footer, c1array, c2array;

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 50%;"');
//     c1array.push(stabClassCntl('style="width: 100%;"'));
//     c2array.push(HBTN.changeStabClassOkBtn);
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push('<h3>' + TXT.change_stab_class + '</h3>');
//     c2array.push(HBTN.changeStabClassCancelBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
// }

// function requestPeakThresholdChange() {
//     var modalChrome, hdr, body, footer, c1array, c2array;
//     var textinput;

//     textinput = '<div><input type="text" id="id_peak_threshold" style="width:90%; height:25px; font-size:20px; text-align:center;" value="' + CSTATE.peakThreshold + '"/></div>';

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 50%;"');
//     c1array.push(textinput);
//     c2array.push(HBTN.changePeakThresholdOkBtn);
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push('<h3>' + TXT.change_peak_threshold + '</h3>');
//     c2array.push(HBTN.changePeakThresholdCancelBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
//     $("#id_peak_threshold").focus();
// }

// function updateNote(cat, logname, etm, note, type) {
//     var method, docrow;

//     //alert("updateNote: " + logname + "\n" + etm + "\n" + note + "\n" + type);
//     if (cat === 'analysis') {
//         datadict = CSTATE.analysisNoteDict[etm];
//     }
//     if (datadict) {
//         datadict.note = note;
//         datadict.db = true;
//         datadict.lock = true;
//     } else {
//         datadict = {"note": note, "db": true, "lock": true};
//     }
//     var ltype = 'dat';
//     if (cat === 'analysis') {
//         CSTATE.analysisNoteDict[etm] = datadict;
//         ltype = 'analysis';
//     }
//     //alert("etm: " + etm);
//     docrow = {"qry": "dataIns"
//             , "LOGNAME": logname
//             , "EPOCH_TIME": etm
//             , "LOGTYPE": ltype
//             , "NOTE_TXT": note};

//     if (type === 'add') {
//         docrow.INSERT_USER = CNSNT.user_id;
//     } else {
//         docrow.UPDATE_USER = CNSNT.user_id;
//     }

//     ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
//     resource = CNSNT.resource_AnzLogNote; //"gdu/<TICKET>/1.0/AnzLog"
//     resource = insertTicket(resource);
//     call_rest(ruri, resource, "jsonp", docrow,
//         function (data) {
//             if (data) {
//                 if (data.indexOf("ERROR: invalid ticket") !== -1) {
//                     get_ticket();
//                     TIMER.getAnalyzerList = setTimeout(getAnalyzerListTimer, CNSNT.fast_timer);
//                     return;
//                 } else {
//                     var datadict;
//                     if (cat === 'analysis') {
//                         datadict = CSTATE.analysisNoteDict[etm];
//                     }
//                     if (datadict) {
//                         datadict.lock = false;
//                     } else {
//                         datadict = {lock: false};
//                     }
//                     if (cat === 'analysis') {
//                         CSTATE.analysisNoteDict[etm] = datadict;
//                     }
//                 }
//             }
//         },
//         function () {
//             var datadict;
//             if (cat === 'analysis') {
//                 datadict = CSTATE.analysisNoteDict[etm];
//             }
//             if (datadict) {
//                 datadict.lock = false;
//             } else {
//                 datadict = {lock: false};
//             }
//             if (cat === 'analysis') {
//                 CSTATE.analysisNoteDict[etm] = datadict;
//             }
//         }
//     );
// }

// function noteUpdate(reqbool, etm, cat) {
//     var noteText, datadict, currnote, ntype, fname, pathCoords, pathMarker, mkr, mkrClr, mkrBbl, mkrOrigin, mkrAnchor;

//     if (reqbool) {
//         if (cat === 'analysis') {
//             datadict = CSTATE.analysisNoteDict[etm];
//             fname = CSTATE.lastAnalysisFilename;
//         }
//         noteText = $("#id_note").val();
//         currnote = datadict.note;
//         if (datadict.db === true) {
//             ntype = "update";
//         } else {
//             ntype = "add";
//         }

//         if (noteText !== currnote) {
//             if (cat === "analysis") {
//                 mkrClr = CNSNT.analysis_bbl_clr;
//                 mkrBbl = CNSNT.analysis_bbl_tail;
//                 mkrOrigin = CNSNT.analysis_bbl_origin;
//                 mkrAnchor = CNSNT.analysis_bbl_anchor;
//                 mkr = CSTATE.analysisNoteMarkers[etm];
//             }
//             if (ntype === "add") {
//                 pathCoords = newLatLng(datadict.lat, datadict.lon);
//                 pathMarker = newNoteMarker(CSTATE.map, pathCoords, noteText, cat);

//                 if (cat === 'analysis') {
//                     CSTATE.analysisNoteMarkers[etm] = pathMarker;
//                 }
//                 attachMarkerListener(pathMarker, etm, cat);
//             } else {
//                 updateNoteMarkerText(CSTATE.map, mkr, noteText, cat);
//             }

//             CSTATE.ignoreTimer = true;
//             //alert("NEW\netm: " + etm + "\ntext: " + noteText);
//             updateNote(cat, fname, etm, noteText, ntype);
//             CSTATE.ignoreTimer = false;
//         }
//     }
//     $("#id_smodal").html("");
// }

// function sortNoteList(a, b) {
//     return a.etm - b.etm;
// }

// function notePaneSwitch(selobj) {
//     var idx;
//     idx = selobj.selectedIndex;
//     notePane(CSTATE.noteSortSel[idx].etm, CSTATE.noteSortSel[idx].cat);
// }

function notePane(etm, cat) {
    log('notePane')
    // var k, kk, options, lst, selected, dsp, noteSel, logseldiv, modalPinNote, hdr, body, buttons, proplist, vlu, datadict, currnote, catstr;

    // noteSel = [];
    // for (kk in CSTATE.analysisNoteDict) {
    //     ko = {
    //         etm: kk,
    //         timeStrings: timeStringFromEtm(parseFloat(kk)),
    //         cat: "analysis"
    //     };
    //     noteSel.push(ko);
    // }
    // options = "";
    // CSTATE.noteSortSel = noteSel.sort(sortNoteList);
    // for (i = 0; i < CSTATE.noteSortSel.length; i += 1) {
    //     selected = "";
    //     if (CSTATE.noteSortSel[i].cat === cat && CSTATE.noteSortSel[i].etm === etm.toString()) {
    //         selected = ' selected="selected" ';
    //     }
    //     dsp = TXT[CSTATE.noteSortSel[i].cat] + ": " + CSTATE.noteSortSel[i].timeStrings;
    //     options += '<option value="' + CSTATE.noteSortSel[i].cat + ":" + CSTATE.noteSortSel[i].etm + '"' + selected + '>' + dsp + '</option>';
    // }
    // logseldiv = "";
    // k = 'note_list';
    // vlu = '<select onchange="notePaneSwitch(this)">';
    // vlu += options;
    // vlu += '</select>';
    // logseldiv += '<div class="clearfix">';
    // logseldiv += '<label for="id_' + k + '">' + TXT[k]  +  '</label>';
    // logseldiv += '<div class="input">';
    // logseldiv += '<span id="id_' + k + '" class="input large">' + vlu + '</span>';
    // logseldiv += '</div>';
    // logseldiv += '</div>';
    // logseldiv += '<br/>';

    // catstr = "'" + cat + "'";
    // if (cat === 'analysis') {
    //     datadict = CSTATE.analysisNoteDict[etm];
    //     lst = CNSNT.analysisNoteList;
    // }

    // hdr = '<h3>' + TXT[cat]  +  ':&nbsp;' + timeStringFromEtm(etm) + '</h3>';
    // proplist = '';

    // $.each(lst, function (ky) {
    //     k = lst[ky];
    //     if (datadict[k]) {
    //         if (k === 'amp') {
    //             vlu = datadict[k].toFixed(2);
    //         } else {
    //             if (k === 'sigma') {
    //                 vlu = datadict[k].toFixed(1);
    //             } else {
    //                 vlu = datadict[k].toFixed(3);
    //             }
    //         }
    //         proplist += '<div class="clearfix">';
    //         proplist += '<label for="id_' + k + '">' + TXT[k]  +  '</label>';
    //         proplist += '<div class="input">';
    //         proplist += '<span id="id_' + k + '" class="uneditable-input">' + vlu + '</span>';
    //         proplist += '</div>';
    //         proplist += '</div>';
    //     }
    // });
    // if (datadict.note) {
    //     currnote = datadict.note;
    // } else {
    //     currnote = '';
    // }

    // if (CNSNT.annotation_url) {
    //     proplist += '<div class="clearfix">';
    //     proplist += '<label for="id_note">' + TXT.note + '</label>';
    //     proplist += '<div class="input">';

    //     if (datadict.lock === true) {
    //         proplist += '<span class="large uneditable-input" id="id_note" name="textarea">';
    //         proplist += currnote;
    //         proplist += '</span>';
    //     } else {
    //         proplist += '<textarea class="large" id="id_note" name="textarea">';
    //         proplist += currnote;
    //         proplist += '</textarea>';
    //     }

    //     proplist += '</div>';
    //     proplist += '</div>';
    // }

    // body = '';
    // body += logseldiv;
    // body += '<div class="row">';
    // body += '<div class="span2 columns">';
    // body += '<fieldset>';
    // body += proplist;
    // body += '</fieldset>';
    // body += '</div>';
    // body += '</div>';


    // buttons = '';
    // if (CNSNT.annotation_url) {
    //     buttons += '<div style="display: hidden;"><button onclick="noteUpdate(true, ' + etm + ',' + catstr + ');"/></div>';
    // }
    // buttons += '<div><button onclick="noteUpdate(false, ' + etm + ',' + catstr + ');" class="btn large">' + TXT.close + '</button></div>';

    // if (CNSNT.annotation_url) {
    //     buttons += '<div><button onclick="noteUpdate(true, ' + etm + ', ' + catstr + ');" class="btn large">' + TXT.save_note + '</button></div>';
    // }

    // modalPinNote = setModalChrome(hdr, body, buttons);

    // $("#id_smodal").html(modalPinNote);
    // $("#id_note").focus();
}

function modalPaneMapControls() {
    log('modalPaneMapControls')
    // var modalPane, showAbubbleCntl, showAnoteCntl, changeMinAmpCntl,
    //     changeStabClassCntl, showWindRayCntl, changePeakThresholdCntl;
    // var achkd, abchkd, wrchkd, hdr, body, footer, c1array, c2array;

    // achkd = TXT.show_txt;
    // if (CSTATE.showAnote) {
    //     achkd = TXT.hide_txt;
    // }
    // achkd += " " + TXT.anote;

    // abchkd = TXT.show_txt;
    // if (CSTATE.showAbubble) {
    //     abchkd = TXT.hide_txt;
    // }
    // abchkd += " " + TXT.abubble;

    // wrchkd = TXT.show_txt;
    // if (CSTATE.showWindRay) {
    //     wrchkd = TXT.hide_txt;
    // }
    // wrchkd += " " + TXT.windRay;

    // showAnoteCntl = '<div><button id="id_showAnoteCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showAnoteCb") + ');" class="btn btn-fullwidth">' + achkd + '</button></div>';
    // showAbubbleCntl = '<div><button id="id_showAbubbleCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showAbubbleCb") + ');" class="btn btn-fullwidth">' + abchkd + '</button></div>';

    // changeMinAmpCntl = '<div><button id="id_changeMinAmp"  type="button" onclick="workingBtnPassThrough(' + single_quote("requestMinAmpChange") + ');"   class="btn btn-fullwidth">' + TXT.change_min_amp + ': ' + CSTATE.minAmp + '</button></div>';
    // changeStabClassCntl = '<div><button id="id_changeStabClass"  type="button" onclick="workingBtnPassThrough(' + single_quote("requestStabClassChange") + ');"   class="btn btn-fullwidth">' + TXT.change_stab_class + ': ' + CSTATE.stabClass + '</button></div>';
    // changePeakThresholdCntl = '<div><button id="id_changePeakThreshold"  type="button" onclick="workingBtnPassThrough(' + single_quote("requestPeakThresholdChange") + ');"   class="btn btn-fullwidth">' + TXT.change_peak_threshold + ': ' + CSTATE.peakThreshold + '</button></div>';

    // // showWindRayCntl = '<div><button id="id_showWindRayCb" type="button" onclick="workingBtnPassThrough(' + single_quote("showWindRayCb") + ');"   class="btn btn-fullwidth">' + wrchkd + '</button></div>';

    // body = "";
    // c1array = [];
    // c2array = [];

    // c1array.push('style="border-style: none; width: 50%; text-align: right;"');
    // c2array.push('style="border-style: none; width: 50%;"');

    // c1array.push(changeMinAmpCntl);
    // c2array.push(changeStabClassCntl);


    // c1array.push(showAbubbleCntl);

    // // if (CNSNT.annotation_url) c2array.push(showAnoteCntl);
    // // else c2array.push('');

    // // c1array.push(showWindRayCntl);
    // c2array.push(changePeakThresholdCntl);

    // //body += '<div class="clearfix">';
    // body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    // //body += tbl;
    // //body += '</div>';

    // c1array = [];
    // c2array = [];
    // c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
    // c2array.push('style="border-style: none; width: 50%; text-align: right;"');
    // c1array.push('<h3>' + TXT.map_controls + '</h3>');
    // c2array.push(HBTN.modChangeCloseBtn);
    // hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
    // footer = '';

    // modalPane = setModalChrome(
    //     hdr,
    //     body,
    //     footer
    //     );

    // $("#id_mod_change").html(modalPane);
    // $("#id_showDnoteCb").focus();
}

// function colorPathFromValveMask(value) {
//     var value_float, value_int, clr, value_binstr, valve0_bit, valve4_bit;
//     value_float = parseFloat(value);
//     value_int = Math.round(value_float);
//     clr = CSTATE.lastPathColor;
//     if (Math.abs(value_float - value_int) <= 1e-4) {
//         // Only change the path color when valve mask is an integer
//         value_binstr = value_int.toString(2);
//         valve0_bit = value_binstr.substring(value_binstr.length-1, value_binstr.length);
//         valve4_bit = value_binstr.substring(value_binstr.length-5, value_binstr.length-4);
//         if (valve0_bit === "1") {
//             clr = CNSNT.analyze_path_color;
//         } else if (valve4_bit === "1") {
//             clr = CNSNT.inactive_path_color;
//         } else {
//             clr = CNSNT.normal_path_color;
//         }
//         CSTATE.lastPathColor = clr;
//     }
//     return clr;
// }

// function colorPathFromInstrumentStatus(clr) {
//     log('colorPathFromInstrumentStatus')
    // Modify color to CNSNT.inactive_path_color if instrument status is not good
    // var good = CNSNT.INSTMGR_STATUS_READY | CNSNT.INSTMGR_STATUS_MEAS_ACTIVE |
    // CNSNT.INSTMGR_STATUS_GAS_FLOWING | CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED |
    // CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED | CNSNT.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED;

    // if ((CSTATE.lastInst & CNSNT.INSTMGR_STATUS_MASK) !== good) {
    //     clr = CNSNT.inactive_path_color;
    //     CSTATE.lastPathColor = clr;
    // }
    // return clr;
// }

// function widthFunc(windspeed,windDirSdev) {
//     var v0 = 5; // 5m/s gives maximum width
//     var w0 = 100;   // Maximum width is 100m
//     return w0*Math.exp(1.0)*(windspeed/v0)*Math.exp(-windspeed/v0);
// }

var updateCount = 0;
var clrCount = 0;
var noClrCount = 0;



function updatePath(pdata, clr, etm, pos) {
    log(updateCount++)
    return;
    // var where, lastPoint, pathLen, npdata;
    // lastPoint = null;
    // where = newLatLng(pdata.lat, pdata.lon);
    // var size = concMarkerSize(pdata.ch4, CSTATE.concMarkerScale, CSTATE.concMarkerOffset);
    // var color = pdata.ch4 < CSTATE.peakThreshold ? CNSNT.concMarkerBelowThresholdColor : CNSNT.concMarkerAboveThresholdColor;
    // /*
    // var concMarker = newConcMarker(CSTATE.map, where, size, color);
    // concMarker.myProperties = {shape:"circle", size:size, color:color, pos:pos, etm:etm, conc:pdata.ch4 };
    // */
    // if (clr === CNSNT.normal_path_color) {
    //     CSTATE.concMarkerLayer.addLayer(L.circleMarker([pdata.lat, pdata.lon],
    //                                                     {radius: size/2, stroke:false, fillColor:color, fillOpacity:0.5}));
    //     // attachConcMarkerListener(concMarker);
    //     // CSTATE.markerByPos[pos] = concMarker;
    //     if ('windN' in pdata) {
    //         var bearingRad = Math.atan2(pdata.windE,pdata.windN);
    //         var bearing = CNSNT.rtd * bearingRad;
    //         var rayLength  = Math.max(10.0,size);
    //         CSTATE.windRayLayer.addLayer(L.polygonMarker([pdata.lat, pdata.lon],[[0,0],[rayLength*Math.sin(bearingRad),-rayLength*Math.cos(bearingRad)]],
    //                         {fill:false, color:'black', weight:1, opacity:1.0}));
    //         // CSTATE.windRayByPos[pos] = newWindRay(CSTATE.map, where, bearing, rayLength);
    //         // CSTATE.windRayByPos[pos].setVisible(CSTATE.showWindRay);
    //     }
    //     // log('clr2' , clrCount++)
    //     // return;
    //     npdata = pdata;
    //     npdata.geohash = encodeGeoHash(where.lat, where.lng);
    //     CSTATE.pathGeoObjs.push(npdata);
    // }
    // else {
    //     CSTATE.concMarkerLayer.addLayer(L.circleMarker([pdata.lat, pdata.lon],{radius: 1, stroke:false, fillColor:'black', fillOpacity:0.5}));
    // }
}

function makeSquare(side,color) {
    // var context;
    // if (!(side in CSTATE.squares)) CSTATE.squares[side] = {};
    // if (!(color in CSTATE.squares[side])) {
    //     var canvas = document.createElement("canvas");
    //     canvas.height = side;
    //     canvas.width = side;
    //     context = canvas.getContext("2d");
    //     context.globalAlpha = 0.5;
    //     context.beginPath();
    //     context.rect(0,0,side,side);
    //     context.fillStyle = color;
    //     context.fill();
    //     CSTATE.squares[side][color] = canvas.toDataURL("image/png");
    // }
    // return CSTATE.squares[side][color];
};

function makeCircle(side,color) {
    // var context;
    // if (!(side in CSTATE.circles)) CSTATE.circles[side] = {};
    // if (!(color in CSTATE.circles[side])) {
    //     var canvas = document.createElement("canvas");
    //     canvas.height = side;
    //     canvas.width = side;
    //     context = canvas.getContext("2d");
    //     context.globalAlpha = 0.5;
    //     context.beginPath();
    //     context.arc(0.5*side,0.5*side,0.5*side,0,2*Math.PI,false);
    //     context.fillStyle = color;
    //     context.fill();
    //     CSTATE.circles[side][color] = canvas.toDataURL("image/png");
    // }
    // return CSTATE.circles[side][color];
};

function makeRay(bearing, rayLength) {
    // var context;
    // var canvas = document.createElement("canvas");
    // bearing = 10*Math.round(bearing/10.0);
    // rayLength = Math.round(rayLength);
    // if (!(rayLength in CSTATE.rays)) {
    //     CSTATE.rays[rayLength] = {};
    // }
    // if (!(bearing in CSTATE.rays[rayLength])) {
    //     var th = CNSNT.dtr*(bearing);
    //     var sth = Math.sin(th), cth = Math.cos(th);
    //     canvas.height = 2*rayLength;
    //     canvas.width = 2*rayLength;
    //     context = canvas.getContext("2d");
    //     context.globalAlpha = 1.0;
    //     context.beginPath();
    //     context.moveTo(rayLength+rayLength*sth,rayLength-rayLength*cth);
    //     context.lineTo(rayLength, rayLength);
    //     context.strokeStyle = "#000000";
    //     context.lineWidth = 1;
    //     context.stroke();
    //     CSTATE.rays[rayLength][bearing] = canvas.toDataURL("image/png");
    // }
    // return CSTATE.rays[rayLength][bearing];
};

/*
function makeWindRose(radius,meanBearing,shaftLength,halfWidth) {
    var wMin = meanBearing - halfWidth;
    var height = 2*radius;
    $("#windRose").sparkline([2*halfWidth,360-2*halfWidth],{"type":"pie","height":height+"px","offset":-90+wMin,"sliceColors":["#ffff00","#cccccc"]});
};
*/

function makeMarker(size,fillColor,strokeColor,msg,font,textColor) {
    log('make marker')
    // var ctx = document.createElement("canvas").getContext("2d");
    // var b = 1.25 * size;
    // var t = 2.0 * size;
    // var nx = 36 * size + 1;
    // var ny = 65 * size + 1;
    // var r = 0.5 * (nx - 1 - t);
    // var h = ny - 1 - t;
    // var phi = Math.PI * 45.0/180.0;
    // var sinPhi = Math.sin(phi);
    // var cosPhi = Math.cos(phi)
    // var theta = 0.5 * Math.PI - phi;
    // var xoff = r + 0.5 * t;
    // var yoff = r + 0.5 * t;
    // var knot = (r - b * sinPhi) / cosPhi;
    // ctx.canvas.width = nx;
    // ctx.canvas.height = ny;
    // ctx.beginPath();
    // ctx.lineWidth = t;
    // ctx.strokeStyle = strokeColor;
    // ctx.fillStyle = fillColor;
    // ctx.translate(xoff, yoff);
    // ctx.moveTo(-b, (h - r));
    // ctx.quadraticCurveTo(-b, knot, -r * sinPhi, r * cosPhi);
    // ctx.arc(0, 0, r, Math.PI - theta, theta, false);
    // ctx.quadraticCurveTo(b, knot, b, (h - r));
    // ctx.closePath();
    // ctx.fill();
    // ctx.stroke();
    // ctx.fillStyle = textColor;
    // ctx.font = font;
    // ctx.textAlign = "center";
    // ctx.textBaseline = "middle";
    // ctx.fillText(msg,0,1.5*size);
    // return ctx.canvas.toDataURL("image/png");
}

function makeWindRose(canvasHeight,radius,meanBearing,halfWidth,shaftLength,arrowheadSide,arrowheadAngle) {
    log('wind rose')
//     var sph = Math.sin(0.5*arrowheadAngle*CNSNT.dtr), cph = Math.cos(0.5*arrowheadAngle*CNSNT.dtr);
//     var centerX, centerY, context;
//     var wMean = CNSNT.dtr*(meanBearing);
//     var sth = Math.sin(wMean), cth = Math.cos(wMean);
//     var wMin = CNSNT.dtr*(meanBearing - halfWidth);
//     var wMax = CNSNT.dtr*(meanBearing + halfWidth);
//     var canvas = document.getElementById("windCanvas");
//     var centerX = canvasHeight/2, centerY = canvasHeight/2;
//     var shaft = Math.min(shaftLength,radius);
//     radius = Math.min(canvasHeight/2,radius);
//     canvas.height = canvasHeight;
//     canvas.width = canvasHeight;
//     context = canvas.getContext("2d");
//     context.beginPath();
//     context.arc(centerX,centerY,radius,0,2*Math.PI,false);
//     context.fillStyle = "#cccccc"
//     context.fill();
//     context.beginPath();
//     context.moveTo(centerX,centerY);
//     context.arc(centerX,centerY,radius,1.5*Math.PI+wMin,1.5*Math.PI+wMax,false);
//     context.lineTo(centerX,centerY);
//     context.fillStyle = "#ffff00"
//     context.fill();
//     context.beginPath();
//     context.moveTo(centerX+shaft*sth,centerY-shaft*cth);
//     context.lineTo(centerX,centerY);
//     context.strokeStyle = "#000000";
//     context.lineWidth = 3;
//     context.stroke();
//     context.beginPath();
//     context.moveTo(centerX-arrowheadSide*cth*sph,centerY-arrowheadSide*sth*sph);
//     context.lineTo(centerX-arrowheadSide*sth*cph,centerY+arrowheadSide*cth*cph);
//     context.lineTo(centerX+arrowheadSide*cth*sph,centerY+arrowheadSide*sth*sph);
//     context.closePath();
//     context.fillStyle = "#000000";
//     context.fill();
};

// function makeWindWedge(radius,meanBearing,halfWidth) {
//     var context;
//     var wMin = CNSNT.dtr*(meanBearing - halfWidth);
//     var wMax = CNSNT.dtr*(meanBearing + halfWidth);
//     var height = 2*radius;
//     var centerX = radius, centerY = radius;
//     var canvas = document.createElement("canvas");
//     canvas.height = height;
//     canvas.width = height;
//     context = canvas.getContext("2d");
//     context.globalAlpha = 0.75;
//     context.beginPath();
//     context.moveTo(centerX,centerY);
//     context.arc(centerX,centerY,radius,1.5*Math.PI+wMin,1.5*Math.PI+wMax,false);
//     context.lineTo(centerX,centerY);
//     context.fillStyle = "#ffff00"
//     context.fill();
//     context.lineWidth = 1;
//     context.strokeStyle = "black";
//     context.stroke();
//     return {radius:radius,url:canvas.toDataURL("image/png")};
// };


function initialize_gdu(winH, winW) {
    var mapTypeCookie, current_zoom, followCookie, overlayCookie, minAmpCookie, latCookie,new_height;
    var abubbleCookie, windRayCookie;

    initialize_btns();
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

    // anoteCookie = getCookie(COOKIE_NAMES.anote);
    // if (anoteCookie) {
    //     CSTATE.showAnote = parseInt(anoteCookie, 2);
    // }

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
log('init ma23p')
    TIMER.data = setTimeout(datTimer, 1000);
}

function initialize_btns() {
    log('init buttons')
    return;
    // var type;
    // $('#cancel').hide();

    // $('#id_statusPane').html(statusPane());
    // $('#id_followPane').html(followPane());
    // $('#id_modePane').html(modePane());

    // if (CNSNT.prime_view) {
    //     $("#id_primeControlButton_span").html(LBTNS.analyzerCntlBtns);
    // } else {
    //     testPrime();
    //     $("#id_primeControlButton_span").html("");
    //     $("#id_exportButton_span").html("");
    //     type = $("#id_selectLogBtn").html();
    //     if (type === "Live") {
    //         $("#id_exportButton_span").html("");
    //     } else {
    //         $("#id_exportButton_span").html(LBTNS.downloadBtns + '<br/>');
    //     }
    // }
}

// function weather_dialog() {
//     CSTATE.showingWeatherDialog = true;
//     init = getCookie(COOKIE_NAMES.weather);
//     try {
//         init = JSON.parse(init);
//         if (null === init) throw "null";
//     }
//     catch (e) {
//         init = [0,0,0];
//     }
//     makeWeatherForm(function (result) {
//         var code, dtype = "json";
//         if (CNSNT.prime_view === true) {
//             dtype = "jsonp";
//         }
//         setCookie(COOKIE_NAMES.weather, JSON.stringify(result), CNSNT.cookie_duration);
//         // Convert the reported weather into a code for inclusion in the auxiliary instrument status
//         //  Note that 1 is added so that we can tell if there is no weather information in the file
//         code = (8*result[2] + 2*result[1] + result[0]) + 1;
//         CSTATE.inferredStabClass = CNSNT.classByWeather[code-1];
//         // alert('Inferred stability class: ' + inferredStabClass);
//         _changeStabClass(CSTATE.inferredStabClass);
//         call_rest(CNSNT.svcurl, "restartDatalog", dtype, {weatherCode:code});
//         restoreModChangeDiv();
//         CSTATE.weatherMissingCountdown = CNSNT.weatherMissingDefer;
//         CSTATE.showingWeatherDialog = false;
//     },init);
// }

// function restart_datalog() {
//     var init;
//     if (confirm(TXT.restart_datalog_msg)) {
//         weather_dialog();
//     }
// }

// function shutdown_analyzer() {
//     if (confirm(TXT.shutdown_anz_msg)) {
//         var dtype = "json";
//         if (CNSNT.prime_view === true) {
//             dtype = "jsonp";
//         }
//         call_rest(CNSNT.svcurl, "shutdownAnalyzer", dtype, {});
//         restoreModChangeDiv();
//     }
// }

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

    // log('calling rest', call_url, method, dtype, params)
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

// function changeFollow() {
//     var checked = $("#id_follow").attr("data-checked");
//     if (checked == 'true') {
//         if (CSTATE.lastwhere && CSTATE.map) {
//             CSTATE.map.setCenter(CSTATE.lastwhere);
//         }
//         $("#id_follow").attr("class","follow-checked").attr("data-checked",'false')
//         CSTATE.follow = true;
//         updateConcPlot();
//     } else {
//         CSTATE.follow = false;
//         $("#id_follow").attr("class","follow").attr("data-checked",'true')
//     }
//     setCookie(COOKIE_NAMES.follow, (CSTATE.follow) ? "1" : "0", CNSNT.cookie_duration);
// }

// function changeMinAmp() {
//     CSTATE.minAmp = $("#id_amplitude").val();
//     try {
//         minAmpFloat = parseFloat(CSTATE.minAmp);
//         if (isNaN(minAmpFloat)) {
//             minAmpFloat = 0.1;
//         }
//         CSTATE.minAmp = minAmpFloat;
//     } catch (err) {
//         CSTATE.minAmp = 0.1;
//     }
//     CNSNT.mapControl.changeControlText(TXT.map_controls  + "<br/>" + CSTATE.minAmp + "&nbsp; &nbsp;" + CSTATE.stabClass);
//     $("#id_amplitude_btn").html(CSTATE.minAmp);
//     setCookie("pcubed_minAmp", CSTATE.minAmp, CNSNT.cookie_duration);
//     resetLeakPosition();
// }

// function changePeakThreshold() {
//     CSTATE.peakThreshold = $("#id_peak_threshold").val();
//     try {
//         peakThresholdFloat = parseFloat(CSTATE.peakThreshold);
//         if (isNaN(peakThresholdFloat)) {
//             peakThresholdFloat = 0.0;
//         }
//         CSTATE.peakThreshold = peakThresholdFloat;
//     } catch (err) {
//         CSTATE.peakThreshold = 0.;
//     }
//     setCookie("pcubed_peakThreshold", CSTATE.peakThreshold, CNSNT.cookie_duration);
//     onPeakThresholdChange();
// }

// function stabClassCntl(style) {
//     var ht, opendiv, closediv, len, i, options, vlu, selcntl, sty;
//     sty = ""
//     if (style) {
//         sty = style
//     }
//     ht = "";
//     options = "";
//     for (sc in CNSNT.stab_control) {
//         vlu = sc //CNSNT.stab_control[sc];
//         selected = "";
//         if (vlu === CSTATE.stabClass) {
//             selected = ' selected="selected" ';
//         }
//         options += '<option value="' + vlu + '"' + selected + '>' + CNSNT.stab_control[sc]
//             + '</option>';
//     }initialize_cookienames
//     selcntl = '<select ' + sty + ' id="id_stabClassCntl">'
//         + options + '</select>';
//     return selcntl;
// }

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

// function changeStabClass() {
//     var value;
//     value = $("#id_stabClassCntl").val();
//     _changeStabClass(value);
// }

// function exportClassCntl(style) {
//     var ht, opendiv, closediv, len, i, options, vlu, selcntl, sty;
//     sty = ""
//     if (style) {
//         sty = style
//     }
//     ht = "";
//     options = "";
//     for (sc in CNSNT.export_control) {
//         vlu = sc //CNSNT.export_control[sc];
//         selected = "";
//         if (vlu === CSTATE.exportClass) {
//             selected = ' selected="selected" ';
//         }
//         options += '<option value="' + vlu + '"' + selected + '>' + CNSNT.export_control[sc]
//             + '</option>';
//     }
//     selcntl = '<select ' + sty + ' id="id_exportClassCntl" onchange="changeExportClass()">'
//         + options + '</select>';
//     return selcntl;
// }

// function changeExportClass() {
//     var value, len, i, aname, mhtml;
//     value = $("#id_exportClassCntl").val()
//     if (value !== CSTATE.exportClass) {
//         CSTATE.exportClass = value;
//         setCookie(COOKIE_NAMES.dspExportClass, CSTATE.exportClass, CNSNT.cookie_duration)
//     }
// }

function setGduTimer(tcat) {
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
    if (tcat === "analysis") {
        TIMER.analysis = setTimeout(analysisTimer, CNSNT.analysisUpdatePeriod);
        return;
    }
    if (tcat === "peakAndWind") {
        TIMER.peakAndWind = setTimeout(peakAndWindTimer, CNSNT.peakAndWindUpdatePeriod);
        return;
    }
    // if (tcat === "anote") {
    //     TIMER.anote = setTimeout(anoteTimer, CNSNT.noteUpdatePeriod);
    //     return;
    // }
    if (tcat === "mode") {
        TIMER.mode = setTimeout(modeTimer, CNSNT.modeUpdatePeriod);
        return;
    }
    // if (tcat === "periph") {
    //     TIMER.periph = setTimeout(periphTimer, CNSNT.periphUpdatePeriod);
    //     return;
    // }
}

function datTimer() {
    if (CSTATE.ignoreTimer) {
        setGduTimer('dat');
        return;
    }
    mapmaster.Controller.getData();
}

function analysisTimer() {
    log('analysisTimer')
//     if (CSTATE.ignoreTimer) {
//         setGduTimer('analysis');
//         return;
//     }
//     showAnalysis();
}

// function anoteTimer() {
//     // if (CSTATE.ignoreTimer) {
//     //     setGduTimer('anote');
//     //     return;
//     // }
//     // getNotes("analysis");
// }

// function modeTimer() {
//     // if (CSTATE.ignoreTimer) {
//     //     setGduTimer('mode');
//     //     return;
//     // }
//     // getMode();
// }

// function periphTimer() {
//     // if (CSTATE.ignoreTimer) {
//     //     setGduTimer('periph');
//     //     return;
//     // }
//     // checkPeriphUpdate();
// }

function statCheck() {
    // log('stat check')

    // var dte, curtime, streamdiff;
    // var good = CNSNT.INSTMGR_STATUS_READY | CNSNT.INSTMGR_STATUS_MEAS_ACTIVE |
    //            CNSNT.INSTMGR_STATUS_GAS_FLOWING | CNSNT.INSTMGR_STATUS_PRESSURE_LOCKED |
    //            CNSNT.INSTMGR_STATUS_CAVITY_TEMP_LOCKED | CNSNT.INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED;

    // dte = new Date();
    // curtime = dte.getTime();
    // streamdiff = curtime - CSTATE.laststreamtime;
    // if (streamdiff > CNSNT.streamerror) {
    //     $("#id_stream_stat").attr("class", "stream-failed");
    //     $("#id_analyzer_stat").attr("class", "analyzer-failed");
    //     if (CSTATE.lastGpsUpdateStatus !== 0) {
    //         $("#id_gps_stat").attr("class", "gps-failed");
    //     }
    //     if (CSTATE.lastWsUpdateStatus !== 0) {
    //         $("#id_ws_stat").attr("class", "ws-failed");
    //     }
    // } else {
    //     if (streamdiff > CNSNT.streamwarning) {
    //         $("#id_stream_stat").attr("class", "stream-warning");
    //     } else {
    //         $("#id_stream_stat").attr("class", "stream-ok");

    //         if (CSTATE.lastGpsUpdateStatus === 2) {
    //             $("#id_gps_stat").attr("class", "gps-failed");
    //         } else if (CSTATE.lastGpsUpdateStatus === 1) {
    //             if (CSTATE.lastFit === 0) {
    //                 $("#id_gps_stat").attr("class", "gps-warning");
    //             } else {
    //                 $("#id_gps_stat").attr("class", "gps-ok");
    //             }restoreModalDiv
    //         }

    //         if (CSTATE.lastWsUpdateStatus === 2) {
    //             $("#id_ws_stat").attr("class", "ws-failed");
    //         } else if (CSTATE.lastWsUpdateStatus === 1) {
    //             $("#id_ws_stat").attr("class", "ws-ok");
    //         }

    //         if ((CSTATE.lastInst & CNSNT.INSTMGR_STATUS_MASK) !== good) {
    //             $("#id_analyzer_stat").attr("class", "analyzer-failed");
    //         } else {
    //             $("#id_analyzer_stat").attr("class", "analyzer-ok");
    //         }
    //     }
    // }
}

// function updateConcPlot() {
//     log("updateConcPlot")
// //    if (CSTATE.follow) $.plot($("#concPlot2"), [ {data: CSTATE.concPlotFollowing, lines: {show: true}, color:"#00f" } ], {xaxis:{ticks:5}} );
//     // $.plot($("#concPlot2"), [ {data: CSTATE.concPlotFollowing, lines: {show: true}, color:"#00f" } ], {xaxis:{ticks:5}} );
// }

// function getMode() {
//     log('get mode');
//     return;
//     // var errorMode = function () {
//     //     CSTATE.getting_mode = false;
//     //     //CSTATE.net_abort_count += 1;
//     //     //if (CSTATE.net_abort_count >= 2) {
//     //     //    $("#id_modal").html(modalNetWarning());
//     //     //}
//     //     $("#errors").html("getMode() error");
//     //     setGduTimer('mode');
//     // }

//     // var mode;
//     // if (!CSTATE.getting_mode) {
//     //     var dtype = "json";
//     //     if (CNSNT.prime_view === true) {
//     //         dtype = "jsonp";
//     //     }
//     //     CSTATE.getting_mode = true;
//     //     call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "rdDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER']"},
//     //         function (data) {
//     //             CSTATE.net_abort_count = 0;
//     //             if (data.result.value !== undefined) {
//     //                 var mode = data.result.value;
//     //                 setModePane(mode);
//     //                 if (mode==0) {
//     //                     $("#id_captureBtn").html(TXT.switch_to_cptr).attr("onclick","captureSwitch();").removeAttr("disabled");
//     //                     $("#id_surveyOnOffBtn").removeAttr("disabled").html(TXT.stop_survey).attr("onclick", "stopSurvey();");
//     //                     $("#id_calibrateBtn").removeAttr("disabled");
//     //                 } else if (mode==1) {
//     //                     $("#id_captureBtn").html(TXT.cancl_cptr).attr("onclick", "cancelCapSwitch();").removeAttr("disabled");
//     //                     $("#id_surveyOnOffBtn").attr("disabled", "disabled");
//     //                     $("#id_calibrateBtn").removeAttr("disabled");
//     //                 } else if (mode==2) {
//     //                     $("#id_captureBtn").html(TXT.cancl_cptr).attr("onclick", "cancelCapSwitch();").removeAttr("disabled");
//     //                     $("#id_surveyOnOffBtn").attr("disabled", "disabled");
//     //                     $("#id_calibrateBtn").attr("disabled", "disabled");
//     //                 } else if (mode==3) {
//     //                     call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "rdDasReg", "args": "['PEAK_DETECT_CNTRL_REMAINING_TRIGGERED_SAMPLES_REGISTER']"},
//     //                         function (data) {
//     //                             if (data.result.hasOwnProperty('value'))
//     //                                 $("#id_captureBtn").html((0.2*data.result.value).toFixed(0) + TXT.cancl_ana_time).attr("onclick", "cancelAnaSwitch();");
//     //                             else
//     //                                 $("#id_captureBtn").html(TXT.cancl_ana).attr("onclick", "cancelAnaSwitch();");
//     //                         }
//     //                     );
//     //                     $("#id_surveyOnOffBtn").attr("disabled", "disabled");
//     //                     $("#id_calibrateBtn").attr("disabled", "disabled");
//     //                 } else if (mode==4) {
//     //                     $("#id_captureBtn").attr("disabled", "disabled");
//     //                     $("#id_surveyOnOffBtn").html(TXT.start_survey).attr("onclick","startSurvey();");
//     //                     $("#id_calibrateBtn").attr("disabled", "disabled");
//     //                 } else if (mode==5) {
//     //                     $("#id_captureBtn").attr("disabled", "disabled");
//     //                     $("#id_surveyOnOffBtn").attr("disabled", "disabled");
//     //                     $("#id_calibrateBtn").attr("disabled", "disabled");
//     //                 } else if (mode==6) {
//     //                     $("#id_captureBtn").html(TXT.cancl_ref).attr("onclick", "cancelRefSwitch();").removeAttr("disabled");
//     //                     $("#id_surveyOnOffBtn").attr("disabled", "disabled");
//     //                     $("#id_calibrateBtn").attr("disabled", "disabled");
//     //                 } else if (mode==7) {
//     //                     $("#id_captureBtn").html(TXT.cancl_ref).attr("onclick", "cancelRefSwitch();").removeAttr("disabled");
//     //                     $("#id_surveyOnOffBtn").attr("disabled", "disabled");
//     //                     $("#id_calibrateBtn").attr("disabled", "disabled");
//     //                 } else if (mode==8) {
//     //                     $("#id_captureBtn").attr("disabled", "disabled");
//     //                     $("#id_surveyOnOffBtn").attr("disabled", "disabled");
//     //                     $("#id_calibrateBtn").attr("disabled", "disabled");
//     //                     injectCal();
//     //                 }
//     //             }
//     //             CSTATE.getting_mode = false;
//     //             setGduTimer('mode');
//     //         }, errorMode);
//     // }
// }

function checkPeriphUpdate() {
    log('checkPeriphUpdate')
    return;
    // var errorPeriph = function() {
    //     CSTATE.getting_periph_time = false;
    //     //CSTATE.net_abort_count += 1;
    //     //if (CSTATE.net_abort_count >= 2) {
    //     //    $("#id_modal").html(modalNetWarning());
    //     //}
    //     $("#errors").html("checkPeriphUpdate() error");
    //     setGduTimer('periph');
    // }

    // if (!CSTATE.getting_periph_time) {
    //     var dtype = "json";
    //     if (CNSNT.prime_view === true) {
    //         dtype = "jsonp";
    //     }
    //     CSTATE.getting_periph_time = true;
    //     call_rest(CNSNT.svcurl, "getLastPeriphUpdate", dtype, {},
    //         function (data) {
    //             CSTATE.net_abort_count = 0;
    //             var gpsPort = CNSNT.gpsPort;
    //             var wsPort = CNSNT.wsPort;
    //             if (gpsPort in data.result) {
    //                 if (data.result[gpsPort] > CNSNT.gpsUpdateTimeout) {
    //                     CSTATE.lastGpsUpdateStatus = 2;
    //                 } else {
    //                     CSTATE.lastGpsUpdateStatus = 1;
    //                 }
    //             } else {
    //                 CSTATE.lastGpsUpdateStatus = 0;
    //             }
    //             if (wsPort in data.result) {
    //                 if (data.result[wsPort] > CNSNT.wsUpdateTimeout) {
    //                     CSTATE.lastWsUpdateStatus = 2;
    //                 } else {
    //                     CSTATE.lastWsUpdateStatus = 1;
    //                 }
    //             } else {
    //                 CSTATE.lastWsUpdateStatus = 0;
    //             }
    //             CSTATE.getting_periph_time = false;
    //             setGduTimer('periph');
    //         }, errorPeriph);
    // }
}

// function analysisIconSize(text) {
//     var testDiv = $('<div id="testDiv"/>'), result;
//     $("body").append(testDiv)
//     testDiv.css("display","none")
//            .css("position","absolute")
//            .css('borderStyle','solid')
//            .css('borderWidth','2px')
//            .css('padding','2px')
//            .css("height","auto")
//            .css("width","auto")
//            .css('font-family','Arial')
//            .css('font-size',16);
//     testDiv.html(text)
//     result = testDiv.width() + 1;
//     $("body").remove("#testDiv");
//     return result;
// }

function showAnalysis() {
    log('show anaylsys')
    return;
    // function successAnalysis(data) {
    //     var resultWasReturned, i, result;
    //     CSTATE.net_abort_count = 0;
    //     resultWasReturned = false;
    //     if (data.result) {
    //         if (data.result.filename) {
    //             if (CSTATE.lastAnalysisFilename === data.result.filename) {
    //                 resultWasReturned = true;
    //             }
    //             //CSTATE.lastAnalysisFilename = data.result.filename;
    //         }
    //     } else {
    //         if (data && (data.indexOf("ERROR: invalid ticket") !== -1)) {
    //             get_ticket();
    //             statCheck();
    //             setGduTimer('analysis');
    //             return;
    //         }
    //     }
    //     if (resultWasReturned) {
    //         if (data.result.CONC) {
    //             if (CSTATE.clearAnalyses) {
    //                 CSTATE.clearAnalyses = false;
    //             } else {
    //                 CSTATE.analysisLine = data.result.nextRow;
    //                 for (i = 0; i < data.result.CONC.length; i += 1) {
    //                     var analysisIcon;
    //                     analysisCoords = newLatLng(data.result.GPS_ABS_LAT[i], data.result.GPS_ABS_LONG[i]);
    //                     result = TXT.delta + ": " + data.result.DELTA[i].toFixed(1) + " +/- " + data.result.UNCERTAINTY[i].toFixed(1);
    //                     $("#analysis").html(result);
    //                     //analysisMarker = newAnalysisMarker(CSTATE.map, analysisCoords, data.result.DELTA[i], data.result.UNCERTAINTY[i]);
    //                     //CSTATE.analysisMarkers[CSTATE.analysisMarkers.length] = analysisMarker;
    //                     analysisIcon = L.divIcon({iconSize:analysisIconSize(result), iconAnchor:[0,0], className: 'analysisIcon', html:result});
    //                     CSTATE.analysisMarkerLayer.addLayer(L.marker(analysisCoords,{icon: analysisIcon}));
    //                     $('.analysisIcon').css('borderStyle','solid').css('borderWidth','2px').css('padding','2px')
    //                                       .css('font-family','Arial').css('font-size',16).css('background-color','rgb(255,96,96)');

    //                     datadict = CSTATE.analysisNoteDict[data.result.EPOCH_TIME[i]];
    //                     if (!datadict) {
    //                         datadict = {};
    //                     }
    //                     datadict.lat = data.result.GPS_ABS_LAT[i];
    //                     datadict.lon = data.result.GPS_ABS_LONG[i];
    //                     datadict.conc = data.result.CONC[i];
    //                     datadict.delta = data.result.DELTA[i];
    //                     datadict.uncertainty = data.result.UNCERTAINTY[i];

    //                     CSTATE.analysisNoteDict[data.result.EPOCH_TIME[i]] = datadict;
    //                     //attachMarkerListener(analysisMarker, data.result.EPOCH_TIME[i], "analysis", true);
    //                 }
    //             }
    //         }
    //     }
    //     setGduTimer('analysis');
    // }
    // function errorAnalysis() {
    //     //CSTATE.net_abort_count += 1;
    //     //if (CSTATE.net_abort_count >= 2) {
    //     //    $("#id_modal").html(modalNetWarning());
    //     //}
    //     $("#errors").html("showAnalysis() error.");
    //     setGduTimer('analysis');
    // }
    // if (!CSTATE.showAbubble) {
    //     setGduTimer('analysis');
    //     return;
    // }
    // if (CSTATE.ticket !== "WAITING") {
    //     //alert("looking for peaks in new resource");
    //     switch(CNSNT.prime_view) {
    //     case false:
    //         if (CSTATE.alog_analysis === "") {
    //             CSTATE.alog_analysis = CSTATE.alog.replace(".dat", ".analysis");
    //         }
    //         ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
    //         resource = CNSNT.resource_AnzLog; //"gdu/<TICKET>/1.0/AnzLog"
    //         resource = insertTicket(resource);
    //         params = {
    //             "qry": "byPos"
    //             , "alog": CSTATE.alog_analysis
    //             , "logtype": "analysis"
    //             , "limit": CSTATE.getDataLimit
    //             , "startPos": CSTATE.analysisLine
    //             , "gmtOffset": CNSNT.gmt_offset
    //             , "doclist": "true"
    //             , "insFilename": "true"
    //             , "timeStrings": "true"
    //             , "insNextLastPos": "true"
    //             , "rtnOnTktError": "1"
    //         };
    //         call_rest(ruri, resource, "jsonp", params, successAnalysis, errorAnalysis);
    //         break;

    //     default:
    //         var dtype = "json";
    //         if (CNSNT.prime_view === true) {
    //             dtype = "jsonp";
    //         }
    //         var params = {'startRow': CSTATE.analysisLine, 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset};
    //         call_rest(CNSNT.svcurl, "getAnalysis", dtype, params, successAnalysis, errorAnalysis);
    //         break;
    //     }
    // } else {
    //     setGduTimer('analysis');
    // }
}

// function equalProperties(obj1, obj2) {
//     var p;
//     for (p in obj1) {
//         if (obj1.hasOwnProperty(p)) {
//             if (obj2.hasOwnProperty(p)) {
//                 if (obj1[p] !== obj2[p]) return false;
//             }
//             else return false;
//         }
//     }
//     for (p in obj2) {
//         if (obj2.hasOwnProperty(p)) {
//             if (obj1.hasOwnProperty(p)) {
//                 if (obj1[p] !== obj2[p]) return false;
//             }
//             else return false;
//         }
//     }
//     return true;
// }

// function getNotes(cat) {
//     function successNotes(data, cat) {
//         var process_result;
//         if (data.result) {
//             process_result = true;
//             if (cat === "analysis") {
//                 if (CSTATE.clearAnalysisNote) {
//                     CSTATE.clearAnalysisNote = false;
//                     process_result = false;
//                 }
//             } else {
//                 if (CSTATE.clearDatNote) {
//                     CSTATE.clearDatNote = false;
//                     process_result = false;
//                 }
//             }
//             if (process_result) {
//                 if (data.result.EPOCH_TIME) {
//                     dropResultNoteBubbles(data.result, cat);
//                 }
//                 if (CNSNT.prime_view) {
//                     if (data.result.nextEtm) {
//                         if (cat === "analysis") {
//                             CSTATE.nextAnalysisEtm = data.result.nextEtm;
//                         } else {
//                             CSTATE.nextDatEtm = data.result.nextEtm;
//                         }
//                     }
//                 } else {
//                     var utm = results.UPDATE_TIME
//                     var lastUtm = utm.pop();
//                     delete utm;
//                     if (cat === "analysis") {
//                         CSTATE.nextAnalysisEtm = lastUtm;
//                     } else {
//                         CSTATE.nextDatEtm = lastUtm;
//                     }
//                 }
//             }
//         } else {
//             if (data && (data.indexOf("ERROR: invalid ticket") !== -1)) {
//                 get_ticket();
//                 statCheck();
//                 if (cat === "analysis") {
//                     setGduTimer('anote');
//                 } else {
//                     setGduTimer('dnote');
//                 }
//                 return;
//             }
//         }
//         if (cat === "analysis") {
//             setGduTimer('anote');
//         } else {
//             setGduTimer('dnote');
//         }
//     }
//     function errorDatNotes(text) {
//         //CSTATE.net_abort_count += 1;
//         //if (CSTATE.net_abort_count >= 2) {
//         //    $("#id_modal").html(modalNetWarning());
//         //}
//         $("#errors").html(text);
//         if (cat === "analysis") {
//             setGduTimer('anote');
//         }
//     }

//     var params, fname, etm;
//     if (cat === "analysis") {
//         if (!CSTATE.showAnote) {
//             setGduTimer('anote');
//             return;
//         }
//         fname = CSTATE.lastAnalysisFilename;
//         etm = CSTATE.nextAnalysisEtm;
//     }

//     if (CSTATE.ticket !== "WAITING") {
//         if (CNSNT.resource_AnzLogNote) {
//             var ltype = 'dat';
//             if (cat === "analysis") {
//                 fname = CSTATE.lastAnalysisFilename;
//                 etm = CSTATE.nextAnalysisEtm;
//                 ltype = 'analysis';
//             }

//             ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
//             resource = CNSNT.resource_AnzLogNote; //"gdu/<TICKET>/1.0/AnzLog"
//             resource = insertTicket(resource);
//             params = {
//                 "qry": "byEpoch"
//                 , "alog": fname
//                 , "startEtm": etm
//                 , "gmtOffset": CNSNT.gmt_offset
//                 , "limit": CSTATE.getDataLimit
//                 , "ltype": ltype
//                 , "doclist": "true"
//                 , "insFilename": "true"
//                 , "timeStrings": "true"
//                 , "byUtm": "true"
//                 , "returnLatLng": "true"
//                 , "excludeStart": "true"
//                 , "rtnOnTktError": "1"
//             };
//             call_rest(ruri, resource, "jsonp", params, function(
//                 json, status, jqXHR) {
//                 CSTATE.net_abort_count = 0;
//                 successNotes(json, cat);
//                 },
//                 function (jqXHR, ts, et) {
//                     errorDatNotes(jqXHR.responseText);
//                 }
//                 );
//         }
//         // NOTE: if there is no resource_AnzLogNote, this will STOP the note timers
//         // as there is no ELSE logic to restart them.
//         // This is the expected behavior.
//     } else {
//         setGduTimer('dat');
//         //alert("waiting again!!");
//     }
// }


// function attachMarkerListener(marker, etm, cat, bubble) {
//     var markerListener = new google.maps.event.addListener(marker, 'click', function () {
//         notePane(etm, cat);
//     });
//     if (cat === "analysis") {
//         if (bubble === true) {
//             CSTATE.analysisBblListener[etm] = markerListener;
//         } else {
//             CSTATE.analysisNoteListener[etm] = markerListener;
//         }
//     }
// }

//drop (or update) the note bubble (and add listener if dropping)
//and update the current state dictionary for the note(s) from the result set
// function dropResultNoteBubbles(results, cat) {
//     var i, etm, ntx, datadict, pathCoords, pathMarker, mkr;
//     utm = results.UPDATE_TIME;
//     etm = results.EPOCH_TIME;
//     ntx = results.NOTE_TXT;
//     lat = results.GPS_ABS_LAT;
//     lon = results.GPS_ABS_LONG;
//     ch4 = results.CH4;
//     last_etm = etm;

//     for (i = 0; i < etm.length; i += 1) {
//         if (cat === 'analysis') {
//             if (!CSTATE.showAnote) {
//                 return;
//             }
//             datadict = CSTATE.analysisNoteDict[etm[i]];
//         } else {
//             if (!CSTATE.showDnote) {
//                 return;
//             }
//             datadict = CSTATE.datNoteDict[etm[i]];
//         }
//         if (!datadict) {
//             datadict = {};
//         }
//         datadict.lat = lat[i];
//         datadict.lon = lon[i];
//         if (ch4) {
//             datadict.ch4 = ch4[i];
//         }

//         datadict.note = ntx[i];
//         datadict.db = true;
//         datadict.lock = false;
//         if (cat === "analysis") {
//             mkr = CSTATE.analysisNoteMarkers[etm[i]];
//         }
//         if (mkr) {
//             updateNoteMarkerText(CSTATE.map, mkr, datadict.note, cat);
//         } else {
//             pathCoords = newLatLng(datadict.lat, datadict.lon);
//             pathMarker = newNoteMarker(CSTATE.map, pathCoords, datadict.note, cat);
//             if (cat === 'analysis') {
//                 CSTATE.analysisNoteMarkers[etm[i]] = pathMarker;
//             }
//             attachMarkerListener(pathMarker, etm[i], cat);
//         }
//         if (cat === 'analysis') {
//             CSTATE.analysisNoteDict[etm[i]] = datadict;
//         }
//     }
// }


// function setModePane(mode) {
//     if (mode==4) {
//         $("#mode").html("<font color='red'>" + modeStrings[mode] + "</font>");
//     } else {
//         $("#mode").html(modeStrings[mode]);
//     }
//     CSTATE.current_mode = mode;
// }

// function captureSwitch() {
//     CSTATE.ignoreTimer = true;
//     $("#analysis").html("");
//     var dtype = "json";
//     if (CNSNT.prime_view === true) {
//         dtype = "jsonp";
//     }
//     call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 1]"});
//     CSTATE.ignoreTimer = false;
//     restoreModChangeDiv();
// }

// function cancelCapSwitch() {
//     if (confirm(TXT.cancel_cap_msg)) {
//         var dtype = "json";
//         if (CNSNT.prime_view === true) {
//             dtype = "jsonp";
//         }
//         call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 0]"});
//         restoreModChangeDiv();
//     }
// }

// function cancelRefSwitch() {
//     if (confirm(TXT.cancel_ref_msg)) {
//         var dtype = "json";
//         if (CNSNT.prime_view === true) {
//             dtype = "jsonp";
//         }
//         call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 5]"});
//         restoreModChangeDiv();
//     }
// }

// function cancelAnaSwitch() {
//     if (confirm(TXT.cancel_ana_msg)) {
//         var dtype = "json";
//         if (CNSNT.prime_view === true) {
//             dtype = "jsonp";
//         }
//         call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 5]"});
//         restoreModChangeDiv();
//     }
// }

// function primingSwitch() {
//     CSTATE.ignoreTimer = true;
//     $("#analysis").html("");
//     var dtype = "json";
//     if (CNSNT.prime_view === true) {
//         dtype = "jsonp";
//     }
//     call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 6]"});
//     CSTATE.ignoreTimer = false;
//     restoreModChangeDiv();
// }

// function referenceGas() {
//     var dtype = "json";
//     if (CNSNT.prime_view === true) {
//         dtype = "jsonp";
//     }
//     call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "interfaceValue", "args": "['PEAK_DETECT_CNTRL_PrimingState']"},
//         function (data) {
//             if (data.result.value == 6) {
//                 if (confirm(TXT.start_ref_msg)) {
//                     setTimeout(primingSwitch, 100);
//                 }
//             }
//             else {
//                 alert("Feature is not available on current analyzer software");
//             }
//         }
//     );
// }

// function injectCal() {
//     captureSwitch();
//     setTimeout(callInject, 1000);
// }

// function callInject() {
//     var dtype = "json";
//     if (CNSNT.prime_view === true) {
//         dtype = "jsonp";
//     }
//     call_rest(CNSNT.svcurl, "injectCal", dtype, {"valve": 3, "flagValve": 4, "samples": 1});
//     restoreModChangeDiv();
// }

// function startSurvey() {
//     var dtype = "json";
//     if (CNSNT.prime_view === true) {
//         dtype = "jsonp";
//     }
//     call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 0]"});
//     restoreModChangeDiv();
// }

// function stopSurvey() {
//     if (confirm(TXT.stop_survey_msg)) {
//         var dtype = "json";
//         if (CNSNT.prime_view === true) {
//             dtype = "jsonp";
//         }
//         call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "wrDasReg", "args": "['PEAK_DETECT_CNTRL_STATE_REGISTER', 4]"});
//         restoreModChangeDiv();
//     }
// }

function completeSurvey() {
    alert("Complete Survey button pressed");
    restoreModChangeDiv();
}

function initialize_cookienames() {
    COOKIE_NAMES = {
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
}

function draw_legend() {
    return;
    // var legendCanvas = document.getElementById("id_legend_canvas");
    // var ctx = legendCanvas.getContext("2d");
    // var i, metrics, text, concList = [1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.5, 3.0, 5.0, 8.0, 10.0], drawings = [];
    // var xpos = 0;
    // ctx.fillStyle = "black";
    // ctx.font = "12px Arial";
    // ctx.clearRect(0, 0, legendCanvas.width, legendCanvas.height);
    // var textHeight = ctx.measureText('M').width;
    // for (i=0; i<concList.length; i++) {
    //     var size = concMarkerSize(concList[i], CSTATE.concMarkerScale, CSTATE.concMarkerOffset);
    //     var drawing = new Image();
    //     var color = concList[i] < CSTATE.peakThreshold ? CNSNT.concMarkerBelowThresholdColor : CNSNT.concMarkerAboveThresholdColor;
    //     drawing.src = makeCircle(size,color);
    //     drawing.xpos = xpos;
    //     drawing.ypos = (ctx.canvas.height-size)/2;
    //     drawing.onload = function() {
    //         ctx.drawImage(this, this.xpos, this.ypos);
    //     }
    //     drawings.push(drawing);
    //     text = concList[i].toFixed(1);
    //     metrics = ctx.measureText(text);
    //     ctx.fillText(text, drawing.xpos+5+size, (ctx.canvas.height + textHeight)/2);
    //     xpos += size + metrics.width + 15;
    // }
}

function initialize(winH, winW) {
    return;
    // if (init_vars) {
    //     init_vars();
    // }

    // //secure ping (to assure browsers can see secure site)
    // $("#id_content_spacer").html('<img src="' + CNSNT.resturl + '/pimg' + '"/>');

    // initialize_cookienames();
    // get_ticket(initialize_gdu);
}

// function showStream() {
//     var modalChrome, hdr, body, footer, c1array, c2array;
//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 30%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 70%;"');
//     c1array.push('<img class="stream-ok" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.stream_ok + '</h4>');
//     c1array.push('<img class="stream-warning" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.stream_warning + '</h4>');
//     c1array.push('<img class="stream-failed" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.stream_failed + '</h4>');
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 30%; text-align: right;"');
//     c1array.push('<h3>' + TXT.stream_title + '</h3>');
//     c2array.push(HBTN.modChangeCloseBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
// }

// function showGps() {
//     var modalChrome, hdr, body, footer, c1array, c2array;
//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 30%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 70%;"');
//     c1array.push('<img class="gps-ok" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.gps_ok + '</h4>');
//     c1array.push('<img class="gps-warning" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.gps_warning + '</h4>');
//     c1array.push('<img class="gps-failed" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.gps_failed + '</h4>');
//     c1array.push('<img class="gps-uninstalled" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.gps_uninstalled + '</h4>');
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 30%; text-align: right;"');
//     c1array.push('<h3>' + TXT.gps_title + '</h3>');
//     c2array.push(HBTN.modChangeCloseBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
// }

// function showWs() {
//     var modalChrome, hdr, body, footer, c1array, c2array;
//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 30%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 70%;"');
//     c1array.push('<img class="ws-ok" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.ws_ok + '</h4>');
//     c1array.push('<img class="ws-failed" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.ws_failed + '</h4>');
//     c1array.push('<img class="ws-uninstalled" src="' + CNSNT.spacer_gif + '" />');
//     c2array.push('<h4>' + TXT.ws_uninstalled + '</h4>');
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 30%; text-align: right;"');
//     c1array.push('<h3>' + TXT.ws_title + '</h3>');
//     c2array.push(HBTN.modChangeCloseBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
// }

// var bar = ['<div id="id_cavity_p_bar" class="progress progress-danger" style="position:relative; top:9px">' +
//            '<div id="id_cavity_p_prog" class="bar" style="width:100%;"><span id="id_cavity_p_val" class="ui-label"><b>?</b></span></div>' +
//            '</div>',
//            '<div id="id_cavity_t_bar" class="progress progress-danger" style="position:relative; top:9px">' +
//            '<div id="id_cavity_t_prog" class="bar" style="width:100%;"><span id="id_cavity_t_val" class="ui-label"><b>?</b></span></div>' +
//            '</div>',
//            '<div id="id_wb_t_bar" class="progress progress-danger" style="position:relative; top:9px">' +
//           '<div id="id_wb_t_prog" class="bar" style="width:100%;"><span id="id_wb_t_val" class="ui-label"><b>?</b></span></div>' +
//           '</div>'];

// function updateBar(id_sp, id_val, id_prog, id_bar, sp, val) {
//     var unit, prog, barClass;
//     if (sp !== null) {
//         barClass = "progress progress-success";
//         if (id_sp ==  '#id_cavity_p_sp') {
//             unit = 'Torr';
//             if (Math.abs(val-sp) > 5.0) {
//                 barClass = "progress progress-warning";
//             }
//             prog = 100.0*Math.exp(-Math.abs(0.05*(val-sp)/5.0));
//         } else {
//             unit = 'C';
//             if (Math.abs(val-sp) > 0.3) {
//                 barClass = "progress progress-warning";
//             }
//             prog = 100.0*Math.exp(-Math.abs(0.05*(val-sp)/0.3));
//         }
//         $(id_sp).html("<h5>" + sp.toFixed(1) + " " + unit + "</h5>");
//         $(id_val).html("<b>" + val.toFixed(1) + "</b>");
//         $(id_prog).css("width", prog + "%")
//         $(id_bar).attr("class", barClass);
//     } else {
//         $(id_sp).html("<h5></h5>");
//         $(id_val).html("<b>?</b>");
//         $(id_prog).css("width", "100%")
//         $(id_bar).attr("class", "progress progress-danger");
//     }
// }

// function updateProgress() {
//     var cavity_p_val, cavity_p_sp, cavity_t_val, cavity_t_sp, wb_t_val, wb_t_sp;
//     if (!CSTATE.getting_warming_status) {
//         CSTATE.getting_warming_status = true;
//         var dtype = "json";
//         if (CNSNT.prime_view === true) {
//             dtype = "jsonp";
//         }
//         call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "getWarmingState", "args": "[]"},
//                 function (data, ts, jqXHR) {
//                 if (data.result.value !== undefined) {
//                     cavity_p_val = data.result.value['CavityPressure'][0];
//                     cavity_p_sp = data.result.value['CavityPressure'][1];
//                     cavity_t_val = data.result.value['CavityTemperature'][0];
//                     cavity_t_sp = data.result.value['CavityTemperature'][1];
//                     wb_t_val = data.result.value['WarmBoxTemperature'][0];
//                     wb_t_sp = data.result.value['WarmBoxTemperature'][1];
//                     updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", cavity_p_sp, cavity_p_val);
//                     updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", cavity_t_sp, cavity_t_val);
//                     updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", wb_t_sp, wb_t_val);
//                 } else {
//                     updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", null, 0.0);
//                     updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", null, 0.0);
//                     updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", null, 0.0);
//                 }
//                 CSTATE.getting_warming_status = false;
//             },
//             function (jqXHR, ts, et) {
//                 $("#errors").html(jqXHR.responseText);
//                 updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", null, 0.0);
//                 updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", null, 0.0);
//                 updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", null, 0.0);
//                 CSTATE.getting_warming_status = false;
//             }
//             );
//     }
//     if (!CSTATE.end_warming_status){
//         TIMER.progress = setTimeout(updateProgress, CNSNT.progressUpdatePeriod);
//     }
// }

// function showAnalyzer() {
//     var modalChrome, hdr, body, footer, c1array, c2array, c3array;

//     c1array = [];
//     c2array = [];
//     c3array = [];
//     c1array.push('style="border-style: none; width: 40%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 40%; "');
//     c3array.push('style="border-style: none; width: 20%; text-align: left;"');

//     c1array.push('<h4>' + TXT.cavity_p + '</h4>');
//     c2array.push(bar[0]);
//     c3array.push('<span id="id_cavity_p_sp"><h5></h5></span>');

//     c1array.push('<h4>' + TXT.cavity_t + '</h4>');
//     c2array.push(bar[1]);
//     c3array.push('<span id="id_cavity_t_sp"><h5></h5></span>');

//     c1array.push('<h4>' + TXT.wb_t + '</h4>');
//     c2array.push(bar[2]);
//     c3array.push('<span id="id_wb_t_sp"><h5></h5></span>');
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array, c3array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 70%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 30%; text-align: right;"');
//     c1array.push('<h3>' + TXT.analyzer_title + '</h3>');
//     c2array.push(HBTN.modChangeCloseBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);

//     if (TIMER.progress == null) {
//         CSTATE.end_warming_status = false;
//         updateProgress();
//     }
// }

// function setupRadioControlGroup(params)
// {
//     var result = '';
//     result += '<div class="control-group" id="' + params.control_group_id + '">';
//     result += '<label class="control-label" for="' + params.control_div_id + '">';
//     result += params.label + '</label>';
//     result += '<div class="controls">';
//     result += '<div id="' + params.control_div_id + '" class="btn-group" data-toggle="buttons-radio">';
//     $.each(params.buttons, function (i, v) {
//         result += '<button id="' + v.id + '" type="button" class="btn btn-large">' + v.caption + '</button>';
//     });
//     result += '</div></div></div>';
//     return result;
// }

// function makeWeatherForm(resultFunc, init) {
//     /* Makes a weather selection form in the modal box "id_weather". There are currently three questions, where the
//      * second question depends on the first
//      *
//      * Day (0) or Night (1)
//      * If Day:   Weak sunlight (0), moderate sunlight (1) or strong sunlight (2)
//      * If Night: <50% cloud cover (0), >50% cloud cover (1)
//      * Calm (0), light wind (1) or strong wind (2)
//      *
//      * The user selects the appropriate options, and the result is returned as a 3 element array.
//      * e.g. [0,1,2] = Day, moderate sunlight, strong wind
//      *      [1,0,1] = Night, <50% cloud cover, light wind
//      *
//      * The initial settings of the buttons in the form can be specified using init, which must be a valid
//      *  3-element array
//      *
//      * After a successful selection has been made, the function "resultFunc" is called. This function has a
//      * single parameter which is the 3-element array of the selections.
//      *  */
//     var weatherFormTemplate = [{label: "<h4>" + TXT.survey_time + "</h4>",
//         control_div_id: "id_day_night",
//         control_group_id: "id_day_night_group",
//         buttons: [{id: "id_day", caption: TXT.day},
//                   {id: "id_night", caption: TXT.night}]},
//        {label: "<h4>" + TXT.sunlight + "</h4>",
//         control_div_id: "id_sunlight",
//         control_group_id: "id_sunlight_group",
//         buttons: [{id: "id_overcast_sunlight", caption: TXT.overcast_sunlight },
//                   {id: "id_moderate_sunlight", caption: TXT.moderate_sunlight },
//                   {id: "id_strong_sunlight", caption: TXT.strong_sunlight }]},
//        {label: "<h4>" + TXT.cloud + "</h4>",
//         control_div_id: "id_cloud",
//         control_group_id: "id_cloud_group",
//         buttons: [{id: "id_less50_cloud", caption: TXT.less50_cloud },
//                   {id: "id_more50_cloud", caption: TXT.more50_cloud }]},
//        {label: "<h4>Wind</h4>",
//         control_div_id: "id_wind",
//         control_group_id: "id_wind_group",
//         buttons: [{id: "id_calm_wind", caption: TXT.calm_wind },
//                   {id: "id_light_wind", caption: TXT.light_wind },
//                   {id: "id_strong_wind", caption: TXT.strong_wind }]}];

//     function addError(field_id, message) {
//         var id = "#" + field_id;
//         if ($(id).next('.help-inline').length === 0) {
//             $(id).after('<span class="help-inline">' + message + '</span>');
//             $(id).parents("div .control-group").addClass("error");
//         }
//         $(id).on('focus keypress click', function () {
//             $(this).next('.help-inline').fadeOut("fast", function () {
//                 $(this).remove();
//             });
//             $(this).parents('.control-group').removeClass('error');
//         });
//     }

//     function getSelected(field_id) {
//         var selection = [];
//         var id = "#" + field_id;
//         $(id).find("button").each(function (i) {
//             if ($(this).hasClass("active")) selection.push(i);
//         });
//         if (selection.length === 0) {
//             addError(field_id,TXT.choose);
//         }
//         return selection;
//     }

//     var modalChrome, header, body, footer, c1array, c2array;
//     c1array = []; c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push('<h3>' + TXT.select_weather + '</h3>');
//     c2array.push(HBTN.weatherFormOkBtn);
//     header = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
//     body = '<form id="id_weather_form" class="form-horizontal"><fieldset>';
//     $.each(weatherFormTemplate, function (i, v) {
//         body += setupRadioControlGroup(v);
//     });
//     body += '</fieldset></form>';
//     footer = '';

//     modalChrome = '<div class="modal-header">' + header + '</div>';
//     modalChrome += '<div class="modal-body">' + body + '</div>';
//     modalChrome += '<div class="modal-footer">' + footer +'</div>';

//     $("#id_weather").html(modalChrome);
//     $("#id_weather").modal({show: true, backdrop: "static", keyboard: false})

//     if (undefined !== init) {
//         $("#"+weatherFormTemplate[0].buttons[init[0]].id).button("toggle");
//         switch (init[0]) {
//         case 0:
//             $("#"+weatherFormTemplate[1].buttons[init[1]].id).button("toggle");
//             $("#id_sunlight_group").removeClass("hide");
//             $("#id_cloud_group").addClass("hide");
//             break;
//         case 1:
//             $("#"+weatherFormTemplate[2].buttons[init[1]].id).button("toggle");
//             $("#id_sunlight_group").addClass("hide");
//             $("#id_cloud_group").removeClass("hide");
//             break;
//         }
//         $("#"+weatherFormTemplate[3].buttons[init[2]].id).button("toggle");
//     }

//     $("#id_day").on("click", function (e) {
//         $("#id_sunlight_group").removeClass("hide");
//         $("#id_cloud_group").addClass("hide");
//     });
//     $("#id_night").on("click", function (e) {
//         $("#id_sunlight_group").addClass("hide");
//         $("#id_cloud_group").removeClass("hide");
//     });
//     $("#id_weatherFormOkBtn").on("click", function (e) {
//         var c, s, result = [];
//         var dn = getSelected("id_day_night");
//         var w  = getSelected("id_wind");

//         if (dn.length > 0) {
//             result.push(dn[0]);
//             if (dn[0] === 0) { // Day selected
//                 s = getSelected("id_sunlight");
//                 if (s.length > 0) result.push(s[0]);
//             }
//             else {  // Night selected
//                 c = getSelected("id_cloud");
//                 if (c.length > 0) result.push(c[0]);
//             }
//         }
//         if (w.length > 0) result.push(w[0]);

//         if (result.length === 3) {
//             $("#id_weather").modal("hide").html("");
//             if (undefined !== resultFunc) resultFunc(result);
//         }
//     });
// }
