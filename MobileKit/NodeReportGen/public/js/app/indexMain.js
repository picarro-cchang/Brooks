// indexMain.js
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
        'jquery.generateFile': '/js/lib/jquery.generateFile',
        'jquery.timezone-picker': '/js/lib/jquery.timezone-picker.min',
        'jquery.maphilight': '/js/lib/jquery.maphilight.min',
        'jstz:': '/js/lib/jstz.min',
        'jquery-ui': '/js/lib/jquery-ui-1.8.20.custom.min',
        'jquery.datetimeentry': '/js/lib/jquery.datetimeentry',
        'jquery.mousewheel': '/js/lib/jquery.mousewheel.min'
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
        'jquery.generateFile': {
            deps: ['jquery']
        },
        'jquery.timezone-picker': {
            deps: ['jquery']
        },
        'jquery.maphilight': {
            deps: ['jquery']
        },
        'jquery-ui': {
            deps: ['jquery']
        },
        'jquery.datetimeentry': {
            deps: ['jquery', 'jquery-ui']
        },
        'jquery.mousewheel': {
            deps: ['jquery', 'jquery-ui']
        },
        'jstz': {
            exports: 'jstz'
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

requirejs(['app/index'],
function (index) {
    'use strict';
    index.initialize();
});
