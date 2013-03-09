// summary.js
/*global $, alert, TEMPLATE_PARAMS */
'use strict';

var CNSNT = {
    defaultSwathColor: [0,0,255],
    DTR: Math.PI/180.0,
    EARTH_RADIUS: 6378100,
    MAX_LAYERS: 16,
    RTD: 180.0/Math.PI
};

function removeFrom(array,value) {
    // Removes value from array, returns whether the value was found in the array
    var where = $.inArray(value,array);
    if (where >= 0) array.splice(where,1);
    return (where >= 0);
}

function hexToRGB(h) {
    var r, g, b;
    if (h.charAt(0)=="#") {
        r = parseInt(h.substring(1,3),16);
        g = parseInt(h.substring(3,5),16);
        b = parseInt(h.substring(5,7),16);
        return [r,g,b];
    }
    else return false;
}

$(document).ready(init);

function init() {
    var ticket = TEMPLATE_PARAMS.ticket + '/' + TEMPLATE_PARAMS.ts;
    var keyFile = '/' + ticket + '/key.json';
    $('#spinEditAmp').spinedit({
        minimum: 0.03,
        maximum: 10,
        step: 0.01,
        value: 0.1,
        numberOfDecimals: 2
    });
    initLayers();
    $.get('/rest/data' + keyFile, function(data) {
        var keyFile = '/'+TEMPLATE_PARAMS.ticket+'/'+TEMPLATE_PARAMS.ts+'/key.json';
        makeReport(data,
                   data.SUBTASKS.getAnalysesData,
                   data.SUBTASKS.getPathsData,
                   data.SUBTASKS.getPeaksData,
                   resultFunc);
        $("#keyContents").html(JSON.stringify(data));
    });
}

