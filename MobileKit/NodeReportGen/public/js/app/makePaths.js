/* makePaths.js renders paths */

define (['app/geohash'],
function (gh) {
    'use strict';
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
            var p = {"pathType": paths[i].attributes.T, "survey": paths[i].attributes.S,
                     "run": paths[i].attributes.N, "row": paths[i].attributes.R,
                     "position": paths[i].attributes.P};
            ctxPath.lineWidth = 2;
            where = gh.decodeGeoHash(p.position);
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
        return ctxPath;
    }
    return makePaths;
});
