// getTableOfContents.js
/*global alert, console, module, P3TXT, require, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';

    var $ = require('jquery');
    var _ = require('underscore');
    var bufferedTimezone = require('app/utils').bufferedTimezone;
    var CNSNT = require('common/cnsnt');
    var instrResource = require('app/utils').instrResource;
    var localrestapi = require('app/localrestapi');
    var REPORT = require('app/reportGlobals');
    var p3restapi = require('app/p3restapi');
    require('common/P3TXT');

    function init() {
        var host = TEMPLATE_PARAMS.host;
        var port = TEMPLATE_PARAMS.port;
        if (host === '' && port === '') {
            REPORT.SurveyorRpt = new localrestapi.GetResource();
            REPORT.Utilities   = new localrestapi.Timezone();
        }
        else {
            var initArgs = {host: host,
                            port: port,
                            site: TEMPLATE_PARAMS.site,
                            identity: TEMPLATE_PARAMS.identity,
                            psys: TEMPLATE_PARAMS.psys,
                            rprocs: ["SurveyorRpt:resource"],
                            svc: "gdu",
                            version: "1.0",
                            resource: "SurveyorRpt",
                            api_timeout: 30.0,
                            jsonp: false,
                            debug: false};
            REPORT.SurveyorRpt = new p3restapi.p3RestApi(initArgs);
            initArgs = { host: host,
                         port: port,
                         site: TEMPLATE_PARAMS.site,
                         identity: TEMPLATE_PARAMS.identity,
                         psys: TEMPLATE_PARAMS.psys,
                         rprocs: ["Utilities:timezone"],
                         svc: "gdu",
                         version: "1.0",
                         resource: "Utilities",
                         api_timeout: 30.0,
                         jsonp: false,
                         debug: false};
            //REPORT.Utilities = new p3restapi.p3RestApi(initArgs);
            REPORT.Utilities = new localrestapi.TimezoneP3(host, port, TEMPLATE_PARAMS.site);
        }

        console.log("GET_TABLE_OF_CONTENTS at " + new Date() + ": " + JSON.stringify(TEMPLATE_PARAMS.qry));
        renderPage();
    }

    function makeTableOfContents(contents) {
        var contentsTable = [];
        var numEntries = contents.length;
        var numCols = 2;
        var rows = [];
        var startRows = [];
        var shortRows = Math.floor(numEntries/numCols);
        var i, j, k;
        // Calculate number of rows for each column
        var row = 0;
        for (i=0; i<numEntries-shortRows*numCols; i++) {
            rows.push(shortRows + 1);
            startRows.push(row);
            row += shortRows + 1;
        }
        for (; i<numCols; i++) {
            rows.push(shortRows);
            startRows.push(row);
            row += shortRows;
        }

        for (j=0; j<shortRows + 1; j++) {
            contentsTable.push('<tr><td></td>');
            for (i=0; i<numCols; i++) {
                if (j < rows[i] && (k = startRows[i] + j) < numEntries) {
                    var name = contents[k].name;
                    var startPage = contents[k].startPage;
                    contentsTable.push('<td style="text-align:left">' + name + '</td><td style="text-align:left">' + startPage + '</td>');
                }
            }
            contentsTable.push('</tr>');
        }
        if (numEntries > 0) {
            var header = [];
            header.push('<table class="table table-striped table-condensed table-fmt1 table-datatable">');
            header.push('<thead><tr>');
            header.push('<th style="width:20%"></th>');
            var nCols = Math.min(numEntries,numCols);
            for (i=0; i<nCols; i++) {
                header.push('<th style="width:10%;text-align:left">Submap</th><th style="width:30%;text-align:left">Page</th>');
            }
            header.push('</tr></thead>');
            header.push('<tbody>');
            contentsTable = header.concat(contentsTable);
            contentsTable.push('</tbody>');
            contentsTable.push('</table>');
        }
        else contentsTable.push('<p>No data in report</p>');
        return contentsTable.join('\n');
    }

    function renderPage() {
        var ticket = TEMPLATE_PARAMS.ticket + '/' + TEMPLATE_PARAMS.ts;
        var keyFile = instrResource(ticket) + '/key.json';

        REPORT.SurveyorRpt.resource(keyFile,
        function (err) {
            console.log('While getting key file data from ' + keyFile + ': ' + err);
            CNSNT.setDoneStatus();
        },
        function (status, data) {
            var params = {hash: data.SUBMIT_KEY.hash, user: data.SUBMIT_KEY.user, title: data.INSTRUCTIONS.title };
            var tz = data.INSTRUCTIONS.timezone;
            var startPosix = (new Date(data.SUBMIT_KEY.time_stamp)).valueOf();
            // Get first submission time in the correct timezone
            bufferedTimezone(REPORT.Utilities.timezone,{tz:tz,posixTimes:[startPosix]},
            function () {
                params.submitTime = data.SUBMIT_KEY.time_stamp;
                makeToc(params);
            },
            function (status, data) {
                params.submitTime  = data.timeStrings[0];
                makeToc(params);
            });
        });
    }

    function makeToc(params) {
        var ticket = TEMPLATE_PARAMS.ticket + '/' + TEMPLATE_PARAMS.ts;
        var tocFile = instrResource(ticket) + '/tableOfContents.json';
        $("#reportTitle").html('<h1>' + params.title + '</h1>');
        $("#leftHead").html(P3TXT.getReport.leftHeading);
        $("#rightHead").html("Contents");
        $("#startPage").html(1);
        $("#leftFoot").html(P3TXT.getReport.firstSubmittedBy + " " + params.user + " " +
            P3TXT.getReport.firstSubmittedAt + " " + params.submitTime);

        REPORT.SurveyorRpt.resource(tocFile,
        function (err) {
            console.log('While getting table of contents data from ' + tocFile + ': ' + err);
            CNSNT.setDoneStatus();
        },
        function (status, toc) {
            var html = makeTableOfContents(toc);
            $("#tableOfContents").html(html);
            CNSNT.setDoneStatus();
        });
    }

    module.exports.initialize = function() { $(document).ready(init); };
});