function makeReport(topLevel, analysesRef, pathsRef, peaksRef, resultFunc) {
    var remainingTasks = [];
    var REPORT = {
        analysesData: null,
        analysesRef: null,
        contexts: {},
        markerTable: [],
        maxLat: null,
        maxLng: null,
        meanLat: null,
        meanLng: null,
        minAmp: null,
        minLat: null,
        minLng: null,
        mpp: null,
        mx: null,
        my: null,
        nx: null,
        ny: null,
        padX: null,
        padY: null,
        pathsData: null,
        pathsRef: null,
        peaksData: null,
        peaksRef: null,
        peakLabels: [],
        peakTable: [],
        runsTable: [],
        scale: null,
        subx: null,
        suby: null,
        xform: null,
        zoom: null
    };

    REPORT.analysesRef = analysesRef;
    REPORT.pathsRef = pathsRef;
    REPORT.peaksRef = peaksRef;

    // Initializes REPORT structure from baseData
    REPORT.padX = 10;
    REPORT.padY = 30;
    // Enumerate the tasks that need to be completed
    remainingTasks.push("base");
    remainingTasks.push("peaks");
    // remainingTasks.push("path");
    // remainingTasks.push("submapGrid");
    //
    setupReport();
    makeBaseLayers();
    makePeaksLayers();
    makePathsLayer();
    // makeSubmapGridLayer();
    // makePathAndSwathLayers();

    $('#spinEditAmp').on("valueChanged", function (e) {
        REPORT.minAmp = e.value;
        updatePeaksLayers();
    });


    function checkDone(artifact) {
        removeFrom(remainingTasks, artifact);
        if (remainingTasks.length === 0) resultFunc(REPORT);
    }


    function setupReport() {
        var cosLat, deltaLat, deltaLng, fac, mppx, mppy, Xp, Yp;
        REPORT.minLat = topLevel.INSTRUCTIONS.swCorner[0];
        REPORT.minLng = topLevel.INSTRUCTIONS.swCorner[1];
        REPORT.maxLat = topLevel.INSTRUCTIONS.neCorner[0];
        REPORT.maxLng = topLevel.INSTRUCTIONS.neCorner[1];
        REPORT.meanLat = 0.5*(REPORT.minLat + REPORT.maxLat);
        REPORT.meanLng = 0.5*(REPORT.minLng + REPORT.maxLng);
        Xp = REPORT.maxLng - REPORT.minLng;
        Yp = REPORT.maxLat - REPORT.minLat;
        // Find largest zoom consistent with these limits
        cosLat = Math.cos(REPORT.meanLat * CNSNT.DTR);
        REPORT.zoom = Math.floor(Math.floor(Math.log(Math.min((360.0 * 640) / (
            256 * Xp), (360.0 * 640 * cosLat) / (256 * Yp))) / Math.log(2.0)));
        // Find the number of pixels in each direction
        fac = (256.0 / 360.0) * Math.pow(2,REPORT.zoom);
        REPORT.mx = Math.ceil(fac * Xp);
        REPORT.my = Math.ceil(fac * Yp / cosLat);
        REPORT.scale = 2;
        REPORT.nx = REPORT.scale * REPORT.mx;
        REPORT.ny = REPORT.scale * REPORT.my;

        // Calculate meters per pixel
        deltaLat = CNSNT.RTD / CNSNT.EARTH_RADIUS;
        deltaLng = CNSNT.RTD / (CNSNT.EARTH_RADIUS * Math.cos(REPORT.meanLat * CNSNT.DTR));
        mppx = Xp / (deltaLng * REPORT.nx);
        mppy = Yp / (deltaLat * REPORT.ny);
        REPORT.mpp = 0.5 * (mppx + mppy);

        // Transformation to pixels
        REPORT.xform = function (lng, lat) {
            var x = Math.round(REPORT.nx * (lng - REPORT.minLng) / (REPORT.maxLng - REPORT.minLng));
            var y = Math.round(REPORT.ny * (lat - REPORT.maxLat) / (REPORT.minLat - REPORT.maxLat));
            return [x,y];
        };
        REPORT.inMap = function (lat,lng) {
            return ( REPORT.minLat <= lat && lat < REPORT.maxLat &&
                     REPORT.minLng <= lng && lng < REPORT.maxLng );
        };
        REPORT.inView = function (xy) {
            return ( -REPORT.padX <= xy[0] && xy[0] < REPORT.nx+REPORT.padX &&
                     -REPORT.padY <= xy[1] && xy[1] < REPORT.ny+REPORT.padY );
        };
    }


    function makeBaseLayers() {
        var image1 = new Image();
        var maptype = "map";
        var params = { center: REPORT.meanLat.toFixed(6) + "," + REPORT.meanLng.toFixed(6),
                       zoom: REPORT.zoom, size: REPORT.mx + "x" + REPORT.my, scale: REPORT.scale,
                       maptype: maptype, sensor: false };
        var url = 'http://maps.googleapis.com/maps/api/staticmap?' + $.param(params);
        image1.src = url;
        remainingTasks.push("map");
        remainingTasks.push("satellite");
        removeFrom(remainingTasks, "base");
        image1.onload = function () {
            var ctx = document.createElement("canvas").getContext("2d");
            ctx.canvas.height = this.height + REPORT.padY;
            ctx.canvas.width = this.width + REPORT.padX;
            ctx.drawImage(this, REPORT.padX, REPORT.padY);
            REPORT.contexts["map"] = ctx;
            checkDone("map");
        };
        var image2 = new Image();
        maptype = "satellite";
        params = { center: REPORT.meanLat.toFixed(6) + "," + REPORT.meanLng.toFixed(6),
                       zoom: REPORT.zoom, size: REPORT.mx + "x" + REPORT.my, scale: REPORT.scale,
                       maptype: maptype, sensor: false };
        url = 'http://maps.googleapis.com/maps/api/staticmap?' + $.param(params);
        image2.src = url;
        image2.onload = function () {
            var ctx = document.createElement("canvas").getContext("2d");
            ctx.canvas.height = this.height + REPORT.padY;
            ctx.canvas.width = this.width + REPORT.padX;
            ctx.drawImage(this, REPORT.padX, REPORT.padY);
            REPORT.contexts["satellite"] = ctx;
            checkDone("satellite");
        };
    }


    function makePeaksLayers() {
        var workDir = '/rest/data/'+REPORT.peaksRef.SUBMIT_KEY.hash+'/'+REPORT.peaksRef.SUBMIT_KEY.dir_name;
        REPORT.peaksData = [];
        REPORT.minAmp = $("#spinEditAmp").val();

        function getPeaksData(fileNames) {
            var names = fileNames.slice(0);
            function next() {
                var url;
                if (names.length === 0) {
                    makePeaks(REPORT);
                    makeWedges(REPORT);
//                  makePeaksTable(REPORT);
                    checkDone("peaks");
                }
                else {
                    url = workDir + '/' + names.shift();
                    $.getJSON(url, function(data) {
                        data.forEach(function (d) { // Can filter by lat-lng limits here
                            REPORT.peaksData.push(d);
                        });
                        next();
                    });
                }
            }
            next();
        }
        getPeaksData(REPORT.peaksRef.OUTPUTS.FILES);
    }

    function updatePeaksLayers() {
        REPORT.minAmp = $("#spinEditAmp").val();
        makePeaks(REPORT);
        makeWedges(REPORT);
//        makePeaksTable(REPORT);
        replaceLayer(REPORT.contexts["wedges"],[0,0],5);
        replaceLayer(REPORT.contexts["peaks"],[0,0],6);
        $("#peakstablediv").html(REPORT.peakTable.join("\n"));
        $(".table-datatable").dataTable({
            "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"
        });
    }

    function makePathsLayer() {
        var workDir = '/rest/data/'+REPORT.pathsRef.SUBMIT_KEY.hash+'/'+REPORT.pathsRef.SUBMIT_KEY.dir_name;
        REPORT.pathsData = [];

        function getPathsData(fileNames) {
            var names = fileNames.slice(0);
            function next() {
                var url;
                if (names.length === 0) {
                    makePaths(REPORT);
                    checkDone("path");
                }
                else {
                    var name = names.shift();
                    var comps = name.split(/[_.]/);
                    var run = +comps[1];
                    var survey = +comps[2];
                    url = workDir + '/' + name;
                    $.getJSON(url, function(data) {
                        data.forEach(function (d) {
                            d["N"] = run;
                            d["S"] = survey;
                            var where = decodeGeoHash(d.P);
                            var lat = where.latitude[2];
                            var lng = where.longitude[2];
                            if (lat >= REPORT.minLat && lat <= REPORT.maxLat &&
                                lng >= REPORT.minLng && lng <= REPORT.maxLng) {
                                REPORT.pathsData.push(d);
                            }
                        });
                        next();
                    });
                }
            }
            next();
        }
        getPathsData(REPORT.pathsRef.OUTPUTS.FILES);
    }
}

