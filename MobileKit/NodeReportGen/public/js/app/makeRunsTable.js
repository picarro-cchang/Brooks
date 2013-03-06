/* makeRunsTable.js renders runs information into an HTML table */

define (['underscore', 'app/utils', 'app/geohash', 'app/reportGlobals'],
function (_, utils, gh, REPORT) {
    'use strict';

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
            runsTable.push('<th style="width:10%">Peaks</th>');
            runsTable.push('<th style="width:10%">Wedges</th>');
            runsTable.push('<th style="width:10%">Fovs</th>');
            runsTable.push('<th style="width:10%">Stab Class</th>');
            runsTable.push('</tr></thead>');
            runsTable.push('<tbody>');
            var timeStringsList = [];
            for (i=0; i<runs.length; i++) {
                var run = REPORT.settings.get("runs").at(runs[i]).attributes;
                timeStringsList.push(run.startEtm);
                timeStringsList.push(run.endEtm);
            }
            var url = '/rest/tz?' + $.param({tz:REPORT.settings.get("timezone"),timeStrings:timeStringsList});
            $.getJSON(url,function (data) {
                var url = '/rest/tz?' + $.param({tz:REPORT.settings.get("reportTimezone"),posixTimes:data.posixTimes});
                $.getJSON(url,function (data) {
                    for (i=0; i<runs.length; i++) {
                        var run = REPORT.settings.get("runs").at(runs[i]).attributes;
                        runsTable.push('<tr>');
                        runsTable.push('<td>' + run.analyzer + '</td>');
                        runsTable.push('<td>' + data.timeStrings.shift() + '</td>');
                        runsTable.push('<td>' + data.timeStrings.shift() + '</td>');
                        runsTable.push('<td>' + run.peaks + '</td>');
                        runsTable.push('<td>' + run.wedges + '</td>');
                        runsTable.push('<td>' + run.fovs + '</td>');
                        runsTable.push('<td>' + run.stabClass + '</td>');
                        runsTable.push('</tr>');
                    }
                    runsTable.push('</tbody>');
                    runsTable.push('</table>');
                    done(null, runsTable);
                }).error(function () { done(new Error("getJSON error:" + url)); });
            }).error(function () { done(new Error("getJSON error:" + url)); });
        }
        else done(null, runsTable);
    }
    return makeRunsTable;
});
