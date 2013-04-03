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

    function init() {
        alert(JSON.stringify(TEMPLATE_PARAMS));
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