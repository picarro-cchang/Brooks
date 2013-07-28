// reportPeaks.js
/*global alert, console, module, require */
/* jshint undef:true, unused:true */

// This defines the model (REPORT.Peak), collection (REPORT.Peaks) and view (REPORT.PeaksTableView) 
//  for representing concentration peaks
// The code to read peaks from a JSON file is the getData method of REPORT.Peaks which is called 
//  from reportViewResources

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var Backbone = require('backbone');
    var CNSNT = require('common/cnsnt');
    var instrResource = require('app/utils').instrResource;
    var REPORT  = require('app/reportGlobals');
    require('jquery.dataTables');

    function reportPeaksInit() {
        REPORT.Peak = Backbone.Model.extend({
            defaults: {
                "A": 0.0,       // Amplitude of peak
                "C": 0.0,       // Concentration at peak
                "T": 0,         // Epoch time
                "P": "",        // Position (geohashed)
                "R": 0,         // Run index
                "S": 0,         // Survey index
                "W": NaN,       // Wind direction (mean)
                "U": NaN        // Wind direction (std dev)
            }
        });

        REPORT.Peaks = Backbone.Collection.extend({
            loadStage: 'init',
            model: REPORT.Peak,
            initialize: function (models, options) {
                this.peaksRef = options.peaksRef;
            },
            getData: function () {  // Get all peaks data from the server which can be in several files
                var that = this;
                var names;
                if (that.loadStage === 'loading') return;
                else if (that.loadStage === 'loaded') that.trigger('loaded');
                else {
                    that.loadStage = 'loading';
                    that.workDir = instrResource(that.peaksRef.SUBMIT_KEY.hash)+'/'+that.peaksRef.SUBMIT_KEY.dir_name;
                    that.peaksFiles = that.peaksRef.OUTPUTS.FILES;
                    names = that.peaksFiles.slice(0);
                    next();
                }
                function next() {   // Sequentially fetch peaks from list of files in "names"
                    if (names.length === 0) {       // Get here after all files are read in
                        that.loadStage = 'loaded';
                        that.trigger('loaded');
                    }
                    else {
                        var url = that.workDir + '/' + names.shift();
                        REPORT.SurveyorRpt.resource(url,
                        function (err) {
                            alert('While getting peaks data from ' + url + ': ' + err);
                        },
                        function (status, data) {
                            console.log('While getting peaks data from ' + url + ': ' + status);
                            data.forEach(function (d) { // Can filter by lat-lng limits here
                                that.push(d, {silent:true});    // All peaks are pushed to the collection
                            });
                            next();
                        });
                    }
                }
            }
        });
        REPORT.PeaksTableView = Backbone.View.extend({
            initialize: function () {
                this.name = "reportPeaks";
                this.listenTo(REPORT.reportViewResources,"init",this.repositoryInit);
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            repositoryInit: function(e) {
                if (e.context === "peaksTable") REPORT.usageTracker.use(this, CNSNT.clearStatusLine);
            },
            repositoryChanged: function (e) {
                if (e.context === "peaksTable") {
                    this.$el.html(REPORT.reportViewResources.peaksTable.join("\n"));
                    if (this.options.dataTables === null || this.options.dataTables) {
                        this.$el.find('table').dataTable({
                         "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"});
                    }
                    REPORT.usageTracker.release(this, CNSNT.setDoneStatus);
                }
            }
        });
    }
    module.exports.init = reportPeaksInit;
});

