// reportCanvasViews.js
/*global module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var _ = require('underscore');
    var Backbone = require('backbone');
    var CNSNT = require('app/cnsnt');
    var newMultiCanvas = require('app/newMultiCanvas');
    var REPORT  = require('app/reportGlobals');

    function reportCanvasViewsInit() {
        REPORT.MultiCanvasView = Backbone.View.extend({
            el: $("#container"),
            events: {
                "mousemove canvas": "onMouseMove",
                "click canvas": "onCanvasClick"
            },
            initialize: function () {
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
            onCanvasClick: function() {
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
                    case 'none':
                        this.addLayer(REPORT.reportViewResources.contexts['none'],[0,0],1,'none');
                        break;
                    case 'map':
                        this.addLayer(REPORT.reportViewResources.contexts['map'],[0,0],2,'map');
                        break;
                    case 'satellite':
                        this.addLayer(REPORT.reportViewResources.contexts['satellite'],[0,0],3,'satellite');
                        break;
                    case 'submapGrid':
                        this.addLayer(REPORT.reportViewResources.contexts['submapGrid'],[0,0],4,'submapGrid');
                        break;
                    case 'paths':
                        this.addLayer(REPORT.reportViewResources.contexts['paths'],[0,0],5,'paths');
                        break;
                    case 'fovs':
                        this.addLayer(REPORT.reportViewResources.contexts['fovs'],[0,0],6,'fovs');
                        break;
                    case 'wedges':
                        this.addLayer(REPORT.reportViewResources.contexts['wedges'],[0,0],7,'wedges');
                        break;
                    case 'tokens':
                        this.addLayer(REPORT.reportViewResources.contexts['tokens'],[0,0],8,'tokens');
                        break;
                    case 'analyses':
                        this.addLayer(REPORT.reportViewResources.contexts['analyses'],[0,0],9,'analyses');
                        break;
                    case 'peaks':
                        this.addLayer(REPORT.reportViewResources.contexts['peaks'],[0,0],10,'peaks');
                        break;
                }
            }
        });

        REPORT.CompositeView = Backbone.View.extend({
            // This is a view consisting of layers from reportViewResources rendered onto a single canvas
            el: $("#container"),
            initialize: function () {
                this.docWidth = $(document).width();
                this.docHeight = $(document).height();
                this.scaleFac = 1.0;
                REPORT.usageTracker.use(this, CNSNT.clearStatusLine);
                this.canvasId = "id_" + this.options.name;
                // this.$el.append('<input type="button" value="Click me">');
                var canvas = '<canvas id="' + this.canvasId + '" style=position:absolute; left:0px; top:0px;"></canvas>';
                this.$el.append(canvas);
                this.context = this.$el.find("canvas")[0].getContext("2d");
                this.layers = this.options.layers;
                this.available = {};
                this.done = false;
                for (var i=0; i<this.layers.length; i++) this.available[this.layers[i]] = false;
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            render: function(padding) {
                var init = false;
                var allLayers = ['none', 'map', 'satellite', 'submapGrid', 'paths', 'fovs', 'wedges', 'tokens', 'analyses', 'peaks'];
                for (var i=0; i<allLayers.length; i++) {
                    var layerName = allLayers[i], s;
                    if (layerName in this.available) {
                        s = REPORT.reportViewResources.contexts[layerName];
                        if (!init) {
                            var aspect = 1.2;
                            var actualWidth = s.canvas.width  + 2 * padding[0];
                            var actualHeight = s.canvas.height + 2 * padding[1];
                            this.scaleFac = Math.min.apply(null,[0.95*this.docWidth/actualWidth, 
                                0.95*aspect*this.docWidth/actualHeight]);
                            this.context.canvas.width  = this.scaleFac * actualWidth;
                            this.context.canvas.height = this.scaleFac * actualHeight;
                            init = true;
                            this.$el.width(this.context.canvas.width);
                            this.$el.height(this.context.canvas.height);
                        }
                        this.context.drawImage(s.canvas, padding[0], padding[1], this.context.canvas.width, this.context.canvas.height);
                    }
                }
            },
            repositoryChanged: function(e) {
                if (this.done) return;
                var allAvailable = true;
                if (e.context in this.available) this.available[e.context] = true;
                for (var l in this.available) allAvailable = allAvailable && this.available[l];
                if (allAvailable) {
                    this.render([0,0]);
                    this.done = true;
                    REPORT.usageTracker.release(this, CNSNT.setDoneStatus);
                }
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
                this.docWidth = $(document).width();
                this.docHeight = $(document).height();
                this.scaleFac = 1.0;
                REPORT.usageTracker.use(this, CNSNT.clearStatusLine);
                this.canvasId = "id_" + this.options.name;
                // this.$el.append('<input type="button" value="Click me">');
                var canvas = '<canvas id="' + this.canvasId + '" style=position:absolute; left:0px; top:0px;"></canvas>';
                this.$el.append(canvas);
                this.context = this.$el.find("canvas")[0].getContext("2d");
                this.hoverLink = null;
                this.layers = this.options.layers;
                this.available = {};
                this.done = false;
                for (var i=0; i<this.layers.length; i++) this.available[this.layers[i]] = false;
                this.listenTo(REPORT.reportViewResources,"change",this.repositoryChanged);
            },
            render: function(padding) {
                var init = false;
                var allLayers = ['none', 'map', 'satellite', 'submapGrid', 'paths', 'fovs', 'wedges', 'tokens', 'analyses', 'peaks'];
                for (var i=0; i<allLayers.length; i++) {
                    var layerName = allLayers[i], s;
                    if (layerName in this.available) {
                        s = REPORT.reportViewResources.contexts[layerName];
                        if (!init) {
                            var aspect = 1.2;
                            var actualWidth = s.canvas.width  + 2 * padding[0];
                            var actualHeight = s.canvas.height + 2 * padding[1];
                            this.scaleFac = Math.min.apply(null,[0.95*this.docWidth/actualWidth, 
                                0.95*aspect*this.docWidth/actualHeight]);
                            this.context.canvas.width  = this.scaleFac * actualWidth;
                            this.context.canvas.height = this.scaleFac * actualHeight;
                            init = true;
                            this.$el.width(this.context.canvas.width);
                            this.$el.height(this.context.canvas.height);
                        }
                        this.context.drawImage(s.canvas, padding[0], padding[1], this.context.canvas.width, this.context.canvas.height);
                    }
                }
            },
            onCanvasClick: function() {
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
                    if (x>=this.scaleFac*(link.linkX-link.linkWidth/2) && x<=this.scaleFac*(link.linkX+link.linkWidth/2) &&
                        y>=this.scaleFac*(link.linkY-link.linkHeight/2) && y<=this.scaleFac*(link.linkY+link.linkHeight/2)) {
                        document.body.style.cursor = "pointer";
                        this.hoverLink = keys[i];
                        break;
                    }
                    else {
                        document.body.style.cursor = "";
                        this.hoverLink = null;
                    }
                }
            },
            repositoryChanged: function(e) {
                if (this.done) return;
                var allAvailable = true;
                if (e.context in this.available) this.available[e.context] = true;
                for (var l in this.available) allAvailable = allAvailable && this.available[l];
                if (allAvailable) {
                    this.render([0,0]);
                    this.done = true;
                    REPORT.usageTracker.release(this, CNSNT.setDoneStatus);
                }
            }
        });
    }
    module.exports.init = reportCanvasViewsInit;
});

