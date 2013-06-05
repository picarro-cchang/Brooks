// reportPaths.js
/*global alert, console, module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var Backbone = require('backbone');
    var gh = require('app/geohash');
    var instrResource = require('app/utils').instrResource;
    var REPORT  = require('app/reportGlobals');

    function reportPathsInit() {

        REPORT.Path = Backbone.Model.extend({
            defaults: {
                "E": "",    // Position of edge of swath (geohashed)
                "N": 0,     // Run index
                "P": "",    // Position of path (geohashed)
                "R": 0,     // Row index
                "S": 0,     // Survey index
                "T": 0      // Epoch time
            }
        });

        REPORT.Paths = Backbone.Collection.extend({
            loadStage: 'init',
            model: REPORT.Path,
            initialize: function (models, options) {
                this.pathsRef = options.pathsRef;
            },
            getData: function () {  // Getting path and fov data is interleaved with rendering, since there can be lots of points
                var that = this;
                var names;
                var neCorner = REPORT.settings.get("neCorner");
                var swCorner = REPORT.settings.get("swCorner");
                var minLat = swCorner[0], minLng = swCorner[1];
                var maxLat = neCorner[0], maxLng = neCorner[1];
                var padLat = 0.05*(maxLat-minLat);
                var padLng = 0.05*(maxLng-minLng);
                if (that.loadStage === 'loading') return;
                else if (that.loadStage === 'loaded') that.trigger('loaded');
                else {
                    that.loadStage = 'loading';
                    that.workDir = instrResource(that.pathsRef.SUBMIT_KEY.hash)+'/'+that.pathsRef.SUBMIT_KEY.dir_name;
                    that.pathsFiles = that.pathsRef.OUTPUTS.FILES;
                    names = that.pathsFiles.slice(0);   // These are all the names of the paths files, by survey and run
                    next();
                }
                function next() {
                    var url;
                    if (names.length === 0) {
                        that.loadStage = 'loaded';  // All paths (and FOVs) have been processed
                        that.trigger('loaded');
                    }
                    else {  // Read contents of one file, and consider that as a "block"
                        var name = names.shift();
                        var comps = name.split(/[_.]/); // Filename splits into following components
                        var type = comps[0];    // "path" or "fov"
                        var survey = +comps[1]; // survey index
                        var run = +comps[2];    // run index
                        url = that.workDir + '/' + name;
                        var processPathData = function(data, fovData) {
                            data.forEach(function (d) { // We render path data, and look if there is FOV information at same location
                                d["N"] = run;
                                d["S"] = survey;
                                var where = gh.decodeGeoHash(d.P);
                                var lat = where.latitude[2];
                                var lng = where.longitude[2];
                                if (lat >= minLat-padLat && lat <= maxLat+padLat &&
                                    lng >= minLng-padLng && lng <= maxLng+padLng) {
                                    if (d["R"] in fovData) { // This is the corresponding location in the FOV data dictionary
                                        d["E"] = fovData[d["R"]]["E"];   // If an edge is available, grab it
                                        if (d["P"] !== fovData[d["R"]]["P"]) alert("Bad FOV data");  // Check path segment is consistent
                                    }
                                    that.push(d,{silent: true});    // Add path (and fov) data to the collection
                                }
                            });
                            that.trigger('block');  // Signal that this block can be rendered
                            next();
                        };
                        if (type === 'path') {  // Get path data from the server - this must later be protected via a ticket
                            REPORT.SurveyorRpt.resource(url,
                            function (err) {
                                alert('While getting path data from ' + url + ': ' + err);
                            },
                            function (status, pathData) {
                                console.log('While getting path data from ' + url + ': ' + status);
                                var fovData = {};
                                var urlFov = url.replace("path", "fov");    // Get corresponding FOV (by filename)
                                if ($.inArray(name.replace("path", "fov"),that.pathsFiles) >= 0) {
                                    REPORT.SurveyorRpt.resource(urlFov,
                                    function (err) {
                                        alert('While getting FOV data from ' + urlFov + ': ' + err);
                                    },
                                    function (status, fData) {
                                        console.log('While getting FOV data from ' + urlFov + ': ' + status);
                                        fData.forEach(function (d) {
                                                fovData[d.R] = d;   // Assemble the FOV data indexed by row number
                                        });
                                        processPathData(pathData, fovData);
                                    });
                                }
                                else {
                                    processPathData(pathData, {});  // If no FOV data are available
                                }
                            });
                        }
                        else next();
                    }
                }
            }
        });
    }
    module.exports.init = reportPathsInit;
});