function resultFunc(report) {
    var sources;
    addLayer(report.contexts["map"],[0,0],1,"map");
    addLayer(report.contexts["satellite"],[0,0],2,"satellite");
    addLayer(report.contexts["path"],[0,0],3,"path");
    addLayer(report.contexts["swath"],[0,0],4,"swath");
    addLayer(report.contexts["wedges"],[0,0],5,"wedges");
    addLayer(report.contexts["peaks"],[0,0],6,"peaks");
    addLayer(report.contexts["submapGrid"],[0,0],7,"submapGrid");
}

function initLayers() {
    function clickMaker(layer) {
        return (function() {
            var $this = $(this);
            var layer = $this.data("layer");
            if ($this.is(":checked")) $('#id_layer' + layer).show();
            else $('#id_layer' + layer).hide();
        });
    }
    for (var layer = 1; layer <= CNSNT.MAX_LAYERS; layer++) {
        var id0 = 'id_label' + layer;
        var id1 = 'id_check' + layer;
        var id2 = 'id_layer' + layer;
        var elem = '<label id="' + id0 + '" class="checkbox"><input id="' + id1 + '" type="checkbox" checked="checked"></input></label>';
        var canvas = '<canvas id="' + id2 + '" style="z-index:' + layer +
                     '; position:absolute; left:0px; top:0px;"></canvas>';
        $("#checkboxdiv").append(elem);
        $("#canvasesdiv").append(canvas);
        $('#' + id1).data("layer", layer);
        $("label[for='" + id1 + "']").hide();
        $('#' + id0).hide();
        $('#' + id2).data("layer", layer).hide();
        // Make checkbox toggle visibility of layer
        $('#' + id1).click(clickMaker(layer));
    }
}

