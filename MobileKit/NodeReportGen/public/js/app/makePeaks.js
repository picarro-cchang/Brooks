/* makePeaks.js renders peaks using markers */

define (['underscore', 'app/geohash', 'app/newMarker', 'app/reportGlobals'],
function (_, gh, newMarker, REPORT) {
    'use strict';
    function peaksColorByRun(run) {
        return REPORT.settings.get("runs").at(run).get("peaks");
    }

    function makePeaks(report) {
        var i, j, x, xy, y;
        var color, colors, ctxPeaks, ctxTokens, data, fovMinAmp, lat, lng, pCanvas, peaks, peaksMinAmp, run, survey, where;
        var runs = {}, surveys = {};
        var size = 0.7;
        peaks = report.peaksData;
        ctxPeaks = document.createElement("canvas").getContext("2d");
        ctxPeaks.canvas.height = report.ny + 2 * report.padY;
        ctxPeaks.canvas.width  = report.nx + 2 * report.padX;

        ctxTokens = document.createElement("canvas").getContext("2d");
        ctxTokens.canvas.height = report.ny + 2 * report.padY;
        ctxTokens.canvas.width  = report.nx + 2 * report.padX;

        // Filter peaks by amplitude (defined per run) and assign ranks to
        //  those remaining. Also determine which colors of marker are required
        report.peakLabels = [];
        colors = {};
        j = 1;
        for (i=0; i<peaks.length; i++) {
            run = peaks[i].attributes.R;
            // peaksMinAmp = data.RUNS[run].peaksMinAmp;
            peaksMinAmp = report.peaksMinAmp;
            fovMinAmp = report.fovMinAmp;
            if (peaks[i].attributes.A >= peaksMinAmp) {
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
                pCanvas[c] = newMarker(size,c,"black");
            }
        }

        var tokenRadius = 3;
        // Get the peaks in reverse rank order so they overlay correctly
        for (i=peaks.length-1; i>=0; i--) {
            run = peaks[i].attributes.R;
            survey = peaks[i].attributes.S;
            color = peaksColorByRun(run);
            where = gh.decodeGeoHash(peaks[i].attributes.P);
            lat = where.latitude[2];
            lng = where.longitude[2];
            xy = report.xform(lng, lat);
            x = xy[0], y = xy[1];
            if (report.inView(xy)) {
                runs[run] = true;
                surveys[survey] = true;
                if (report.peakLabels[i] && color) {
                    pCanvas[color].annotate(ctxPeaks, x+report.padX, y+report.padY, report.peakLabels[i], "bold 13px sans-serif", "black");
                }
                else if (peaks[i].attributes.A >= fovMinAmp) {
                    ctxPeaks.fillStyle = color;
                    ctxPeaks.beginPath();
                    ctxPeaks.arc(x + report.padX, y + report.padY, tokenRadius, 0.0, 2*Math.PI);
                    ctxPeaks.fill();
                    ctxPeaks.strokeStyle = 'black';
                    ctxPeaks.stroke();
                }
                if (peaks[i].attributes.A >= fovMinAmp) {
                    ctxTokens.fillStyle = color;
                    ctxTokens.beginPath();
                    ctxTokens.arc(x + report.padX, y + report.padY, tokenRadius, 0.0, 2*Math.PI);
                    ctxTokens.fill();
                    ctxTokens.strokeStyle = 'black';
                    ctxTokens.stroke();
                }
            }
        }

        return {"peaks": ctxPeaks, "tokens": ctxTokens, "runs": _.clone(runs), "surveys": _.clone(surveys) };
    }
    return makePeaks;
});
