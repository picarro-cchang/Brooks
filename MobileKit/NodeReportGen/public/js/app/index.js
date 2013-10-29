// index.js
/*global alert, console, define, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var DASHBOARD = require('app/dashboardGlobals');
    var jstz = require('jstz');
    var newRptGenService = require('app/newRptGenService');
    var dashboardInstructions = require('app/dashboardInstructions');
    var dashboardJobs = require('app/dashboardJobs');
    var p3restapi = require('app/p3restapi');
    var localrestapi = require('app/localrestapi');

    function init() {
        var initArgs = {host: TEMPLATE_PARAMS.host,
                        port: TEMPLATE_PARAMS.port,
                        site: TEMPLATE_PARAMS.site,
                        identity: TEMPLATE_PARAMS.identity,
                        psys: TEMPLATE_PARAMS.psys,
                        rprocs: ["SurveyorRpt:resource",
                                 "SurveyorRpt:getStatus",
                                 "SurveyorRpt:submit",
                                 "SurveyorRpt:updateDashboard",
                                 "SurveyorRpt:getDashboard"
                                ],
                        svc: "gdu",
                        version: "1.0",
                        resource: "SurveyorRpt",
                        api_timeout: 30.0,
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
                    api_timeout: 30.0,
                    jsonp: false,
                    debug: false};
        //DASHBOARD.Utilities = new p3restapi.p3RestApi(initArgs);
        DASHBOARD.Utilities = new localrestapi.TimezoneP3(TEMPLATE_PARAMS.host,
            TEMPLATE_PARAMS.port, TEMPLATE_PARAMS.site);
        initArgs = {host: TEMPLATE_PARAMS.host,
                    port: TEMPLATE_PARAMS.port,
                    site: TEMPLATE_PARAMS.site,
                    identity: TEMPLATE_PARAMS.identity,
                    psys: TEMPLATE_PARAMS.psys,
                    rprocs: ["AnzMeta:resource"],
                    svc: "gdu",
                    version: "1.0",
                    resource: "AnzMeta",
                    api_timeout: 30.0,
                    jsonp: false,
                    debug: false};
        DASHBOARD.AnzMeta = new p3restapi.p3RestApi(initArgs);

	DASHBOARD.analyzers = [];
    DASHBOARD.analyzersDict = {};
	var url = "/all?limit=all";
        DASHBOARD.AnzMeta.resource(url,
        function (err) {
            console.log('While retrieving analyzer list from ' + url + ': ' + err);
            startViews();
        },
        function (status, data) {
            for (var i=0; i<data.length; i++) {
                DASHBOARD.analyzers.push(data[i].ANALYZER);
            }
            DASHBOARD.analyzers.sort();
            for (i=0; i<DASHBOARD.analyzers.length; i++) {
                DASHBOARD.analyzersDict[DASHBOARD.analyzers[i]] = DASHBOARD.analyzers[i];
            }
            startViews();
        });

        function startViews() {
            console.log('Analyzers', DASHBOARD.analyzers);
            DASHBOARD.timezone = jstz.determine().name();
            DASHBOARD.user = TEMPLATE_PARAMS.user;
            DASHBOARD.force = TEMPLATE_PARAMS.force;
            dashboardJobs.init();
            dashboardInstructions.init();
            var proxyUrl = TEMPLATE_PARAMS.host + ':' + TEMPLATE_PARAMS.port;
            var protocol = (TEMPLATE_PARAMS.port == 443) ? "https" : "http";
            DASHBOARD.rptGenService = newRptGenService({"rptgen_url": protocol + "://" + proxyUrl});
            DASHBOARD.submittedJobs = new DASHBOARD.SubmittedJobs();
            DASHBOARD.SurveyorRpt.getDashboard({user: DASHBOARD.user},
            function (err) {
                console.log("Error fetching user's dashboard: " + err);
            },
            function (s, result) {
                if (result.error) console.log("Error fetching user's dashboard: " + result.error);
                else {
                    var start = performance.now();
                    result.dashboard.forEach(function(row) {
                        DASHBOARD.submittedJobs.add(row, {silent:true});
                    });
                  	console.log('Time to load submittedJobs: ' + (performance.now() - start) + ' ms');
                    DASHBOARD.instructionsFileModel = new DASHBOARD.InstructionsFileModel();
                    DASHBOARD.jobsView = new DASHBOARD.JobsView();
                    DASHBOARD.jobsView.render();
                }
            });
            // DASHBOARD.submittedJobs.fetch();    // from local storage
            // DASHBOARD.submittedJobs.models.forEach(function (job) { job.updateStatus(); });
        }
    }
    module.exports.initialize = function () { $(document).ready(init); };
});
