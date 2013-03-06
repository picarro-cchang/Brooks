/*global TEMPLATE_PARAMS:true, $:true, decodeGeoHash:true, encodeGeoHash:true, _:true */

var CNSNT = {
    defaultSwathColor: [0,0,255],
    DTR: Math.PI/180.0,
    EARTH_RADIUS: 6378100,
    MAX_LAYERS: 16,
    RTD: 180.0/Math.PI,
    svcurl: '/rest'
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

function makeSubmapGrid(report) {
    var ctxGrid, dx, dy, height, maxLat, maxLng, minLat, minLng, mx, my;
    var name, necorner, rect, row, swcorner, url, width, x, xy, y;
    var submaps = [], rowList;
    ctxGrid = document.createElement("canvas").getContext("2d");
    ctxGrid.canvas.height = report.ny + 2 * report.padY;
    ctxGrid.canvas.width  = report.nx + 2 * report.padX;
    // Create the submap regions
    if (report.subx > 1 || report.suby > 1) {
        dx = (report.maxLng - report.minLng) / report.subx;
        dy = (report.maxLat - report.minLat) / report.suby;
        maxLat = report.maxLat;
        for (my=0; my<report.suby; my++) {
            minLat = maxLat - dy;
            minLng = report.minLng;
            rowList = [];
            for (mx=0; mx<report.subx; mx++) {
                maxLng = minLng + dx;
                rowList.push({"minLng": minLng, "minLat": minLat, "maxLng": maxLng, "maxLat": maxLat});
                minLng = maxLng;
            }
            submaps.push(rowList);
            maxLat = minLat;
        }
        ctxGrid.strokeStyle = "blue";
        ctxGrid.lineWidth = 1;
        ctxGrid.fillStyle = "blue";
        ctxGrid.font = "bold 36px sans-serif";
        ctxGrid.textAlign = "center";
        ctxGrid.textBaseline = "middle";
        $("#submaplinks").empty();
        for (my=0; my<submaps.length; my++) {
            row = submaps[my];
            for (mx=0; mx<row.length; mx++) {
                rect = row[mx];
                xy = report.xform(rect.minLng, rect.maxLat);
                x = xy[0];
                y = xy[1];
                xy = report.xform(rect.maxLng, rect.minLat);
                width = xy[0] - x;
                height = xy[1] - y;
                ctxGrid.strokeRect(x + report.padX, y + report.padY, width, height);
                name = String.fromCharCode(65+my) + (mx + 1);
                ctxGrid.fillText(name, x + report.padX + width / 2, y + report.padY + height / 2);
                swcorner = encodeGeoHash(rect.minLat, rect.minLng);
                necorner = encodeGeoHash(rect.maxLat, rect.maxLng);
                url = '/rest/getJsonReport?' + $.param({"ticket": TEMPLATE_PARAMS.ticket, "region": TEMPLATE_PARAMS.region,
                                                        "swcorner": swcorner, "necorner": necorner });
                $("#submaplinks").append('<p><a href="' + url + '" target="_blank">' + name + '</a></p>');
            }
        }
    }
    report.contexts["submapGrid"] = ctxGrid;
}

function makePath(report) {
    // Draw the vehicle path
    var i, k, l;
    var coords, ctxPath, data, lat, lng, run, survey, where;
    var pathColor = [[0,0,255,1.0], [0,0,0,1.0], [255,0,0,1.0], [255,0,0,1.0]];

    data = report.pathData;
    ctxPath = document.createElement("canvas").getContext("2d");
    ctxPath.canvas.height = report.ny + 2 * report.padY;
    ctxPath.canvas.width  = report.nx + 2 * report.padX;

    for (i=0; i<data.PATHS.length; i++) {
        var path = [];
        var p = data.PATHS[i];
        var pathType = p.TYPE;
        coords = p.PATH;
        survey = p.SURVEY;
        run = p.RUN;
        ctxPath.lineWidth = 2;
        ctxPath.strokeStyle = "rgba(" + pathColor[pathType][0] + "," + pathColor[pathType][1] + "," +
                                    pathColor[pathType][2] + "," + pathColor[pathType][3] + ")";
        for (k=0; k<coords.length; k++) {
            where = decodeGeoHash(coords[k]);
            lng = where.longitude[2];
            lat = where.latitude[2];
            var xy = report.xform(lng, lat);
            var x = xy[0], y = xy[1];
            if (report.inView(xy)) {
                path.push([x,y]);
            }
            else {
                if (path.length > 0) {
                    ctxPath.beginPath();
                    ctxPath.moveTo(path[0][0] + report.padX, path[0][1] + report.padY);
                    for (l=1; l<path.length; l++) {
                        ctxPath.lineTo(path[l][0] + report.padX, path[l][1] + report.padY);
                    }
                    ctxPath.stroke();
                    path = [];
                }
            }
        }
        if (path.length > 0) {
            ctxPath.beginPath();
            ctxPath.moveTo(path[0][0] + report.padX, path[0][1] + report.padY);
            for (l=1; l<path.length; l++) {
                ctxPath.lineTo(path[l][0] + report.padX, path[l][1] + report.padY);
            }
            ctxPath.stroke();
        }
    }
    report.contexts["path"] = ctxPath;
}

function makeSwath(report) {
    var i, k, s;
    var color, coords, edges, ctxSwath, data, lat, lng, run, survey, where;

    data = report.pathData;
    ctxSwath = document.createElement("canvas").getContext("2d");
    ctxSwath.canvas.height = report.ny + 2 * report.padY;
    ctxSwath.canvas.width  = report.nx + 2 * report.padX;

    for (i=0; i<data.SWATHS.length; i++) {
        s = data.SWATHS[i];
        edges = s.EDGE;
        coords = s.PATH;
        survey = s.SURVEY;
        run = s.RUN;
        color = hexToRGB(data.RUNS[run].swath);
        if (!color) color = CNSNT.defaultSwathColor;
        ctxSwath.fillStyle = "rgba(" + color[0] + "," + color[1] + "," + color[2] + ",0.4)";
        ctxSwath.strokeStyle = "rgba(" + color[0] + "," + color[1] + "," + color[2] + ",0.5)";
        ctxSwath.lineWidth = 1;
        var lastLng = null, lastLat = null;
        var lastEdgeLng = null, lastEdgeLat = null;

        for (k=0; k<coords.length; k++) {
            where = decodeGeoHash(coords[k]);
            lng = where.longitude[2];
            lat = where.latitude[2];
            var edge = decodeGeoHash(edges[k]);
            var edgeLng = edge.longitude[2];
            var edgeLat = edge.latitude[2];
            if (lastLng !== null) {
                var noLastView = (where == edge);
                if (!noLastView) {
                    var xy1 = report.xform(lastEdgeLng, lastEdgeLat);
                    if (report.inView(xy1)) {
                        var xy2 = report.xform(lastLng, lastLat);
                        if (report.inView(xy2)) {
                            var xy3 = report.xform(lng, lat);
                            if (report.inView(xy3)) {
                                var xy4 = report.xform(edgeLng, edgeLat);
                                if (report.inView(xy4)) {
                                    ctxSwath.beginPath();
                                    ctxSwath.moveTo(report.padX + xy1[0], report.padY + xy1[1]);
                                    ctxSwath.lineTo(report.padX + xy2[0], report.padY + xy2[1]);
                                    ctxSwath.lineTo(report.padX + xy3[0], report.padY + xy3[1]);
                                    ctxSwath.lineTo(report.padX + xy4[0], report.padY + xy4[1]);
                                    ctxSwath.stroke();
                                    ctxSwath.fill();
                                }
                            }
                        }
                    }
                }
            }
            lastLng = lng;
            lastLat = lat;
            lastEdgeLng = edgeLng;
            lastEdgeLat = edgeLat;
        }
    }
    report.contexts["swath"] = ctxSwath;
}

function makePeaks(report) {
    var i, j, x, xy, y;
    var color, colors, ctxPeaks, data, lat, lng, minAmpl, pCanvas, peaks, run, where;
    var size = 0.7;
    data = report.peaksData;
    peaks = data.PEAKS;
    ctxPeaks = document.createElement("canvas").getContext("2d");
    ctxPeaks.canvas.height = report.ny + 2 * report.padY;
    ctxPeaks.canvas.width  = report.nx + 2 * report.padX;

    // Filter peaks by amplitude (defined per run) and assign ranks to
    //  those remaining. Also determine which colors of marker are required
    report.peakLabels = [];
    colors = {};
    j = 1;
    for (i=0; i<peaks.LOCATION.length; i++) {
        run = peaks.RUN[i];
        // minAmpl = data.RUNS[run].minAmpl;
        minAmpl = report.minAmpl;
        if (peaks.AMPLITUDE[i] >= minAmpl) {
            report.peakLabels.push("" + (j++));
            color = data.RUNS[run].marker;
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
    for (i=peaks.LOCATION.length-1; i>=0; i--) {
        run = peaks.RUN[i];
        color = data.RUNS[run].marker;
        where = decodeGeoHash(peaks.LOCATION[i]);
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

function makeWedges(report) {
    var i, x, xy, y;
    var color, ctxWedges, data, lat, lng, peaks, run, where;

    data = report.peaksData;
    peaks = data.PEAKS;
    // Draw the wind wedges on a canvas
    ctxWedges = document.createElement("canvas").getContext("2d");
    ctxWedges.canvas.height = report.ny + 2 * report.padY;
    ctxWedges.canvas.width  = report.nx + 2 * report.padX;

    for (i=peaks.LOCATION.length-1; i>=0; i--) {
        run = peaks.RUN[i];
        color = data.RUNS[run].wedges;
        if (report.peakLabels[i] && color) {
            where = decodeGeoHash(peaks.LOCATION[i]);
            lat = where.latitude[2];
            lng = where.longitude[2];
            var wedgeColor = hexToRGB(color);
            var windMean = peaks.WIND_DIR_MEAN[i];
            var windSdev = peaks.WIND_DIR_SDEV[i];
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

function makeRunsTable(report) {
    var i, j, runs;
    var peaksData = report.peaksData;
    var pathData = report.pathData;
    runs = [];
    if (pathData) {
        for (i=0; i<pathData.RUNS.length; i++) {
            for (j=0; j<runs.length; j++) {
                if (_.isEqual(runs[j],pathData.RUNS[i])) break;
            }
            if (j === runs.length) {
                runs.push(pathData.RUNS[i]);
            }
        }
    }
    if (peaksData) {
        for (i=0; i<peaksData.RUNS.length; i++) {
            for (j=0; j<runs.length; j++) {
                if (_.isEqual(runs[j],peaksData.RUNS[i])) break;
            }
            if (j === runs.length) {
                runs.push(peaksData.RUNS[i]);
            }
        }
    }
    report.runsTable = [];
    report.runsTable.push('<table class="table table-striped table-condensed table-fmt1">');
    report.runsTable.push('<thead><tr>');
    report.runsTable.push('<th style="width:20%">Analyzer</th>');
    report.runsTable.push('<th style="width:15%">Start (GMT)</th>');
    report.runsTable.push('<th style="width:15%">End (GMT)</th>');
    report.runsTable.push('<th style="width:10%">Peaks</th>');
    report.runsTable.push('<th style="width:10%">Wedges</th>');
    report.runsTable.push('<th style="width:10%">Swath</th>');
    report.runsTable.push('<th style="width:10%">Excl Radius</th>');
    report.runsTable.push('<th style="width:10%">Stab Class</th>');
    report.runsTable.push('</tr></thead>');
    report.runsTable.push('<tbody>');
    for (j=0; j<runs.length; j++) {
        var run = runs[j];
        report.runsTable.push('<tr>');
        report.runsTable.push('<td>' + run.analyzer + '</td>');
        report.runsTable.push('<td>' + run.startEtm + '</td>');
        report.runsTable.push('<td>' + run.endEtm + '</td>');
        report.runsTable.push('<td>' + run.marker + '</td>');
        report.runsTable.push('<td>' + run.wedges + '</td>');
        report.runsTable.push('<td>' + run.swath + '</td>');
        report.runsTable.push('<td>' + run.exclRadius + '</td>');
        report.runsTable.push('<td>' + run.stabClass + '</td>');
        report.runsTable.push('</tr>');
    }
    report.runsTable.push('</tbody>');
    report.runsTable.push('</table>');
}

function makeSurveysTable(report) {
    var i, j, survey, surveys;
    var peaksData = report.peaksData;
    var pathData = report.pathData;
    surveys = [];
    if (pathData) {
        for (i=0; i<pathData.SURVEYS.length; i++) {
            survey = pathData.SURVEYS[i].substr(0,pathData.SURVEYS[i].lastIndexOf("."));
            for (j=0; j<surveys.length; j++) {
                if (surveys[j] === survey) break;
            }
            if (j === surveys.length) {
                surveys.push(survey);
            }
        }
    }
    if (peaksData) {
        for (i=0; i<peaksData.SURVEYS.length; i++) {
            survey = peaksData.SURVEYS[i].substr(0,peaksData.SURVEYS[i].lastIndexOf("."));
            for (j=0; j<surveys.length; j++) {
                if (surveys[j] === survey) break;
            }
            if (j === surveys.length) {
                surveys.push(survey);
            }
        }
    }
    report.surveysTable = [];
    report.surveysTable.push('<table class="table table-striped table-condensed table-fmt1">');
    report.surveysTable.push('<thead><tr>');
    report.surveysTable.push('<th style="width:100%">Survey</th>');
    report.surveysTable.push('</tr></thead>');
    report.surveysTable.push('<tbody>');
    for (j=0; j<surveys.length; j++) {
        survey = surveys[j];
        report.surveysTable.push('<tr>');
        report.surveysTable.push('<td>' + survey + '</td>');
        report.surveysTable.push('</tr>');
    }
    report.surveysTable.push('</tbody>');
    report.surveysTable.push('</table>');
}

function makePeaksTable(report) {
    var i;
    var ampl, anz, ch4, data, etm, lat, lng, peaks, where;

    data = report.peaksData;
    if (data) {
        peaks = data.PEAKS;
        // Generate the peakTable

        var zoom = 18;
        report.peakTable = [];
        report.peakTable.push('<table class="table table-striped table-condensed table-fmt1 table-datatable">');
        report.peakTable.push('<thead><tr>');
        report.peakTable.push('<th style="width:10%">Rank</th>');
        report.peakTable.push('<th style="width:30%">Designation</th>');
        report.peakTable.push('<th style="width:20%">Latitude</th>');
        report.peakTable.push('<th style="width:20%">Longitude</th>');
        report.peakTable.push('<th style="width:10%">Conc</th>');
        report.peakTable.push('<th style="width:10%">Ampl</th>');
        report.peakTable.push('</tr></thead>');
        report.peakTable.push('<tbody>');

        for (i=0; i<peaks.LOCATION.length; i++) {
            ampl = peaks.AMPLITUDE[i];
            if (report.peakLabels[i]) {
                etm = peaks.EPOCH_TIME[i];
                anz = peaks.ANALYZER[i];
                where = decodeGeoHash(peaks.LOCATION[i]);
                lat = where.latitude[2];
                lng = where.longitude[2];
                ch4 = peaks.CH4[i];
                if (report.inMap(lat,lng)) {
                    var des = anz + '_' + getDateTime(new Date(1000*etm));
                    var url = "http://maps.google.com?q=(" + lat + "," + lng + ")+(" + des + ")&z=" + zoom;
                    report.peakTable.push('<tr>');
                    report.peakTable.push('<td>' + report.peakLabels[i] + '</td>');
                    report.peakTable.push('<td><a href="' + url + '" target="_blank">' +  des + '</a></td>');
                    report.peakTable.push('<td>' + lat.toFixed(6) + '</td>');
                    report.peakTable.push('<td>' + lng.toFixed(6) + '</td>');
                    report.peakTable.push('<td>' + ch4.toFixed(1) + '</td>');
                    report.peakTable.push('<td>' + ampl.toFixed(2) + '</td>');
                    report.peakTable.push('</tr>');
                }
            }
        }
        report.peakTable.push('</tbody>');
        report.peakTable.push('</table>');
    }
}

function makeReport(minLat, minLng, maxLat, maxLng, pathDataUrl, peaksDataUrl, resultFunc) {
    var remainingTasks = [];
    var REPORT = {
        contexts: {},
        markerTable: [],
        maxLat: null,
        maxLng: null,
        meanLat: null,
        meanLng: null,
        minAmpl: null,
        minLat: null,
        minLng: null,
        mpp: null,
        mx: null,
        my: null,
        nx: null,
        ny: null,
        padX: null,
        padY: null,
        pathDataUrl: null,
        pathData: null,
        peaksDataUrl: null,
        peaksData: null,
        peakLabels: [],
        peakTable: [],
        runsTable: [],
        scale: null,
        subx: null,
        suby: null,
        xform: null,
        zoom: null
    };

    function checkDone(artifact) {
        removeFrom(remainingTasks, artifact);
        if (remainingTasks.length === 0) resultFunc(REPORT);
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

    function makeSubmapGridLayer() {
        REPORT.subx = $("#spinEditCols").val();
        REPORT.suby = $("#spinEditRows").val();
        makeSubmapGrid(REPORT);
        checkDone("submapGrid");
    }

    function updateSubmapGridLayer() {
        REPORT.subx = $("#spinEditCols").val();
        REPORT.suby = $("#spinEditRows").val();
        makeSubmapGrid(REPORT);
        replaceLayer(REPORT.contexts["submapGrid"],[0,0],7);
    }

    function makePathAndSwathLayers() {
        $.getJSON(pathDataUrl, function(data) {
            REPORT.pathData = data;
            makePath(REPORT);
            makeSwath(REPORT);
            checkDone("path");
        }).fail(function(jqXHR, textStatus, errorThrown) {
            checkDone("path")
        });
    }

    function makePeaksLayers() {
        $.getJSON(peaksDataUrl, function(data) {
            REPORT.minAmpl = $("#spinEditAmpl").val();
            REPORT.peaksData = data;
            makePeaks(REPORT);
            makeWedges(REPORT);
            makePeaksTable(REPORT);
            checkDone("peaks");
        });
    }

    function updatePeaksLayers() {
        REPORT.minAmpl = $("#spinEditAmpl").val();
        makePeaks(REPORT);
        makeWedges(REPORT);
        makePeaksTable(REPORT);
        replaceLayer(REPORT.contexts["wedges"],[0,0],5);
        replaceLayer(REPORT.contexts["peaks"],[0,0],6);
        $("#peakstablediv").html(REPORT.peakTable.join("\n"));
        $(".table-datatable").dataTable({
            "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"
        });
    }

    REPORT.pathDataUrl = pathDataUrl;
    REPORT.peaksDataUrl = peaksDataUrl;
    // Initializes REPORT structure from baseData
    REPORT.padX = 10;
    REPORT.padY = 30;
    // Enumerate the tasks that need to be completed
    remainingTasks.push("base");
    remainingTasks.push("path");
    remainingTasks.push("peaks");
    remainingTasks.push("submapGrid");

    function setupReport() {
        var cosLat, deltaLat, deltaLng, fac, mppx, mppy, Xp, Yp;
        REPORT.minLat = minLat;
        REPORT.minLng = minLng;
        REPORT.maxLat = maxLat;
        REPORT.maxLng = maxLng;
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
    setupReport();
    makeBaseLayers();
    makeSubmapGridLayer();
    makePathAndSwathLayers();
    makePeaksLayers();
    $('#spinEditCols').on("valueChanged", function (e) {
        REPORT.suby = e.value;
        updateSubmapGridLayer();
    });
    $('#spinEditRows').on("valueChanged", function (e) {
        REPORT.subx = e.value;
        updateSubmapGridLayer();
    });
    $('#spinEditAmpl').on("valueChanged", function (e) {
        REPORT.minAmpl = e.value;
        updatePeaksLayers();
    });
}

function resultFunc(report)
{
    var sources;
    addLayer(report.contexts["map"],[0,0],1,"map");
    addLayer(report.contexts["satellite"],[0,0],2,"satellite");
    addLayer(report.contexts["path"],[0,0],3,"path");
    addLayer(report.contexts["swath"],[0,0],4,"swath");
    addLayer(report.contexts["wedges"],[0,0],5,"wedges");
    addLayer(report.contexts["peaks"],[0,0],6,"peaks");
    addLayer(report.contexts["submapGrid"],[0,0],7,"submapGrid");
    $("#peakstablediv").html(report.peakTable.join("\n"));
    /*
    sources = [report.contexts["map"],report.contexts["path"],report.contexts["wedges"],report.contexts["peaks"]];
    makeComposite("canvases2div", sources, [0,0]);
    sources = [report.contexts["satellite"],report.contexts["path"],report.contexts["swath"]];
    makeComposite("canvases3div", sources, [0,0]);
    */
    makeRunsTable(report);
    $("#runstablediv").html(report.runsTable.join("\n"));
    makeSurveysTable(report);
    $("#surveystablediv").html(report.surveysTable.join("\n"));
    $(".table-datatable").dataTable({
        "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"
    });
}

function init() {
    var ticket = TEMPLATE_PARAMS.ticket;
    var name = "baseData." + TEMPLATE_PARAMS.region;
    var baseDataUrl = CNSNT.svcurl + "/getJson?" + $.param({ticket: ticket, name: name});
    name = "pathData." + TEMPLATE_PARAMS.region;
    var pathDataUrl = CNSNT.svcurl + "/getJson?" + $.param({ticket: ticket, name: name});
    name = "peaksData." + TEMPLATE_PARAMS.region;
    var peaksDataUrl = CNSNT.svcurl + "/getJson?" + $.param({ticket: ticket, name: name});
    $.extend( $.fn.dataTableExt.oStdClasses, {
        "sWrapper": "dataTables_wrapper form-inline"
    });
    $('#spinEditRows').spinedit({
        minimum: 1,
        maximum: 10,
        step: 1,
        value: 1,
        numberOfDecimals: 0
    });
    $('#spinEditCols').spinedit({
        minimum: 1,
        maximum: 10,
        step: 1,
        value: 1,
        numberOfDecimals: 0
    });
    $('#spinEditAmpl').spinedit({
        minimum: 0.03,
        maximum: 10,
        step: 0.01,
        value: 0.1,
        numberOfDecimals: 2
    });
    initLayers();
    if (TEMPLATE_PARAMS.swcorner && TEMPLATE_PARAMS.necorner) {
        var swcorner = decodeGeoHash(TEMPLATE_PARAMS.swcorner);
        var necorner = decodeGeoHash(TEMPLATE_PARAMS.necorner);
        makeReport(swcorner.latitude[2], swcorner.longitude[2], necorner.latitude[2], necorner.longitude[2],
                   pathDataUrl, peaksDataUrl, resultFunc);
    }
    else {
        $.getJSON(baseDataUrl,function(baseData) {
            var minLat = baseData.BASE.swCorner[0];
            var minLng = baseData.BASE.swCorner[1];
            var maxLat = baseData.BASE.neCorner[0];
            var maxLng = baseData.BASE.neCorner[1];
            makeReport(minLat, minLng, maxLat, maxLng, pathDataUrl, peaksDataUrl, resultFunc);
        });
    }

}

function dec2hex(i,nibbles) {
    // Convert unsigned integer to hexadecimal of specified length with zero padding
    return (i+Math.pow(2,4*nibbles)).toString(16).substr(-nibbles).toUpperCase();
}

function colorTuple2Hex(colors) {
    var hexStr = [];
    for (var i=0; i<colors.length; i++) {
        hexStr.push(dec2hex(colors[i],2));
    }
    return hexStr.join("");
}

function getDateTime(d){
    // padding function
    var s = function(a,b) { return(1e15+a+"").slice(-b); };
    return d.getUTCFullYear() +
        s(d.getUTCMonth()+1,2) +
        s(d.getUTCDate(),2) + 'T' +
        s(d.getUTCHours(),2) +
        s(d.getUTCMinutes(),2) +
        s(d.getUTCSeconds(),2);
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
    // Replace the image in a specifiec layer in a collection of canvases
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

var Marker = function(size,fillColor,strokeColor) {
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
};

Marker.prototype.annotate = function(ctx, x, y, msg, font, textColor) {
    ctx.fillStyle = textColor;
    ctx.font = font;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.drawImage(this.canvas,x-18*this.size,y-65*this.size);
    ctx.fillText(msg,x,y-44.5*this.size);
};

//=============================================================================
// Initialize
//=============================================================================

function initialize(winH, winW)
{
    init();
}
