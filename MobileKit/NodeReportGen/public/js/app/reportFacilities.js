// reportFacilities.js
/*global alert, console, module, require */
/* jshint undef:true, unused:true */

// This defines the model (REPORT.Facility) and collection (REPORT.Facilities) for representing 
//  user-defined facilities
// The code to read facilities from a JSON file is the getData method of REPORT.Facilities which 
//  is called from reportViewResources. When it completes, it emits a 'loaded' event.
//  It can be called many times if necessary.

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var Backbone = require('backbone');
    var instrResource = require('app/utils').instrResource;
    var REPORT  = require('app/reportGlobals');

    function reportFacilitiesInit() {
        REPORT.Facility = Backbone.Model.extend({
            defaults: {
                "P": [],        // Positions (geohashed)
                "W": 1,         // Linewidth used to render facility
                "C": "#000000"  // Color of line
            }
        });

        REPORT.Facilities = Backbone.Collection.extend({
            loadStage: 'init',
            model: REPORT.Facility,
            initialize: function (models, options) {
                this.facilitiesRef = options.facilitiesRef;
            },
            getData: function () {  // Get all facilities data from the server
                var that = this;
                var names;
                if (that.loadStage === 'loading') return;
                else if (that.loadStage === 'loaded') that.trigger('loaded');
                else {
                    that.loadStage = 'loading';
                    that.workDir = instrResource(that.facilitiesRef.SUBMIT_KEY.hash)+'/'+that.facilitiesRef.SUBMIT_KEY.dir_name;
                    that.facilitiesFiles = that.facilitiesRef.OUTPUTS.FILES;
                    names = that.facilitiesFiles.slice(0);
                    next();
                }
                function next() {   // Sequentially fetch facilities from list of files in "names"
                    if (names.length === 0) {       // Get here after all files are read in
                        that.loadStage = 'loaded';
                        that.trigger('loaded');
                    }
                    else {
                        var url = that.workDir + '/' + names.shift();
                        REPORT.SurveyorRpt.resource(url,
                        function (err) {
                            console.log('While getting facilities data from ' + url + ': ' + err);
                        },
                        function (status, data) {
                            // console.log('While getting facilities data from ' + url + ': ' + status);
                            data.forEach(function (d) { // Can filter by lat-lng limits here
                                that.push(d, {silent:true});    // All facilities are pushed to the collection
                            });
                            next();
                        });
                    }
                }
            }
        });
    }
    module.exports.init = reportFacilitiesInit;
});

