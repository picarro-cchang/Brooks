/* makeSurveysTable.js renders runs information into an HTML table */

define (['app/utils', 'app/geohash', 'app/reportGlobals'],
function (utils, gh, REPORT) {
    'use strict';

    function makeSurveysTable(report, done) {
        var i, surveysTable = [];
        var surveys = [], allSurveys = {};
        // Merge the surveys from peaks, paths and analyses into a single sorted surveys array
        _.keys(report.surveysData).forEach(function (src) {
            _.keys(report.surveysData[src]).forEach(function (surveyIndex) {
                var attr = {}, name;
                attr[src] = +surveyIndex;
                name = REPORT.surveys.where(attr)[0].get("id");
                allSurveys[name] = true;
            });
        });
        _.keys(allSurveys).forEach(function (survey) { surveys.push(survey); });
        surveys.sort();

        // Generate the surveysTable
        if (surveys.length > 0) {
            surveysTable.push('<table class="table table-striped table-condensed table-fmt1">');
            surveysTable.push('<thead><tr>');
            surveysTable.push('<th style="width:25%">Analyzer</th>');
            surveysTable.push('<th style="width:25%">Start</th>');
            surveysTable.push('<th style="width:25%">End</th>');
            surveysTable.push('<th style="width:25%">Name</th>');
            surveysTable.push('</tr></thead>');
            surveysTable.push('<tbody>');
            var etmList = [];
            // Batch convert the epoch times to the current timezone
            for (i=0; i<surveys.length; i++) {
                var run = REPORT.surveys.where({"id": surveys[i]})[0].attributes;
                etmList.push(1000*run.minetm);
                etmList.push(1000*run.maxetm);
            }
            var url = '/rest/tz?' + $.param({tz:REPORT.settings.get("reportTimezone"),posixTimes:etmList});
            $.getJSON(url,function (data) {
                for (i=0; i<surveys.length; i++) {
                    var run = REPORT.surveys.where({"id": surveys[i]})[0].attributes;
                    surveysTable.push('<tr>');
                    surveysTable.push('<td>' + run.ANALYZER + '</td>');
                    surveysTable.push('<td>' + data.timeStrings.shift() + '</td>');
                    surveysTable.push('<td>' + data.timeStrings.shift() + '</td>');
                    surveysTable.push('<td>' + run.id + '</td>');
                    surveysTable.push('</tr>');
                }
                surveysTable.push('</tbody>');
                surveysTable.push('</table>');
                done(null, surveysTable);
            }).error(function () { done(new Error("getJSON error:" + url)); });
        }
        else done(null, surveysTable);
    }
    return makeSurveysTable;
});
