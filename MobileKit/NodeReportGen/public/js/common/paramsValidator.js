/* paramsValidator.js provides an object to validate values in a ductionary */
/*global console, module, P3TXT, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var _ = require('underscore');
    require('./P3TXT');

    /****************************************************************************/
    /*  Routines for parameter validation                                       */
    /****************************************************************************/
    function ParamsValidator(paramsDict, checkList, postCheck) {
    //    Fetches parameters from paramsDict and checks if they satisfy checkList.
    //    After this, the optional function postCheck is called to perform any other
    //     validation.
    //
    //    The elements of checkList are objects with the following keys:
    //            (name, required, type_or_predicate_or_regex, default_value)
    //
    //        name:           name of the parameter
    //        required:       Boolean indicating if the parameter must be present in paramsDict
    //        validator:      Used to validate the parameter value. It can be
    //            - A type string: We check using typeof if value is of this type
    //            - A function: This is applied to the value an object with the following keys
    //                "valid": Boolean indicating if value is valid
    //                "errorList": List of strings indicating any errors
    //                "normValues": Normalized values with defaults filled in, etc.
    //            - A regex:  Used to determine if the parameter matches the pattern.
    //        default_value:  If the parameter is not required and is not present, this is the value
    //                         (undefined is used if no default_value is specified)
    //        transform:      If present, the parameter is transformed by this function before use
    //
    //    The validation takes place when the ParamsValidator object is created. Methods are
    //        used to report if validation passed and retrieve error messages. Parameter values
    //        may be retrieved by calling the ParamsValidator object with the parameter name
    //        as the argument.
    //
    //    postCheck(resultDict,errorList) is called with an object with all the normalized validated 
    //     parameters and with the current list of errors. It should push any further errors it 
    //     detects onto errorList

        var resultDict = {};
        var errorList = [];

        _.each(checkList, function (c, i, l) {
            var name = c.name;
            var required = c.required;
            var validator = c.validator;
            var transform = c.transform;
            var default_value = c.default_value;

            if (!_.has(paramsDict, name)) {
                if (!required) {
                    // Use default value
                    resultDict[name] = default_value;
                } else {
                    errorList.push(P3TXT.validator_missing_parameter + name);
                }
            } else {
                var value = paramsDict[name];
                if (!_.isUndefined(transform)) {
                    try {
                        value = transform(value);
                    }
                    catch (e) {
                        errorList.push(P3TXT.validator_fails_transformation + name);
                    }
                }
                // We have a parameter, validate it
                if (_.isUndefined(validator)) {
                        resultDict[name] = value;
                }
                else if (_.isRegExp(validator)) {
                    var matches = validator.exec(value);
                    if (matches && matches[0] === matches.input) {
                        resultDict[name] = value;
                    } else {
                        errorList.push(P3TXT.validator_regex_not_matched + name);
                    }
                }
                else if (_.isFunction(validator)) {
                    var v = validator(value);
                    if (v.valid) {
                        if (_.has(v,'normValues')) resultDict[name] = v.normValues;
                        else resultDict[name] = value;
                    } else {
                        errorList.push(P3TXT.validator_predicate_returns_false + name);
                        if (_.has(v,'errorList')) {
                            v.errorList.forEach(function (e) {
                                errorList.push("  " + e);
                            });
                        }
                    }
                }
                else {
                    if (typeof value === validator) {
                        resultDict[name] = value;
                    } else {
                        errorList.push(P3TXT.validator_wrong_type + name);
                    }
                }

            }
        });
        if (_.isFunction(postCheck)) {
            postCheck(resultDict, errorList);
        }
        this.resultDict = resultDict;
        this.errorList = errorList;
    }

    ParamsValidator.prototype.ok = function() {
        return _.isEmpty(this.errorList);
    };

    ParamsValidator.prototype.errors = function() {
        return this.errorList.join("\n");
    };

    ParamsValidator.prototype.validate = function() {
        return {"valid": _.isEmpty(this.errorList), "errorList":this.errorList, "normValues":this.resultDict};
    };

    ParamsValidator.prototype.get = function(key) {
        return this.resultDict[key];
    };

    function newParamsValidator(paramsDict, checkList, postCheck) {
        return new ParamsValidator(paramsDict, checkList, postCheck);
    }

    /****************************************************************************/
    /*  Conversion of string to Boolean. A useful transform.                    */
    /****************************************************************************/
    function stringToBoolean(string){
        switch(string.toLowerCase()){
            case "true": case "yes": case "1": return true;
            case "false": case "no": case "0": case null: return false;
            default: return Boolean(string);
        }
    }

    /****************************************************************************/
    /*  Validator for a latitude, longitude pair                                */
    /****************************************************************************/
    function latlngValidator(data) {
        try {
            if (data.length == 2 &&
                typeof data[0] === "number" && typeof data[1] === "number" &&
                data[0] >= -90.0 && data[0] <= 90.0 &&
                data[1] >= -180.0 && data[1] <= 180.0) {
                return {"valid": true};
            }
            else return {"valid": false, "errorList": [P3TXT.validator_invalid_latlng]};
        }
        catch (e) {
            return {"valid": false, "errorList": [P3TXT.validator_invalid_latlng]};
        }
    }

    /****************************************************************************/
    /*  Wrap a validator of an entity to give a validator for a list of zero    */
    /*   or more of the entity                                                  */
    /****************************************************************************/
    function validateListUsing(validator) {
        function listValidator(data) {
            var errorList = [], normValues = [];
            try {
                for (var i=0; i<data.length; i++) {
                    var r = data[i];
                    var v = validator(r);
                    if (v.valid) {
                        normValues.push(v.normValues);
                    }
                    else {
                        for (var j=0; j<v.errorList.length; j++) {
                            var e = v.errorList[j];
                            errorList.push(i + ': ' + e);
                        }
                        normValues.push(null);
                    }
                }
                if (_.isEmpty(errorList)) return {"valid": true, "normValues": normValues};
                else return {"valid": false, "errorList": errorList, "normValues": normValues};
            }
            catch (err) {
                return {"valid": false, "errorList": [err.message], "normValues": []};
            }
        }
        return listValidator;
    }

    exports.latlngValidator = latlngValidator;
    exports.newParamsValidator = newParamsValidator;
    exports.stringToBoolean = stringToBoolean;
    exports.validateListUsing = validateListUsing;

});
