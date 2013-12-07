requirejs.config({
	baseUrl: '/public/js/test/',
    paths: {
		'mocha' : '/node_modules/mocha/mocha',
		'chai' : '/node_modules/chai/chai',
    },
	/*
	paths: {
		'jquery' : '/app/libs/jquery',
		'underscore' : '/app/libs/underscore',
		'backbone' : '/app/libs/backbone',
		'mocha' : 'libs/mocha',
		'chai' : 'libs/chai',
		'chai-jquery' : 'libs/chai-jquery',
		'models' : '/app/models'
	},
	shim: {
		'underscore': {
			exports: '_'
		},
		'jquery': {
			exports: '$'
		},
		'backbone': {
			deps: ['underscore', 'jquery'],
			exports: 'Backbone'
		},
		'chai-jquery': ['jquery', 'chai']
		},
	*/
	urlArgs: 'bust=' + (new Date()).getTime()
});

requirejs(['mytest'], function () {
    if (window.mochaPhantomJS) { mochaPhantomJS.run(); }
    else { mocha.run(); }
});