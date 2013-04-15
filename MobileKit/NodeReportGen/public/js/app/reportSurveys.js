// reportSurveys.js
/*global module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var Backbone = require('backbone');
    var CNSNT = require('app/cnsnt');
    var REPORT  = require('app/reportGlobals');
    require('jquery.dataTables');

    function reportSurveysInit() {
        REPORT.Survey = Backbone.Model.extend({
            defaults: {
                "ANALYZER": "",
                "minetm": 0,
                "maxetm": 0,
                "name": "",
                "stabClass":""
            }
        });

        REPORT.Surveys = Backbone.Collection.extend({
            model: REPORT.Survey
        });

        REPORT.SurveysTableView = Backbone.View.extend({
            initialize: function () {
                this.listenTo(REPORT.reportViewResources,"init",this.repositoryInit);
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            repositoryInit: function(e) {
                if (e.context === "surveysTable") REPORT.usageTracker.use(this, CNSNT.clearStatusLine);
            },
            repositoryChanged: function (e) {
                if (e.context === "surveysTable") {
                    this.$el.html(REPORT.reportViewResources.surveysTable.join("\n"));
                    if (this.options.dataTables === null || this.options.dataTables) {
                        this.$el.find('table').dataTable({
                         "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"});
                    }
                    REPORT.usageTracker.release(this, CNSNT.setDoneStatus);
                }
            }
        });

    }
    module.exports.init = reportSurveysInit;
});

