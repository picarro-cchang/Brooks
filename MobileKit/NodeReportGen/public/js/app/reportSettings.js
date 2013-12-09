// reportSettings.js
/*global module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var Backbone = require('backbone');
    var REPORT  = require('app/reportGlobals');

    function reportSettingsInit() {
        REPORT.Settings = Backbone.Model.extend({
            defaults: function () {
                return {
                    "title": "<Sample Report>",
                    "swCorner": [ 36.58838, -121.93108 ],
                    "neCorner": [ 36.62807, -121.88112 ],
                    "submaps": {"nx": 1, "ny": 2},
                    "exclRadius": 0,
                    "fovMinAmp": 0.03,
                    "fovMinLeak": 1.0,
                    "fovNWindow": 10,
                    "peaksMinAmp": 0.1,
                    "timezone": "GMT",
                    "startPage": 1
                };
            }
        });

        REPORT.ReportTables = Backbone.Model.extend({
            defaults: {
                "analysesTable": false,
                "peaksTable": false,
                "surveysTable": false,
                "runsTable": false
            }
        });

        REPORT.PageComponent = Backbone.Model.extend({
            defaults: {
                "baseType": "map",
                "fovs": false,
                "paths": false,
                "peaks": false,
                "submapLegend": false,
                "tokens": false,
                "wedges": false
            },
            set: function(attributes, options) {
                if (attributes.fovs && !attributes.peaks) attributes.tokens = true;
                return Backbone.Model.prototype.set.call(this, attributes, options);
            }
        });

        REPORT.PageComponents = Backbone.Collection.extend({
            model: REPORT.PageComponent
        });

        REPORT.SettingsView = Backbone.View.extend({
            el: $("#getReportApp"),
            events: {
                "valueChanged #spinEditAmp": "minAmpChanged",
                "valueChanged #spinEditRows": "submapsChanged",
                "valueChanged #spinEditCols": "submapsChanged"
            },
            initialize: function () {
                $('#spinEditRows').spinedit({
                    minimum: 1,
                    maximum: 10,
                    step: 1,
                    value: REPORT.settings.get("submaps")["ny"],
                    numberOfDecimals: 0
                });
                $('#spinEditCols').spinedit({
                    minimum: 1,
                    maximum: 10,
                    step: 1,
                    value: REPORT.settings.get("submaps")["nx"],
                    numberOfDecimals: 0
                });
                $('#spinEditAmp').spinedit({
                    minimum: 0.03,
                    maximum: 10,
                    step: 0.01,
                    value: REPORT.settings.get("peaksMinAmp"),
                    numberOfDecimals: 2
                });
                this.listenTo(REPORT.settings, 'change:peaksMinAmp', this.updateMinAmp);
                this.listenTo(REPORT.settings, 'change:submaps', this.updateSubmaps);
            },
            minAmpChanged: function (e) {
                REPORT.settings.set({"peaksMinAmp": e.value });
            },
            submapsChanged: function () {
                var submaps = {"nx": +$("#spinEditCols")[0].value,"ny":+$("#spinEditRows")[0].value};
                REPORT.settings.set({"submaps":submaps});
            },
            updateMinAmp: function () {
                var minAmp = REPORT.settings.get("peaksMinAmp");
                $('#spinEditAmp').spinedit('setValue', minAmp);
            },
            updateSubmaps: function () {
                var sm = REPORT.settings.get("submaps");
                $('#spinEditRows').spinedit('setValue', sm.ny);
                $('#spinEditCols').spinedit('setValue', sm.nx);
            }
        });
    }
    module.exports.init = reportSettingsInit;
});

