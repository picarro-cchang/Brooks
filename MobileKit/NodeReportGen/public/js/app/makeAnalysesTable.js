/* makeAnalysesTable.js renders isotopic analysis results into an HTML table */
/* jshint undef:true, unused:true */
/*global module, require, P3TXT */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var gh = require('app/geohash');
    var REPORT = require('app/reportGlobals');
    var utils = require('app/utils');
    require('common/P3TXT');
    
    function analyzerByRun(run) {
        return REPORT.settings.get("runs").at(run).get("analyzer");
    }

    function makeAnalysesTable(report) {
        var i;
        var analyses, anz, col, conc, delta, disposition, etm, lat, lng, row, uncertainty, where;
        var analysesTable = [];

        var dispositionStrings = {0:P3TXT.getReport.dispositions.complete,
                                  1:P3TXT.getReport.dispositions.cancelled,
                                  2:P3TXT.getReport.dispositions.uncertain,
                                  3:P3TXT.getReport.dispositions.outside_range,
                                  4:P3TXT.getReport.dispositions.not_enough_data};

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
                col = Math.floor(report.subx*(lng - report.minLng)/(report.maxLng - report.minLng));
                row = Math.floor(report.suby*(lat - report.maxLat)/(report.minLat - report.maxLat));
                conc = analyses[i].attributes.C;
                // N.B. If the default disposition changes, make corresponding change
                //  in makeAnalyses.js in this directory 
                if (analyses[i].attributes.hasOwnProperty('Q'))
                    disposition = analyses[i].attributes.Q;
                else
                    disposition = 0;
                if (report.inMap(lat,lng)) {
                    var des = anz + '_' + utils.getDateTime(new Date(1000*etm)) + 'I';
                    var url = "https://maps.google.com/maps?q=loc:" + lat +"" + "," + lng + "+(" + des + ")&t=m&z=" + zoom + "&output=html";
					
                    analysesTable.push('<tr>');
                    analysesTable.push('<td>' + report.analysisLabels[i] + '</td>');
                    analysesTable.push('<td><a href="' + url + '" target="_blank">' +  des + '</a></td>');
                    if (report.subx > 1 || report.suby > 1) {
                        var submapGridString = utils.submapGridString(row, col);
                        var link = REPORT.reportViewResources.submapLinks[submapGridString];
                        url = window.location.pathname + '?' + $.param({"swCorner": link.swCorner,
                                  "neCorner": link.neCorner, "name":submapGridString });
                        analysesTable.push('<td><a href="' + url + '" target="_blank">' + submapGridString + '</a></td>');
                    }
                    analysesTable.push('<td>' + lat.toFixed(6) + '</td>');
                    analysesTable.push('<td>' + lng.toFixed(6) + '</td>');
                    analysesTable.push('<td>' + conc.toFixed(1) + '</td>');
                    analysesTable.push('<td>' + delta.toFixed(1) + '</td>');
                    analysesTable.push('<td>' + uncertainty.toFixed(1) + '</td>');
                    analysesTable.push('<td>' + dispositionStrings[disposition] + '</td>');
                    analysesTable.push('</tr>');
                }
            }
            if (analysesTable.length > 0) {
                var header = [];
                header.push('<table class="table table-striped table-condensed table-fmt1 table-datatable">');
                header.push('<thead><tr>');
                header.push('<th style="width:8%">Label</th>');
                if (report.subx > 1 || report.suby > 1) {
                    header.push('<th style="width:20%">Designation</th>');
                    header.push('<th style="width:10%">Submap</th>');
                }
                else {
                    header.push('<th style="width:30%">Designation</th>');
                }
                header.push('<th style="width:15%">Latitude</th>');
                header.push('<th style="width:15%">Longitude</th>');
                header.push('<th style="width:8%">Conc</th>');
                header.push('<th style="width:8%">Isotopic Ratio</th>');
                header.push('<th style="width:8%">Uncertainty</th>');
                header.push('<th style="width:8%">Disposition</th>');
                header.push('</tr></thead>');
                header.push('<tbody>');
                analysesTable = header.concat(analysesTable);
                analysesTable.push('</tbody>');
                analysesTable.push('</table>');
            }
            else analysesTable.push('<p>No data in isotopic analysis table</p>');
        }
        return analysesTable;
    }
    module.exports = makeAnalysesTable;
});
