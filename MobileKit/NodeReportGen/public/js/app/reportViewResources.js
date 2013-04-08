// reportViewResources.js
/*global module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var _ = require('underscore');
    var Backbone = require('backbone');
    var CNSNT = require('app/cnsnt');
    var makeAnalyses = require('app/makeAnalyses');
    var makeAnalysesTable = require('app/makeAnalysesTable');
    var makePeaks = require('app/makePeaks');
    var makePeaksTable = require('app/makePeaksTable');
    var makeRunsTable = require('app/makeRunsTable');
    var makeSubmapGrid = require('app/makeSubmapGrid');
    var makeSurveysTable = require('app/makeSurveysTable');
    var makeWedges = require('app/makeWedges');
    var newPathsMaker = require('app/newPathsMaker');
    var REPORT  = require('app/reportGlobals');


    function reportViewResourcesInit() {
        REPORT.ReportViewResources = Backbone.View.extend({
            initialize: function () {
                this.listenTo(REPORT.settings, "change", this.settingsChanged);
                this.contexts = {'analyses': null, 'map':null, 'satellite':null, 'peaks': null,
                                 'tokens': null, 'fovs': null, 'paths': null, 'wedges': null,
                                 'submapGrid': null };
                this.padX = 30;
                this.padY = 30;
                this.submapLinks = {};
                this.runsData = {};
                this.surveysData = {};
            },
            settingsChanged: function (e) {
                var that = this;
                _.keys(e.changed).forEach(function (setting) {
                    switch (setting) {
                    case "submaps":
                        that.makeSubmapGridLayer();
                        break;
                    case "peaksMinAmp":
                        that.makePeaksLayers();
                        that.makeWedgesLayer();
                        that.makePeaksTable();
                        break;
                    }
                });
            },
            render: function () {
                this.setupReport();
                this.makeMapLayer();
                this.makeSatelliteLayer();
                this.makeSubmapGridLayer();
                this.makePeaksLayers();
                this.makeWedgesLayer();
                this.makeAnalysesLayer();
                this.makePathsLayers();
                this.makePeaksTable();
                this.makeAnalysesTable();
            },
            setupReport: function () {
                var cosLat, deltaLat, deltaLng, fac, mppx, mppy, Xp, Yp;
                this.minLat = REPORT.settings.get("swCorner")[0];
                this.minLng = REPORT.settings.get("swCorner")[1];
                this.maxLat = REPORT.settings.get("neCorner")[0];
                this.maxLng = REPORT.settings.get("neCorner")[1];
                this.meanLat = 0.5*(this.minLat + this.maxLat);
                this.meanLng = 0.5*(this.minLng + this.maxLng);
                Xp = this.maxLng - this.minLng;
                Yp = this.maxLat - this.minLat;
                // Find largest zoom consistent with these limits
                cosLat = Math.cos(this.meanLat * CNSNT.DTR);
                this.zoom = Math.floor(Math.floor(Math.log(Math.min((360.0 * 640) / (
                    256 * Xp), (360.0 * 640 * cosLat) / (256 * Yp))) / Math.log(2.0)));
                // Find the number of pixels in each direction
                fac = (256.0 / 360.0) * Math.pow(2,this.zoom);
                this.mx = Math.ceil(fac * Xp);
                this.my = Math.ceil(fac * Yp / cosLat);
                this.scale = 2;
                this.nx = this.scale * this.mx;
                this.ny = this.scale * this.my;

                // Calculate meters per pixel
                deltaLat = CNSNT.RTD / CNSNT.EARTH_RADIUS;
                deltaLng = CNSNT.RTD / (CNSNT.EARTH_RADIUS * Math.cos(this.meanLat * CNSNT.DTR));
                mppx = Xp / (deltaLng * this.nx);
                mppy = Yp / (deltaLat * this.ny);
                this.mpp = 0.5 * (mppx + mppy);

                // Transformation to pixels
                this.xform = function (lng, lat) {
                    var x = Math.round(this.nx * (lng - this.minLng) / (this.maxLng - this.minLng));
                    var y = Math.round(this.ny * (lat - this.maxLat) / (this.minLat - this.maxLat));
                    return [x,y];
                };
                this.inMap = function (lat,lng) {
                    return ( this.minLat <= lat && lat < this.maxLat &&
                             this.minLng <= lng && lng < this.maxLng );
                };
                this.inView = function (xy) {
                    return ( -this.padX <= xy[0] && xy[0] < this.nx+this.padX &&
                             -this.padY <= xy[1] && xy[1] < this.ny+this.padY );
                };
            },
            makeMapLayer: function () {
                var that = this;
                var image = new Image();
                var params = { center: this.meanLat.toFixed(6) + "," + this.meanLng.toFixed(6),
                               zoom: this.zoom, size: this.mx + "x" + this.my, scale: this.scale,
                               maptype: "map", sensor: false };
                var url = 'http://maps.googleapis.com/maps/api/staticmap?' + $.param(params);
                image.src = url;
                that.trigger("init",{"context": "map"});
                image.onload = function () {
                    var ctx = document.createElement("canvas").getContext("2d");
                    ctx.canvas.height = this.height + that.padY;
                    ctx.canvas.width = this.width + that.padX;
                    ctx.drawImage(this, that.padX, that.padY);
                    that.contexts["map"] = ctx;
                    that.trigger("change",{"context": "map"});
                };
            },
            makeSatelliteLayer: function () {
                var that = this;
                var image = new Image();
                var params = { center: this.meanLat.toFixed(6) + "," + this.meanLng.toFixed(6),
                               zoom: this.zoom, size: this.mx + "x" + this.my, scale: this.scale,
                               maptype: "satellite", sensor: false };
                var url = 'http://maps.googleapis.com/maps/api/staticmap?' + $.param(params);
                image.src = url;
                that.trigger("init",{"context": "satellite"});
                image.onload = function () {
                    var ctx = document.createElement("canvas").getContext("2d");
                    ctx.canvas.height = this.height + that.padY;
                    ctx.canvas.width = this.width + that.padX;
                    ctx.drawImage(this, that.padX, that.padY);
                    that.contexts["satellite"] = ctx;
                    that.trigger("change",{"context": "satellite"});
                };
            },
            makeSubmapGridLayer: function() {
                this.trigger("init",{"context": "submapGrid"});
                var submaps = REPORT.settings.get("submaps");
                this.subx = submaps.nx;
                this.suby = submaps.ny;
                var result = makeSubmapGrid(this);
                this.contexts["submapGrid"] = result.context;
                this.submapLinks = result.links;
                this.trigger("change",{"context": "submapGrid"});
            },
            makePeaksLayers: function() {
                var that = this;
                that.trigger("init",{"context": "peaks"});
                that.trigger("init",{"context": "tokens"});
                REPORT.peaks.once("loaded", function () {
                    that.peaksData = REPORT.peaks.models;
                    that.peaksMinAmp = REPORT.settings.get("peaksMinAmp");
                    that.fovMinAmp = REPORT.settings.get("fovMinAmp");
                    var result = makePeaks(that);
                    that.contexts["peaks"] = result.peaks;
                    that.contexts["tokens"] = result.tokens;
                    that.runsData["peaks"] = result.runs;
                    that.surveysData["peaks"] = result.surveys;
                    that.trigger("change",{"context": "peaks"});
                    that.trigger("change",{"context": "tokens"});
                    that.makeRunsTable();
                    that.makeSurveysTable();
                });
                REPORT.peaks.getData();
            },
            makeWedgesLayer: function() {
                var that = this;
                that.trigger("init",{"context": "wedges"});
                REPORT.peaks.once("loaded", function () {
                    that.peaksData = REPORT.peaks.models;
                    that.peaksMinAmp = REPORT.settings.get("peaksMinAmp");
                    that.contexts["wedges"] = makeWedges(that);
                    that.trigger("change",{"context": "wedges"});
                });
                REPORT.peaks.getData();
            },
            makeAnalysesLayer: function() {
                var that = this;
                that.trigger("init",{"context": "analyses"});
                REPORT.analyses.once("loaded", function () {
                    that.analysesData = REPORT.analyses.models;
                    that.contexts["analyses"] = makeAnalyses(that)["context"];
                    that.trigger("change",{"context": "analyses"});
                });
                REPORT.analyses.getData();
            },
            makePathsLayers: function () {
                if (!REPORT.paths) return;
                var that = this;
                var pathsMaker = newPathsMaker(that);
                that.pathsCollection = REPORT.paths;
                function doBlock(survey,run) {
                    pathsMaker.makePaths(survey,run);
                }
                REPORT.paths.on("block", doBlock);
                that.trigger("init",{"context": "paths"});
                that.trigger("init",{"context": "fovs"});
                REPORT.paths.once("loaded", function () {
                    var result = pathsMaker.completePaths();
                    that.contexts["paths"] = result.paths;
                    that.contexts["fovs"]  = result.fovs;
                    that.runsData["paths"] = result.runs;
                    that.surveysData["paths"] = result.surveys;
                    REPORT.paths.off("block",doBlock);
                    that.trigger("change",{"context": "paths"});
                    that.trigger("change",{"context": "fovs"});
                    that.makeRunsTable();
                    that.makeSurveysTable();
                });
                REPORT.paths.getData();
            },
            makeAnalysesTable: function () {
                var that = this;
                that.trigger("init",{"context": "analysesTable"});
                REPORT.analyses.once("loaded", function () {
                    that.analysesData = REPORT.analyses.models;
                    that.analysesTable = makeAnalysesTable(that);
                    that.trigger("change",{"context": "analysesTable"});
                });
                REPORT.analyses.getData();
            },
            makePeaksTable: function () {
                var that = this;
                that.trigger("init",{"context": "peaksTable"});
                REPORT.peaks.once("loaded", function () {
                    that.peaksData = REPORT.peaks.models;
                    that.minAmp = REPORT.settings.get("peaksMinAmp");
                    that.peaksTable = makePeaksTable(that);
                    that.trigger("change",{"context": "peaksTable"});
                });
                REPORT.peaks.getData();
            },
            makeRunsTable: function () {
                var that = this;
                that.trigger("init",{"context": "runsTable"});
                makeRunsTable(that, function (err, data) {
                    if (err) that.trigger("error", err);
                    else {
                        that.runsTable = data;
                        that.trigger("change",{"context": "runsTable"});
                    }
                });
            },
            makeSurveysTable: function () {
                var that = this;
                that.trigger("init",{"context": "surveysTable"});
                makeSurveysTable(that, function (err, data) {
                    if (err) that.trigger("error", err);
                    else {
                        that.surveysTable = data;
                        that.trigger("change",{"context": "surveysTable"});
                    }
                });
            }
        });

    }
    module.exports.init = reportViewResourcesInit;
});

