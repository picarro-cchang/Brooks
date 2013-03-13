/*global before, beforeEach, console, describe, it, require  */

'use strict';
require("should");
var pv = require("../lib/paramsValidator");
var newParamsValidator = pv.newParamsValidator;
var latlngValidator = pv.latlngValidator;

describe('parameterValidation', function () {
    describe('simpleValidation', function () {
        var options;
        var checkList = [
                {"name": "psys",         "required": true,  "validator": "string"},
                {"name": "identity",     "required": true,  "validator": /[0-9a-fA-F]{32}/},
                {"name": "debug",        "required": false, "validator": "boolean", "default_value": false},
                {"name": "timeout",      "required": false, "validator": "number",  "default_value": 5.0}
        ];

        describe('#checkValidData', function () {
            var mypv;
            before(function () {
                options = {"psys": "mysys", "identity":"1234ABCD1234ABCD1234ABCD1234ABCD",
                           "debug": true};
                mypv = newParamsValidator(options, checkList);
            });
            it('should work with valid data', function() {
                mypv.ok().should.be.true;
                mypv.validate().valid.should.be.true;
            });
            it('should allow access to the normalized values', function() {
                var v = mypv.validate();
                v.normValues.should.have.property("psys", options.psys);
                v.normValues.should.have.property("identity", options.identity);
                v.normValues.should.have.property("debug", true);
                v.normValues.should.have.property("timeout", 5.0);
            });
            it('should allow access via get method', function() {
                mypv.get("psys").should.equal(options.psys);
                mypv.get("identity").should.equal(options.identity);
                mypv.get("debug").should.be.true;
                mypv.get("timeout").should.equal(5.0);
            });
            it('should substitute defaults correctly', function() {
                mypv.get("debug").should.be.true;
                mypv.get("timeout").should.equal(5.0);
            });
        });

        describe('#checkBadType', function () {
            var mypv;
            before(function () {
                options = {"psys": 42, "identity":"1234ABCD1234ABCD1234ABCD1234ABCD"};
                mypv = newParamsValidator(options, checkList);
            });
            it('should recognize bad type', function() {
                mypv.ok().should.be.false;
                mypv.validate().valid.should.be.false;
            });
            it('should report error', function() {
                mypv.errors().should.match(/psys fails type based validation/)
            });
        });

        describe('#checkBadRegex', function () {
            var mypv;
            before(function () {
                options = {"psys": "mysys", "identity":"1234ABCD1234ABCD1234ABCD1234"};
                mypv = newParamsValidator(options, checkList);
            });
            it('should recognize regex does not match', function() {
                mypv.ok().should.be.false;
                mypv.validate().valid.should.be.false;
            });
            it('should report error', function() {
                mypv.errors().should.match(/identity fails regex based validation/)
            });
        });

        describe('#checkMissingParameter', function () {
            var mypv;
            before(function () {
                options = {"psys": "mysys"};
                mypv = newParamsValidator(options, checkList);
            });
            it('should recognize missing parameter', function() {
                mypv.ok().should.be.false;
                mypv.validate().valid.should.be.false;
            });
            it('should report error', function() {
                mypv.errors().should.match(/Required parameter identity missing/)
            });
        });

    });

    describe('returnDefaults', function () {
        function componentsValidator (components) {
            var rpv = newParamsValidator(components,
                [{"name": "baseType", "required":false, "validator": /satellite|map/, "default_value": "map"},
                 {"name": "paths", "required":false, "validator": "boolean", "default_value": false},
                 {"name": "peaks", "required":false, "validator": "boolean", "default_value": false},
                 {"name": "wedges", "required":false, "validator": "boolean", "default_value": false},
                 {"name": "fovs", "required":false, "validator": "boolean", "default_value": false},
                 {"name": "submapGrid", "required":false, "validator": "boolean", "default_value": false}
                ]);
            return rpv.validate();
        }

        function templateTablesValidator (tables) {
            var rpv = newParamsValidator(tables,
                [{"name": "peaksTable", "required":false, "validator": "boolean", "default_value": false},
                 {"name": "surveysTable", "required":false, "validator": "boolean", "default_value": false},
                 {"name": "runsTable", "required":false, "validator": "boolean", "default_value": false}
                ]);
            return rpv.validate();
        }

        function templateSummaryValidator (summary) {
            var rpv = newParamsValidator(summary,
                [{"name": "figures", "required":false, "validator": pv.validateListUsing(componentsValidator), "default_value": []},
                 {"name": "tables", "required":false, "validator": templateTablesValidator, "default_value": templateTablesValidator({}).normValues}
                ]);
            return rpv.validate();
        }
        it('should fill up defaults from empty object', function () {
            var blankInput = templateSummaryValidator({});
            blankInput.valid.should.be.true;
            blankInput.normValues.tables.should.have.property("peaksTable", false);
            blankInput.normValues.tables.should.have.property("surveysTable", false);
            blankInput.normValues.tables.should.have.property("runsTable", false);
            blankInput.normValues.figures.should.be.empty;
        });
    });

    describe('predicateValidation', function() {
        function rectValidator (rect) {
            var rpv = newParamsValidator(rect,
                [{"name": "swCorner", "required":true, "validator": latlngValidator},
                 {"name": "neCorner", "required":true, "validator": latlngValidator},
                 {"name": "color", "required":false, "validator": /#\d{6}/, "default_value": "#00FF00"}
                ]);
            return rpv.validate();
        }
        var options;
        var checkList = [
                {"name": "identity",     "required": true,  "validator": /[0-9a-fA-F]{32}/},
                {"name": "rectangle",    "required": true,  "validator": rectValidator}
        ];

        describe('#checkValidData', function () {
            var mypv;
            before(function () {
                options = {"identity": "f1d0deadf1d0deadf1d0deadf1d0dead",
                           "rectangle": { "swCorner": [10.0, -30.0], "neCorner": [11.0, -29.0] }};
                mypv = newParamsValidator(options, checkList);
            });
            it('should work with valid data', function() {
                mypv.ok().should.be.true;
                mypv.validate().valid.should.be.true;
            });
            it('should allow access to the normalized values', function() {
                var v = mypv.validate();
                v.normValues.identity.should.be.equal(options.identity);
                v.normValues.rectangle.swCorner.should.eql(options.rectangle.swCorner);
                v.normValues.rectangle.neCorner.should.eql(options.rectangle.neCorner);
                v.normValues.rectangle.color.should.equal("#00FF00");
            });
            it('should allow access via get method', function() {
                mypv.get("identity").should.equal(options.identity);
                mypv.get("rectangle").swCorner.should.eql(options.rectangle.swCorner);
                mypv.get("rectangle").neCorner.should.eql(options.rectangle.neCorner);
                mypv.get("rectangle").color.should.equal("#00FF00");
            });
        });

        describe('#checkBadParams', function () {
            var mypv;
            before(function () {
                options = {"identity": "f1d0deadf1d0deadf1d0deadf1d0dead",
                           "rectangle": { "swCorner": 42 }};
                mypv = newParamsValidator(options, checkList);
            });
            it('should recognize bad data', function() {
                mypv.ok().should.be.false;
                mypv.validate().valid.should.be.false;
            });
            it('should report errors correctly', function() {
                var errors = mypv.errors();
                errors.indexOf("Parameter rectangle fails predicate based validation").should.not.be.below(0);
                errors.indexOf("Parameter swCorner fails predicate based validation").should.not.be.below(0);
                errors.indexOf("Required parameter neCorner missing").should.not.be.below(0);
            });
        });
    });

    describe('listValidation', function() {
        function rectValidator (rect) {
            var rpv = newParamsValidator(rect,
                [{"name": "swCorner", "required":true, "validator": latlngValidator},
                 {"name": "neCorner", "required":true, "validator": latlngValidator},
                 {"name": "color", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value": "#00FF00"}
                ]);
            return rpv.validate();
        }
        var options;
        var checkList = [
                {"name": "identity",     "required": true,  "validator": /[0-9a-fA-F]{32}/},
                {"name": "rectangles",   "required": true,  "validator": pv.validateListUsing(rectValidator)}
        ];

        describe('#checkValidData', function () {
            var mypv;
            before(function () {
                options = {"identity": "f1d0deadf1d0deadf1d0deadf1d0dead",
                           "rectangles": [
                                { "swCorner": [10.0, -30.0], "neCorner": [11.0, -29.0] },
                                { "swCorner": [8.0, -35.0], "neCorner": [9.0, -34.0], "color": "#FF00FF" }
                            ]};
                mypv = newParamsValidator(options, checkList);
            });
            it('should work with valid data', function() {
                mypv.ok().should.be.true;
                mypv.validate().valid.should.be.true;
            });
            it('should allow access to the normalized values', function() {
                var v = mypv.validate();
                v.normValues.identity.should.be.equal(options.identity);
                v.normValues.rectangles[0].swCorner.should.eql(options.rectangles[0].swCorner);
                v.normValues.rectangles[1].swCorner.should.eql(options.rectangles[1].swCorner);
                v.normValues.rectangles[0].neCorner.should.eql(options.rectangles[0].neCorner);
                v.normValues.rectangles[1].neCorner.should.eql(options.rectangles[1].neCorner);
                v.normValues.rectangles[0].color.should.equal("#00FF00");
                v.normValues.rectangles[1].color.should.equal("#FF00FF");
            });
        });
        describe('#checkBadParams', function () {
            var mypv;
            before(function () {
                options = {"identity": "f1d0deadf1d0deadf1d0deadf1d0dead",
                           "rectangles": [
                                { "neCorner": [11.0, -29.0] },
                                { "swCorner": [8.0, -35.0], "neCorner": 123.0, "color": "#FF00FF" }
                            ]};
                mypv = newParamsValidator(options, checkList);
            });
            it('should recognize bad data', function() {
                mypv.ok().should.be.false;
                mypv.validate().valid.should.be.false;
            });
            it('should report errors correctly', function() {
                var errors = mypv.errors();
                errors.indexOf("Parameter rectangles fails predicate based validation").should.not.be.below(0);
                errors.indexOf("0: Required parameter swCorner missing").should.not.be.below(0);
                errors.indexOf("1: Parameter neCorner fails predicate based validation").should.not.be.below(0);
                errors.indexOf("1:   Invalid latitude, longitude pair").should.not.be.below(0);
            });
        });
    });
});
