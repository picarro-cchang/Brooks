/* newPathsMaker.js returns an object for incrementally rendering paths and fields off view  */

define (['underscore', 'app/geohash', 'app/utils', 'app/reportGlobals'],
function ( _, gh, utils, REPORT) {
    'use strict';

    function fovsColorByRun(run) {
        return REPORT.settings.get("runs").at(run).get("fovs");
    }

    function PathsMaker(report) {
        this.report = report;
        this.path = [];
        this.runs = {};
        this.surveys = {};
        this.lastP = {};
        this.ctxPaths = document.createElement("canvas").getContext("2d");
        this.ctxPaths.canvas.height = report.ny + 2 * report.padY;
        this.ctxPaths.canvas.width  = report.nx + 2 * report.padX;
        this.ctxFovs = document.createElement("canvas").getContext("2d");
        this.ctxFovs.canvas.height = report.ny + 2 * report.padY;
        this.ctxFovs.canvas.width  = report.nx + 2 * report.padX;
    }

    PathsMaker.prototype.renderPath = function (path) {
        var l, lastX, lastY;
        if (path.length > 0) {
            this.ctxPaths.beginPath();
            this.ctxPaths.moveTo((lastX = path[0][0]) + this.report.padX, (lastY = path[0][1]) + this.report.padY);
            for (l=1; l<path.length; l++) {
                //if (Math.pow((lastX - path[l][0]), 2) + Math.pow((lastY != path[l][1]), 2) > 4) {
                    // This works around a problem with wkhtmltopdf which seems to draw "ticks" when asked to join
                    //  neighboring points
                    this.ctxPaths.lineTo((lastX = path[l][0]) + this.report.padX, (lastY = path[l][1]) + this.report.padY);
                //}
            }
            this.ctxPaths.stroke();
        }
    };

    PathsMaker.prototype.makePaths = function () {
        var that = this;
        // Draw the vehicle path
        var i, k;
        var lat, lng, where;
        var pathColor = [[0,0,255,1.0], [0,0,0,1.0], [255,0,0,1.0], [255,0,0,1.0]];
        var paths = that.report.pathsCollection;

        while (paths.length > 0) {
            var fp = paths.shift();
            var p = {"pathType": fp.attributes.T, "survey": fp.attributes.S,
                     "run": fp.attributes.N, "row": fp.attributes.R,
                     "position": fp.attributes.P, "edge": fp.attributes.E };
            that.ctxPaths.lineWidth = 2;
            where = gh.decodeToLatLng(p.position);
            lat = where[0];
            lng = where[1];
            var xy = that.report.xform(lng, lat);
            p.x = xy[0], p.y = xy[1];
            if (that.report.inMap(lat,lng)) {
                that.runs[p.run] = true;
                that.surveys[p.survey] = true;
            }
            if (p.edge !== undefined && p.edge !== "") {
                where = gh.decodeToLatLng(p.edge);
                lat = where[0];
                lng = where[1];
                xy = that.report.xform(lng, lat);
                p.ex = xy[0], p.ey = xy[1];
            }
            // Here follows logic to draw the path depending on the last point and this point
            var inView = that.report.inView([p.x,p.y]);
            var adjacentPoints = (p.row === (that.lastP.row + 1)) && (p.survey === that.lastP.survey) && (p.run === that.lastP.run);
            var sameType = (p.pathType === that.lastP.pathType);
            if (!(adjacentPoints && sameType && inView)) {  // Write out any old path
                that.renderPath(that.path);
                that.path = [];
            }
            else { // Render a swath polygon
                var fovColor = utils.hex2RGB(fovsColorByRun(p.run));
                that.ctxFovs.strokeStyle = "rgba(" + fovColor[0] + "," + fovColor[1] + "," +
                                                     fovColor[2] + ", 0.4 )";
                that.ctxFovs.fillStyle = "rgba(" + fovColor[0] + "," + fovColor[1] + "," +
                                                   fovColor[2] + ", 0.5 )";

                if (p.pathType === 0 && p.ex !== undefined && that.lastP.ex !== undefined) {
                    that.ctxFovs.beginPath();
                    that.ctxFovs.moveTo(that.report.padX + that.lastP.ex, that.report.padY + that.lastP.ey);
                    that.ctxFovs.lineTo(that.report.padX + that.lastP.x, that.report.padY + that.lastP.y);
                    that.ctxFovs.lineTo(that.report.padX + p.x, that.report.padY + p.y);
                    that.ctxFovs.lineTo(that.report.padX + p.ex, that.report.padY + p.ey);
                    that.ctxFovs.stroke();
                    that.ctxFovs.fill();
                }
            }
            // Update to new style according to the path type
            that.ctxPaths.strokeStyle = "rgba(" + pathColor[p.pathType][0] + "," + pathColor[p.pathType][1] + "," +
                                            pathColor[p.pathType][2] + "," + pathColor[p.pathType][3] + ")";
            if (adjacentPoints && !sameType && inView) that.path.push([that.lastP.x, that.lastP.y]);
            if (inView)  that.path.push([p.x, p.y]);
            that.lastP = p;
        }
    };

    PathsMaker.prototype.completePaths = function () {
        var that = this;
        that.renderPath(that.path);
        that.path = [];
        return {"paths": that.ctxPaths, "fovs": that.ctxFovs, "runs": _.clone(that.runs), "surveys": _.clone(that.surveys)};
    };


    function newPathsMaker(report) {
        return new PathsMaker(report);
    }

    return newPathsMaker;
});
