/* makeRunsTable.js renders runs information into an HTML table */
/*global alert, console, module, require, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';

    var _ = require('underscore');
    var REPORT = require('app/reportGlobals');
    var utils = require('app/utils');
    var bufferedTimezone = utils.bufferedTimezone;

    function makeColorPatch(value) {
        var result;
        if (value === "None") {
            result = "None";
        }
        else {
            result = '<div style="width:15px;height:15px;border:1px solid #000;margin:0 auto;';
            result += 'background-color:' + value + ';"></div>';
        }
        return (undefined !== value) ? result : '';
    }

    function makeRunsTable(report, done) {
        var i, runsTable = [];
        var runs = [], allRuns = {};
        // Merge the runs from peaks and from paths into a single sorted runs array
        _.keys(report.runsData).forEach(function (src) {
            allRuns = _.extend(allRuns,report.runsData[src]);
        });
        _.keys(allRuns).forEach(function (run) { runs.push(+run); });
        runs.sort(function (x,y) { return x-y; });

        if (runs.length > 0) {
            // Generate the runsTable
            runsTable.push('<table class="table table-striped table-condensed table-fmt1">');
            runsTable.push('<thead><tr>');
            runsTable.push('<th style="width:20%">Analyzer</th>');
            runsTable.push('<th style="width:20%">Start</th>');
            runsTable.push('<th style="width:20%">End</th>');
            runsTable.push('<th style="width:8%">Peaks</th>');
            runsTable.push('<th style="width:8%">LISA</th>');
            runsTable.push('<th style="width:8%">Isotopic</th>');
            runsTable.push('<th style="width:8%">FOV</th>');
            runsTable.push('<th style="width:8%">Stab Class</th>');
            runsTable.push('</tr></thead>');
            runsTable.push('<tbody>');
            var posixTimes = [];
            for (i=0; i<runs.length; i++) {
                var run = REPORT.settings.get("runs").at(runs[i]).attributes;
                posixTimes.push(1000*run.startEtm);
                posixTimes.push(1000*run.endEtm);
            }
            bufferedTimezone(REPORT.Utilities.timezone,{tz:REPORT.settings.get("timezone"),posixTimes:posixTimes},
            function (err) {
                var msg = 'While processing timezone in makeRunsTable: ' + err;
                console.log(msg);
                done(new Error(msg));
            },
            function (status, data) {
                // console.log('While processing timezone in makeRunsTable: ' + status);
                for (i=0; i<runs.length; i++) {
                    var run = REPORT.settings.get("runs").at(runs[i]).attributes;
                    runsTable.push('<tr>');
                    runsTable.push('<td>' + run.analyzer + '</td>');
                    runsTable.push('<td>' + data.timeStrings.shift() + '</td>');
                    runsTable.push('<td>' + data.timeStrings.shift() + '</td>');
                    runsTable.push('<td>' + makeColorPatch(run.peaks) + '</td>');
                    runsTable.push('<td>' + makeColorPatch(run.wedges) + '</td>');
                    runsTable.push('<td>' + makeColorPatch(run.analyses) + '</td>');
                    runsTable.push('<td>' + makeColorPatch(run.fovs) + '</td>');
                    runsTable.push('<td>' + run.stabClass + '</td>');
                    runsTable.push('</tr>');
                }
                runsTable.push('</tbody>');
                runsTable.push('</table>');
                done(null, runsTable);
            });
        }
        else {
            runsTable.push('<p>No data in runs table</p>');
            done(null, runsTable);
        }
    }
    module.exports = makeRunsTable;
});
