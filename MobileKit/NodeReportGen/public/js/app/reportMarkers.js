// reportMarkers.js
/*global alert, console, module, require */
/* jshint undef:true, unused:true */

// This defines the model (REPORT.Marker) and collection (REPORT.Markers) for representing 
//  user-defined markers
// The code to read markers from a JSON file is the getData method of REPORT.Markers which 
//  is called from reportViewResources. When it completes, it emits a 'loaded' event.
//  It can be called many times if necessary.

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var Backbone = require('backbone');
    var instrResource = require('app/utils').instrResource;
    var REPORT  = require('app/reportGlobals');

    function reportMarkersInit() {
        REPORT.Marker = Backbone.Model.extend({
            defaults: {
                "P": "",        // Position (geohashed)
                "T": "",        // Text in marker
                "C": "#FFFFFF"  // Color of marker
            }
        });

        REPORT.Markers = Backbone.Collection.extend({
            loadStage: 'init',
            model: REPORT.Marker,
            initialize: function (models, options) {
                this.markersRef = options.markersRef;
            },
            getData: function () {  // Get all markers data from the server
                var that = this;
                var names;
                if (that.loadStage === 'loading') return;
                else if (that.loadStage === 'loaded') that.trigger('loaded');
                else {
                    that.loadStage = 'loading';
                    that.workDir = instrResource(that.markersRef.SUBMIT_KEY.hash)+'/'+that.markersRef.SUBMIT_KEY.dir_name;
                    that.markersFiles = that.markersRef.OUTPUTS.FILES;
                    names = that.markersFiles.slice(0);
                    next();
                }
                function next() {   // Sequentially fetch markers from list of files in "names"
                    if (names.length === 0) {       // Get here after all files are read in
                        that.loadStage = 'loaded';
                        that.trigger('loaded');
                    }
                    else {
                        var url = that.workDir + '/' + names.shift();
                        REPORT.SurveyorRpt.resource(url,
                        function (err) {
                            alert('While getting markers data from ' + url + ': ' + err);
                        },
                        function (status, data) {
                            console.log('While getting markers data from ' + url + ': ' + status);
                            data.forEach(function (d) { // Can filter by lat-lng limits here
                                that.push(d, {silent:true});    // All markers are pushed to the collection
                            });
                            next();
                        });
                    }
                }
            }
        });
    }
    module.exports.init = reportMarkersInit;
});

