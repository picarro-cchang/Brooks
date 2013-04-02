// getReport.js
/*global module, require, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';

    var $ = require('jquery');
    var _ = require('underscore');
    var gh = require('app/geohash');
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

    var instructionsLoaded = false;

    function init() {
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
            $.get('/rest/data' + keyFile, function(data) {
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

                // Figure out if we are a summary view or a submap view depending on whether the coordinates
                //  are passed in on the command line

                var summary = !('swCorner' in qry) && !('neCorner' in qry);
                if (summary) makePdfReport(REPORT.settings.get("template").summary, qry.name);
                else makePdfReport(REPORT.settings.get("template").submaps, qry.name);
            });
        }
    }

    function makePdfReport(subreport, name) {
        var figureComponents = [ "fovs", "paths", "peaks", "wedges", "analyses", "submapGrid" ];
        var id, neCorner = REPORT.settings.get("neCorner"), swCorner = REPORT.settings.get("swCorner");
        var title = REPORT.settings.get("title");
        $("#getReportApp").append('<h2 style="text-align:center;">' + title + ' - ' + name + '</h2>');
        $("#getReportApp").append('<div style="container-fluid">');
        $("#getReportApp").append('<div style="row-fluid">');
        $("#getReportApp").append('<div style="span12">');
        $("#getReportApp").append('<p><b>SW Corner: </b>' + swCorner[0].toFixed(5) + ', ' + swCorner[1].toFixed(5) +
                                  ' <b>NE Corner: </b>' + neCorner[0].toFixed(5) + ', ' + neCorner[1].toFixed(5) + '</p>');
        $("#getReportApp").append('<p><b>Min peak amplitude: </b>' + REPORT.settings.get("peaksMinAmp").toFixed(2) +
                                  ' <b>Exclusion radius (m): </b>' + REPORT.settings.get("exclRadius").toFixed(0) + '</p>');
        for (var i=0; i<subreport.figures.models.length; i++) {
            var layers = [];
            var pageComponent = subreport.figures.models[i];
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