if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var pv = require('./paramsValidator');
    var newParamsValidator = pv.newParamsValidator;
    var validateListUsing = pv.validateListUsing;
    var latlngValidator = pv.latlngValidator;

    function offsetsValidator(data) {
        try {
            if (data.length == 2 &&
                typeof data[0] === "number" && typeof data[1] === "number" &&
                data[0] >= -0.01 && data[0] <= 0.01 &&
                data[1] >= -0.01 && data[1] <= 0.01) {
                return {"valid": true};
            }
            else return {"valid": false, "errorList": ["Invalid latitude, longitude offsets"]};
        }
        catch (e) {
            return {"valid": false, "errorList": ["Invalid latitude, longitude offsets"]};
        }
    }

    function facValidator(fac) {
        var  rpv = newParamsValidator(fac,
            [{"name": "filename", "required": true, "validator": "string"},
             {"name": "hash", "required": true, "validator": /[0-9a-fA-F]{32}/},
             {"name": "offsets", "required": false, "validator": offsetsValidator, "default_value":[0.0,0.0]},
             {"name": "linewidth", "required": false, "validator": "number", "default_value": 2},
             {"name": "linecolor", "required": false, "validator": /#[0-9a-fA-F]{6}/, "default_value": "#000000"},
             {"name": "xpath", "required": false, "validator": "string", "default_value": ".//coordinates"}
            ]);
        return rpv.validate();
    }

    function markersFileValidator(fac) {
        var  rpv = newParamsValidator(fac,
            [{"name": "filename", "required": true, "validator": "string"},
             {"name": "hash", "required": true, "validator": /[0-9a-fA-F]{32}/}
            ]);
        return rpv.validate();
    }

    function runValidator(run) {
        function postCheck(resultDict, errorList) {
            if (resultDict.startEtm >= resultDict.endEtm) {
                errorList.push("Starting time must come before ending time");
            }
        }
        var rpv = newParamsValidator(run,
            [{"name": "analyzer", "required":true, "validator": "string"},
             {"name": "startEtm", "required":true, "validator": "number" },
             {"name": "endEtm", "required":true, "validator": "number" },
             {"name": "stabClass", "required":false,"validator": /[a-fA-F*]/, "default_value":"*"},
             {"name": "peaks", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value":"#FFFF00"},
             {"name": "wedges", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value":"#0000FF"},
             {"name": "analyses", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value":"#FF0000"},
             {"name": "fovs", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value":"#00FF00"}
            ], postCheck);
        return rpv.validate();
    }

    function componentsValidator (components) {
        var rpv = newParamsValidator(components,
            [{"name": "baseType", "required":false, "validator": /satellite|map|none/, "default_value": "map"},
             {"name": "facilities", "required":false, "validator": "boolean", "default_value": false},
             {"name": "paths", "required":false, "validator": "boolean", "default_value": false},
             {"name": "peaks", "required":false, "validator": "boolean", "default_value": false},
             {"name": "markers", "required":false, "validator": "boolean", "default_value": false},
             {"name": "wedges", "required":false, "validator": "boolean", "default_value": false},
             {"name": "analyses", "required":false, "validator": "boolean", "default_value": false},
             {"name": "fovs", "required":false, "validator": "boolean", "default_value": false},
             {"name": "submapGrid", "required":false, "validator": "boolean", "default_value": false}
            ]);
        return rpv.validate();
    }

    function templateTablesValidator (tables) {
        var rpv = newParamsValidator(tables,
            [{"name": "analysesTable", "required":false, "validator": "boolean", "default_value": false},
             {"name": "peaksTable", "required":false, "validator": "boolean", "default_value": false},
             {"name": "surveysTable", "required":false, "validator": "boolean", "default_value": false},
             {"name": "runsTable", "required":false, "validator": "boolean", "default_value": false}
            ]);
        return rpv.validate();
    }

    function templateSummaryValidator (summary) {
        var rpv = newParamsValidator(summary,
            [{"name": "figures", "required":false, "validator": validateListUsing(componentsValidator), "default_value": []},
             {"name": "tables", "required":false, "validator": templateTablesValidator, "default_value": templateTablesValidator({}).normValues}
            ]);
        return rpv.validate();
    }

    function templateSubmapsValidator (submaps) {
        var rpv = newParamsValidator(submaps,
            [{"name": "figures", "required":false, "validator": validateListUsing(componentsValidator), "default_value": []},
             {"name": "tables", "required":false, "validator": templateTablesValidator, "default_value": templateTablesValidator({}).normValues}
            ]);
        return rpv.validate();
    }

    function templateValidator (template) {
        console.log(template);
        var defSummary = templateSummaryValidator({}).normValues;
        var defSubmaps = templateSubmapsValidator({}).normValues;
        var rpv = newParamsValidator(template,
            [{"name": "summary", "required":false, "validator": templateSummaryValidator, "default_value": defSummary},
             {"name": "submaps", "required":false, "validator": templateSubmapsValidator, "default_value": defSubmaps}
            ]);
        return rpv.validate();
    }

    function submapsValidator (submaps) {
        var rpv = newParamsValidator(submaps,
            [{"name": "nx", "required":false, "validator": "number", "default_value": 1},
             {"name": "ny", "required":false, "validator": "number", "default_value": 1}
            ]);
        return rpv.validate();
    }

    function instrValidator(instr) {
        function postCheck(resultDict, errorList) {
            try {
                if (resultDict.swCorner[0] >= resultDict.neCorner[0]) {
                    errorList.push("SW corner latitude must be less than NE corner latitude.");
                }
                if (resultDict.swCorner[1] >= resultDict.neCorner[1]) {
                    errorList.push("SW corner longitude must be less than NE corner longitude.");
                }
            }
            catch(e) {
            }
        }
        var rpv = newParamsValidator(instr,
            [{"name": "title", "required": true, "validator": function(s) {
                var valid = ((typeof s === "string") && s.trim() !== "" );
                if (valid) return {valid: true};
                else return {valid: false, "errorList": ["Title must be a non-empty string"]};
             }},
             {"name": "instructions_type", "required": false, "validator": "string", "default_value": "makeReport"},
             {"name": "makePdf", "required": false, "validator": "boolean", "default_value": false},
             {"name": "swCorner", "required": true, "validator": latlngValidator},
             {"name": "neCorner", "required": true, "validator": latlngValidator},
             {"name": "submaps", "required": false, "validator": submapsValidator, "default_value": {"nx": 1, "ny": 1}},
             {"name": "exclRadius", "required": false, "validator": "number", "default_value": 0},
             {"name": "fovMinAmp", "required": false, "validator": "number", "default_value": 0.03},
             {"name": "fovMinLeak", "required": false, "validator": "number", "default_value": 1.0},
             {"name": "fovNWindow", "required": false, "validator": "number", "default_value": 10},
             {"name": "peaksMinAmp", "required": false, "validator": "number", "default_value": 0.03},
             {"name": "runs", "required": true, "validator": validateListUsing(runValidator)},
             {"name": "markersFiles", "required": false, "validator": validateListUsing(markersFileValidator), "default_value":[]},
             {"name": "facilities", "required": false, "validator": validateListUsing(facValidator), "default_value":[]},
             {"name": "timezone", "required":false, "validator": "string", "default_value": "UTC"},
             {"name": "template", "required": true, "validator": templateValidator}], postCheck);
        return rpv.validate();
    }

    exports.instrValidator = instrValidator;
});
