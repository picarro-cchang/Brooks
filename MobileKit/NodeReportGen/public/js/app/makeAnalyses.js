/* makeAnalyses.js renders analysis results */
/*global module, require */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var CNSNT = require('common/cnsnt');
    var gh = require('app/geohash');
    var utils = require('app/utils');
    var newIsoMarker = require('app/newIsoMarker');
    var REPORT = require('app/reportGlobals');

    function analysisColorByRun(run) {
        return REPORT.settings.get("runs").at(run).get("analyses");
    }

    function makeAnalyses(report) {
        var aCanvas, analyses, color, colors, ctxAnalyses, disposition, i, j, lat, lng, run, where, x, xy, y;
        var size = 1.0;
        var txtSize = size*18;
        var grey = "#A0A0A0";

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
        // We reserve grey markers for bad captures
        aCanvas[grey] = newIsoMarker(size,grey,"black");
        for (var c in colors) {
            if (colors.hasOwnProperty(c)) {
                aCanvas[c] = newIsoMarker(size,c,"black");
            }
        }

        // Get the peaks in reverse rank order so they overlay correctly
        for (i=0; i<analyses.length; i++) {
            color = analysisColorByRun(run);
            where = gh.decodeGeoHash(analyses[i].attributes.P);
            // N.B. If the default disposition changes, make corresponding change
            //  in makeAnalysesTable.js in this directory 
            if (analyses[i].attributes.hasOwnProperty('Q'))
                disposition = analyses[i].attributes.Q;
            else
                disposition = 0;
            if (disposition != 0) color = grey;
            lat = where.latitude[2];
            lng = where.longitude[2];
            xy = report.xform(lng, lat);
            x = xy[0];
            y = xy[1];
            if (report.inView(xy)) {
                aCanvas[color].annotate(ctxAnalyses, x+report.padX, y+report.padY, report.analysisLabels[i],
                    "bold " + txtSize + "px sans-serif", "white");
            }
        }

        return {"context": ctxAnalyses };
    }
    module.exports = makeAnalyses;
});
