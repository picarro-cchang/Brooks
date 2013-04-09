// getReport.js
/*global alert, console, module, require, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';

    var $ = require('jquery');
    var _ = require('underscore');
    var gh = require('app/geohash');
    var localrestapi = require('app/localrestapi');
    var newUsageTracker = require('app/newUsageTracker');
    var REPORT = require('app/reportGlobals');
    var reportAnalyses = require('app/reportAnalyses');
    var reportCanvasViews = require('app/reportCanvasViews');
    var reportPaths = require('app/reportPaths');
    var reportPeaks = require('app/reportPeaks');
    var reportRuns = require('app/reportRuns');
    var reportSettings = require('app/reportSettings');
    var reportSurveys = require('app/reportSurveys');
    var reportViewResources = require('app/reportViewResources');
    var p3restapi = require('app/p3restapi');

    var instructionsLoaded = false;

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
                         jsonp: false,
                         debug: false};
            //REPORT.Utilities = new p3restapi.p3RestApi(initArgs);
            REPORT.Utilities = new localrestapi.TimezoneP3(host, port, TEMPLATE_PARAMS.site);
        }

        reportAnalyses.init();
        reportPaths.init();
        reportPeaks.init();
        reportRuns.init();
        reportSettings.init();
        reportSurveys.init();
        reportViewResources.init();
        reportCanvasViews.init();
        REPORT.usageTracker = newUsageTracker();
        REPORT.settings = new REPORT.Settings();
        renderPage();
    }

    function normalizeSurveys(surveys,indexName) {
        // Extract only the required fields from each survey and compute an id so that
        //  duplicates are eliminated
        var results = [];
        surveys.forEach(function (survey, i){
            survey = _.pick(survey,_.keys((new REPORT.Survey()).attributes));
            survey.id = survey.name.substring(0,survey.name.lastIndexOf("."));
            survey[indexName] = i;
            results.push(survey);
        });
        return results;
    }

    function readSurveys(data) {
        if (data.SUBTASKS.getPeaksData) {
            REPORT.surveys.add(normalizeSurveys(data.SUBTASKS.getPeaksData.OUTPUTS.META,"peaks"),{"merge": true});
        }
        if (data.SUBTASKS.getAnalysesData) {
            REPORT.surveys.add(normalizeSurveys(data.SUBTASKS.getAnalysesData.OUTPUTS.META,"analyses"),{"merge": true});
        }
        if (data.SUBTASKS.getFovsData) {
            REPORT.surveys.add(normalizeSurveys(data.SUBTASKS.getFovsData.OUTPUTS.META,"paths"),{"merge": true});
        }
    }

    function renderPage() {
        var ticket = TEMPLATE_PARAMS.ticket + '/' + TEMPLATE_PARAMS.ts;
        var qry = TEMPLATE_PARAMS.qry;
        var keyFile = '/' + ticket + '/key.json';
        var settingsKeys = _.keys((new REPORT.Settings()).attributes);
        if (!instructionsLoaded) {
            instructionsLoaded = true;
            REPORT.SurveyorRpt.resource(keyFile,
            function (err) {
                alert('While getting key file data from ' + keyFile + ': ' + err);
            },
            function (status, data) {
                console.log('While getting key file data from ' + keyFile + ': ' + status);

                REPORT.settings.set(_.pick(data.INSTRUCTIONS,settingsKeys));

                // Override the corners from the qry parameters if they exist
                if ('swCorner' in qry) {
                    REPORT.settings.set({"swCorner": gh.decodeToLatLng(qry.swCorner), "submaps":{"nx":1, "ny":1}});
                }
                if ('neCorner' in qry) {
                    REPORT.settings.set({"neCorner": gh.decodeToLatLng(qry.neCorner), "submaps":{"nx":1, "ny":1}});
                }
                // Construct the runs collection and the templatate
                REPORT.settings.set({"runs": new REPORT.Runs(data.INSTRUCTIONS.runs)});
                REPORT.settings.set({"template": {"summary": { tables: new REPORT.ReportTables(data.INSTRUCTIONS.template.summary.tables),
                                                               figures: new REPORT.PageComponents(data.INSTRUCTIONS.template.summary.figures)},
                                                  "submaps": { tables: new REPORT.ReportTables(data.INSTRUCTIONS.template.submaps.tables),
                                                               figures: new REPORT.PageComponents(data.INSTRUCTIONS.template.submaps.figures)}}});
                // Construct the surveys collection
                REPORT.surveys = new REPORT.Surveys();
                readSurveys(data);
                // Set up the collections for peaks, analyses and paths data (to be read from .json files)
                REPORT.peaks = new REPORT.Peaks(null, {peaksRef:data.SUBTASKS.getPeaksData});
                REPORT.analyses = new REPORT.Analyses(null, {analysesRef:data.SUBTASKS.getAnalysesData});
                if (data.SUBTASKS.hasOwnProperty("getFovsData")) REPORT.paths = new REPORT.Paths(null, {pathsRef:data.SUBTASKS.getFovsData});
                else REPORT.paths = null;
                // Create a ReportViewResources object to hold the canvases which make the report
                REPORT.reportViewResources = new REPORT.ReportViewResources();

                var params = {hash: data.SUBMIT_KEY.hash, user: data.SUBMIT_KEY.user, name: qry.name};
                var tz = data.INSTRUCTIONS.timezone;
                var startPosix = (new Date(data.SUBMIT_KEY.time_stamp)).valueOf();
                // Get first submission time in the correct timezone
                REPORT.Utilities.timezone({tz:tz,posixTimes:[startPosix]},
                function () {
                    params.submitTime = data.SUBMIT_KEY.time_stamp;
                    doIt();
                },
                function (status, data) {
                    params.submitTime  = data.timeStrings[0];
                    doIt();
                });
                function doIt() {
                    // Figure out if we are a summary view or a submap view depending on whether the coordinates
                    //  are passed in on the command line
                    var summary = !('swCorner' in qry) && !('neCorner' in qry);
                    if (summary) makePdfReport(REPORT.settings.get("template").summary, params);
                    else makePdfReport(REPORT.settings.get("template").submaps, params);
                }
            });
        }
    }

    function boolToIcon(value) {
        var name = (value) ? ("icon-ok") : ("icon-remove");
        return (undefined !== value) ? '<i class="' + name + '"></i>' : '';
    }

    function makePdfReport(subreport, params) {
        var figureComponents = [ "paths", "fovs", "wedges", "tokens", "peaks", "analyses", "submapGrid" ];
        var id, neCorner = REPORT.settings.get("neCorner"), swCorner = REPORT.settings.get("swCorner");
        var title = REPORT.settings.get("title");
        var name = params.name;

        $("#reportTitle").html(title);
        $("#rightHead").html(name);
        $("#leftFoot").html("First submitted by " + params.user + " at " + params.submitTime);
        $("#getReportApp").append('<div style="container-fluid">');
        $("#getReportApp").append('<div style="row-fluid">');
        $("#getReportApp").append('<div style="span12">');
        $("#getReportApp").append('<h1 style="text-align:center;">' + title + '</h1>');

        var settingsTableTop = [];
        var settingsTableBottom = [];
        settingsTableTop.push('<table class="table table-condensed table-fmt1">');
        settingsTableTop.push('<thead><tr>');
        settingsTableTop.push('<th>SW Corner (Lat,Lng)</th>');
        settingsTableTop.push('<th>NE Corner (Lat,Lng)</th>');
        settingsTableTop.push('<th>Min Peak Ampl (ppm)</th>');
        settingsTableTop.push('<th>Excl Radius (m)</th>');
        settingsTableTop.push('<th>Paths</th>');
        settingsTableTop.push('<th>Peaks</th>');
        settingsTableTop.push('<th>LISAs</th>');
        settingsTableTop.push('<th>FOV</th>');
        settingsTableTop.push('<th>Isotopic</th>');
        settingsTableTop.push('</tr></thead>');
        settingsTableTop.push('<tbody>');
        settingsTableTop.push('<tr>');
        settingsTableTop.push('<td>' + swCorner[0].toFixed(5) + ', ' + swCorner[1].toFixed(5) + '</td>');
        settingsTableTop.push('<td>' + neCorner[0].toFixed(5) + ', ' + neCorner[1].toFixed(5) + '</td>');
        settingsTableTop.push('<td>' + REPORT.settings.get("peaksMinAmp").toFixed(2) + '</td>');
        settingsTableTop.push('<td>' + REPORT.settings.get("exclRadius").toFixed(0) + '</td>');
        settingsTableBottom.push('</tr>');
        settingsTableBottom.push('</tbody></table>');
        for (var i=0; i<subreport.figures.models.length; i++) {
            var pageComponent = subreport.figures.models[i];
            var layers = [];
            var settingsTableMid = [];
            settingsTableMid.push('<td>' + boolToIcon(pageComponent.get("paths")) + '</td>');
            settingsTableMid.push('<td>' + boolToIcon(pageComponent.get("peaks")) + '</td>');
            settingsTableMid.push('<td>' + boolToIcon(pageComponent.get("wedges")) + '</td>');
            settingsTableMid.push('<td>' + boolToIcon(pageComponent.get("fovs")) + '</td>');
            settingsTableMid.push('<td>' + boolToIcon(pageComponent.get("analyses")) + '</td>');
            $("#getReportApp").append('<div class="reportTable"; style="position:relative;">' +
                settingsTableTop.join("") + settingsTableMid.join("") + settingsTableBottom.join("") + '</div>');

            layers.push(pageComponent.get("baseType"));
            for (var j=0; j<figureComponents.length; j++) {
                if (pageComponent.get(figureComponents[j])) {
                    layers.push(figureComponents[j]);
                }
            }
            var id_fig = 'id_page_' + (i+1) + 'fig';
            $("#getReportApp").append('<div id="' + id_fig + '" class="reportFigure"; style="position:relative;"/>');
            new REPORT.CompositeViewWithLinks({el: $('#' + id_fig), name: id_fig.slice(3), layers:layers.slice(0)});
        }
        if (subreport.tables.get("analysesTable")) {
            id = 'id_analysesTable';
            $("#getReportApp").append('<h2 class="reportTableHeading">Isotopic Analysis Table</h2>');
            $("#getReportApp").append('<div id="' + id + '" class="reportTable"; style="position:relative;"/>');
            new REPORT.AnalysesTableView({el: $('#' + id), dataTables: false});
        }
        if (subreport.tables.get("peaksTable")) {
            id = 'id_peaksTable';
            $("#getReportApp").append('<h2 class="reportTableHeading">Peaks Table</h2>');
            $("#getReportApp").append('<div id="' + id + '" class="reportTable"; style="position:relative;"/>');
            new REPORT.PeaksTableView({el: $('#' + id), dataTables: false});
        }
        if (subreport.tables.get("runsTable")) {
            id = 'id_runsTable';
            $("#getReportApp").append('<h2 class="reportTableHeading">Runs Table</h2>');
            $("#getReportApp").append('<div id="' + id + '" class="reportTable"; style="position:relative;"/>');
            new REPORT.RunsTableView({el: $('#' + id), dataTables: false});
        }
        if (subreport.tables.get("surveysTable")) {
            id = 'id_surveysTable';
            $("#getReportApp").append('<h2 class="reportTableHeading">Surveys Table</h2>');
            $("#getReportApp").append('<div id="' + id + '" class="reportTable"; style="position:relative;"/>');
            new REPORT.SurveysTableView({el: $('#' + id), dataTables: false});
        }
        REPORT.reportViewResources.render();
        $("#getReportApp").append('</div></div></div>');
    }
                /* 
                REPORT.multiCanvasView = new REPORT.MultiCanvasView(
                {   el: $("#multiCanvasDiv"),
                    name: "example1"
                });
                REPORT.figure2 = new REPORT.MultiCanvasView(
                {   el: $("#figure2"),
                    name: "figure2"
                });
                REPORT.figure3 = new REPORT.CompositeView(
                {   el: $("#figure3"),
                    name: "figure3",
                    layers: ['map', 'paths', 'wedges', 'peaks']
                });
                REPORT.figure4 = new REPORT.CompositeView(
                {   el: $("#figure4"),
                    name: "figure4",
                    layers: ['satellite', 'paths', 'wedges', 'peaks', 'fovs']
                });

                REPORT.reportViewResources.render();
                REPORT.peaksTableView = new REPORT.PeaksTableView({el: $("#peaksTable1Div")});
                REPORT.runsTableView = new REPORT.RunsTableView({el: $("#runsTable1Div")});
                REPORT.surveysTableView = new REPORT.SurveysTableView({el: $("#surveysTable1Div")});
                $("#keyContents").html(JSON.stringify(data));
            });
        }
    }
    */
    module.exports.initialize = function() { $(document).ready(init); };

});