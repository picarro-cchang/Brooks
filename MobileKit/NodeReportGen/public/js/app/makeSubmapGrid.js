/* makeSubmapGrid.js renders submap grid lines */
/*global module, require */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var gh = require('app/geohash');
    var utils = require('app/utils');

    function makeSubmapGrid(report) {
        var ctxGrid, dx, dy, height, linkHeight, linkWidth, maxLat, maxLng, minLat;
        var minLng, mx, my, name, neCorner, rect, row, swCorner, width, x, xy, y;
        var links = {}, submaps = [], rowList;
        ctxGrid = document.createElement("canvas").getContext("2d");
        ctxGrid.canvas.height = report.ny + 2 * report.padY;
        ctxGrid.canvas.width  = report.nx + 2 * report.padX;
        // Create the submap regions
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
                name = utils.submapGridString(my, mx);
                ctxGrid.fillText(name, x + report.padX + width / 2, y + report.padY + height / 2);
                swCorner = gh.encodeGeoHash(rect.minLat, rect.minLng);
                neCorner = gh.encodeGeoHash(rect.maxLat, rect.maxLng);
                linkWidth = ctxGrid.measureText(name).width;
                linkHeight = 36;
                links[name] = {"swCorner": swCorner, "neCorner": neCorner,
                               "linkX": x + report.padX + width / 2,
                               "linkY": y + report.padY + height / 2,
                               "linkWidth": linkWidth, "linkHeight": linkHeight
                              };
            }
        }
        return {"context": ctxGrid, "links": links};
    }
    module.exports = makeSubmapGrid;
});
