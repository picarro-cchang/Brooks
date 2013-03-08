// getReport.js
/*global console, requirejs, TEMPLATE_PARAMS */

define(['jquery', 'underscore', 'backbone', 'app/dashboardGlobals',
        'jquery-migrate', 'bootstrap-modal', 'bootstrap-dropdown', 'bootstrap-spinedit', 'bootstrap-transition',
        'jquery.dataTables', 'jquery.ba-bbq'],

function ($, _, Backbone, DASHBOARD) {
    'use strict';

    function init() {
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
                $.event.fixHooks.drop = {props: ["dataTransfer"]};
            },
            onSaveInstructions: function() { console.log("onSaveInstructions"); },
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
                        this.$el.find(".file").val(f.name);
                        //reader = new FileReader();
                        // Set up the reader to read a text file
                        //reader.readAsText(f);
                        //reader.onload = readerOnLoad(f);
                    }
                }
            },
            onMakeReport: function() { console.log("onMakeReport"); },
            onSelectFile: function(e) {
                var files = e.target.files; // FileList object
                if (files.length > 1) alert('Cannot process more than one file');
                else {
                    for (var i = 0, f; undefined !== (f = files[i]); i++) {
                        this.$el.find(".file").val(f.name);
                    }
                }
            }
        });
        var instrView = new DASHBOARD.InstructionsView();
    }

    return { "initialize": function() { $(document).ready(init); }};

});