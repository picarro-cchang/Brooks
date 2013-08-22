/* makeMarkers.js renders markers */
/*global console, module, exports, process, require */
/*jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var gh = require('app/geohash');
    var newMarker = require('app/newMarker');

    function makeMarkers(report) {
        var i, j, x, xy, y;
        var color, colors, ctxMarkers, lat, lng, mCanvas, markers, text, where;
        var size = 1.0;
        var txtSize = size*18;

        markers = report.markersData;
        ctxMarkers = document.createElement("canvas").getContext("2d");
        ctxMarkers.canvas.height = report.ny + 2 * report.padY;
        ctxMarkers.canvas.width  = report.nx + 2 * report.padX;

        // Determine which colors of marker are required
        report.markerLabels = [];
        colors = {};
        j = 1;
        for (i=0; i<markers.length; i++) {
            color = markers[i].attributes.C;
            if (color) {
                if (!(color in colors)) colors[color] = true;
            }
        }

        // Make empty bubbles for each marker color required
        mCanvas = {};
        for (var c in colors) {
            if (colors.hasOwnProperty(c)) {
                mCanvas[c] = newMarker(size,c,"black");
            }
        }

        for (i=0; i<markers.length; i++) {
            color = markers[i].attributes.C;
            text = markers[i].attributes.T;
            where = gh.decodeGeoHash(markers[i].attributes.P);
            lat = where.latitude[2];
            lng = where.longitude[2];
            xy = report.xform(lng, lat);
            x = xy[0], y = xy[1];
            if (report.inView(xy)) {
                mCanvas[color].annotate(ctxMarkers, x+report.padX, y+report.padY, text,
                    "bold " + txtSize + "px sans-serif", "black");
            }
        }

        return {"markers": ctxMarkers };
    }
    module.exports = makeMarkers;
});
