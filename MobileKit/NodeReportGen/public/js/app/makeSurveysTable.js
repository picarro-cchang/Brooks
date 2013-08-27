/* makeSurveysTable.js renders runs information into an HTML table */
/*global alert, console, module, require, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';

    var _ = require('underscore');
    var REPORT = require('app/reportGlobals');
    var utils = require('app/utils');
    var bufferedTimezone = utils.bufferedTimezone;

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
            surveysTable.push('<th>Analyzer</th>');
            surveysTable.push('<th>Start</th>');
            surveysTable.push('<th>End</th>');
            surveysTable.push('<th>Name</th>');
            surveysTable.push('<th>Stab Class</th>');
            surveysTable.push('</tr></thead>');
            surveysTable.push('<tbody>');
            var etmList = [];
            // Batch convert the epoch times to the current timezone
            for (i=0; i<surveys.length; i++) {
                var survey = REPORT.surveys.where({"id": surveys[i]})[0].attributes;
                etmList.push(1000*survey.minetm);
                etmList.push(1000*survey.maxetm);
            }

            bufferedTimezone(REPORT.Utilities.timezone,{tz:REPORT.settings.get("timezone"),posixTimes:etmList},
            function (err) {
                var msg = 'While processing timezone in makeSurveysTable: ' + err;
                console.log(msg);
                done(new Error(msg));
            },
            function (status, data) {
                // console.log('While processing timezone in makeSurveysTable: ' + status);
                for (i=0; i<surveys.length; i++) {
                    var survey = REPORT.surveys.where({"id": surveys[i]})[0].attributes;
                    surveysTable.push('<tr>');
                    surveysTable.push('<td>' + survey.ANALYZER + '</td>');
                    surveysTable.push('<td>' + data.timeStrings.shift() + '</td>');
                    surveysTable.push('<td>' + data.timeStrings.shift() + '</td>');
                    surveysTable.push('<td>' + survey.id + '</td>');
                    surveysTable.push('<td>' + '* => ' + survey.stabClass + '</td>');
                    surveysTable.push('</tr>');
                }
                surveysTable.push('</tbody>');
                surveysTable.push('</table>');
                done(null, surveysTable);
            });
        }
        else {
            surveysTable.push('<p>No data in surveys table</p>');
            done(null, surveysTable);
        }
    }
    module.exports = makeSurveysTable;
});
