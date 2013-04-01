/* newIsoMarker.js provides isotopic ratio markers */

define ([],
function () {
    'use strict';
    /* Generate a marker */
    function IsoMarker(size,fillColor,strokeColor) {
        var ctx = document.createElement("canvas").getContext("2d");
        var t = 2.0 * size;
        this.nx = 36 * size + 1;
        this.ny = 48 * size + 1;
        this.size = size;
        ctx.canvas.width = this.nx;
        ctx.canvas.height = this.ny;
        ctx.beginPath();
        ctx.lineWidth = t;
        ctx.strokeStyle = strokeColor;
        ctx.fillStyle = fillColor;
        ctx.moveTo(18*size, 0);
        ctx.lineTo(36*size, 24*size);
        ctx.lineTo(36*size, 48*size);
        ctx.lineTo(0, 48*size);
        ctx.lineTo(0, 24*size);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        this.canvas = ctx.canvas;
    }

    IsoMarker.prototype.annotate = function(ctx, x, y, msg, font, textColor) {
        ctx.fillStyle = textColor;
        ctx.font = font;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.drawImage(this.canvas,x-18*this.size,y);
        ctx.fillText(msg,x,y+30*this.size);
    };

    return function (size,fillColor,strokeColor) {
        return new IsoMarker(size,fillColor,strokeColor);
    };
});
