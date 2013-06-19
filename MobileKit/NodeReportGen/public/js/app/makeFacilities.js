/* makeFacilities.js renders facilities */
/*global console, module, exports, process, require */
/*jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var gh = require('app/geohash');

    function makeFacilities(report, facInstructions) {
        var i, j, x, xy, y;
        var color, ctxFacilities, lat, lng, facilities, where, width;

        facilities = report.facilitiesData;
        ctxFacilities = document.createElement("canvas").getContext("2d");
        ctxFacilities.canvas.height = report.ny + 2 * report.padY;
        ctxFacilities.canvas.width  = report.nx + 2 * report.padX;

        for (i=0; i<facilities.length; i++) {
            color = facilities[i].attributes.C;
            width = facilities[i].attributes.W;
            var fileIndex = facilities[i].attributes.F;
            var offsets = facInstructions[fileIndex].offsets;
            var points = facilities[i].attributes.P;
            ctxFacilities.beginPath();
            for (j=0; j<points.length; j++) {
                where = gh.decodeGeoHash(points[j]);
                lat = where.latitude[2] + offsets[0];
                lng = where.longitude[2] + offsets[1];
                xy = report.xform(lng, lat);
                x = xy[0], y = xy[1];
                if (j === 0) ctxFacilities.moveTo(x + report.padX, y + report.padY);
                else ctxFacilities.lineTo(x + report.padX, y + report.padY);
            }
            ctxFacilities.lineWidth = +width;
            ctxFacilities.strokeStyle = color;
            ctxFacilities.stroke();
        }

        return {"facilities": ctxFacilities };
    }
    module.exports = makeFacilities;
});
