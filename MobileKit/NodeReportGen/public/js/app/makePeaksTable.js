/* makePeaksTable.js renders peaks into an HTML table */
/*global module, require */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var gh = require('app/geohash');
    var utils = require('app/utils');
    var REPORT = require('app/reportGlobals');

    function analyzerByRun(run) {
        return REPORT.settings.get("runs").at(run).get("analyzer");
    }

    function makePeaksTable(report) {
        var i;
        var amp, anz, ch4, etm, lat, lng, peaks, where, row, col;
        var peaksTable = [];
        peaks = report.peaksData;
        // alert("Corners: (" + report.minLat + "," + report.minLng + "), (" + report.maxLat + "," + report.maxLng + 
        //     "). Submaps: " + report.suby + "x" + report.subx);
        if (peaks) {
            // Generate the peaksTable
            var zoom = 18;

            for (i=0; i<peaks.length; i++) {
                amp = peaks[i].attributes.A;
                if (report.peakLabels[i]) {
                    etm = peaks[i].attributes.T;
                    anz = analyzerByRun(peaks[i].attributes.R);
                    where = gh.decodeGeoHash(peaks[i].attributes.P);
                    lat = where.latitude[2];
                    lng = where.longitude[2];
                    ch4 = peaks[i].attributes.C;
                    col = Math.floor(report.subx*(lng - report.minLng)/(report.maxLng - report.minLng));
                    row = Math.floor(report.suby*(lat - report.maxLat)/(report.minLat - report.maxLat));
                    if (report.inMap(lat,lng)) {
                        var des = anz + '_' + utils.getDateTime(new Date(1000*etm));
						var url = "https://maps.google.com/maps?q=loc:" + lat +"" + "," + lng + "+(" + des + ")&t=m&z=" + zoom + "&output=html";
                        peaksTable.push('<tr>');
                        peaksTable.push('<td>' + report.peakLabels[i] + '</td>');
                        peaksTable.push('<td><a href="' + url + '" target="_blank">' +  des + '</a></td>');
                        if (report.subx > 1 || report.suby > 1) {
                            var submapGridString = utils.submapGridString(row, col);
                            var link = REPORT.reportViewResources.submapLinks[submapGridString];
                            url = window.location.pathname + '?' + $.param({"swCorner": link.swCorner,
                                      "neCorner": link.neCorner, "name":submapGridString });
                            peaksTable.push('<td><a href="' + url + '" target="_blank">' + submapGridString + '</a></td>');
                        }
                        peaksTable.push('<td>' + lat.toFixed(6) + '</td>');
                        peaksTable.push('<td>' + lng.toFixed(6) + '</td>');
                        peaksTable.push('<td>' + ch4.toFixed(1) + '</td>');
                        peaksTable.push('<td>' + amp.toFixed(2) + '</td>');
                        peaksTable.push('</tr>');
                    }
                }
            }
            if (peaksTable.length > 0) {
                var header = [];
                header.push('<table class="table table-striped table-condensed table-fmt1 table-datatable">');
                header.push('<thead><tr>');
                header.push('<th style="width:10%">Rank</th>');
                if (report.subx > 1 || report.suby > 1) {
                    header.push('<th style="width:20%">Designation</th>');
                    header.push('<th style="width:10%">Submap</th>');
                }
                else {
                    header.push('<th style="width:30%">Designation</th>');
                }
                header.push('<th style="width:20%">Latitude</th>');
                header.push('<th style="width:20%">Longitude</th>');
                header.push('<th style="width:10%">Conc</th>');
                header.push('<th style="width:10%">Ampl</th>');
                header.push('</tr></thead>');
                header.push('<tbody>');
                peaksTable = header.concat(peaksTable);
                peaksTable.push('</tbody>');
                peaksTable.push('</table>');
            }
            else peaksTable.push('<p>No data in peaks table</p>');
        }
        return peaksTable;
    }
    module.exports = makePeaksTable;
});
