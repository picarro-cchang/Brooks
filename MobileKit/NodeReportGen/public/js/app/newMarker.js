/* marker.js provides map markers */

define ([],
function () {
    'use strict';
    /* Generate a marker */
    function Marker(size,fillColor,strokeColor) {
        var ctx = document.createElement("canvas").getContext("2d");
        var b = 1.25 * size;
        var t = 2.0 * size;
        this.nx = 36 * size + 1;
        this.ny = 65 * size + 1;
        this.size = size;
        var r = 0.5 * (this.nx - 1 - t);
        var h = this.ny - 1 - t;
        var phi = Math.PI * 45.0/180.0;
        var theta = 0.5 * Math.PI - phi;
        var xoff = r + 0.5 * t;
        var yoff = r + 0.5 * t;
        var knot = (r - b * Math.sin(phi)) / Math.cos(phi);
        ctx.canvas.width = this.nx;
        ctx.canvas.height = this.ny;
        ctx.beginPath();
        ctx.lineWidth = t;
        ctx.strokeStyle = strokeColor;
        ctx.fillStyle = fillColor;
        ctx.translate(xoff, yoff);
        ctx.moveTo(-b, (h - r));
        ctx.quadraticCurveTo(-b, knot, -r * Math.sin(phi), r * Math.cos(phi));
        ctx.arc(0, 0, r, Math.PI - theta, theta, false);
        ctx.quadraticCurveTo(b, knot, b, (h - r));
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        this.canvas = ctx.canvas;
    }

    Marker.prototype.annotate = function(ctx, x, y, msg, font, textColor) {
        ctx.fillStyle = textColor;
        ctx.font = font;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.drawImage(this.canvas,x-18*this.size,y-65*this.size);
        ctx.fillText(msg,x,y-44.5*this.size);
    };

    return function (size,fillColor,strokeColor) {
        return new Marker(size,fillColor,strokeColor);
    };
});
