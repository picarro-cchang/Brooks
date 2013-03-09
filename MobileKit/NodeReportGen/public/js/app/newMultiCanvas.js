/* layers.js provides functions for manipulating, showing and hiding layers */

define (['jquery', 'app/cnsnt'],
function ($,        CNSNT) {
    'use strict';

    function MultiCanvas(name, container) {
        this.name = name;
        this.container = container;
    }

    MultiCanvas.prototype.initLayers = function () {
        var that = this;
        var id_checkboxDiv = 'id_' + that.name + '_checkboxDiv';
        var id_canvasesDiv = 'id_' + that.name + '_canvasesDiv';
        var id0_base = 'id_' + that.name + '_label';
        var id1_base = 'id_' + that.name + '_check';
        var id2_base = 'id_' + that.name + '_layer';
        function clickMaker(layer) {
            return (function() {
                var $this = $(this);
                var layer = $this.data("layer");
                var id2 = id2_base + layer;
                if ($this.is(":checked")) $('#' + id2).show();
                else $('#' + id2).hide();
            });
        }
        $(that.container).append('<div id="'+ id_checkboxDiv + '" style="position:relative" />');
        $(that.container).append('<div id="'+ id_canvasesDiv + '" style="position:relative" />');
        for (var layer = 1; layer <= CNSNT.MAX_LAYERS; layer++) {
            var id0 = id0_base + layer;
            var id1 = id1_base + layer;
            var id2 = id2_base + layer;
            var elem = '<label id="' + id0 + '" class="checkbox" style="display:inline-block;">' +
                       '<input id="' + id1 + '" type="checkbox" checked="checked"></input></label>';
            var canvas = '<canvas id="' + id2 + '" style="z-index:' + layer +
                         '; position:absolute; left:0px; top:0px;"></canvas>';
            $('#' + id_checkboxDiv).append(elem);
            $('#' + id_canvasesDiv).append(canvas);
            $('#' + id1).data("layer", layer);
            $("label[for='" + id1 + "']").hide();
            $('#' + id0).hide();
            $('#' + id2).data("layer", layer).hide();
            // Make checkbox toggle visibility of layer
            $('#' + id1).click(clickMaker(layer));
        }
    };

    MultiCanvas.prototype.addLayer = function(source, padding, layer, caption, show) {
        var that = this;
        var id_checkboxDiv = 'id_' + that.name + '_checkboxDiv';
        var id_canvasesDiv = 'id_' + that.name + '_canvasesDiv';
        var id0_base = 'id_' + that.name + '_label';
        var id1_base = 'id_' + that.name + '_check';
        var id2_base = 'id_' + that.name + '_layer';
        // Add the image as a new layer in the collection of canvases which make up the
        //  composite map
        if (source) {
            var id0 = id0_base + layer;
            var id1 = id1_base + layer;
            var id2 = id2_base + layer;
            var ctx = $('#' + id2)[0].getContext("2d");
            if (ctx.canvas.width === source.canvas.width + 2 * padding[0] &&
                ctx.canvas.height === source.canvas.height + 2 * padding[1]) { // Replace
                ctx.clearRect(0,0,ctx.canvas.width,ctx.canvas.height);
                ctx.drawImage(source.canvas, padding[0], padding[1]);
            }
            else {
                if (show === undefined) show = true;
                $('#' + id0).append(caption + '&nbsp;&nbsp;').show();
                ctx.canvas.width = source.canvas.width + 2 * padding[0];
                ctx.canvas.height = source.canvas.height + 2 * padding[1];
                ctx.drawImage(source.canvas, padding[0], padding[1]);
            }
            if (show !== undefined) $('#' + id1).attr('checked', show);
            if ($('#' + id1).is(":checked")) $('#' + id2).show();
            if (ctx.canvas.width > $('#' + id_canvasesDiv).width()) $('#' + id_canvasesDiv).width(ctx.canvas.width);
            if (ctx.canvas.height > $('#' + id_canvasesDiv).height()) $('#' + id_canvasesDiv).height(ctx.canvas.height);
        }
    };
/*
    function makeComposite(id, sources, padding) {
        var i, s, init;
        var canvas = '<canvas style="position:absolute; left:0px; top:0px;"></canvas>';
        var $div = $("#" + id);
        $div.append(canvas);
        var ctx = $("#" + id + ">canvas")[0].getContext("2d");
        init = false;
        for (i=0; i<sources.length; i++) {
            s = sources[i];
            if (s) {
                if (!init) {
                    ctx.canvas.width  = s.canvas.width  + 2 * padding[0];
                    ctx.canvas.height = s.canvas.height + 2 * padding[1];
                    $div.width(ctx.canvas.width);
                    $div.height(ctx.canvas.height);
                    init = true;
                }
                ctx.drawImage(s.canvas, padding[0], padding[1]);
            }
        }
    }
*/
    function newMultiCanvas(name, container) {
        return new MultiCanvas(name, container);
    }

    return newMultiCanvas;
});
