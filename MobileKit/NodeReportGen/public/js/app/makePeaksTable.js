/* makePeaksTable.js renders peaks into an HTML table */

define (['app/utils', 'app/geohash', 'app/reportGlobals'],
function (utils, gh, REPORT) {
    'use strict';

    function analyzerByRun(run) {
        return REPORT.settings.get("runs").at(run).get("analyzer");
    }

    function makePeaksTable(report) {
        var i;
        var amp, anz, ch4, data, etm, lat, lng, peaks, where;
        var peaksTable = [];
        peaks = report.peaksData;
        if (peaks) {
            // Generate the peaksTable
            var zoom = 18;
            peaksTable.push('<table class="table table-striped table-condensed table-fmt1 table-datatable">');
            peaksTable.push('<thead><tr>');
            peaksTable.push('<th style="width:10%">Rank</th>');
            peaksTable.push('<th style="width:30%">Designation</th>');
            peaksTable.push('<th style="width:20%">Latitude</th>');
            peaksTable.push('<th style="width:20%">Longitude</th>');
            peaksTable.push('<th style="width:10%">Conc</th>');
            peaksTable.push('<th style="width:10%">Ampl</th>');
            peaksTable.push('</tr></thead>');
            peaksTable.push('<tbody>');

            for (i=0; i<peaks.length; i++) {
                amp = peaks[i].attributes.A;
                if (report.peakLabels[i]) {
                    etm = peaks[i].attributes.T;
                    anz = analyzerByRun(peaks[i].attributes.R);
                    where = gh.decodeGeoHash(peaks[i].attributes.P);
                    lat = where.latitude[2];
                    lng = where.longitude[2];
                    ch4 = peaks[i].attributes.C;
                    if (report.inMap(lat,lng)) {
                        var des = anz + '_' + utils.getDateTime(new Date(1000*etm));
                        var url = "http://maps.google.com?q=(" + lat + "," + lng + ")+(" + des + ")&z=" + zoom;
                        peaksTable.push('<tr>');
                        peaksTable.push('<td>' + report.peakLabels[i] + '</td>');
                        peaksTable.push('<td><a href="' + url + '" target="_blank">' +  des + '</a></td>');
                        peaksTable.push('<td>' + lat.toFixed(6) + '</td>');
                        peaksTable.push('<td>' + lng.toFixed(6) + '</td>');
                        peaksTable.push('<td>' + ch4.toFixed(1) + '</td>');
                        peaksTable.push('<td>' + amp.toFixed(2) + '</td>');
                        peaksTable.push('</tr>');
                    }
                }
            }
            peaksTable.push('</tbody>');
            peaksTable.push('</table>');
        }
        return peaksTable;
    }
    return makePeaksTable;
});
