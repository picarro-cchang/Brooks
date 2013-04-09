/* makeAnalyses.js renders analysis results */
/* jshint undef:true, unused:true */
/* global define */

define (['app/cnsnt', 'app/geohash', 'app/utils', 'app/newIsoMarker', 'app/reportGlobals'],
function (CNSNT,       gh,            utils,       newIsoMarker,       REPORT) {
    'use strict';

    function analysisColorByRun(run) {
        return REPORT.settings.get("runs").at(run).get("analyses");
    }

    function makeAnalyses(report) {
        var aCanvas, analyses, color, colors, ctxAnalyses, i, j, lat, lng, run, where, x, xy, y;
        var size = 1.0;
        var txtSize = size*18;

        analyses = report.analysesData;
        // Draw the isotopic analyses results on a canvas
        ctxAnalyses = document.createElement("canvas").getContext("2d");
        ctxAnalyses.canvas.height = report.ny + 2 * report.padY;
        ctxAnalyses.canvas.width  = report.nx + 2 * report.padX;

        /* Find the labels and colors used in the markers */
        report.analysisLabels = [];
        colors = {};
        j = 1;
        for (i=0; i<analyses.length; i++) {
            run = analyses[i].attributes.R;
            report.analysisLabels.push("" + (j++));
            color = analysisColorByRun(run);
            if (color) {
                if (!(color in colors)) colors[color] = true;
            }
        }

        // Make empty bubbles for each marker color required. Use white labels for isotopic analysis
        aCanvas = {};
        for (var c in colors) {
            if (colors.hasOwnProperty(c)) {
                aCanvas[c] = newIsoMarker(size,c,"black");
            }
        }

        // Get the peaks in reverse rank order so they overlay correctly
        for (i=0; i<analyses.length; i++) {
            color = analysisColorByRun(run);
            where = gh.decodeGeoHash(analyses[i].attributes.P);
            lat = where.latitude[2];
            lng = where.longitude[2];
            xy = report.xform(lng, lat);
            x = xy[0], y = xy[1];
            if (report.inView(xy)) {
                aCanvas[color].annotate(ctxAnalyses, x+report.padX, y+report.padY, report.analysisLabels[i],
                    "bold " + txtSize + "px sans-serif", "white");
            }
        }

        return {"context": ctxAnalyses };
    }
    return makeAnalyses;
});
