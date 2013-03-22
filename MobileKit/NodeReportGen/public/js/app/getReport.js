// getReport.js
/*global console, requirejs, TEMPLATE_PARAMS */

define(['jquery', 'underscore', 'backbone', 'app/geohash', 'app/reportGlobals', 'app/cnsnt',
        'app/makePeaks', 'app/makeWedges', 'app/newPathsMaker','app/makePeaksTable',
        'app/makeRunsTable', 'app/makeSurveysTable', 'app/makeSubmapGrid', 'app/newMultiCanvas',
        'jquery-migrate', 'json2',
        'bootstrap-modal', 'bootstrap-dropdown', 'bootstrap-spinedit', 'bootstrap-transition',
        'jquery.dataTables', 'jquery.ba-bbq'],

function ($, _, Backbone, gh, REPORT, CNSNT,
          makePeaks, makeWedges, newPathsMaker, makePeaksTable,
          makeRunsTable, makeSurveysTable, makeSubmapGrid, newMultiCanvas) {
    'use strict';

    var instructionsLoaded = false;

    function formatNumberLength(num, length) {
        // Zero pads a number to the specified length
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    function init() {

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
                    "timezone": "GMT"
                };
            }
        });

        REPORT.ReportTables = Backbone.Model.extend({
            defaults: {
                "peaksTable": false,
                "surveysTable": false,
                "runsTable": false
            }
        });

        REPORT.PageComponent = Backbone.Model.extend({
            defaults: {
                "baseType": "map",
                "paths": false,
                "peaks": false,
                "wedges": false,
                "fovs": false,
                "submapLegend": false
            }
        });

        REPORT.PageComponents = Backbone.Collection.extend({
            model: REPORT.PageComponent
        });

        REPORT.Run = Backbone.Model.extend({
            defaults: {
                "analyzer": "",
                "startEtm": 0,
                "endEtm": 0,
                "stabClass": "*",
                "peaks": "#00FFFF",
                "wedges": "#FFFF00",
                "fovs": "#00FF00"
            }
        });

        REPORT.Runs = Backbone.Collection.extend({
            model: REPORT.Run
        });

        REPORT.Survey = Backbone.Model.extend({
            defaults: {
                "ANALYZER": "",
                "minetm": 0,
                "maxetm": 0,
                "name": ""
            }
        });

        REPORT.Surveys = Backbone.Collection.extend({
            model: REPORT.Survey
        });

        REPORT.Peak = Backbone.Model.extend({
            defaults: {
                "A": 0.0,
                "C": 0.0,
                "T": 0,
                "P": "",
                "R": 0,
                "S": 0,
                "W": NaN,
                "U": NaN
            }
        });

        REPORT.Peaks = Backbone.Collection.extend({
            loadStage: 'init',
            model: REPORT.Peak,
            initialize: function (models, options) {
                this.peaksRef = options.peaksRef;
            },
            getData: function () {
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
                function next() {
                    var url;
                    if (names.length === 0) {
                        console.log(REPORT.peaks);
                        that.loadStage = 'loaded';
                        that.trigger('loaded');
                    }
                    else {
                        url = that.workDir + '/' + names.shift();
                        $.getJSON(url, function(data) {
                            data.forEach(function (d) { // Can filter by lat-lng limits here
                                that.push(d, {silent:true});
                            });
                            next();
                        });
                    }
                }
            }
        });

        REPORT.Path = Backbone.Model.extend({
            defaults: {
                "E": "",
                "N": 0,
                "P": "",
                "R": 0,
                "S": 0,
                "T": 0
            }
        });

        REPORT.Paths = Backbone.Collection.extend({
            loadStage: 'init',
            model: REPORT.Path,
            initialize: function (models, options) {
                this.pathsRef = options.pathsRef;
            },
            getData: function () {
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
                    that.workDir = '/rest/data/'+that.pathsRef.SUBMIT_KEY.hash+'/'+that.pathsRef.SUBMIT_KEY.dir_name;
                    that.pathsFiles = that.pathsRef.OUTPUTS.FILES;
                    names = that.pathsFiles.slice(0);
                    next();
                }
                function next() {
                    var url;
                    if (names.length === 0) {
                        console.log(REPORT.paths);
                        that.loadStage = 'loaded';
                        that.trigger('loaded');
                    }
                    else {
                        var name = names.shift();
                        var comps = name.split(/[_.]/);
                        var type = comps[0];
                        var survey = +comps[1];
                        var run = +comps[2];
                        url = that.workDir + '/' + name;
                        var processPathData = function(data, fovData) {
                            data.forEach(function (d) {
                                d["N"] = run;
                                d["S"] = survey;
                                var where = gh.decodeGeoHash(d.P);
                                var lat = where.latitude[2];
                                var lng = where.longitude[2];
                                if (lat >= minLat-padLat && lat <= maxLat+padLat &&
                                    lng >= minLng-padLng && lng <= maxLng+padLng) {
                                //if (true) {
                                    //d["id"] = formatNumberLength(survey,5) + "_" +
                                    //          formatNumberLength(run,5) + "_" +
                                    //          formatNumberLength(d["R"],6);
                                    if (d.row in fovData) {
                                        d["E"] = fovData[d.row]["E"];
                                        if (d["P"] !== fovData[d.row]["P"]) alert("Bad FOV data");
                                    }
                                    that.push(d,{silent: true});
                                }
                            });
                            that.trigger('block');
                            next();
                        };
                        if (type === 'path') {
                            $.getJSON(url, function(data) {
                                var fovData = {};
                                var urlFov = url.replace("path", "fov");
                                if ($.inArray(name.replace("path", "fov"),that.pathsFiles) >= 0) {
                                    $.getJSON(urlFov, function(data) {
                                        data.forEach(function (d) {
                                            fovData[d.R] = d;
                                        });
                                        processPathData(data, fovData);
                                    });
                                }
                                else {
                                    processPathData(data, {});
                                }
                            });
                        }
                        else next();
                    }
                }
            }
        });


        REPORT.ReportViewResources = Backbone.View.extend({
            initialize: function () {
                this.listenTo(REPORT.settings, "change", this.settingsChanged);
                this.contexts = {'map':null, 'satellite':null, 'peaks': null, 'fovs': null,
                                 'paths': null, 'wedges': null, 'submapGrid': null };
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
                        that.makePeaksLayer();
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
                this.makePeaksLayer();
                this.makeWedgesLayer();
                this.makePathsLayers();
                this.makePeaksTable();
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
                var submaps = REPORT.settings.get("submaps");
                this.subx = submaps.nx;
                this.suby = submaps.ny;
                var result = makeSubmapGrid(this);
                this.contexts["submapGrid"] = result.context;
                this.submapLinks = result.links;
                this.trigger("change",{"context": "submapGrid"});
            },
            makePeaksLayer: function() {
                var that = this;
                REPORT.peaks.once("loaded", function () {
                    that.peaksData = REPORT.peaks.models;
                    that.peaksMinAmp = REPORT.settings.get("peaksMinAmp");
                    that.fovMinAmp = REPORT.settings.get("fovMinAmp");
                    var result = makePeaks(that);
                    that.contexts["peaks"] = result.context;
                    that.runsData["peaks"] = result.runs;
                    that.surveysData["peaks"] = result.surveys;
                    that.trigger("change",{"context": "peaks"});
                    that.makeRunsTable();
                    that.makeSurveysTable();
                });
                REPORT.peaks.getData();
            },
            makeWedgesLayer: function() {
                var that = this;
                REPORT.peaks.once("loaded", function () {
                    that.peaksData = REPORT.peaks.models;
                    that.peaksMinAmp = REPORT.settings.get("peaksMinAmp");
                    that.contexts["wedges"] = makeWedges(that);
                    that.trigger("change",{"context": "wedges"});
                });
                REPORT.peaks.getData();
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
            makePeaksTable: function () {
                var that = this;
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
                makeSurveysTable(that, function (err, data) {
                    if (err) that.trigger("error", err);
                    else {
                        that.surveysTable = data;
                        that.trigger("change",{"context": "surveysTable"});
                    }
                });
            }
        });

        REPORT.MultiCanvasView = Backbone.View.extend({
            el: $("#container"),
            events: {
                "mousemove canvas": "onMouseMove",
                "click canvas": "onCanvasClick"
            },
            initialize: function () {
                console.log("Initializing MultiCanvasView");
                // this.$el.append('<input type="button" value="Click me">');
                this.multiCanvas = newMultiCanvas(this.options.name, this.$el);
                this.multiCanvas.initLayers();
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
                this.hoverLink = null;
                // REPORT.reportViewResources.on("change",this.repositoryChanged,this);
            },
            addLayer: function(source, padding, layer, caption, show) {
                this.multiCanvas.addLayer(source, padding, layer, caption, show);
            },
            addLayerFromUrl: function(url, padding, layer, caption, show) {
                var that = this;
                var image = new Image();
                image.onload = function () {
                    var ctx = document.createElement("canvas").getContext("2d");
                    ctx.canvas.height = this.height;
                    ctx.canvas.width = this.width;
                    ctx.drawImage(this,0,0);
                    that.addLayer(ctx,padding,layer,caption, show);
                };
                image.src = url;
            },
            onCanvasClick: function(e) {
                if (this.hoverLink) {
                    var link = REPORT.reportViewResources.submapLinks[this.hoverLink];
                    var url = window.location.pathname + '?' + $.param({"swCorner": link.swCorner,
                                             "neCorner": link.neCorner, "name":this.hoverLink });
                    window.open(url);
                }
            },
            onMouseMove: function(e) {
                var offset = this.$el.find("canvas").offset();
                var x = e.pageX - offset.left, y = e.pageY - offset.top;
                var links = REPORT.reportViewResources.submapLinks;
                var keys = _.keys(links);
                for (var i=0; i<keys.length; i++) {
                    var link = links[keys[i]];
                    if (x>=link.linkX-link.linkWidth/2 && x<=link.linkX+link.linkWidth/2 &&
                        y>=link.linkY-link.linkHeight/2 && y<=link.linkY+link.linkHeight/2) {
                        document.body.style.cursor = "pointer";
                        this.hoverLink = keys[i];
                        console.log(keys[i]);
                        break;
                    }
                    else {
                        document.body.style.cursor = "";
                        this.hoverLink = null;
                    }
                }
            },
            repositoryChanged: function(e) {
                switch (e.context) {
                    case 'map':
                        this.addLayer(REPORT.reportViewResources.contexts['map'],[0,0],1,'map');
                        break;
                    case 'satellite':
                        this.addLayer(REPORT.reportViewResources.contexts['satellite'],[0,0],2,'satellite');
                        break;
                    case 'paths':
                        this.addLayer(REPORT.reportViewResources.contexts['paths'],[0,0],3,'paths');
                        break;
                    case 'fovs':
                        this.addLayer(REPORT.reportViewResources.contexts['fovs'],[0,0],4,'fovs');
                        break;
                    case 'wedges':
                        this.addLayer(REPORT.reportViewResources.contexts['wedges'],[0,0],5,'wedges');
                        break;
                    case 'peaks':
                        this.addLayer(REPORT.reportViewResources.contexts['peaks'],[0,0],6,'peaks');
                        break;
                    case 'submapGrid':
                        this.addLayer(REPORT.reportViewResources.contexts['submapGrid'],[0,0],7,'submapGrid');
                        break;
                }
            }
        });

        REPORT.CompositeView = Backbone.View.extend({
            // This is a view consisting of layers from reportViewResources rendered onto a single canvas
            el: $("#container"),
            initialize: function () {
                console.log("Initializing CompositeView");
                this.canvasId = "id_" + this.options.name;
                // this.$el.append('<input type="button" value="Click me">');
                var canvas = '<canvas id="' + this.canvasId + '" style=position:absolute; left:0px; top:0px;"></canvas>';
                this.$el.append(canvas);
                this.context = this.$el.find("canvas")[0].getContext("2d");
                this.layers = this.options.layers;
                this.available = {};
                for (var i=0; i<this.layers.length; i++) this.available[this.layers[i]] = false;
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },

            render: function(padding) {
                var init = false;
                var allLayers = ['map', 'satellite', 'paths', 'fovs', 'wedges', 'peaks', 'submapGrid'];
                for (var i=0; i<allLayers.length; i++) {
                    var layerName = allLayers[i], s;
                    if (layerName in this.available) {
                        s = REPORT.reportViewResources.contexts[layerName];
                        if (!init) {
                            this.context.canvas.width  = s.canvas.width  + 2 * padding[0];
                            this.context.canvas.height = s.canvas.height + 2 * padding[1];
                            this.$el.width(this.context.canvas.width);
                            this.$el.height(this.context.canvas.height);
                            init = true;
                        }
                        this.context.drawImage(s.canvas, padding[0], padding[1]);
                    }
                }
            },

            repositoryChanged: function(e) {
                var allAvailable = true;
                if (e.context in this.available) this.available[e.context] = true;
                for (var l in this.available) allAvailable = allAvailable && this.available[l];
                if (allAvailable) this.render([0,0]);
            }
        });

        REPORT.CompositeViewWithLinks = Backbone.View.extend({
            // This is a view consisting of layers from reportViewResources rendered onto a single canvas
            el: $("#container"),
            events: {
                "mousemove canvas": "onMouseMove",
                "click canvas": "onCanvasClick"
            },
            initialize: function () {
                console.log("Initializing CompositeView");
                this.canvasId = "id_" + this.options.name;
                // this.$el.append('<input type="button" value="Click me">');
                var canvas = '<canvas id="' + this.canvasId + '" style=position:absolute; left:0px; top:0px;"></canvas>';
                this.$el.append(canvas);
                this.context = this.$el.find("canvas")[0].getContext("2d");
                this.hoverLink = null;
                this.layers = this.options.layers;
                this.available = {};
                for (var i=0; i<this.layers.length; i++) this.available[this.layers[i]] = false;
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            render: function(padding) {
                var init = false;
                var allLayers = ['map', 'satellite', 'paths', 'fovs', 'wedges', 'peaks', 'submapGrid'];
                for (var i=0; i<allLayers.length; i++) {
                    var layerName = allLayers[i], s;
                    if (layerName in this.available) {
                        s = REPORT.reportViewResources.contexts[layerName];
                        if (!init) {
                            this.context.canvas.width  = s.canvas.width  + 2 * padding[0];
                            this.context.canvas.height = s.canvas.height + 2 * padding[1];
                            this.$el.width(this.context.canvas.width);
                            this.$el.height(this.context.canvas.height);
                            init = true;
                        }
                        this.context.drawImage(s.canvas, padding[0], padding[1]);
                    }
                }
            },
            onCanvasClick: function(e) {
                if (this.hoverLink) {
                    var link = REPORT.reportViewResources.submapLinks[this.hoverLink];
                    var url = window.location.pathname + '?' + $.param({"swCorner": link.swCorner,
                        "neCorner": link.neCorner, "name": this.hoverLink });
                    window.open(url);
                }
            },
            onMouseMove: function(e) {
                var offset = this.$el.find("canvas").offset();
                var x = e.pageX - offset.left, y = e.pageY - offset.top;
                var links = REPORT.reportViewResources.submapLinks;
                var keys = _.keys(links);
                for (var i=0; i<keys.length; i++) {
                    var link = links[keys[i]];
                    if (x>=link.linkX-link.linkWidth/2 && x<=link.linkX+link.linkWidth/2 &&
                        y>=link.linkY-link.linkHeight/2 && y<=link.linkY+link.linkHeight/2) {
                        document.body.style.cursor = "pointer";
                        this.hoverLink = keys[i];
                        console.log(keys[i]);
                        break;
                    }
                    else {
                        document.body.style.cursor = "";
                        this.hoverLink = null;
                    }
                }
            },
            repositoryChanged: function(e) {
                var allAvailable = true;
                if (e.context in this.available) this.available[e.context] = true;
                for (var l in this.available) allAvailable = allAvailable && this.available[l];
                if (allAvailable) this.render([0,0]);
            }
        });

        REPORT.PeaksTableView = Backbone.View.extend({
            initialize: function () {
                console.log("Initializing PeaksTableView");
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            repositoryChanged: function (e) {
                if (e.context === "peaksTable") {
                    this.$el.html(REPORT.reportViewResources.peaksTable.join("\n"));
                    if (this.options.dataTables === null || this.options.dataTables) {
                        this.$el.find('table').dataTable({
                         "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"});
                    }
                }
            }
        });

        REPORT.RunsTableView = Backbone.View.extend({
            initialize: function () {
                console.log("Initializing RunsTableView");
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            repositoryChanged: function (e) {
                if (e.context === "runsTable") {
                    this.$el.html(REPORT.reportViewResources.runsTable.join("\n"));
                    if (this.options.dataTables === null || this.options.dataTables) {
                        this.$el.find('table').dataTable({
                         "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"});
                    }
                }
            }
        });

        REPORT.SurveysTableView = Backbone.View.extend({
            initialize: function () {
                console.log("Initializing SurveysTableView");
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            repositoryChanged: function (e) {
                if (e.context === "surveysTable") {
                    this.$el.html(REPORT.reportViewResources.surveysTable.join("\n"));
                    if (this.options.dataTables === null || this.options.dataTables) {
                        this.$el.find('table').dataTable({
                         "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>"});
                    }
                }
            }
        });

        REPORT.AppView = Backbone.View.extend({
            el: $("#getReportApp"),
            events: {
                "valueChanged #spinEditAmp": "minAmpChanged",
                "valueChanged #spinEditRows": "submapsChanged",
                "valueChanged #spinEditCols": "submapsChanged"
            },
            initialize: function () {
                console.log($("#spinEditAmp"));
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
            submapsChanged: function (e) {
                console.log("submapsChanged event fired");
                var submaps = {"nx": +$("#spinEditCols")[0].value,"ny":+$("#spinEditRows")[0].value};
                console.log(submaps);
                console.log(REPORT.settings.set({"submaps":submaps}));
            },
            updateMinAmp: function () {
                var minAmp = REPORT.settings.get("peaksMinAmp");
                console.log("Model reports changed minAmp: " + minAmp);
                $('#spinEditAmp').spinedit('setValue', minAmp);
            },
            updateSubmaps: function () {
                var sm = REPORT.settings.get("submaps");
                console.log("Model reports changed submaps: " + sm);
                $('#spinEditRows').spinedit('setValue', sm.ny);
                $('#spinEditCols').spinedit('setValue', sm.nx);
            }
        });

        var Router = Backbone.Router.extend({
            routes: {
                ':settings': 'settings',
                '*catchall': 'func'
            },
            settings: function (par) {
                // Get the settings #/nx=2&ny=2&minAmp=0.03
                REPORT.settings.set({"localSettings":$.deparam.querystring(par)});
                renderPage();
            },
            func: function (actions) {
                REPORT.settings.set({"localSettings":{}});
                renderPage();
            }
        });

        REPORT.settings = new REPORT.Settings();
        var router = new Router();
        Backbone.history.start();
    }



    function normalizeSurveys(surveys,indexName) {
        // Extract only the required fields from each survey and compute an id so that
        //  duplicates are eliminated
        var results = [];
        surveys.forEach(function (survey, i){
            survey = _.pick(survey,_.keys((new REPORT.Survey()).attributes));
            survey.id = survey.name.substring(0,survey.name.lastIndexOf("."));
            survey[indexName] = i;
            results.push(survey);
        });
        return results;
    }

    function readSurveys(data) {
        if (data.SUBTASKS.getPeaksData) {
            REPORT.surveys.add(normalizeSurveys(data.SUBTASKS.getPeaksData.OUTPUTS.META,"peaks"),{"merge": true});
        }
        if (data.SUBTASKS.getAnalysesData) {
            REPORT.surveys.add(normalizeSurveys(data.SUBTASKS.getAnalysesData.OUTPUTS.META,"analyses"),{"merge": true});
        }
        if (data.SUBTASKS.getFovsData) {
            REPORT.surveys.add(normalizeSurveys(data.SUBTASKS.getFovsData.OUTPUTS.META,"paths"),{"merge": true});
        }
    }

    function renderPage() {
        var ticket = TEMPLATE_PARAMS.ticket + '/' + TEMPLATE_PARAMS.ts;
        var qry = TEMPLATE_PARAMS.qry;
        var keyFile = '/' + ticket + '/key.json';
        var settingsKeys = _.keys((new REPORT.Settings()).attributes);
        // $("#canvasesDiv").hide();
        // $("#canvasControlDiv").hide();
        if (!instructionsLoaded) {
            instructionsLoaded = true;
            $.get('/rest/data' + keyFile, function(data) {
                REPORT.settings.set(_.pick(data.INSTRUCTIONS,settingsKeys));

                // Override the corners from the qry parameters if they exist
                if ('swCorner' in qry) {
                    REPORT.settings.set({"swCorner": gh.decodeToLatLng(qry.swCorner), "submaps":{"nx":1, "ny":1}});
                }
                if ('neCorner' in qry) {
                    REPORT.settings.set({"neCorner": gh.decodeToLatLng(qry.neCorner), "submaps":{"nx":1, "ny":1}});
                }
                // Construct the runs collection and the templatate
                REPORT.settings.set({"runs": new REPORT.Runs(data.INSTRUCTIONS.runs)});
                REPORT.settings.set({"template": {"summary": { tables: new REPORT.ReportTables(data.INSTRUCTIONS.template.summary.tables),
                                                               figures: new REPORT.PageComponents(data.INSTRUCTIONS.template.summary.figures)},
                                                  "submaps": { tables: new REPORT.ReportTables(data.INSTRUCTIONS.template.submaps.tables),
                                                               figures: new REPORT.PageComponents(data.INSTRUCTIONS.template.submaps.figures)}}});
                // Construct the surveys collection
                REPORT.surveys = new REPORT.Surveys();
                readSurveys(data);

                console.log(REPORT.settings);
                // Set up the collections for peaks and paths data (to be read from .json files)
                REPORT.peaks = new REPORT.Peaks(null, {peaksRef:data.SUBTASKS.getPeaksData});
                if (data.SUBTASKS.hasOwnProperty("getFovsData")) REPORT.paths = new REPORT.Paths(null, {pathsRef:data.SUBTASKS.getFovsData});
                else REPORT.paths = null;
                // TODO: Update settings with local settings, perhaps with some form
                //  of validation

                // Create a ReportViewResources object to hold the canvases which make the report

                REPORT.reportViewResources = new REPORT.ReportViewResources();

                // Figure out if we are a summary view or a submap view depending on whether the coordinates
                //  are passed in on the command line

                var summary = !('swCorner' in qry) && !('neCorner' in qry);

                if (summary) makePdfReport(REPORT.settings.get("template").summary, qry.name);
                else makePdfReport(REPORT.settings.get("template").submaps, qry.name);
            });
        }
    }

    function makePdfReport(subreport, name) {
        var figureComponents = [ "fovs", "paths", "peaks", "wedges", "submapGrid" ];
        var id, neCorner = REPORT.settings.get("neCorner"), swCorner = REPORT.settings.get("swCorner");
        var title = REPORT.settings.get("title");
        $("#getReportApp").append('<h2 style="text-align:center;">' + title + ' - ' + name + '</h2>');
        $("#getReportApp").append('<div style="container-fluid">');
        $("#getReportApp").append('<div style="row-fluid">');
        $("#getReportApp").append('<div style="span12">');
        $("#getReportApp").append('<p><b>SW Corner: </b>' + swCorner[0].toFixed(5) + ', ' + swCorner[1].toFixed(5) +
                                  ' <b>NE Corner: </b>' + neCorner[0].toFixed(5) + ', ' + neCorner[1].toFixed(5) + '</p>');
        $("#getReportApp").append('<p><b>Min peak amplitude: </b>' + REPORT.settings.get("peaksMinAmp").toFixed(2) +
                                  ' <b>Exclusion radius (m): </b>' + REPORT.settings.get("exclRadius").toFixed(0) + '</p>');
        for (var i=0; i<subreport.figures.models.length; i++) {
            var layers = [];
            var pageComponent = subreport.figures.models[i];
            layers.push(pageComponent.get("baseType"));
            for (var j=0; j<figureComponents.length; j++) {
                if (pageComponent.get(figureComponents[j])) {
                    layers.push(figureComponents[j]);
                }
            }
            var id_fig = 'id_page_' + (i+1) + 'fig';
            $("#getReportApp").append('<div id="' + id_fig + '" class="reportFigure"; style="position:relative;"/>');
            new REPORT.CompositeViewWithLinks({el: $('#' + id_fig), name: id_fig.slice(3), layers:layers.slice(0)});
        }
        if (subreport.tables.get("peaksTable")) {
            id = 'id_peaksTable';
            $("#getReportApp").append('<h2 class="reportTableHeading">Peaks Table</h2>');
            $("#getReportApp").append('<div id="' + id + '" class="reportTable"; style="position:relative;"/>');
            new REPORT.PeaksTableView({el: $('#' + id), dataTables: false});
        }
        if (subreport.tables.get("runsTable")) {
            id = 'id_runsTable';
            $("#getReportApp").append('<h2 class="reportTableHeading">Runs Table</h2>');
            $("#getReportApp").append('<div id="' + id + '" class="reportTable"; style="position:relative;"/>');
            new REPORT.RunsTableView({el: $('#' + id), dataTables: false});
        }
        if (subreport.tables.get("surveysTable")) {
            id = 'id_surveysTable';
            $("#getReportApp").append('<h2 class="reportTableHeading">Surveys Table</h2>');
            $("#getReportApp").append('<div id="' + id + '" class="reportTable"; style="position:relative;"/>');
            new REPORT.SurveysTableView({el: $('#' + id), dataTables: false});
        }
        REPORT.reportViewResources.render();
        $("#getReportApp").append('</div></div></div>');
    }
                /* 
                REPORT.multiCanvasView = new REPORT.MultiCanvasView(
                {   el: $("#multiCanvasDiv"),
                    name: "example1"
                });
                REPORT.figure2 = new REPORT.MultiCanvasView(
                {   el: $("#figure2"),
                    name: "figure2"
                });
                REPORT.figure3 = new REPORT.CompositeView(
                {   el: $("#figure3"),
                    name: "figure3",
                    layers: ['map', 'paths', 'wedges', 'peaks']
                });
                REPORT.figure4 = new REPORT.CompositeView(
                {   el: $("#figure4"),
                    name: "figure4",
                    layers: ['satellite', 'paths', 'wedges', 'peaks', 'fovs']
                });

                REPORT.reportViewResources.render();
                REPORT.peaksTableView = new REPORT.PeaksTableView({el: $("#peaksTable1Div")});
                REPORT.runsTableView = new REPORT.RunsTableView({el: $("#runsTable1Div")});
                REPORT.surveysTableView = new REPORT.SurveysTableView({el: $("#surveysTable1Div")});
                $("#keyContents").html(JSON.stringify(data));
            });
        }
    }
    */
    return { "initialize": function() { $(document).ready(init); }};

});