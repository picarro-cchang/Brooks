// reportPeaks.js
/*global module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var Backbone = require('backbone');
    var CNSNT = require('app/cnsnt');
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
                    that.workDir = '/rest/data/'+that.peaksRef.SUBMIT_KEY.hash+'/'+that.peaksRef.SUBMIT_KEY.dir_name;
                    that.peaksFiles = that.peaksRef.OUTPUTS.FILES;
                    names = that.peaksFiles.slice(0);
                    next();
                }
                function next() {   // Sequentially fetch peaks from list of files in "names"
                    var url;
                    if (names.length === 0) {       // Get here after all files are read in
                        that.loadStage = 'loaded';
                        that.trigger('loaded');
                    }
                    else {
                        url = that.workDir + '/' + names.shift();
                        $.getJSON(url, function(data) { // Get peaks data from the server - this must later be protected via a ticket
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

