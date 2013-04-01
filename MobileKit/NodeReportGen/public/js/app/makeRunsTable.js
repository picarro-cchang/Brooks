/* makeRunsTable.js renders runs information into an HTML table */

define (['underscore', 'app/utils', 'app/geohash', 'app/reportGlobals'],
function (_, utils, gh, REPORT) {
    'use strict';

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
            var url = '/rest/tz?' + $.param({tz:REPORT.settings.get("timezone"),posixTimes:posixTimes});
            $.getJSON(url,function (data) {
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
            }).error(function () { done(new Error("getJSON error:" + url)); });
        }
        else done(null, runsTable);
    }
    return makeRunsTable;
});