function addLayer(source, padding, layer, caption) {
    // Add the image as a new layer in the collection of canvases which make up the
    //  composite map
    if (source) {
        var id0 = 'id_label' + layer;
        var id1 = 'id_check' + layer;
        var id2 = 'id_layer' + layer;
        $('#' + id0).append(caption + '&nbsp;&nbsp;').show();
        var ctx = $('#' + id2)[0].getContext("2d");
        ctx.canvas.width = source.canvas.width + 2 * padding[0];
        ctx.canvas.height = source.canvas.height + 2 * padding[1];
        ctx.drawImage(source.canvas, padding[0], padding[1]);
        if ($('#' + id1).is(":checked")) $('#' + id2).show();
        if (ctx.canvas.width > $('#canvasesdiv').width()) $('#canvasesdiv').width(ctx.canvas.width);
        if (ctx.canvas.height > $('#canvasesdiv').height()) $('#canvasesdiv').height(ctx.canvas.height);
    }
}

function replaceLayer(source, padding, layer) {
    // Replace the image in a specified layer in a collection of canvases
    var id2 = 'id_layer' + layer;
    var ctx = $('#' + id2)[0].getContext("2d");
    ctx.clearRect(0,0,ctx.canvas.width,ctx.canvas.height);
    ctx.beginPath();
    ctx.drawImage(source.canvas, padding[0], padding[1]);
}

function makeComposite(id, sources, padding) {
    var i, s, init;
    var canvas = '<canvas style="position:absolute; left:0px; top:0px;"></canvas>';
    var $div = $("#" + id);
    $div.append(canvas);
    var ctx = $("#" + id + ">canvas")[0].getContext("2d");
    init = false;
    for (i=0; i<sources.length; i++) {
        s = sources[i];
        if (s) {
            if (!init) {
                ctx.canvas.width  = s.canvas.width  + 2 * padding[0];
                ctx.canvas.height = s.canvas.height + 2 * padding[1];
                $div.width(ctx.canvas.width);
                $div.height(ctx.canvas.height);
                init = true;
            }
            ctx.drawImage(s.canvas, padding[0], padding[1]);
        }
    }
}

function peaksColorByRun(run) {
    return "#FFFF00";
}

