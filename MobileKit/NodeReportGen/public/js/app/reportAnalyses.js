// reportAnalyses.js
/*global alert, console, module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var Backbone = require('backbone');
    var CNSNT = require('common/cnsnt');
    var instrResource = require('app/utils').instrResource;
    var REPORT  = require('app/reportGlobals');
    require('jquery.dataTables');

    function reportAnalysesInit() {
        REPORT.Analysis = Backbone.Model.extend({
            defaults: {
                "C": 0.0,       // Concentration at peak
                "D": 0.0,       // Delta value
                "P": "",        // Position (geohashed)
                "R": 0,         // Run index
                "S": 0,         // Survey index
                "T": 0,         // Epoch time
                "U": 0          // Uncertainty in delta
            }
        });

        REPORT.Analyses = Backbone.Collection.extend({
            loadStage: 'init',
            model: REPORT.Analysis,
            initialize: function (models, options) {
                this.analysesRef = options.analysesRef;
            },
            getData: function () {  // Get all analyses data from the server which can be in several files
                var that = this;
                var names;
                if (that.loadStage === 'loading') return;
                else if (that.loadStage === 'loaded') that.trigger('loaded');
                else {
                    that.loadStage = 'loading';
                    that.workDir = instrResource(that.analysesRef.SUBMIT_KEY.hash)+'/'+that.analysesRef.SUBMIT_KEY.dir_name;
                    that.analysesFiles = that.analysesRef.OUTPUTS.FILES;
                    names = that.analysesFiles.slice(0);
                    next();
                }
                function next() {   // Sequentially fetch analyses from list of files in "names"
                    if (names.length === 0) {       // Get here after all files are read in
                        that.loadStage = 'loaded';
                        that.trigger('loaded');
                    }
                    else {
                        var url = that.workDir + '/' + names.shift();
                        REPORT.SurveyorRpt.resource(url,
                        function (err) {
                            console.log('While getting analyses data from ' + url + ': ' + err);
                        },
                        function (status, data) {
                            // console.log('While getting analyses data from ' + url + ': ' + status);
                            data.forEach(function (d) { // Can filter by lat-lng limits here
                                that.push(d, {silent:true});    // All peaks are pushed to the collection
                            });
                            next();
                        });
                    }
                }
            }
        });

        REPORT.AnalysesTableView = Backbone.View.extend({
            initialize: function () {
                this.name = "reportAnalyses";
                this.listenTo(REPORT.reportViewResources,"init",this.repositoryInit);
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            repositoryInit: function(e) {
                if (e.context === "analysesTable") REPORT.usageTracker.use(this, CNSNT.clearStatusLine);
            },
            repositoryChanged: function (e) {
                if (e.context === "analysesTable") {
                    this.$el.html(REPORT.reportViewResources.analysesTable.join("\n"));
                    if (this.options.dataTables === null || this.options.dataTables) {
                        this.$el.find('table').dataTable({
                         "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"});
                    }
                    REPORT.usageTracker.release(this, CNSNT.setDoneStatus);
                }
            }
        });

    }
    module.exports.init = reportAnalysesInit;
});

