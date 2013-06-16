/* cnsnt.js provides constants */
/*global module, require */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    module.exports = {
        clearStatusLine: function () { window.status = ''; },
        defaultSwathColor: [0,0,255],
        DTR: Math.PI/180.0,
        EARTH_RADIUS: 6378100,
        MAX_LAYERS: 16,
        MAX_OFFSETS: 0.01,
        RTD: 180.0/Math.PI,
        setDoneStatus: function () { window.status = 'done'; }
    };
});
