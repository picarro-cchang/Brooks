// dashboardSettings.js
/*global module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var Backbone = require('backbone');
    var DASHBOARD = require('app/dashboardGlobals');
    var jstz = require('jstz');
    require('jquery.maphilight');
    require('jquery.timezone-picker');

    function dashboardSettingsInit() {
        DASHBOARD.DashboardSettings = Backbone.Model.extend({
            defaults: {
                timezone: null,
                user: "demo"
            },
            initialize: function () {
                var tz = jstz.determine();  // Get from browser
                this.set({"timezone": tz.name()});
            }
        });

        DASHBOARD.SettingsView = Backbone.View.extend({
            el: $("#id_settings"),
            events: {
                "shown #id_timezoneModal": "onModalShown",
                "click #id_save_timezone": "onTimezoneSaved"
            },
            initialize: function () {
                $('#timezone-image').timezonePicker({
                    target: '#edit-date-default-timezone',
                    countryTarget: '#edit-site-default-country'
                });
                this.listenTo(DASHBOARD.dashboardSettings,"change:timezone",this.render);
            },
            onModalShown: function () {
                $("#edit-date-default-timezone").val(DASHBOARD.dashboardSettings.get("timezone")).change();
            },
            onTimezoneSaved: function () {
                DASHBOARD.dashboardSettings.set({"timezone": $("#edit-date-default-timezone").val()});
            },
            render: function () {
                $("#id_timezone").val(DASHBOARD.dashboardSettings.get("timezone"));
                return this;
            }
        });
    }
    module.exports.init = dashboardSettingsInit;
});