function makePeaks(report) {
    var i, j, x, xy, y;
    var color, colors, ctxPeaks, data, lat, lng, minAmp, pCanvas, peaks, run, where;
    var size = 0.7;
    peaks = report.peaksData;
    ctxPeaks = document.createElement("canvas").getContext("2d");
    ctxPeaks.canvas.height = report.ny + 2 * report.padY;
    ctxPeaks.canvas.width  = report.nx + 2 * report.padX;

    // Filter peaks by amplitude (defined per run) and assign ranks to
    //  those remaining. Also determine which colors of marker are required
    report.peakLabels = [];
    colors = {};
    j = 1;
    for (i=0; i<peaks.length; i++) {
        run = peaks[i].R;
        // minAmp = data.RUNS[run].minAmp;
        minAmp = report.minAmp;
        if (peaks[i].A >= minAmp) {
            report.peakLabels.push("" + (j++));
            color = peaksColorByRun(run);
            if (color) {
                if (!(color in colors)) colors[color] = true;
            }
        }
        else {
            report.peakLabels.push("");
        }
    }

    // Make empty bubbles for each marker color required
    pCanvas = {};
    for (var c in colors) {
        if (colors.hasOwnProperty(c)) {
            pCanvas[c] = new Marker(size,c,"black");
        }
    }
    // Get the peaks in reverse rank order so they overlay correctly
    for (i=peaks.length-1; i>=0; i--) {
        run = peaks[i].R;
        color = peaksColorByRun(run);
        where = decodeGeoHash(peaks[i].P);
        lat = where.latitude[2];
        lng = where.longitude[2];
        xy = report.xform(lng, lat);
        x = xy[0], y = xy[1];
        if (report.inView(xy)) {
            if (report.peakLabels[i] && color) {
                pCanvas[color].annotate(ctxPeaks, x+report.padX, y+report.padY, report.peakLabels[i], "bold 13px sans-serif", "black");
            }
            else {
                var radius = 4;
                ctxPeaks.fillStyle = color;
                ctxPeaks.beginPath();
                ctxPeaks.arc(x + report.padX, y + report.padY, radius, 0.0, 2*Math.PI);
                ctxPeaks.fill();
                ctxPeaks.strokeStyle = 'black';
                ctxPeaks.stroke();
            }
        }
    }
    report.contexts["peaks"] = ctxPeaks;
}

function wedgeColorByRun(run) {
    return "#0000FF";
}

function makeWedges(report) {
    var i, x, xy, y;
    var color, ctxWedges, data, lat, lng, peaks, run, where;

    peaks = report.peaksData;
    // Draw the wind wedges on a canvas
    ctxWedges = document.createElement("canvas").getContext("2d");
    ctxWedges.canvas.height = report.ny + 2 * report.padY;
    ctxWedges.canvas.width  = report.nx + 2 * report.padX;

    for (i=peaks.length-1; i>=0; i--) {
        run = peaks[i].R;
        color = wedgeColorByRun(run);
        if (report.peakLabels[i] && color) {
            where = decodeGeoHash(peaks[i].P);
            lat = where.latitude[2];
            lng = where.longitude[2];
            var wedgeColor = hexToRGB(color);
            var windMean = peaks[i].W;
            var windSdev = peaks[i].U;
            xy = report.xform(lng, lat);
            x = xy[0], y = xy[1];
            ctxWedges.fillStyle = "rgba(" + wedgeColor[0] + "," + wedgeColor[1] + "," + wedgeColor[2] + ",0.7)";
            if (report.inView(xy)) {
                var radius = 50.0 / report.mpp;
                var minBearing, maxBearing;
                if (typeof(windMean) === "number" && typeof(windSdev) === "number") {
                    if (windSdev < 90.0) {
                        minBearing = windMean - Math.min(2*windSdev, 180.0);
                        maxBearing = windMean + Math.min(2*windSdev, 180.0);
                        ctxWedges.beginPath();
                        ctxWedges.moveTo(x + report.padX, y + report.padY);
                        ctxWedges.lineTo(x + report.padX + radius * Math.sin(CNSNT.DTR * minBearing),
                                   y + report.padY - radius * Math.cos(CNSNT.DTR * minBearing));
                        ctxWedges.arc(x + report.padX, y + report.padY, radius,
                                CNSNT.DTR*minBearing-0.5*Math.PI, CNSNT.DTR*maxBearing-0.5*Math.PI, false);
                        ctxWedges.closePath();
                        ctxWedges.fill();
                        continue;
                    }
                }
                // Draw a full circle if we have no information about the direction
                ctxWedges.beginPath();
                ctxWedges.arc(x + report.padX, y + report.padY, radius, 0.0, 2*Math.PI);
                ctxWedges.fill();
            }
        }
    }
    report.contexts["wedges"] = ctxWedges;
}

