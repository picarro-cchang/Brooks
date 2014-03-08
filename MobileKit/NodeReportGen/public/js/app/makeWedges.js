/* makeWedges.js renders LISAs */
/*global module, require */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var CNSNT = require('common/cnsnt');
    var gh = require('app/geohash');
    var utils = require('app/utils');
    var REPORT = require('app/reportGlobals');

    function wedgeColorByRun(run) {
        return REPORT.settings.get("runs").at(run).get("wedges");
    }

    function makeWedges(report) {
        var i, x, xy, y;
        var color, ctxWedges,lat, lng, peaks, run, where;
        var wedgeRadius = REPORT.settings.get("wedgeRadius");

        peaks = report.peaksData;
        // Draw the wind wedges on a canvas
        ctxWedges = document.createElement("canvas").getContext("2d");
        ctxWedges.canvas.height = report.ny + 2 * report.padY;
        ctxWedges.canvas.width  = report.nx + 2 * report.padX;

        for (i=peaks.length-1; i>=0; i--) {
            run = peaks[i].attributes.R;
            color = wedgeColorByRun(run);
            if (report.peakLabels[i] && color) {
                where = gh.decodeGeoHash(peaks[i].attributes.P);
                lat = where.latitude[2];
                lng = where.longitude[2];
                var wedgeColor = utils.hex2RGB(color);
                var windMean = peaks[i].attributes.W;
                var windSdev = peaks[i].attributes.U;
                xy = report.xform(lng, lat);
                x = xy[0], y = xy[1];
                ctxWedges.fillStyle = "rgba(" + wedgeColor[0] + "," + wedgeColor[1] + "," + wedgeColor[2] + ",0.5)";
                if (report.inView(xy)) {
                    var radius = wedgeRadius / report.mpp;
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
        return ctxWedges;
    }
    module.exports = makeWedges;
});
