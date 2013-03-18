// index.js
/*global console, requirejs, TEMPLATE_PARAMS */

define(['jquery', 'underscore', 'backbone', 'app/dashboardGlobals', 'jstz', 'app/newRptGenService',
        'common/rptGenStatus', 'common/instructionsValidator', 'common/canonical_stringify', 'app/tableFuncs',
        'jquery-migrate', 'bootstrap-modal', 'bootstrap-dropdown', 'bootstrap-spinedit', 'bootstrap-transition',
        'jquery.dataTables', 'jquery.generateFile', 'jquery.maphilight', 'jquery.timezone-picker', 'jquery-ui',
        'jquery.datetimeentry', 'jquery.mousewheel'],


function ($, _, Backbone, DASHBOARD, jstz, newRptGenService,
          rptGenStatus, iv, cjs, tableFuncs) {
    'use strict';

    function formatNumberLength(num, length) {
        // Zero pads a number to the specified length
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }


    // ============================================================================
    //  Handlers for special table fields
    // ============================================================================
    function boolToIcon(value) {
        var name = (value) ? ("icon-ok") : ("icon-remove");
        return (undefined !== value) ? '<i class="' + name + '"></i>' : '';
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

    function processComments(value, params) {
        var fieldWidth = 15;
        if (undefined !== params && undefined !== params.fieldWidth) {
            fieldWidth = params.fieldWidth;
        }
        if (value.length <= fieldWidth) {
            return value;
        }
        else {
            return value.substring(0, fieldWidth - 3) + "...";
        }
    }

    function parseFloats(value) {
        var coords = value.split(","), i;
        for (i = 0; i < coords.length; i++) {
            coords[i] = parseFloat(coords[i]);
        }
        return coords;
    }

    function floatsToString(floatArray) {
        var i, result = [];
        for (i = 0; i < floatArray.length; i++) {
            result.push(String(floatArray[i]));
        }
        return result.join(", ");
    }

    function editRunsChrome()
    {
        var header, body, footer;
        var controlClass = "input-large";
        var tz = DASHBOARD.dashboardSettings.get("timezone");
        header = '<div class="modal-header"><h3>' + "Add new run" + '</h3></div>';
        body   = '<div class="modal-body">';
        body += '<form class="form-horizontal">';
        body += tableFuncs.editControl("Analyzer", tableFuncs.makeInput("id_analyzer", {"class": controlClass,
                "placeholder": "Name of analyzer"}));
        body += tableFuncs.editControl("Start Time", '<div class="input-append">' + tableFuncs.makeInput("id_start_etm",
                {"class": "input-medium datetimeRange", "placeholder": "YYYY-MM-DD HH:MM"}) + '<span class="add-on">' + tz + '</span></div>');
        body += tableFuncs.editControl("End Time", '<div class="input-append">' + tableFuncs.makeInput("id_end_etm",
                {"class": "input-medium datetimeRange", "placeholder": "YYYY-MM-DD HH:MM"}) + '<span class="add-on">' + tz + '</span></div>');
        body += tableFuncs.editControl("Peaks", tableFuncs.makeSelect("id_marker", {"class": controlClass},
                {"#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red",
                 "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
        body += tableFuncs.editControl("LISAs", tableFuncs.makeSelect("id_wedges", {"class": controlClass},
                {"None": "None", "#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red",
                 "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
        body += tableFuncs.editControl("Field of View", tableFuncs.makeSelect("id_swath", {"class": controlClass},
                {"#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red",
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

    function beforeRunsShow(done)
    {
        // Get the current time as the latest allowed end time
        var now;
        var posixTime = (new Date()).valueOf();
        var tz = DASHBOARD.dashboardSettings.get('timezone');
        function datetimeRange(input) {
            if ("" === $('#id_end_etm').val()) $('#id_end_etm').datetimeEntry('setDatetime',now);
            return {minDatetime: (input.id=='id_end_etm'   ? $('#id_start_etm').datetimeEntry('getDatetime'): null),
                    maxDatetime: (input.id=='id_start_etm' ? $('#id_end_etm').datetimeEntry('getDatetime'): now )};
        }
        DASHBOARD.rptGenService.get("tz",{tz:tz, posixTimes:[posixTime]},function (err, result) {
            if (err) done(err);
            else {
                now = result.timeStrings[0];
                now = now.substring(0,now.lastIndexOf(':'));
                console.log(now);
                $.datetimeEntry.setDefaults({spinnerImage: null, datetimeFormat: 'Y-O-D H:M', show24Hours: true });
                $('input.datetimeRange').datetimeEntry({beforeShow:datetimeRange});
                done(null);
            }
        });
    }

    var initRunRow = {"analyzer": "FCDS2008", "peaks": "#FFFF00", "wedges": "#0000FF", "fovs": "#00FF00", "stabClass": "*"};

    function validateRun(eidByKey,template,container,onSuccess) {
        var numErr = 0;
        var startEtm = $("#"+eidByKey["startEtm"]).val();
        var endEtm= $("#"+eidByKey["endEtm"]).val();
        if ("" === startEtm) {
            tableFuncs.addError(eidByKey["startEtm"], "Invalid start time");
            numErr += 1;
        }
        if ("" === endEtm) {
            tableFuncs.addError(eidByKey["endEtm"], "Invalid end time");
            numErr += 1;
        }
        if (numErr === 0) {
            onSuccess();
        }
    }

    function extractLocal(x) {
        return x.localTime;
    }

    function insertLocal(v) {
        return {localTime: v, timezone: DASHBOARD.dashboardSettings.get('timezone')};
    }

    function editTime(s,b) {
        // For editing we only want YYYY-MM-DD HH:MM
        var ts = b.localTime.match(/\d{4}[-]\d{2}[-]\d{2} \d{2}:\d{2}/);
        $(s).val(ts);
    }

    // We store start and end times as an objects with keys posixTime, localTime and timezone. We call the functions
    //  toLocalTime as needed to convert the posixTime data in the entire table to local time in the current timezone. 
    //  We also convert to Posix time after a row is edited or updated.

    var runsDefinition = {id: "runTable", layout: [
        {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
        {key: "analyzer", width: "20%", th: "Analyzer", tf: String, eid: "id_analyzer", cf: String},
        {key: "startEtm", width: "20%", th: "Start", tf: extractLocal, eid: "id_start_etm", cf: insertLocal, ef: editTime},
        {key: "endEtm", width: "20%", th: "End", tf: extractLocal, eid: "id_end_etm", cf: insertLocal, ef: editTime},
        {key: "peaks", width: "9%", th: "Peaks", tf: makeColorPatch, eid: "id_marker", cf: String},
        {key: "wedges", width: "9%", th: "LISA", tf: makeColorPatch, eid: "id_wedges", cf: String},
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
            var tz = DASHBOARD.dashboardSettings.get('timezone');
            DASHBOARD.rptGenService.get("tz",{tz:tz, timeStrings:[rowData.startEtm.localTime,rowData.endEtm.localTime]},function (err, result) {
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


    function editSummaryChrome()
    {
        var header, body, footer;
        var controlClass = "input-large";
        var tz = DASHBOARD.dashboardSettings.get("timezone");
        header = '<div class="modal-header"><h3>' + "Add new figure for summary" + '</h3></div>';
        body   = '<div class="modal-body">';
        body += '<form class="form-horizontal">';
        body += tableFuncs.editControl("Background Type", tableFuncs.makeSelect("id_summary_type", {"class": controlClass},
                {"map": "Google map", "satellite": "Satellite"}));
        body += tableFuncs.editControl("Paths", tableFuncs.makeSelect("id_summary_paths", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Peaks", tableFuncs.makeSelect("id_summary_peaks", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("LISA", tableFuncs.makeSelect("id_summary_wedges", {"class": controlClass}, {"true": "Yes", "false": "No"}));
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

    function editSubmapsChrome()
    {
        var header, body, footer;
        var controlClass = "input-large";
        var tz = DASHBOARD.dashboardSettings.get("timezone");
        header = '<div class="modal-header"><h3>' + "Add new figure for each submap" + '</h3></div>';
        body   = '<div class="modal-body">';
        body += '<form class="form-horizontal">';
        body += tableFuncs.editControl("Background Type", tableFuncs.makeSelect("id_submaps_type", {"class": controlClass},
                {"map": "Google map", "satellite": "Satellite"}));
        body += tableFuncs.editControl("Paths", tableFuncs.makeSelect("id_submaps_paths", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Peaks", tableFuncs.makeSelect("id_submaps_peaks", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("LISA", tableFuncs.makeSelect("id_submaps_wedges", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += tableFuncs.editControl("Field of View", tableFuncs.makeSelect("id_submaps_fovs", {"class": controlClass}, {"true": "Yes", "false": "No"}));
        body += '</form></div>';
        footer = '<div class="modal-footer">';
        footer += '<p class="validate_tips alert alert-error hide"></p>';
        footer += '<button type="button" class="btn btn-primary btn-ok">' + "OK" + '</button>';
        footer += '<button type="button" class="btn btn-cancel">' + "Cancel" + '</button>';
        footer += '</div>';
        return header + body + footer;
    }

    var summaryDefinition = {id: "summarytable", layout: [
        {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
        {key: "baseType", width: "21%", th: "Type", tf: String, eid: "id_summary_type", cf: String},
        {key: "paths", width: "15%", th: "Paths", tf: boolToIcon, eid: "id_summary_paths",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "peaks", width: "15%", th: "Peaks", tf: boolToIcon, eid: "id_summary_peaks",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "wedges", width: "15%", th: "LISA", tf: boolToIcon, eid: "id_summary_wedges",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "fovs", width: "15%", th: "FOV", tf: boolToIcon, eid: "id_summary_fovs",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "submapGrid", width: "15%", th: "Grid", tf: boolToIcon, eid: "id_summary_grid",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
    ]};

    var submapsDefinition = {id: "submapstable", layout: [
        {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
        {key: "baseType", width: "24%", th: "Type", tf: String, eid: "id_submaps_type", cf: String},
        {key: "paths", width: "18%", th: "Paths", tf: boolToIcon, eid: "id_submaps_paths",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "peaks", width: "18%", th: "Peaks", tf: boolToIcon, eid: "id_submaps_peaks",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "wedges", width: "18%", th: "LISA", tf: boolToIcon, eid: "id_submaps_wedges",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {key: "fovs", width: "18%", th: "FOV", tf: boolToIcon, eid: "id_submaps_fovs",
          ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
        {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
    ]};

    var initSummaryRow = {type: 'map', paths: false, peaks: false, wedges: false, fovs: false, submapGrid: true };
    var initSubmapRow  = {type: 'map', paths: false, peaks: false, wedges: false, fovs: false };

    function init() {
        DASHBOARD.InstructionsFileModel = Backbone.Model.extend({
            defaults: {
                file: null,
                contents: "",
                instructions: {}
            }
        });

        function styleTable(id) {
            $(id + " table").addClass("table table-condensed table-striped table-fmt1");
            $(id + " tbody").addClass("sortable");
            $(".sortable").sortable({helper: tableFuncs.sortableHelper});
        }

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
                var that = this;
                this.modalContainer = $("#id_modal");
                this.currentTemplate = {};
                $("#id_summary_table_div").html(tableFuncs.makeTable([], summaryDefinition));
                styleTable("#id_summary_table_div");
                $("#id_submaps_table_div").html(tableFuncs.makeTable([], submapsDefinition));
                styleTable("#id_submaps_table_div");
                // $("#id_edit_template").click(function () { that.editTemplate(); });
            },
            editTemplate: function () {
                this.render();
                $("#id_editTemplateModal").modal({show: true, backdrop: "static"});
            },
            saveTemplate: function () {
                // Save the template into this.currentTemplate. Does NOT modify the model
                var instructions = DASHBOARD.instructionsFileModel.get('instructions');
                var summaryData = {figures: tableFuncs.getTableData(summaryDefinition)};
                var submapsData = {figures: tableFuncs.getTableData(submapsDefinition)};
                // Set submapGrid of all submapsData figures to false since these are not editable
                submapsData.figures.forEach(function (fig) { fig.submapGrid = false; });
                summaryData.tables = {peaksTable:$("#id_summary_peaksTable").prop('checked'),
                                      surveysTable:$("#id_summary_surveysTable").prop('checked'),
                                      runsTable:$("#id_summary_runsTable").prop('checked')};
                submapsData.tables = {peaksTable:$("#id_submaps_peaksTable").prop('checked'),
                                      surveysTable:$("#id_submaps_surveysTable").prop('checked'),
                                      runsTable:$("#id_submaps_runsTable").prop('checked')};
                this.currentTemplate = {summary: summaryData, submaps: submapsData};
            },
            loadTemplate: function () {
                var instructions = DASHBOARD.instructionsFileModel.get('instructions');
                this.currentTemplate = $.extend(true,{},instructions.template);
            },
            render: function () {
                if (!_.isEmpty(this.currentTemplate)) {
                    var summary = this.currentTemplate.summary;
                    var submaps = this.currentTemplate.submaps;
                    $("#id_summary_peaksTable").prop('checked',summary.tables.peaksTable);
                    $("#id_summary_runsTable").prop('checked',summary.tables.runsTable);
                    $("#id_summary_surveysTable").prop('checked',summary.tables.surveysTable);
                    $("#id_submaps_peaksTable").prop('checked',submaps.tables.peaksTable);
                    $("#id_submaps_runsTable").prop('checked',submaps.tables.runsTable);
                    $("#id_submaps_surveysTable").prop('checked',submaps.tables.surveysTable);
                    $("#id_summary_table_div").html(tableFuncs.makeTable(summary.figures, summaryDefinition));
                    $("#id_submaps_table_div").html(tableFuncs.makeTable(submaps.figures, submapsDefinition));
                    styleTable("#id_summary_table_div");
                    styleTable("#id_submaps_table_div");
                }
            },
            newSummaryRow: function (e) {
                tableFuncs.insertRow(e, summaryDefinition, this.modalContainer, editSummaryChrome, null, initSummaryRow);
            },
            clearSummary: function (e) {
                $(e.currentTarget).closest("table").find("tbody").empty();
            },
            deleteSummaryRow: function (e) {
                $(e.currentTarget).closest("tr").remove();
            },
            editSummaryRow: function (e) {
                tableFuncs.editRow($(e.currentTarget).closest("tr"), summaryDefinition, this.modalContainer, editSummaryChrome);
                console.log(tableFuncs.getTableData(summaryDefinition));
            },
            newSubmapsRow: function (e) {
                tableFuncs.insertRow(e, submapsDefinition, this.modalContainer, editSubmapsChrome, null, initSubmapRow);
            },
            clearSubmaps: function (e) {
                $(e.currentTarget).closest("table").find("tbody").empty();
            },
            deleteSubmapsRow: function (e) {
                $(e.currentTarget).closest("tr").remove();
            },
            editSubmapsRow: function (e) {
                tableFuncs.editRow($(e.currentTarget).closest("tr"), submapsDefinition, this.modalContainer, editSubmapsChrome);
                console.log(tableFuncs.getTableData(submapsDefinition));
            }
        });

        DASHBOARD.InstructionsView = Backbone.View.extend({
            el: $("#id_instructions"),
            events: {
                "click #id_runs_table_div table button.table-new-row": "newRunsRow",
                "click #id_runs_table_div table button.table-clear": "clearRuns",
                "click #id_runs_table_div tbody button.table-delete-row": "deleteRunsRow",
                "click #id_runs_table_div tbody button.table-edit-row": "editRunsRow",
                "click #id_edit_template": "editTemplate"
            },
            initialize: function () {
                var that = this;
                this.templateView = new DASHBOARD.TemplateView();
                this.listenTo(DASHBOARD.dashboardSettings, "change:timezone", this.onChangeTimezone);
                this.listenTo(DASHBOARD.instructionsFileModel, "change:instructions", this.render);
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
            render: function () {
                var that = this;
                var instructions = DASHBOARD.instructionsFileModel.get('instructions');
                $("#id_title").val(instructions.title);
                $("#id_make_pdf").prop('checked',instructions.makePdf);
                $("#id_swCorner").val(instructions.swCorner[0] + ', ' + instructions.swCorner[1]);
                $("#id_neCorner").val(instructions.neCorner[0] + ', ' + instructions.neCorner[1]);
                $("#id_peaksMinAmp").spinedit("setValue",instructions.peaksMinAmp);
                $("#id_exclRadius").spinedit("setValue",instructions.exclRadius);
                $("#id_submapsRows").spinedit("setValue",instructions.submaps.ny);
                $("#id_submapsColumns").spinedit("setValue",instructions.submaps.nx);
                // Render the template tables
                this.templateView.loadTemplate();
                this.templateView.render();
                // Set up the runs table. Some translation is needed because of the timezone 
                var tz = DASHBOARD.dashboardSettings.get('timezone');
                var posixTimes = [];
                instructions.runs.forEach(function (run) {
                    posixTimes.push(1000*run.startEtm);
                    posixTimes.push(1000*run.endEtm);
                });
                DASHBOARD.rptGenService.get("tz",{tz:tz, posixTimes:posixTimes},function (err, result) {
                    var runsTableData = [];
                    instructions.runs.forEach(function (run) {
                        var row = $.extend({},run);
                        // Get the epoch times coverted
                        row.startEtm = {posixTime: result.posixTimes.shift(), localTime: result.timeStrings.shift(), timezone: tz};
                        row.endEtm = {posixTime: result.posixTimes.shift(), localTime: result.timeStrings.shift(), timezone: tz};
                        runsTableData.push(row);
                    });
                    // Display the runs table
                    $("#id_runs_table_div").html(tableFuncs.makeTable(runsTableData, runsDefinition));
                    styleTable("#id_runs_table_div");
                });
            },
            getCurrentInstructions: function () {
                // Get instructions from GUI elements
                var current = $.extend(true,{},DASHBOARD.instructionsFileModel.get('instructions'));
                var oldContents = cjs(DASHBOARD.instructionsFileModel.get('instructions'),null,2);
                current.title = $("#id_title").val();
                current.makePdf = $("#id_make_pdf").prop("checked");
                current.swCorner = parseFloats($("#id_swCorner").val());
                current.neCorner = parseFloats($("#id_neCorner").val());
                current.submaps = {nx: +$('#id_submapsColumns').val(), ny: +$('#id_submapsRows').val()};
                current.exclRadius = +$('#id_exclRadius').val();
                current.peaksMinAmp = +$('#id_peaksMinAmp').val();
                current.runs = tableFuncs.getTableData(runsDefinition);
                for (var i=0; i<current.runs.length; i++) {
                    current.runs[i].startEtm = Math.round(current.runs[i].startEtm.posixTime/1000);
                    current.runs[i].endEtm = Math.round(current.runs[i].endEtm.posixTime/1000);
                }
                current.timezone = DASHBOARD.dashboardSettings.get("timezone");
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
            editTemplate: function () {
                this.templateView.editTemplate();
            },
            newRunsRow: function (e) {
                tableFuncs.insertRow(e, runsDefinition, this.modalContainer, editRunsChrome, beforeRunsShow, initRunRow);
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
            onChangeTimezone: function () {
                var tableData = tableFuncs.getTableData(runsDefinition);
                var posixTimes = [];
                var tz = DASHBOARD.dashboardSettings.get('timezone');
                for (var i=0; i<tableData.length; i++) {
                    var rowData = tableData[i];
                    posixTimes.push(rowData.startEtm.posixTime);
                    posixTimes.push(rowData.endEtm.posixTime);
                }
                DASHBOARD.rptGenService.get("tz", {tz:tz, posixTimes:posixTimes}, function (err, result) {
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
            onMakeReport: function () {
                var that = this;
                if (this.getCurrentInstructions()) {
                    var contents = DASHBOARD.instructionsFileModel.get("contents");
                    var qryparms = {'qry': 'submit', 'contents': contents};
                    DASHBOARD.rptGenService.get('RptGen', qryparms, function (err, result) {
                        if (err) alert("Bad instructions: " + err);
                        else {
                            var request_ts = result.request_ts;
                            var rpt_start_ts_date = new Date(result.rpt_start_ts);
                            var posixTime = rpt_start_ts_date.valueOf();
                            var hash = result.rpt_contents_hash;
                            var dirName = formatNumberLength(rpt_start_ts_date.getTime(),13);
                            var status = result.status;
                            var job = new DASHBOARD.SubmittedJob({hash: hash,
                                                                  directory: dirName,
                                                                  rpt_start_ts: result.rpt_start_ts,
                                                                  startPosixTime: posixTime,
                                                                  status: status});
                            job.addLocalTime(function (err) {
                                DASHBOARD.submittedJobs.add(job);
                                if (status >= rptGenStatus["DONE"]) that.reportDone(job.cid, status);
                                else setTimeout(function () { that.pollStatus(job.cid); }, 5000);
                            });
                        }
                    });
                }
            },
            pollStatus: function (cid) {
                var that = this;
                var job = _.findWhere(DASHBOARD.submittedJobs.models, {cid: cid});
                var qryparms = {'qry': 'getStatus', 'contents_hash': job.get('hash'),
                                'start_ts': job.get('rpt_start_ts') };
                DASHBOARD.rptGenService.get('RptGen', qryparms, function (err, result) {
                    var status = result.status;
                    if (err) job.set({status:'<b>Error</b> ' + err});
                    else if (status < 0) job.set({status:'<b>Error</b> ' + status});
                    else if (status >= rptGenStatus["DONE"]) that.reportDone(job.cid, status);
                    else setTimeout(function () { that.pollStatus(job.cid); }, 5000);
                });
            },
            reportDone: function (cid, status) {
                var job = _.findWhere(DASHBOARD.submittedJobs.models, {cid: cid});
                var viewUrl = '/getReport/' + job.get('hash') + '/' + job.get('directory');
                var pdfurl = '/rest/data/' +  job.get('hash') + '/' + job.get('directory') + '/report.pdf';
                if (status === rptGenStatus.DONE_WITH_PDF) {
                    job.set({status: '<b><a href="' + viewUrl + '" target="_blank"> View</a><a href="' + pdfurl +
                        '" target="_blank"> PDF</a></b>'});
                }
                else if (status === rptGenStatus.DONE_NO_PDF) {
                    job.set({status: '<b><a href="' + viewUrl + '" target="_blank"> View</a></b>'});
                }
                DASHBOARD.submittedJobs.update(job,{remove:false});
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
            onSaveInstructions: function (e) {
                var that = this;
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
                        script      : '/rest/download'
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
                var contents = e.target.result, lines;
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
                    if (!v.valid) throw new Error('Instructions failed validation');
                    // Make sure to send change events, in case file is reloaded
                    DASHBOARD.instructionsFileModel.set({"contents": null}, {silent: true});
                    DASHBOARD.instructionsFileModel.set({"contents": body});
                    DASHBOARD.instructionsFileModel.set({"instructions": null}, {silent: true});
                    DASHBOARD.instructionsFileModel.set({"instructions": v.normValues});
                }
                catch (err) {
                    alert("Invalid instructions file");
                    DASHBOARD.instructionsFileModel.set({"file": null});
                    return;
                }
                console.log(DASHBOARD.instructionsFileModel.get("contents"));
                console.log(DASHBOARD.instructionsFileModel.get("instructions"));
            }

        });

        DASHBOARD.DashboardSettings = Backbone.Model.extend({
            defaults: {
                timezone: null,
                user: "demo"
            },
            initialize: function () {
                var tz = jstz.determine();  // Get from browser
                this.set({"timezone": tz.name()});
            }
        });

        DASHBOARD.SettingsView = Backbone.View.extend({
            el: $("#id_settings"),
            events: {
                "shown #id_timezoneModal": "onModalShown",
                "click #id_save_timezone": "onTimezoneSaved"
            },
            render: function () {
                $("#id_timezone").val(DASHBOARD.dashboardSettings.get("timezone"));
            },
            onModalShown: function () {
                $("#edit-date-default-timezone").val(DASHBOARD.dashboardSettings.get("timezone")).change();
            },
            onTimezoneSaved: function () {
                DASHBOARD.dashboardSettings.set({"timezone": $("#edit-date-default-timezone").val()});
            },
            initialize: function () {
                $('#timezone-image').timezonePicker({
                    target: '#edit-date-default-timezone',
                    countryTarget: '#edit-site-default-country'
                });
                this.listenTo(DASHBOARD.dashboardSettings,"change:timezone",this.render);
            }
        });

        DASHBOARD.SubmittedJob = Backbone.Model.extend({
            defaults: {
                hash: null,
                directory: null,
                status: 0,
                user: "demo",
                startPosixTime: 0,
                startLocalTime: null
            },
            /*
            set: function (attributes,options) {
                // Fill up local time when a model is created. This unfortunately involves a synchronous
                //  AJAX call. Provide an alternative batch processing of all times in a collection. 
                if (attributes.startPosixTime && !attributes.startLocalTime) {
                    var tz = DASHBOARD.dashboardSettings.get('timezone');
                    var url = '/rest/tz?' + $.param({tz:tz, posixTimes:[attributes.startPosixTime]});
                    var result = JSON.parse($.ajax({type: 'GET', url: url, dataType:'json', async:false}).responseText);
                    attributes.startLocalTime = result.timeStrings[0];
                }
                Backbone.Model.prototype.set.call(this,attributes,options);
            },
            */
            addLocalTime: function (done) {
                var that = this;
                var tz = DASHBOARD.dashboardSettings.get('timezone');
                DASHBOARD.rptGenService.get("tz",{tz:tz, posixTimes:[this.get("startPosixTime")]},function (err, result) {
                    if (err) done(err);
                    else {
                        that.set({"startLocalTime": result.timeStrings[0]});
                        done(null);
                    }
                });
            }
        });

        DASHBOARD.SubmittedJobs = Backbone.Collection.extend({
            initialize: function ()  {
                this.listenTo(DASHBOARD.dashboardSettings, "change:timezone", this.resetTimeZone);
            },
            model: DASHBOARD.SubmittedJob,
            resetTimeZone: function () {
                var that = this;
                var tz = DASHBOARD.dashboardSettings.get('timezone');
                // Batch convert all the startPosixTime values to startLocalTime values using the specified timezone
                //  Triggers a reset when done
                var etmList = [];
                for (var i=0; i<this.length; i++) etmList.push(this.at(i).get('startPosixTime'));
                DASHBOARD.rptGenService.get("tz", {tz:tz, posixTimes:etmList}, function (err, data) {
                    if (!err) {
                        for (var i=0; i<that.length; i++) {
                            var model = that.at(i);
                            model.set({'startLocalTime': data.timeStrings.shift()});
                            that.update(model,{remove: false, silent: true});
                        }
                        that.trigger('reset');
                    }
                });
            }
        });

        DASHBOARD.JobsView = Backbone.View.extend({
            el: $("#id_submittedJobs"),
            events: {
                "click #id_testAdd": "onTestAdd",
                "click #id_testRemove": "onTestRemove",
                "click #id_testUpdate": "onTestUpdate"
            },
            initialize: function () {
                this.$el.find("#id_jobTableDiv").html('<table cellpadding="0" cellspacing="0" border="0" class="display" id="id_example"></table>');
                this.jobTable = $("#id_example").dataTable({
                    "aoColumns": [
                        { "sTitle": "Hash", "mData": "hash", "sClass": "center"},
                        { "sTitle": "Directory", "mData": "directory", "sClass": "center"},
                        { "sTitle": "StartTime", "mData": "startLocalTime", "sClass": "center"},
                        { "sTitle": "Status", "mData": "status", "sClass": "center"},
                        { "sTitle": "User", "mData": "user", "sClass": "center"}
                    ]
                });
                this.cidToRow = {};
                this.listenTo(DASHBOARD.submittedJobs, "add", this.addJob);
                this.listenTo(DASHBOARD.submittedJobs, "remove", this.removeJob);
                this.listenTo(DASHBOARD.submittedJobs, "change", this.changeJob);
                this.listenTo(DASHBOARD.submittedJobs, "reset", this.resetJobs);
                this.addIndex = 0;
            },
            mDataPosixTime: function (source, type, val) {
                switch (type) {
                case 'set':
                    var url = '/rest/tz?' + $.param({tz:"America/Los_Angeles",posixTimes:[source.startPosixTime]});
                    var result = JSON.parse($.ajax({type: 'GET', url: url, dataType:'json', async:false}).responseText);
                    source.timeString = result.timeStrings[0];
                    break;
                case 'display':
                    return source.timeString;
                default:
                    return source.startPosixTime;
                }
            },
            handlePosixTime: function (data, type, row) {
                switch (type) {
                case 'display':
                    var url = '/rest/tz?' + $.param({tz:"America/Los_Angeles",posixTimes:[data]});
                    var result = JSON.parse($.ajax({type: 'GET', url: url, dataType:'json', async:false}).responseText);
                    return result.timeStrings[0];
                default:
                    return data;
                }
            },
            changeJob: function (model) {
                this.jobTable.fnUpdate(model.attributes, this.cidToRow[model.cid]);
            },
            removeJob: function (model) {
                this.jobTable.fnDeleteRow(this.cidToRow[model.cid]);
                delete this.cidToRow[model.cid];
                console.log(this.cidToRow);
            },
            addJob: function (model) {
                this.cidToRow[model.cid] = this.jobTable.fnGetNodes(this.jobTable.fnAddData(model.attributes)[0]);
                console.log(this.cidToRow);
            },
            resetJobs: function () {
                this.render();
            },
            render: function () {
                var that = this;
                this.jobTable.fnClearTable();
                _.forEach(DASHBOARD.submittedJobs.models, function (model) {
                    that.cidToRow[model.cid] = that.jobTable.fnGetNodes(that.jobTable.fnAddData(model.attributes)[0]);
                });
                console.log(that.cidToRow);
            },
            onTestAdd: function () {
                var job = new DASHBOARD.SubmittedJob({hash:this.addIndex++,
                                             directory:Math.random().toString(36).substring(2,8),
                                             startPosixTime:(new Date()).valueOf()});
                job.addLocalTime(function (err) {
                    DASHBOARD.submittedJobs.add(job);
                });
            },
            onTestRemove: function () {
                var n = DASHBOARD.submittedJobs.length;
                if (n > 0) {
                    var which = Math.floor(n * Math.random());
                    console.log("Removing " + DASHBOARD.submittedJobs.at(which).get("hash"));
                    DASHBOARD.submittedJobs.remove(DASHBOARD.submittedJobs.at(which));
                    console.log("Number of rows: " + DASHBOARD.submittedJobs.length);
                }
                else alert("No data to remove");
            },
            onTestUpdate: function () {
                var n = DASHBOARD.submittedJobs.length;
                if (n > 0) {
                    var which = Math.floor(n * Math.random());
                    var model = DASHBOARD.submittedJobs.at(which);
                    console.log("Updating " + model.get("hash"));
                    model.set({"hash":Math.random().toString(36).substring(2,8), "status":Math.floor(Math.random()*100)});
                    DASHBOARD.submittedJobs.update(model,{remove:false});
                    console.log("Number of rows: " + DASHBOARD.submittedJobs.length);
                }
                else alert("No data to update");
            }
        });

        DASHBOARD.rptGenService = newRptGenService({"rptgen_url": "http://localhost:5300"});
        DASHBOARD.dashboardSettings = new DASHBOARD.DashboardSettings();
        DASHBOARD.submittedJobs = new DASHBOARD.SubmittedJobs();
        DASHBOARD.instructionsFileModel = new DASHBOARD.InstructionsFileModel();
        var settingsView = new DASHBOARD.SettingsView();
        var instrFileView = new DASHBOARD.InstructionsFileView();
        var jobsView = new DASHBOARD.JobsView();
        settingsView.render();
        jobsView.render();
    }

    return { "initialize": function () { $(document).ready(init); }};

});