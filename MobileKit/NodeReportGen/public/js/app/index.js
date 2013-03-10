// index.js
/*global console, requirejs, TEMPLATE_PARAMS */

define(['jquery', 'underscore', 'backbone', 'app/dashboardGlobals', 'jstz',
        'jquery-migrate', 'bootstrap-modal', 'bootstrap-dropdown', 'bootstrap-spinedit', 'bootstrap-transition',
        'jquery.dataTables', 'jquery.generateFile', 'jquery.maphilight', 'jquery.timezone-picker'],


function ($, _, Backbone, DASHBOARD, jstz) {
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
            el: $("#id_instructionsfiles"),
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
            set: function(attributes,options) {
                // Fill up local time when a model is created. This unfortunately involves a synchronous
                //  AJAX call. Provide an alternative batch processing of all times in a collection. 
                if (attributes.startPosixTime && !attributes.startLocalTime) {
                    var tz = DASHBOARD.dashboardSettings.get('timezone');
                    var url = '/rest/tz?' + $.param({tz:tz, posixTimes:[attributes.startPosixTime]});
                    var result = JSON.parse($.ajax({type: 'GET', url: url, dataType:'json', async:false}).responseText);
                    attributes.startLocalTime = result.timeStrings[0];
                }
                Backbone.Model.prototype.set.call(this,attributes,options);
            }
        });

        DASHBOARD.SubmittedJobs = Backbone.Collection.extend({
            initialize: function ()  {
                this.listenTo(DASHBOARD.dashboardSettings, "change:timezone", this.resetTimeZone);
            },
            model: DASHBOARD.SubmittedJob,
            resetTimeZone: function() {
                var that = this;
                var tz = DASHBOARD.dashboardSettings.get('timezone');
                // Batch convert all the startPosixTime values to startLocalTime values using the specified timezone
                //  Triggers a reset when done
                var etmList = [];
                for (var i=0; i<this.length; i++) etmList.push(this.at(i).get('startPosixTime'));
                var url = '/rest/tz?' + $.param({tz:tz, posixTimes:etmList});
                $.getJSON(url,function (data) {
                    for (var i=0; i<that.length; i++) {
                        var model = that.at(i);
                        model.set({'startLocalTime': data.timeStrings.shift()});
                        that.update(model,{remove: false, silent: true});
                    }
                    that.trigger('reset');
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
                _.forEach(DASHBOARD.submittedJobs.models, function(model) {
                    that.cidToRow[model.cid] = that.jobTable.fnGetNodes(that.jobTable.fnAddData(model.attributes)[0]);
                });
                console.log(that.cidToRow);
            },
            onTestAdd: function () {
                DASHBOARD.submittedJobs.add({hash:this.addIndex++,
                                             directory:Math.random().toString(36).substring(2,8),
                                             startPosixTime:(new Date()).valueOf()});
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
        DASHBOARD.dashboardSettings = new DASHBOARD.DashboardSettings();
        DASHBOARD.submittedJobs = new DASHBOARD.SubmittedJobs();
        DASHBOARD.instructionsFileModel = new DASHBOARD.InstructionsFileModel();
        var settingsView = new DASHBOARD.SettingsView();
        var instrView = new DASHBOARD.InstructionsView();
        var jobsView = new DASHBOARD.JobsView();
        settingsView.render();
        jobsView.render();
    }

    return { "initialize": function() { $(document).ready(init); }};

});