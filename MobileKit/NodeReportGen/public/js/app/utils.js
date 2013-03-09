/* utils.js provides utilities for rendering reports */

define ([],
function () {
    'use strict';
    function hex2RGB(h) {
        var r, g, b;
        if (h.charAt(0)=="#") {
            r = parseInt(h.substring(1,3),16);
            g = parseInt(h.substring(3,5),16);
            b = parseInt(h.substring(5,7),16);
            return [r,g,b];
        }
        else return false;
    }

    function dec2hex(i,nibbles) {
        // Convert unsigned integer to hexadecimal of specified length with zero padding
        return (i+Math.pow(2,4*nibbles)).toString(16).substr(-nibbles).toUpperCase();
    }

    function colorTuple2Hex(colors) {
        var hexStr = [];
        for (var i=0; i<colors.length; i++) {
            hexStr.push(dec2hex(colors[i],2));
        }
        return hexStr.join("");
    }

    function getDateTime(d){
        // padding function
        var s = function(a,b) { return(1e15+a+"").slice(-b); };
        return d.getUTCFullYear() +
            s(d.getUTCMonth()+1,2) +
            s(d.getUTCDate(),2) + 'T' +
            s(d.getUTCHours(),2) +
            s(d.getUTCMinutes(),2) +
            s(d.getUTCSeconds(),2);
    }

    return { "hex2RGB": hex2RGB,
             "dec2hex": dec2hex,
             "colorTuple2Hex": colorTuple2Hex,
             "getDateTime": getDateTime };
});
