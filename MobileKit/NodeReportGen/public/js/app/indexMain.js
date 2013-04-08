// indexMain.js
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
        'localStorage': assets + 'js/lib/backbone.localStorage-min',
        'jquery.dataTables': assets + 'js/lib/jquery.dataTables.min',
        'jquery.generateFile': assets + 'js/lib/jquery.generateFile',
        'jquery.timezone-picker': assets + 'js/lib/jquery.timezone-picker.min',
        'jquery.maphilight': assets + 'js/lib/jquery.maphilight.min',
        'jstz:': assets + 'js/lib/jstz.min',
        'jquery-ui': assets + 'js/lib/jquery-ui-1.10.2.custom.min',
        'jquery.datetimeentry': assets + 'js/lib/jquery.datetimeentry',
        'jquery.mousewheel': assets + 'js/lib/jquery.mousewheel.min',
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
        'jquery.jsonp': {
            deps: ['jquery']
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