function makePaths(report) {
    // Draw the vehicle path
    var i, k;
    var coords, ctxPath, data, lat, lng, run, survey, where;
    var pathColor = [[0,0,255,1.0], [0,0,0,1.0], [255,0,0,1.0], [255,0,0,1.0]];

    var paths = report.pathsData;
    ctxPath = document.createElement("canvas").getContext("2d");
    ctxPath.canvas.height = report.ny + 2 * report.padY;
    ctxPath.canvas.width  = report.nx + 2 * report.padX;

    function renderPath(path) {
        var l;
        if (path.length > 0) {
            ctxPath.beginPath();
            ctxPath.moveTo(path[0][0] + report.padX, path[0][1] + report.padY);
            for (l=1; l<path.length; l++) {
                ctxPath.lineTo(path[l][0] + report.padX, path[l][1] + report.padY);
            }
            ctxPath.stroke();
        }
    }
 
    var path = [];
    var lastP = {};
    for (i=0; i<paths.length; i++) {
        var p = {"pathType": paths[i].T, "survey": paths[i].S, "run": paths[i].N,
                 "row": paths[i].R, "position": paths[i].P};
        ctxPath.lineWidth = 2;
        where = decodeGeoHash(p.position);
        lng = where.longitude[2];
        lat = where.latitude[2];
        var xy = report.xform(lng, lat);
        p.x = xy[0], p.y = xy[1];
        // Here follows logic to draw the path depending on the last point and this point
        var inMap = report.inView(xy);
        var adjacentPoints = (p.row === (lastP.row + 1)) && (p.survey === lastP.survey) && (p.run === lastP.run);
        var sameType =  (p.pathType === lastP.pathType);
        if (!(adjacentPoints && sameType && inMap)) {  // Write out any old path
            renderPath(path);
            path = [];
        }
        // Update to new style according to the path type
        ctxPath.strokeStyle = "rgba(" + pathColor[p.pathType][0] + "," + pathColor[p.pathType][1] + "," +
                                        pathColor[p.pathType][2] + "," + pathColor[p.pathType][3] + ")";
        if (adjacentPoints && !sameType && inMap) path.push([lastP.x, lastP.y]);
        if (inMap)  path.push([p.x, p.y]);
        lastP = p;
    }
    renderPath(path);
    path = [];
    report.contexts["path"] = ctxPath;
}


/* Generate a marker */

function Marker(size,fillColor,strokeColor) {
    var ctx = document.createElement("canvas").getContext("2d");
    var b = 1.25 * size;
    var t = 2.0 * size;
    this.nx = 36 * size + 1;
    this.ny = 65 * size + 1;
    this.size = size;
    var r = 0.5 * (this.nx - 1 - t);
    var h = this.ny - 1 - t;
    var phi = Math.PI * 45.0/180.0;
    var theta = 0.5 * Math.PI - phi;
    var xoff = r + 0.5 * t;
    var yoff = r + 0.5 * t;
    var knot = (r - b * Math.sin(phi)) / Math.cos(phi);
    ctx.canvas.width = this.nx;
    ctx.canvas.height = this.ny;
    ctx.beginPath();
    ctx.lineWidth = t;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = fillColor;
    ctx.translate(xoff, yoff);
    ctx.moveTo(-b, (h - r));
    ctx.quadraticCurveTo(-b, knot, -r * Math.sin(phi), r * Math.cos(phi));
    ctx.arc(0, 0, r, Math.PI - theta, theta, false);
    ctx.quadraticCurveTo(b, knot, b, (h - r));
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    this.canvas = ctx.canvas;
}

Marker.prototype.annotate = function(ctx, x, y, msg, font, textColor) {
    ctx.fillStyle = textColor;
    ctx.font = font;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.drawImage(this.canvas,x-18*this.size,y-65*this.size);
    ctx.fillText(msg,x,y-44.5*this.size);
};
