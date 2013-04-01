/* makeAnalysesTable.js renders isotopic analysis results into an HTML table */
/* jshint undef:true, unused:true */
/* global define */

define (['app/utils', 'app/geohash', 'app/reportGlobals'],
function (utils, gh, REPORT) {
    'use strict';

    function analyzerByRun(run) {
        return REPORT.settings.get("runs").at(run).get("analyzer");
    }

    function makeAnalysesTable(report) {
        var i;
        var analyses, anz, conc, delta, etm, lat, lng, uncertainty, where;
        var analysesTable = [];
        analyses = report.analysesData;
        if (analyses) {
            // Generate the analysesTable
            var zoom = 18;

            for (i=0; i<analyses.length; i++) {
                delta = analyses[i].attributes.D;
                uncertainty = analyses[i].attributes.U;
                etm = analyses[i].attributes.T;
                anz = analyzerByRun(analyses[i].attributes.R);
                where = gh.decodeGeoHash(analyses[i].attributes.P);
                lat = where.latitude[2];
                lng = where.longitude[2];
                conc = analyses[i].attributes.C;
                if (report.inMap(lat,lng)) {
                    var des = anz + '_' + utils.getDateTime(new Date(1000*etm)) + 'I';
                    var url = "http://maps.google.com?q=(" + lat + "," + lng + ")+(" + des + ")&z=" + zoom;
                    analysesTable.push('<tr>');
                    analysesTable.push('<td>' + report.analysisLabels[i] + '</td>');
                    analysesTable.push('<td><a href="' + url + '" target="_blank">' +  des + '</a></td>');
                    analysesTable.push('<td>' + lat.toFixed(6) + '</td>');
                    analysesTable.push('<td>' + lng.toFixed(6) + '</td>');
                    analysesTable.push('<td>' + conc.toFixed(1) + '</td>');
                    analysesTable.push('<td>' + delta.toFixed(1) + '</td>');
                    analysesTable.push('<td>' + uncertainty.toFixed(1) + '</td>');
                    analysesTable.push('</tr>');
                }
            }
            if (analysesTable.length > 0) {
                var header = [];
                header.push('<table class="table table-striped table-condensed table-fmt1 table-datatable">');
                header.push('<thead><tr>');
                header.push('<th style="width:10%">Label</th>');
                header.push('<th style="width:20%">Designation</th>');
                header.push('<th style="width:20%">Latitude</th>');
                header.push('<th style="width:20%">Longitude</th>');
                header.push('<th style="width:10%">Conc</th>');
                header.push('<th style="width:10%">Isotopic Ratio</th>');
                header.push('<th style="width:10%">Uncertainty</th>');
                header.push('</tr></thead>');
                header.push('<tbody>');
                analysesTable = header.concat(analysesTable);
                analysesTable.push('</tbody>');
                analysesTable.push('</table>');
            }
        }
        return analysesTable;
    }
    return makeAnalysesTable;
});
