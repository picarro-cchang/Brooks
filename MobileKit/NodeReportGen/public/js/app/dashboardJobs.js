// dashboardJobs.js
/*global alert, module, require, setTimeout, window */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var $ = require('jquery');
    var _ = require('underscore');
    var Backbone = require('backbone');
    var DASHBOARD = require('app/dashboardGlobals');
    var rptGenStatus = require('common/rptGenStatus');
    require('localStorage');
    require('jquery.dataTables');

    function dashboardJobsInit() {
        _.templateSettings = {
          evaluate : /\{\[([\s\S]+?)\]\}/g,
          interpolate : /\{\{([\s\S]+?)\}\}/g,
          variable: "data"
        };

        DASHBOARD.SubmittedJob = Backbone.Model.extend({
            defaults: {
                hash: null,
                directory: null,
                title:"",
                status: 0,
                msg: "",
                user: "demo",
                startPosixTime: 0,
                startLocalTime: null
            },
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
            },
            analyzeStatus: function (err, status, msg)  {
                var that = this;
                if (status < 0) {
                    this.set({'msg': msg, 'status': status});
                }
                else if (err) {
                    this.set({'msg': err, 'status': rptGenStatus.OTHER_ERROR});
                }
                else if (status >= rptGenStatus.DONE) {
                    this.set({'status': status});
                }
                else setTimeout(function () { that.updateStatus(); }, 5000);
            },
            updateStatus: function () {
                var that = this;
                var qryparms = {'qry': 'getStatus', 'contents_hash': this.get('hash'),
                                'start_ts': this.get('rpt_start_ts') };
                DASHBOARD.rptGenService.get('RptGen', qryparms, function (err, result) {
                    that.analyzeStatus(err, result.status, result.msg);
                });
            }
        });

        DASHBOARD.SubmittedJobs = Backbone.Collection.extend({
            initialize: function ()  {
                this.listenTo(DASHBOARD.dashboardSettings, "change:timezone", this.resetTimeZone);
            },
            localStorage: new Backbone.LocalStorage("JobCollection"),
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
                "click #id_jobTableDiv button.btn" : "onRetrieveInstructions",
                "click a.pdfLink" : "onPdfLink",
                "click a.viewLink" : "onViewLink"
            },
            initialize: function () {
                this.instrFileView = new DASHBOARD.InstructionsFileView();
                this.$el.find("#id_jobTableDiv").html('<table cellpadding="0" cellspacing="0" border="0" class="display" id="id_example"></table>');
                this.jobTable = $("#id_example").dataTable({
                    "aoColumns": [
                        { "sTitle": "Reload", "mData": "link", "sClass": "center"},
                        { "sTitle": "StartTime", "mData": "startLocalTime", "sClass": "center"},
                        { "sTitle": "Title", "mData": "title", "sClass": "center"},
                        { "sTitle": "Status", "mData": "statusDisplay", "sClass": "center"},
                        { "sTitle": "User", "mData": "user", "sClass": "center"}
                    ],
                    "sDom":'<"top"lf>rt<"bottom"ip>'
                });
                this.jobTable.fnSort([[1,'desc']]);
                this.cidToRow = {};
                this.linkTemplate = _.template('<button type="button" data-cid="{{ data.cid }}" class="btn btn-warning btn-mini"><i class="icon-pencil icon-white"></i></button>');
                this.listenTo(DASHBOARD.submittedJobs, "add", this.addJob);
                this.listenTo(DASHBOARD.submittedJobs, "remove", this.removeJob);
                this.listenTo(DASHBOARD.submittedJobs, "change", this.changeJob);
                this.listenTo(DASHBOARD.submittedJobs, "reset", this.resetJobs);
                this.addIndex = 0;
                this.selectedRow = null;
            },
            addJob: function (model) {
                this.cidToRow[model.cid] = this.jobTable.fnGetNodes(this.jobTable.fnAddData(this.formatSpecials(model))[0]);
                if (this.selectedRow) {
                    $(this.selectedRow).removeClass('row_selected');
                    this.selectedRow = null;
                }
                this.highLightJob(model);
            },
            changeJob: function (model) {
                this.jobTable.fnUpdate(this.formatSpecials(model), this.cidToRow[model.cid]);
            },
            formatSpecials: function(model) {
                var link = this.linkTemplate({cid: model.cid});
                var statusDisplay;
                var status = model.get('status');
                if (status < 0) {
                    statusDisplay = '<span>Error: ' + model.get('msg') + '</span>';
                }
                else if (status >= rptGenStatus.DONE) {
                    if (status === rptGenStatus.DONE_WITH_PDF) {
                        statusDisplay = '<a class="pdfLink btn btn-mini btn-inverse" href="#" data-hash="' + model.get('hash') +
                                        '" data-directory="' + model.get('directory') + '">Download PDF</a>' +
                                        '</b>';
                    }
                    else if (status === rptGenStatus.DONE_NO_PDF) {
                        statusDisplay = '<b><a class="viewLink" href="#" data-hash="' + model.get('hash') +
                                        '" data-directory="' + model.get('directory') + '">View</a></b>';
                    }
                }
                else {
                    statusDisplay = '<span>Working...</span>';
                }
                return $.extend({link: link, statusDisplay: statusDisplay}, model.attributes);
            },
            highLightJob: function (model) {
                var row = this.cidToRow[model.cid];
                this.instrFileView.$el.find(".file").val(model.get("startLocalTime"));
                if (this.selectedRow) $(this.selectedRow).removeClass('row_selected');
                this.selectedRow = $(row).addClass('row_selected');
            },
            onPdfLink: function (e) {
                var pdfUrl = '/rest/data/' + $(e.currentTarget).data('hash') + '/' + $(e.currentTarget).data('directory') + '/report.pdf';
                window.open(pdfUrl,'_blank');
                return false;
            },
            onRetrieveInstructions: function(e) {
                var that = this;
                var cid = $(e.currentTarget).data("cid");
                var job = _.findWhere(DASHBOARD.submittedJobs.models, {cid: cid});
                var url = "/rest/data/" + job.get("hash") + '/instructions.json';
                $.ajax({
                    dataType: "text",
                    url: url,
                    type: "GET",
                    success: function (data) {
                        that.instrFileView.loadContents(data);
                        that.highLightJob(job);
                    }
                }).error(function () { alert('Unable to retrieve instructions for this job'); });
            },
            onViewLink: function (e) {
                var viewUrl = '/getReport/' + $(e.currentTarget).data('hash') + '/' + $(e.currentTarget).data('directory') + '?name=Summary';
                window.open(viewUrl,'_blank');
            },
            removeJob: function (model) {
                this.jobTable.fnDeleteRow(this.cidToRow[model.cid]);
                delete this.cidToRow[model.cid];
            },
            render: function () {
                var that = this;
                this.cidToRow = [];
                this.jobTable.fnClearTable();
                _.forEach(DASHBOARD.submittedJobs.models, function (model) {
                    that.cidToRow[model.cid] = that.jobTable.fnGetNodes(that.jobTable.fnAddData(that.formatSpecials(model))[0]);
                });
                return this;
            },
            resetJobs: function () {
                this.render();
                if (this.selectedRow) {
                    $(this.selectedRow).removeClass('row_selected');
                    this.selectedRow = null;
                }
            }
        });
    }
    module.exports.init = dashboardJobsInit;
});

