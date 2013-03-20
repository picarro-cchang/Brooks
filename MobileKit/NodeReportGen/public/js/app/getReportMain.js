// getReportMain.js
/*global console, requirejs, TEMPLATE_PARAMS */

// See http://backbonetutorials.com/organizing-backbone-using-modules/
requirejs.config({
    //By default load any module IDs from js/lib
    baseUrl: '/js/lib',
    //except, if the module ID starts with "app",
    //load it from the js/app directory. paths
    //config is relative to the baseUrl, and
    //never includes a ".js" extension since
    //the paths config could be for a directory.
    paths: {
        'app': '/js/app',
        'common': '/js/common',
        'jquery-migrate': '/js/lib/jquery-migrate-1.1.1.min',
        'underscore': '/js/lib/underscore-min',
        'backbone': '/js/lib/backbone-min',
        'jquery.dataTables': '/js/lib/jquery.dataTables.min',
        'jquery.ba-bbq': '/js/lib/jquery.ba-bbq.min'
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
        'bootstrap-spinedit': {
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
