// getReportMain.js
/*global console, requirejs, TEMPLATE_PARAMS */

// See http://backbonetutorials.com/organizing-backbone-using-modules/
var assets = ASSETS ? ASSETS : '/';
requirejs.config({
    //By default load any module IDs from js/lib
    baseUrl: assets + 'js/lib',
    //except, if the module ID starts with "app",
    //load it from the js/app directory. paths
    //config is relative to the baseUrl, and
    //never includes a ".js" extension since
    //the paths config could be for a directory.
    paths: {
        'app': assets + 'js/app',
        'common': assets + 'js/common',
        'jquery-migrate': assets + 'js/lib/jquery-migrate-1.1.1.min',
        'underscore': assets + 'js/lib/underscore-min',
        'backbone': assets + 'js/lib/backbone-min',
        'jquery.dataTables': assets + 'js/lib/jquery.dataTables.min',
        'jquery.ba-bbq': assets + 'js/lib/jquery.ba-bbq.min',
        'jquery.jsonp': assets + 'js/lib/jquery.jsonp-2.4.0.min'
    },
    shim: {
        'jquery-migrate': {
            deps: ['jquery']
        },
        'bootstrap-modal': {
            deps: ['jquery']
        },
        'bootstrap-dropdown': {
            deps: ['jquery']
        },
        'bootstrap-spinedit-modified': {
            deps: ['jquery', 'jquery-migrate']
        },
        'bootstrap-transition': {
            deps: ['jquery']
        },
        'jquery.dataTables': {
            deps: ['jquery']
        },
        'jquery.ba-bbq': {
            deps: ['jquery']
        },
        'jquery.jsonp': {
            deps: ['jquery']
        },
        'backbone': {
            deps: ['underscore','jquery'],
            exports: "Backbone"
        },
        'underscore' : {
            exports: '_'
        }
    }
});

requirejs(['app/getReport'],
function (getReport) {
    'use strict';
    getReport.initialize();
});
