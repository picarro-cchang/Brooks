// dashboardInstructions.js
/*global alert, ASSETS, console, FileReader, module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

var assets = ASSETS ? ASSETS : '/';
define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var _ = require('underscore');
    var Backbone = require('backbone');
    var cjs = require('common/canonical_stringify');
    var DASHBOARD = require('app/dashboardGlobals');
    var iv = require('common/instructionsValidator');
    var tableFuncs = require('app/tableFuncs');
    require('jquery-migrate'),
    require('jquery-ui');
    require('jquery.maphilight');
    require('jquery.timezone-picker');
    require('jquery.datetimeentry');
    require('jquery.generateFile');
    require('jquery.mousewheel');
    require('bootstrap-modal');
    require('bootstrap-dropdown');
    require('bootstrap-spinedit');
    require('bootstrap-transition');

    // ============================================================================
    //  Handlers for special table fields
    // ============================================================================
    function boolToIcon(value) {
        var name = (value) ? ("icon-ok") : ("icon-remove");
        return (undefined !== value) ? '<i class="' + name + '"></i>' : '';
    }

    function editTime(s,b) {
        // For editing we only want YYYY-MM-DD HH:MM
        var ts = b.localTime.match(/\d{4}[-]\d{2}[-]\d{2} \d{2}:\d{2}/);
        $(s).val(ts);
    }

    function extractLocal(x) {
        return x.localTime;
    }


    function formatNumberLength(num, length) {
        // Zero pads a number to the specified length
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    function insertLocal(v) {
        return {localTime: v, timezone: DASHBOARD.timezone};
    }

    function makeColorPatch(value) {
        var result;
        if (value === "None") {
            result = "None";
        }
        else {
            result = '<div style="width:15px;height:15px;border:1px solid #000;margin:0 auto;';
            result += 'background-color:' + value + ';"></div>';
        }
        return (undefined !== value) ? result : '';
    }

    function parseFloats(value) {
        var coords = value.split(","), i;
        for (i = 0; i < coords.length; i++) {
            coords[i] = parseFloat(coords[i]);
        }
        return coords;
    }

    // ============================================================================
    //  Definitions of tables which can be edited by the user
    // ============================================================================
    // We store start and end times as an objects with keys posixTime, localTime and timezone. We call the functions
    //  toLocalTime as needed to convert the posixTime data in the entire table to local time in the current timezone. 
    //  We also convert to Posix time after a row is edited or updated.

    var runsDefinition = {id: "runTable", layout: [
        {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
        {key: "analyzer", width: "17%", th: "Analyzer", tf: String, eid: "id_analyzer", cf: String},
        {key: "startEtm", width: "17%", th: "Start", tf: extractLocal, eid: "id_start_etm", cf: insertLocal, ef: editTime},
        {key: "endEtm", width: "17%", th: "End", tf: extractLocal, eid: "id_end_etm", cf: insertLocal, ef: editTime},
        {key: "peaks", width: "9%", th: "Peaks", tf: makeColorPatch, eid: "id_marker", cf: String},
        {key: "wedges", width: "9%", th: "LISA", tf: makeColorPatch, eid: "id_wedges", cf: String},
        {key: "analyses", width: "9%", th: "Isotopic", tf: makeColorPatch, eid: "id_analyses", cf: String},
        {key: "fovs", width: "9%", th: "FOV", tf: makeColorPatch, eid: "id_swath", cf: String},
        {key: "stabClass", width: "9%", th: "Stab Class", tf: String, eid: "id_stab_class", cf: String},
        {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
    ],
    vf: function (eidByKey, template, container, onSuccess) {
        return validateRun(eidByKey, template, container, onSuccess);
    },
    cb: function (type, data, rowData, row) {
        // Convert the local time to posix time using the server and update the local time string with the time zone
        if (type === "add" || type === "update") {
            var tz = DASHBOARD.timezone;
            DASHBOARD.Utilities.timezone({tz:tz, timeStrings:[rowData.startEtm.localTime,rowData.endEtm.localTime]},
            function (err) {
                var msg = 'While converting timezone: ' + err;
                alert(msg);
            },
            function (s, result) {
                console.log('While converting timezone: ' + s);
                rowData.startEtm.posixTime = result.posixTimes[0];
                rowData.endEtm.posixTime = result.posixTimes[1];
                rowData.startEtm.localTime = result.timeStrings[0];
                rowData.endEtm.localTime = result.timeStrings[1];
                tableFuncs.setCell(row,"startEtm",rowData.startEtm,runsDefinition);
                tableFuncs.setCell(row,"endEtm",rowData.endEtm,runsDefinition);
            });
        }
        console.log(data);
    }};

    var submapsDefinition = {id: "submapstable", layout: [
        {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
        {key: "baseType", width: "21%", th: "Type", tf: String, eid: "id_submaps_type", cf: String},
        {key: "paths", width: "15%", th: "Paths", tf: boolToIcon, eid: "id_submaps_paths",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "peaks", width: "15%", th: "Peaks", tf: boolToIcon, eid: "id_submaps_peaks",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "wedges", width: "15%", th: "LISA", tf: boolToIcon, eid: "id_submaps_wedges",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "analyses", width: "15%", th: "Isotopic", tf: boolToIcon, eid: "id_summary_analyses",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "fovs", width: "15%", th: "FOV", tf: boolToIcon, eid: "id_submaps_fovs",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
    ]};

    var summaryDefinition = {id: "summarytable", layout: [
        {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
        {key: "baseType", width: "18%", th: "Type", tf: String, eid: "id_summary_type", cf: String},
        {key: "paths", width: "13%", th: "Paths", tf: boolToIcon, eid: "id_summary_paths",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "peaks", width: "13%", th: "Peaks", tf: boolToIcon, eid: "id_summary_peaks",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "wedges", width: "13%", th: "LISA", tf: boolToIcon, eid: "id_summary_wedges",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "analyses", width: "13%", th: "Isotopic", tf: boolToIcon, eid: "id_summary_analyses",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "fovs", width: "13%", th: "FOV", tf: boolToIcon, eid: "id_summary_fovs",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "submapGrid", width: "13%", th: "Grid", tf: boolToIcon, eid: "id_summary_grid",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
    ]};
    // ============================================================================
    //  Definitions of forms used to edit a row of a table
    // ============================================================================
    function editRunsChrome()
    {
        var header, body, footer;
        var controlClass = "input-large";
        var tz = DASHBOARD.timezone;
        header = '<div class="modal-header"><h3>' + "Add new run" + '</h3></div>';
        body   = '<div class="modal-body">';
        body += '<form class="form-horizontal">';
        if (_.isEmpty(DASHBOARD.analyzers)) {
            body += tableFuncs.editControl("Analyzer", tableFuncs.makeInput("id_analyzer", {"class": controlClass,
                    "placeholder": "Name of analyzer"}));
        }
        else {
            body += tableFuncs.editControl("Analyzer", tableFuncs.makeSelect("id_analyzer", {"class": controlClass},
                    DASHBOARD.analyzersDict));
        }
        body += tableFuncs.editControl("Start Time", '<div class="input-append">' + tableFuncs.makeInput("id_start_etm",
                {"class": "input-medium datetimeRange", "placeholder": "YYYY-MM-DD HH:MM"}) + '<span class="add-on">' + tz + '</span></div>');
        body += tableFuncs.editControl("End Time", '<div class="input-append">' + tableFuncs.makeInput("id_end_etm",
                {"class": "input-medium datetimeRange", "placeholder": "YYYY-MM-DD HH:MM"}) + '<span class="add-on">' + tz + '</span></div>');
        body += tableFuncs.editControl("Peaks", tableFuncs.makeSelect("id_marker", {"class": controlClass},
                {"#FFFFFF": "white", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red",
                 "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
        body += tableFuncs.editControl("LISAs", tableFuncs.makeSelect("id_wedges", {"class": controlClass},
                {"#FFFFFF": "white", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red",
                 "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
        body += tableFuncs.editControl("Isotopic", tableFuncs.makeSelect("id_analyses", {"class": controlClass},
                {"#000000": "black", "#00009F": "blue", "#009F00": "green", "#9F0000": "red",
                 "#009F9F": "cyan",  "#9F009F": "magenta", "#9F9F00": "yellow" }));
        body += tableFuncs.editControl("Field of View", tableFuncs.makeSelect("id_swath", {"class": controlClass},
                {"#FFFFFF": "white", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red",
                 "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
        body += tableFuncs.editControl("Stability Class", tableFuncs.makeSelect("id_stab_class", {"class": controlClass},
                {"*": "*: Use reported weather data", "A": "A: Very Unstable", "B": "B: Unstable",
                 "C": "C: Slightly Unstable", "D": "D: Neutral", "E": "E: Slightly Stable", "F": "F: Stable" }));
        body += '</form></div>';
        footer = '<div class="modal-footer">';
        footer += '<p class="validate_tips alert alert-error hide"></p>';
        footer += '<button type="button" class="btn btn-primary btn-ok">' + "OK" + '</button>';
        footer += '<button type="button" class="btn btn-cancel">' + "Cancel" + '</button>';
        footer += '</div>';
        return header + body + footer;
    }

    function editSubmapsChrome()
    {
        var header, body, footer;
        var controlClass = "input-large";
        header = '<div class="modal-header"><h3>' + "Add new figure for each submap" + '</h3></div>';
        body   = '<div class="modal-body">';
        body += '<form class="form-horizontal">';
        body += tableFuncs.editControl("Background Type", tableFuncs.makeSelect("id_submaps_type", {"class": controlClass},
                {"map": "Google map", "satellite": "Satellite"}));
        body += tableFuncs.editControl("Paths", tableFuncs.makeSelect("id_submaps_paths", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Peaks", tableFuncs.makeSelect("id_submaps_peaks", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("LISA", tableFuncs.makeSelect("id_submaps_wedges", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Isotopic", tableFuncs.makeSelect("id_summary_analyses", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Field of View", tableFuncs.makeSelect("id_submaps_fovs", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += '</form></div>';
        footer = '<div class="modal-footer">';
        footer += '<p class="validate_tips alert alert-error hide"></p>';
        footer += '<button type="button" class="btn btn-primary btn-ok">' + "OK" + '</button>';
        footer += '<button type="button" class="btn btn-cancel">' + "Cancel" + '</button>';
        footer += '</div>';
        return header + body + footer;
    }

    function editSummaryChrome()
    {
        var header, body, footer;
        var controlClass = "input-large";
        header = '<div class="modal-header"><h3>' + "Add new figure for summary" + '</h3></div>';
        body   = '<div class="modal-body">';
        body += '<form class="form-horizontal">';
        body += tableFuncs.editControl("Background Type", tableFuncs.makeSelect("id_summary_type", {"class": controlClass},
                {"map": "Google map", "satellite": "Satellite"}));
        body += tableFuncs.editControl("Paths", tableFuncs.makeSelect("id_summary_paths", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Peaks", tableFuncs.makeSelect("id_summary_peaks", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("LISA", tableFuncs.makeSelect("id_summary_wedges", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Isotopic", tableFuncs.makeSelect("id_summary_analyses", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Field of View", tableFuncs.makeSelect("id_summary_fovs", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Submap Grid", tableFuncs.makeSelect("id_summary_grid", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += '</form></div>';
        footer = '<div class="modal-footer">';
        footer += '<p class="validate_tips alert alert-error hide"></p>';
        footer += '<button type="button" class="btn btn-primary btn-ok">' + "OK" + '</button>';
        footer += '<button type="button" class="btn btn-cancel">' + "Cancel" + '</button>';
        footer += '</div>';
        return header + body + footer;
    }

    // ============================================================================
    //  Helper functions for editing runs
    // ============================================================================
    function beforeRunsShow(done)
    {
        // Get the current time as the latest allowed start or end time
        var now;
        var posixTime = (new Date()).valueOf();
        var tz = DASHBOARD.timezone;
        function datetimeRange() {
            if ("" === $('#id_end_etm').val()) $('#id_end_etm').datetimeEntry('setDatetime',now);
            return {minDatetime: null, maxDatetime: now};
        }
        DASHBOARD.Utilities.timezone({tz:tz, posixTimes:[posixTime]},
        function (err) {
            var msg = 'While converting timezone: ' + err;
            alert(msg);
            done(new Error(msg));
        },
        function (s, result) {
            console.log('While converting timezone: ' + s);
            now = result.timeStrings[0];
            now = now.substring(0,now.lastIndexOf(':'));
            console.log(now);
            $.datetimeEntry.setDefaults({spinnerImage: null, datetimeFormat: 'Y-O-D H:M', show24Hours: true });
            $('input.datetimeRange').datetimeEntry({beforeShow:datetimeRange});
            done(null);
        });
    }

    function validateRun(eidByKey,template,container,onSuccess) {
        var regex = /(\d{1,4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})/;

        var numErr = 0;
        var startEtm = $("#"+eidByKey.startEtm).val();
        var endEtm= $("#"+eidByKey.endEtm).val();
        var startMatch = regex.exec(startEtm);
        var endMatch = regex.exec(endEtm);

        if (!startMatch) {
            tableFuncs.addError(eidByKey.startEtm, "Invalid start time");
            numErr += 1;
        }
        if (!endMatch) {
            tableFuncs.addError(eidByKey.endEtm, "Invalid end time");
            numErr += 1;
        }

        if (startMatch && endMatch) {
            for (var i=1; i<=5; i++) {
                var sVal = +startMatch[i];
                var eVal = +endMatch[i];
                if (eVal < sVal) {
                    tableFuncs.addError(eidByKey.endEtm, "End time must be after start time");
                    numErr += 1;
                    break;
                }
                else if (eVal > sVal) break;
            }
            if (i>5) {
                tableFuncs.addError(eidByKey.endEtm, "End time must be after start time");
                numErr += 1;
            }
        }
        if (numErr === 0) onSuccess();
    }

    // ============================================================================
    //  Style the table visually, and so that the rows can be dragged around
    // ============================================================================
    function styleTable(id) {
        $(id + " table").addClass("table table-condensed table-striped table-fmt1");
        $(id + " tbody").addClass("sortable");
        $(".sortable").sortable({helper: tableFuncs.sortableHelper});
    }

    // ============================================================================
    //  Default values for new rows in table
    // ============================================================================
    var initRunRow = {"analyzer": "FCDS2008", "peaks": "#FFFF00", "wedges": "#0000FF", "fovs": "#00FF00",
                      "analyses": "#FF0000", "stabClass": "*"};
    var initSubmapRow  = {type: 'map', paths: false, peaks: false, wedges: false, analyses: false, fovs: false };
    var initSummaryRow = {type: 'map', paths: false, peaks: false, wedges: false, analyses: false, fovs: false, submapGrid: true };

    // ============================================================================
    //  Define models, views and collections for handling instructions
    // ============================================================================

    function dashboardInstructionsInit() {

        // ============================================================================
        //  InstructionsFiles 
        // ============================================================================

        DASHBOARD.InstructionsFileModel = Backbone.Model.extend({
            defaults: {
                file: null,
                contents: "",
                instructions: {}
            }
        });

        DASHBOARD.InstructionsFileView = Backbone.View.extend({
            el: $("#id_instructionsfiles"),
            events: {
                "change .fileinput": "onSelectFile",
                "dragover .file": "onDragOver",
                "drop .file": "onDrop",
                "click #id_make_report": "onMakeReport",
                "click #id_save_instructions": "onSaveInstructions"
            },
            initialize: function () {
                this.instrView = new DASHBOARD.InstructionsView();
                this.inputFile = this.$el.find('.fileinput');
                this.inputFile.wrap('<div />');
                $.event.fixHooks.drop = {props: ["dataTransfer"]};
                this.listenTo(DASHBOARD.instructionsFileModel,"change:file",this.instructionsFileChanged);
            },
            getCurrentInstructions: function () {
                var iv = this.instrView;
                if (iv.getCurrentInstructions()) {
                    if (iv.changed) {
                        // Make sure to send change events
                        DASHBOARD.instructionsFileModel.set({"contents": null}, {silent: true});
                        DASHBOARD.instructionsFileModel.set({"contents": iv.currentContents});
                        DASHBOARD.instructionsFileModel.set({"instructions": null}, {silent: true});
                        DASHBOARD.instructionsFileModel.set({"instructions": iv.currentInstructions});
                        this.$el.find(".file").val('** Instructions not saved **');
                    }
                    return true;
                }
                else return false;
            },
            instructionsFileChanged: function (e) {
                var f = e.get("file");
                var that = this;
                if (f !== null) {
                    this.$el.find(".file").val(f.name);
                    var reader = new FileReader();
                    // Set up the reader to read a text file
                    reader.readAsText(f);
                    reader.onload = function (e) { that.loadFile(e); };
                }
                else this.$el.find(".file").val("");
            },
            loadFile: function (e) {
                this.loadContents(e.target.result);
            },
            loadContents: function (contents) {
                var lines;
                // Remake input element so that change is triggered if same
                //  file is selected next time.
                var old = this.inputFile.parent().html();
                this.inputFile.parent().html(old);
                this.inputFile = this.$el.find('.fileinput');
                // Do simple validation to reject malformed files quickly
                try {
                    lines = contents.split('\n', 16384);
                    // lines.shift();   TODO: Reimplement security stamp for user instruction files
                    var body = lines.join('\n');
                    var instructions = JSON.parse(body);
                    var v = iv.instrValidator(instructions);
                    if (!v.valid) throw new Error('Instructions failed validation\n' + v.errorList.join("\n"));
                    // Make sure to send change events, in case file is reloaded
                    DASHBOARD.instructionsFileModel.set({"contents": null}, {silent: true});
                    DASHBOARD.instructionsFileModel.set({"contents": body});
                    DASHBOARD.instructionsFileModel.set({"instructions": null}, {silent: true});
                    DASHBOARD.instructionsFileModel.set({"instructions": v.normValues});
                }
                catch (err) {
                    alert("Invalid instructions file: " + err.message);
                    DASHBOARD.instructionsFileModel.set({"file": null});
                    return;
                }
                console.log(DASHBOARD.instructionsFileModel.get("contents"));
                console.log(DASHBOARD.instructionsFileModel.get("instructions"));
            },
            onDragOver: function (e) {
                e.stopPropagation();
                e.preventDefault();
                // e.dataTransfer.dropEffect = 'copy';
                console.log("onDragOver");
            },
            onDrop: function (e) {
                e.stopPropagation();
                e.preventDefault();
                var files = e.dataTransfer.files;
                if (files.length > 1) alert('Cannot process more than one file');
                else {
                    for (var i = 0, f; undefined !== (f = files[i]); i++) {
                        // Make sure we trigger a change to reload files, if necessary
                        DASHBOARD.instructionsFileModel.set({"file": null},{silent:true});
                        DASHBOARD.instructionsFileModel.set({"file": f});
                    }
                }
            },
            onMakeReport: function () {
                if (this.getCurrentInstructions()) {
                    var contents = DASHBOARD.instructionsFileModel.get("contents");
                    var instructions = DASHBOARD.instructionsFileModel.get("instructions");
                    var v = iv.instrValidator(instructions);
                    if (!v.valid) {
                        alert('Instructions failed validation\n' + v.errorList.join("\n"));
                        return;
                    }
                    DASHBOARD.SurveyorRpt.submit({'contents': contents, 'user': DASHBOARD.user, 'force': DASHBOARD.force},
                    function (err) {
                        var msg = 'While submitting instructions: ' + err;
                        alert(msg);
                    },
                    function (s, result) {
                        console.log('While submitting instructions: ' + s);
                        var request_ts = result.request_ts;
                        var start_ts = result.rpt_start_ts;
                        var rpt_start_ts_date = new Date(start_ts);
                        var posixTime = rpt_start_ts_date.valueOf();
                        var hash = result.rpt_contents_hash;
                        var dirName = formatNumberLength(rpt_start_ts_date.getTime(),13);
                        var status = result.status;
                        var msg = result.msg;
                        var timezone = instructions.timezone;

                        var job = new DASHBOARD.SubmittedJob({
                                  directory: dirName,
                                  hash: hash,
                                  msg: msg,
                                  rpt_start_ts: result.rpt_start_ts,
                                  shown: true,
                                  startPosixTime: posixTime,
                                  status: status,
                                  timezone: timezone,
                                  title: instructions.title,
                                  user: DASHBOARD.user
                                  });
                        // Check if this has been previously submitted
                        if (request_ts !== start_ts) {
                            alert("This is a duplicate of a previously submitted report");
                            var prev = DASHBOARD.submittedJobs.where({hash: hash, directory: dirName});
                            if (prev.length > 0) {
                                DASHBOARD.jobsView.highLightJob(prev[0]);
                            }
                            else {
                                // This is a pre-existing job, but not on the current user's dashboard
                                //  Find out who originally submitted it 
                                var keyFile = '/' + hash + '/' + dirName + '/key.json';
                                DASHBOARD.SurveyorRpt.resource(keyFile,
                                function (err) {
                                    alert('While getting key file data from ' + keyFile + ': ' + err);
                                },
                                function (status, data) {
                                    console.log('While getting key file data from ' + keyFile + ': ' + status);
                                    job.set({user: data.SUBMIT_KEY.user});
                                    job.addLocalTime(function (err) {
                                        DASHBOARD.submittedJobs.add(job);
                                        job.save();
                                        job.analyzeStatus(err, status, msg);
                                    }, timezone);
                                });
                            }
                        }
                        else {
                            job.addLocalTime(function (err) {
                                DASHBOARD.submittedJobs.add(job);
                                job.save();
                                job.analyzeStatus(err, status, msg);
                            });
                        }
                    });
                }
            },
            onSaveInstructions: function (e) {
                var iv = this.instrView;
                if (iv.getCurrentInstructions()) {
                    var d = new Date();
                    var name = "instructions_" + formatNumberLength(d.getUTCFullYear(),4) +
                                formatNumberLength(d.getUTCMonth()+1,2) + formatNumberLength(d.getUTCDate(),2) +
                               "T" + formatNumberLength(d.getUTCHours(),2) + formatNumberLength(d.getUTCMinutes(),2) +
                               formatNumberLength(d.getUTCSeconds(),2) + '.json';
                    $.generateFile({
                        filename    : name,
                        content     : iv.currentContents,
                        script      : assets + 'rest/download'
                    });
                    e.preventDefault();
                    this.$el.find(".file").val(name);
                }
            },
            onSelectFile: function (e) {
                var files = e.target.files; // FileList object
                if (files.length > 1) alert('Cannot process more than one file');
                else {
                    for (var i = 0, f; undefined !== (f = files[i]); i++) {
                        // Make sure we trigger a change to reload files, if necessary
                        DASHBOARD.instructionsFileModel.set({"file": null},{silent:true});
                        DASHBOARD.instructionsFileModel.set({"file": f});
                    }
                }
            }
        });

        // ============================================================================
        //  Instructions - View contains some form elements, the runs table and
        //   editing of the template
        // ============================================================================

        DASHBOARD.InstructionsView = Backbone.View.extend({
            el: $("#id_instructions"),
            events: {
                "click #id_runs_table_div table button.table-new-row": "newRunsRow",
                "click #id_runs_table_div table button.table-clear": "clearRuns",
                "click #id_runs_table_div tbody button.table-delete-row": "deleteRunsRow",
                "click #id_runs_table_div tbody button.table-edit-row": "editRunsRow",
                "click #id_edit_template": "editTemplate",
                "shown #id_timezoneModal": "onModalShown",
                "click #id_save_timezone": "onTimezoneSaved"
            },
            initialize: function () {
                this.templateView = new DASHBOARD.TemplateView();
                this.listenTo(DASHBOARD.instructionsFileModel, "change:instructions", this.render);
                $('#timezone-image').timezonePicker({
                    target: '#edit-date-default-timezone',
                    countryTarget: '#edit-site-default-country'
                });
                $("#id_reportTimezone").val(DASHBOARD.timezone);
                this.modalContainer = $("#id_modal");
                this.currentInstructions = {};
                this.currentContent = "";
                this.changed = false;
                this.currentValid = false;
                $('#id_peaksMinAmp').spinedit({
                    minimum: 0.03,
                    maximum: 2.0,
                    step: 0.01,
                    value: 0.1,
                    numberOfDecimals: 2
                });
                $('#id_exclRadius').spinedit({
                    minimum: 0,
                    maximum: 30,
                    step: 5,
                    value: 5,
                    numberOfDecimals: 0
                });
                $('#id_submapsRows').spinedit({
                    minimum: 1,
                    maximum: 10,
                    step: 1,
                    value: 1,
                    numberOfDecimals: 0
                });
                $('#id_submapsColumns').spinedit({
                    minimum: 1,
                    maximum: 10,
                    step: 1,
                    value: 1,
                    numberOfDecimals: 0
                });
                $("#id_runs_table_div").html(tableFuncs.makeTable([], runsDefinition));
                styleTable("#id_runs_table_div");

            },
            clearRuns: function (e) {
                $(e.currentTarget).closest("table").find("tbody").empty();
            },
            deleteRunsRow: function (e) {
                $(e.currentTarget).closest("tr").remove();
            },
            editRunsRow: function (e) {
                tableFuncs.editRow($(e.currentTarget).closest("tr"), runsDefinition, this.modalContainer, editRunsChrome, beforeRunsShow);
                console.log(tableFuncs.getTableData(runsDefinition));
            },
            editTemplate: function () {
                this.templateView.editTemplate();
            },
            getCurrentInstructions: function () {
                // Get instructions from GUI elements
                var current = $.extend(true,{},DASHBOARD.instructionsFileModel.get('instructions'));
                var oldContents = cjs(DASHBOARD.instructionsFileModel.get('instructions'),null,2);
                current.title = $("#id_title").val();
                current.makePdf = $("#id_make_pdf").prop("checked");
                current.swCorner = parseFloats($("#id_swCorner").val());
                current.neCorner = parseFloats($("#id_neCorner").val());
                current.timezone = $("#id_reportTimezone").val();
                current.submaps = {nx: +$('#id_submapsColumns').val(), ny: +$('#id_submapsRows').val()};
                current.exclRadius = +$('#id_exclRadius').val();
                current.peaksMinAmp = +$('#id_peaksMinAmp').val();
                current.runs = tableFuncs.getTableData(runsDefinition);
                for (var i=0; i<current.runs.length; i++) {
                    current.runs[i].startEtm = Math.round(current.runs[i].startEtm.posixTime/1000);
                    current.runs[i].endEtm = Math.round(current.runs[i].endEtm.posixTime/1000);
                }
                current.template = this.templateView.currentTemplate;
                var v = iv.instrValidator(current);
                this.currentValid = v.valid;
                if (!v.valid) alert(v.errorList.join("\n"));
                else {
                    this.currentInstructions = v.normValues;
                    this.currentContents = cjs(v.normValues,null,2);
                    this.changed = (oldContents !== this.currentContents);
                }
                return v.valid;
            },
            newRunsRow: function (e) {
                tableFuncs.insertRow(e, runsDefinition, this.modalContainer, editRunsChrome, beforeRunsShow, initRunRow);
            },
            render: function () {
                var instructions = DASHBOARD.instructionsFileModel.get('instructions');
                $("#id_title").val(instructions.title);
                $("#id_make_pdf").prop('checked',instructions.makePdf);
                $("#id_swCorner").val(instructions.swCorner[0] + ', ' + instructions.swCorner[1]);
                $("#id_neCorner").val(instructions.neCorner[0] + ', ' + instructions.neCorner[1]);
                $("#id_reportTimezone").val(instructions.timezone);
                $("#id_peaksMinAmp").spinedit("setValue",instructions.peaksMinAmp);
                $("#id_exclRadius").spinedit("setValue",instructions.exclRadius);
                $("#id_submapsRows").spinedit("setValue",instructions.submaps.ny);
                $("#id_submapsColumns").spinedit("setValue",instructions.submaps.nx);
                // Render the template tables
                this.templateView.loadTemplate();
                this.templateView.render();
                // Set up the runs table. Some translation is needed because of the timezone 
                var tz = DASHBOARD.timezone = instructions.timezone;
                var posixTimes = [];
                instructions.runs.forEach(function (run) {
                    posixTimes.push(1000*run.startEtm);
                    posixTimes.push(1000*run.endEtm);
                });
                DASHBOARD.Utilities.timezone({tz:tz, posixTimes:posixTimes},
                function (err) {
                    var msg = 'While converting timezone: ' + err;
                    alert(msg);
                },
                function (s, result) {
                    console.log('While converting timezone: ' + s);
                    var runsTableData = [];
                    instructions.runs.forEach(function (run) {
                        var row = $.extend({},run);
                        // Get the epoch times converted
                        row.startEtm = {posixTime: result.posixTimes.shift(), localTime: result.timeStrings.shift(), timezone: tz};
                        row.endEtm = {posixTime: result.posixTimes.shift(), localTime: result.timeStrings.shift(), timezone: tz};
                        runsTableData.push(row);
                    });
                    // Display the runs table
                    $("#id_runs_table_div").html(tableFuncs.makeTable(runsTableData, runsDefinition));
                    styleTable("#id_runs_table_div");
                });
                return this;
            },
            onModalShown: function () {
                $("#edit-date-default-timezone").val($("#id_reportTimezone").val()).change();
            },
            onTimezoneSaved: function () {
                // This is the only thing that can change the current time zone
                var tz = DASHBOARD.timezone = $("#edit-date-default-timezone").val();
                $("#id_reportTimezone").val(DASHBOARD.timezone);
                var tableData = tableFuncs.getTableData(runsDefinition);
                var posixTimes = [];
                for (var i=0; i<tableData.length; i++) {
                    var rowData = tableData[i];
                    posixTimes.push(rowData.startEtm.posixTime);
                    posixTimes.push(rowData.endEtm.posixTime);
                }
                DASHBOARD.Utilities.timezone({tz:tz, posixTimes:posixTimes},
                function (err) {
                    var msg = 'While converting timezone: ' + err;
                    alert(msg);
                },
                function (s, result) {
                    console.log('While converting timezone: ' + s);
                    var localTimes = result.timeStrings;
                    for (var i=0; i<tableData.length; i++) {
                        var rowData = tableData[i];
                        rowData.startEtm.localTime = localTimes.shift();
                        rowData.startEtm.timezone = tz;
                        rowData.endEtm.localTime = localTimes.shift();
                        rowData.endEtm.timezone = tz;
                        var row = tableFuncs.getRowByIndex(i, runsDefinition);
                        tableFuncs.setCell(row,"startEtm", rowData.startEtm, runsDefinition);
                        tableFuncs.setCell(row,"endEtm", rowData.endEtm, runsDefinition);
                    }
                });
            }
        });

        // ============================================================================
        //  Template - Allow editing of elements in summary and submap pages
        // ============================================================================

        DASHBOARD.TemplateView = Backbone.View.extend({
            el: $("#id_editTemplateModal"),
            events: {
                "click #id_summary_table_div table button.table-new-row": "newSummaryRow",
                "click #id_summary_table_div table button.table-clear": "clearSummary",
                "click #id_summary_table_div tbody button.table-delete-row": "deleteSummaryRow",
                "click #id_summary_table_div tbody button.table-edit-row": "editSummaryRow",
                "click #id_submaps_table_div table button.table-new-row": "newSubmapsRow",
                "click #id_submaps_table_div table button.table-clear": "clearSubmaps",
                "click #id_submaps_table_div tbody button.table-delete-row": "deleteSubmapsRow",
                "click #id_submaps_table_div tbody button.table-edit-row": "editSubmapsRow",
                "click #id_save_template": "saveTemplate"
            },
            initialize: function () {
                this.modalContainer = $("#id_modal");
                this.currentTemplate = {};
                $("#id_summary_table_div").html(tableFuncs.makeTable([], summaryDefinition));
                styleTable("#id_summary_table_div");
                $("#id_submaps_table_div").html(tableFuncs.makeTable([], submapsDefinition));
                styleTable("#id_submaps_table_div");
                // $("#id_edit_template").click(function () { that.editTemplate(); });
            },
            clearSubmaps: function (e) {
                $(e.currentTarget).closest("table").find("tbody").empty();
            },
            clearSummary: function (e) {
                $(e.currentTarget).closest("table").find("tbody").empty();
            },
            deleteSubmapsRow: function (e) {
                $(e.currentTarget).closest("tr").remove();
            },
            deleteSummaryRow: function (e) {
                $(e.currentTarget).closest("tr").remove();
            },
            editSubmapsRow: function (e) {
                tableFuncs.editRow($(e.currentTarget).closest("tr"), submapsDefinition, this.modalContainer, editSubmapsChrome);
                console.log(tableFuncs.getTableData(submapsDefinition));
            },
            editSummaryRow: function (e) {
                tableFuncs.editRow($(e.currentTarget).closest("tr"), summaryDefinition, this.modalContainer, editSummaryChrome);
                console.log(tableFuncs.getTableData(summaryDefinition));
            },
            editTemplate: function () {
                this.render();
                $("#id_editTemplateModal").modal({show: true, backdrop: "static"});
            },
            loadTemplate: function () {
                var instructions = DASHBOARD.instructionsFileModel.get('instructions');
                this.currentTemplate = $.extend(true,{},instructions.template);
            },
            newSubmapsRow: function (e) {
                tableFuncs.insertRow(e, submapsDefinition, this.modalContainer, editSubmapsChrome, null, initSubmapRow);
            },
            newSummaryRow: function (e) {
                tableFuncs.insertRow(e, summaryDefinition, this.modalContainer, editSummaryChrome, null, initSummaryRow);
            },
            render: function () {
                if (!_.isEmpty(this.currentTemplate)) {
                    var summary = this.currentTemplate.summary;
                    var submaps = this.currentTemplate.submaps;
                    $("#id_summary_analysesTable").prop('checked',summary.tables.analysesTable);
                    $("#id_summary_peaksTable").prop('checked',summary.tables.peaksTable);
                    $("#id_summary_runsTable").prop('checked',summary.tables.runsTable);
                    $("#id_summary_surveysTable").prop('checked',summary.tables.surveysTable);
                    $("#id_submaps_analysesTable").prop('checked',submaps.tables.analysesTable);
                    $("#id_submaps_peaksTable").prop('checked',submaps.tables.peaksTable);
                    $("#id_submaps_runsTable").prop('checked',submaps.tables.runsTable);
                    $("#id_submaps_surveysTable").prop('checked',submaps.tables.surveysTable);
                    $("#id_summary_table_div").html(tableFuncs.makeTable(summary.figures, summaryDefinition));
                    $("#id_submaps_table_div").html(tableFuncs.makeTable(submaps.figures, submapsDefinition));
                    styleTable("#id_summary_table_div");
                    styleTable("#id_submaps_table_div");
                }
                return this;
            },
            saveTemplate: function () {
                // Save the template into this.currentTemplate. Does NOT modify the model
                var summaryData = {figures: tableFuncs.getTableData(summaryDefinition)};
                var submapsData = {figures: tableFuncs.getTableData(submapsDefinition)};
                // Set submapGrid of all submapsData figures to false since these are not editable
                submapsData.figures.forEach(function (fig) { fig.submapGrid = false; });
                summaryData.tables = {analysesTable:$("#id_summary_analysesTable").prop('checked'),
                                      peaksTable:$("#id_summary_peaksTable").prop('checked'),
                                      surveysTable:$("#id_summary_surveysTable").prop('checked'),
                                      runsTable:$("#id_summary_runsTable").prop('checked')};
                submapsData.tables = {analysesTable:$("#id_submaps_analysesTable").prop('checked'),
                                      peaksTable:$("#id_submaps_peaksTable").prop('checked'),
                                      surveysTable:$("#id_submaps_surveysTable").prop('checked'),
                                      runsTable:$("#id_submaps_runsTable").prop('checked')};
                this.currentTemplate = {summary: summaryData, submaps: submapsData};
            }
        });
    }
    module.exports.init = dashboardInstructionsInit;
});

