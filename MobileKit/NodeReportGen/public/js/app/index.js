// index.js
/*global alert, define, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var DASHBOARD = require('app/dashboardGlobals');
    var newRptGenService = require('app/newRptGenService');
    var dashboardInstructions = require('app/dashboardInstructions');
    var dashboardJobs = require('app/dashboardJobs');
    var dashboardSettings = require('app/dashboardSettings');
    var p3restapi = require('app/p3restapi');

    function init() {
        var initArgs = {host: TEMPLATE_PARAMS.host,
                        port: TEMPLATE_PARAMS.port,
                        site: TEMPLATE_PARAMS.site,
                        identity: TEMPLATE_PARAMS.identity,
                        psys: TEMPLATE_PARAMS.psys,
                        rprocs: ["SurveyorRpt:resource","SurveyorRpt:getStatus","SurveyorRpt:submit"],
                        svc: "gdu",
                        version: "1.0",
                        resource: "SurveyorRpt",
                        jsonp: false,
                        debug: false};
        DASHBOARD.SurveyorRpt = new p3restapi.p3RestApi(initArgs);
        initArgs = {host: TEMPLATE_PARAMS.host,
                        port: TEMPLATE_PARAMS.port,
                        site: TEMPLATE_PARAMS.site,
                        identity: TEMPLATE_PARAMS.identity,
                        psys: TEMPLATE_PARAMS.psys,
                        rprocs: ["Utilities:timezone"],
                        svc: "gdu",
                        version: "1.0",
                        resource: "Utilities",
                        jsonp: false,
                        debug: false};
        DASHBOARD.Utilities = new p3restapi.p3RestApi(initArgs);

        dashboardSettings.init();
        dashboardJobs.init();
        dashboardInstructions.init();
        var proxyUrl = TEMPLATE_PARAMS.host + ':' + TEMPLATE_PARAMS.port;
        var protocol = (TEMPLATE_PARAMS.port == 443) ? "https" : "http";
        DASHBOARD.rptGenService = newRptGenService({"rptgen_url": protocol + "://" + proxyUrl});
        DASHBOARD.dashboardSettings = new DASHBOARD.DashboardSettings();
        DASHBOARD.submittedJobs = new DASHBOARD.SubmittedJobs();
        DASHBOARD.submittedJobs.fetch();    // from local storage
        DASHBOARD.submittedJobs.models.forEach(function (job) { job.updateStatus(); });
        DASHBOARD.instructionsFileModel = new DASHBOARD.InstructionsFileModel();

        DASHBOARD.jobsView = new DASHBOARD.JobsView();
        (new DASHBOARD.SettingsView()).render();
        DASHBOARD.jobsView.render();
    }

    module.exports.initialize = function () { $(document).ready(init); };
});