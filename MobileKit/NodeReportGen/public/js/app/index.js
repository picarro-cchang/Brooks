// getReport.js
/*global console, requirejs, TEMPLATE_PARAMS */

define(['jquery', 'underscore', 'backbone', 'app/dashboardGlobals',
        'jquery-migrate', 'bootstrap-modal', 'bootstrap-dropdown', 'bootstrap-spinedit', 'bootstrap-transition',
        'jquery.dataTables', 'jquery.generateFile'],


function ($, _, Backbone, DASHBOARD) {
    'use strict';

    function formatNumberLength(num, length) {
        // Zero pads a number to the specified length
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    function init() {
        DASHBOARD.InstructionsFileModel = Backbone.Model.extend({
            defaults: {
                file: null,
                instructions: null
            }
        });

        DASHBOARD.InstructionsView = Backbone.View.extend({
            el: $("#instructionsfiles"),
            events: {
                "change .fileinput": "onSelectFile",
                "dragover .file": "onDragOver",
                "drop .file": "onDrop",
                "click #id_make_report": "onMakeReport",
                "click #id_save_instructions": "onSaveInstructions"
            },
            initialize: function () {
                this.inputFile = this.$el.find('.fileinput');
                this.inputFile.wrap('<div />');
                $.event.fixHooks.drop = {props: ["dataTransfer"]};
                this.listenTo(DASHBOARD.instructionsFileModel,"change:file",this.instructionsFileChanged);
            },
            onMakeReport: function() { console.log(DASHBOARD.instructionsFileModel.get("instructions")); },
            onDragOver: function(e) {
                e.stopPropagation();
                e.preventDefault();
                // e.dataTransfer.dropEffect = 'copy';
                console.log("onDragOver");
            },
            onDrop: function(e) {
                e.stopPropagation();
                e.preventDefault();
                var files = e.dataTransfer.files;
                if (files.length > 1) alert('Cannot process more than one file');
                else {
                    for (var i = 0, f; undefined !== (f = files[i]); i++) {
                        DASHBOARD.instructionsFileModel.set({"file": f});
                    }
                }
            },
            onSaveInstructions: function(e) {
                var that = this;
                var d = new Date();
                var name = "instructions_" + formatNumberLength(d.getUTCFullYear(),4) +
                            formatNumberLength(d.getUTCMonth()+1,2) + formatNumberLength(d.getUTCDate(),2) +
                           "T" + formatNumberLength(d.getUTCHours(),2) + formatNumberLength(d.getUTCMinutes(),2) +
                           formatNumberLength(d.getUTCSeconds(),2) + '.json';
                $.generateFile({
                    filename    : name,
                    content     : JSON.stringify(DASHBOARD.instructionsFileModel.get("instructions")),
                    script      : '/rest/download'
                });
                e.preventDefault();
                this.$el.find(".file").val(name);
                console.log("onSaveInstructions"); },
            onSelectFile: function(e) {
                var files = e.target.files; // FileList object
                if (files.length > 1) alert('Cannot process more than one file');
                else {
                    for (var i = 0, f; undefined !== (f = files[i]); i++) {
                        DASHBOARD.instructionsFileModel.set({"file": f});
                    }
                }
            },
            instructionsFileChanged: function(e) {
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
                // Do simple validation to reject malformed files quickly
                try {
                    lines = contents.split('\n', 1024);
                    // lines.shift();   TODO: Reimplement security stamp for user instruction files
                    DASHBOARD.instructionsFileModel.set({"instructions": JSON.parse(lines.join('\n'))});
                }
                catch (err) {
                    alert("Invalid instructions file");
                    DASHBOARD.instructionsFileModel.set({"file": null});
                    // Remake input element so that change is triggered if same
                    //  file is selected next time.
                    var old = this.inputFile.parent().html();
                    this.inputFile.parent().html(old);
                    this.inputFile = this.$el.find('.fileinput');
                    return;
                }
                console.log(contents);
            }

        });

        DASHBOARD.instructionsFileModel = new DASHBOARD.InstructionsFileModel();
        var instrView = new DASHBOARD.InstructionsView();
    }

    return { "initialize": function() { $(document).ready(init); }};

});