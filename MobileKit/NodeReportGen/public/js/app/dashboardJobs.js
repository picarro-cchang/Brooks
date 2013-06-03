// dashboardJobs.js
/*global alert, console, module, require, setTimeout, window */
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
    var rptGenStatus = require('common/rptGenStatus');
    // require('localStorage');
    require('jquery.dataTables');

    $.fn.dataTableExt.oApi.fnDisplayRow = function ( oSettings, nRow )
    {
        // Account for the "display" all case - row is already displayed
        if ( oSettings._iDisplayLength == -1 )
        {
            return;
        }
        // Find the node in the table
        var iPos = -1;
        for( var i=0, iLen=oSettings.aiDisplay.length ; i<iLen ; i++ )
        {
            if( oSettings.aoData[ oSettings.aiDisplay[i] ].nTr == nRow )
            {
                iPos = i;
                break;
            }
        }
        // Alter the start point of the paging display
        if( iPos >= 0 )
        {
            oSettings._iDisplayStart = ( Math.floor(i / oSettings._iDisplayLength) ) * oSettings._iDisplayLength;
            this.oApi._fnCalculateEnd( oSettings );
        }
        this.oApi._fnDraw( oSettings );
    };

    $.fn.dataTableExt.oApi.fnStandingRedraw = function(oSettings, action) {
        if(oSettings.oFeatures.bServerSide === false){
            var before = oSettings._iDisplayStart;
            if (action !== undefined) {
                action();
            }
            oSettings.oApi._fnReDraw(oSettings);
            // iDisplayStart has been reset to zero - so lets change it back
            oSettings._iDisplayStart = before;
            oSettings.oApi._fnCalculateEnd(oSettings);
        }
        // draw the 'current' page
        oSettings.oApi._fnDraw(oSettings);
    };

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
                startLocalTime: null,
                timezone: "UTC",
                shown: true
            },
            addLocalTime: function (done, tz) {
                var that = this;
                if (!tz) tz = DASHBOARD.timezone;
                DASHBOARD.Utilities.timezone({tz:tz, posixTimes:[this.get("startPosixTime")]},
                function (err) {
                    var msg = 'While converting timezone: ' + err;
                    alert(msg);
                    done(msg);
                },
                function (s, result) {
                    console.log('While converting timezone: ' + s);
                    that.set({"startLocalTime": result.timeStrings[0]});
                    done(null);
                });
            },
            analyzeStatus: function (err, status, msg)  {
                var that = this;
                if (status === rptGenStatus.TASK_NOT_FOUND) {
                    this.set({'msg': 'Report not found or expired - resubmit', 'status': status});
                }
                else if (status < 0) {
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
                var qryparms = {'contents_hash': this.get('hash'),
                                'start_ts': this.get('rpt_start_ts') };
                DASHBOARD.SurveyorRpt.getStatus(qryparms,
                function (err) {
                    that.analyzeStatus(err);
                },
                function (s, result) {
                    console.log('While getting status: ' + s);
                    that.analyzeStatus(null, result.status, result.msg);
                });
            }
        });

        DASHBOARD.SubmittedJobs = Backbone.Collection.extend({
            initialize: function ()  {
            },
            // localStorage: new Backbone.LocalStorage("JobCollection"),
            model: DASHBOARD.SubmittedJob
        });

        function timeWithOffsetToPosix(x) {
            var comps = x.match(/(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}[+-]\d{4})/);
            return (new Date(comps[1]+'T'+comps[2])).valueOf();
        }

        DASHBOARD.JobsView = Backbone.View.extend({
            el: $("#id_submittedJobs"),
            events: {
                "click #id_jobTableDiv button.btn.reload" : "onRetrieveInstructions",
                "click #id_jobTableDiv button.showAll" : "onShowAll",
                "click #id_jobTableDiv button.showSelected" : "onShowSelected",
                "click a.pdfLink" : "onPdfLink",
                "click a.viewLink" : "onViewLink",
                "click .rowCheck" : "onRowCheck"
            },
            initialize: function () {
                var that = this;
                this.instrFileView = new DASHBOARD.InstructionsFileView();
                this.$el.find("#id_jobTableDiv").html('<table cellpadding="0" cellspacing="0" border="0" class="display" id="id_jobTable"></table>');
                /* Define two custom functions (asc and desc) for string sorting */
                $.fn.dataTableExt.oSort['time-with-offset-asc']  = function(x,y) {
                    x = timeWithOffsetToPosix(x);
                    y = timeWithOffsetToPosix(y);
                    return ((x < y) ? -1 : ((x > y) ?  1 : 0));
                };
                $.fn.dataTableExt.oSort['time-with-offset-desc'] = function(x,y) {
                    x = timeWithOffsetToPosix(x);
                    y = timeWithOffsetToPosix(y);
                    return ((x < y) ?  1 : ((x > y) ? -1 : 0));
                };
                this.showAll = false;
                this.jobTable = $("#id_jobTable").dataTable({
                    "aoColumns": [
                        { "sWidth": "5%", "sTitle": "Reload", "mData": "link", "sClass": "center"},
                        { "sWidth": "15%", "sTitle": "First submitted at", "mData": "startLocalTime", "sClass": "center", "sType":'time-with-offset'},
                        { "sWidth": "15%", "sTitle": "Time zone", "mData": "timezone", "sClass": "center"},
                        { "sWidth": "30%", "sTitle": "Title", "mData": "title", "sClass": "center"},
                        { "sWidth": "20%", "sTitle": "Status", "mData": "statusDisplay", "sClass": "center"},
                        { "sWidth": "10%", "sTitle": "User", "mData": "user", "sClass": "center"},
                        { "sWidth": "5%", "sTitle": '<button type="button" class="btn btn-mini btn-inverse showAll">Show All</button>',
                          "sClass": "center", "mData": "selected", "bSortable": false}
                    ],
                    "sDom":'<"top"lf>rt<"bottom"ip>'
                });
                this.jobTable.fnSort([[1,'desc']]);
                $.fn.dataTableExt.afnFiltering.push(
                function( oSettings, aData ) {
                    return that.showAll || $(aData[6]).is(':checked');
                });

                this.cidToRow = {};
                this.linkTemplate = _.template('<button type="button" data-cid="{{ data.cid }}" class="btn btn-warning btn-mini reload"><i class="icon-pencil icon-white"></i></button>');
                this.listenTo(DASHBOARD.submittedJobs, "add", this.addJob);
                this.listenTo(DASHBOARD.submittedJobs, "remove", this.removeJob);
                this.listenTo(DASHBOARD.submittedJobs, "change", this.changeJob);
                this.listenTo(DASHBOARD.submittedJobs, "reset", this.resetJobs);
                this.addIndex = 0;
                this.selectedRow = null;
                var update_size = function () {
                    $(that.jobTable).css({width: $(that.jobTable).parent().width()});
                    that.jobTable.fnAdjustColumnSizing();
                };
                $(window).resize(function() {
                    clearTimeout(window.refresh_size);
                    window.refresh_size = setTimeout(function () { update_size(); }, 250);
                });
            },
            onShowAll: function (e) {
                var el = $(e.currentTarget);
                this.showAll = true;
                el.html('Show Selected').addClass('showSelected').removeClass('showAll');
                this.jobTable.fnStandingRedraw();
            },
            onShowSelected: function (e) {
                var el = $(e.currentTarget);
                this.showAll = false;
                el.html('Show All').addClass('showAll').removeClass('showSelected');
                this.jobTable.fnStandingRedraw();
            },
            onRowCheck: function (e) {
                // Find the model associated with the row
                var el = $(e.currentTarget);
                var cid = el.data("cid");
                var job = _.findWhere(DASHBOARD.submittedJobs.models, {cid: cid});

                this.jobTable.fnStandingRedraw(function () {
                    job.set({shown: el.is(':checked')});
                });
            },
            addJob: function (model) {
                DASHBOARD.SurveyorRpt.updateDashboard({user: DASHBOARD.user, object: JSON.stringify(model), action:'add'},
                    function (err) {
                        alert('While updating dashboard: ' + err);
                    },
                    function (s) {
                        console.log('While updating dashboard: ' + s);
                    });
                this.cidToRow[model.cid] = this.jobTable.fnGetNodes(this.jobTable.fnAddData(this.formatSpecials(model))[0]);
                if (this.selectedRow) {
                    $(this.selectedRow).removeClass('row_selected');
                    this.selectedRow = null;
                }
                this.highLightJob(model);
            },
            changeJob: function (model) {
                DASHBOARD.SurveyorRpt.updateDashboard({user: DASHBOARD.user, object: JSON.stringify(model), action:'update'},
                    function (err) {
                        alert('While updating dashboard: ' + err);
                    },
                    function (s) {
                        console.log('While updating dashboard: ' + s);
                    });
                this.jobTable.fnUpdate(this.formatSpecials(model), this.cidToRow[model.cid]);
            },
            formatSpecials: function(model) {
                // Make special fields for datatables row. "link" is a button which allows us to reload the instructions
                //  for editing, "status" indicates if processing is in progress. When complete, it turns into links to the
                //  results and "shown" is a checkbox which allows the user to hide unwanted rows of the table. Since we have
                //  the model on entry, we can use this to tag the html elements that later need to access the model.
                var link = this.linkTemplate({cid: model.cid});
                var statusDisplay;
                var status = model.get('status');
                if (status < 0) {
                    statusDisplay = '<span>Error: ' + model.get('msg') + '</span>';
                }
                else if (status >= rptGenStatus.DONE) {
                    if (status === rptGenStatus.DONE_WITH_PDF) {
                        statusDisplay = '<a class="pdfLink btn btn-mini btn-inverse" href="#" data-hash="' + model.get('hash') +
                                        '" data-directory="' + model.get('directory') + '">Download PDF</a>';
                    }
                    else if (status === rptGenStatus.DONE_NO_PDF) {
                        statusDisplay = '<b><a class="viewLink" href="#" data-hash="' + model.get('hash') +
                                        '" data-directory="' + model.get('directory') + '">View</a></b>';
                    }
                }
                else {
                    statusDisplay = '<span>Working...</span>';
                }
                var sel = model.get('shown') ?
                            '<input class="rowCheck" type="checkbox" data-cid="' + model.cid + '" checked>' :
                            '<input class="rowCheck" type="checkbox" data-cid="' + model.cid + '">';
                return $.extend({link: link, statusDisplay: statusDisplay, selected: sel}, model.attributes);
            },
            highLightJob: function (model) {
                var row = this.cidToRow[model.cid];
                model.set({"shown": true});
                this.jobTable.fnStandingRedraw();
                this.instrFileView.$el.find(".file").val(model.get("startLocalTime"));
                if (this.selectedRow) $(this.selectedRow).removeClass('row_selected');
                this.selectedRow = $(row).addClass('row_selected');
                this.jobTable.fnDisplayRow(this.selectedRow[0]);
            },
            onPdfLink: function (e) {
                var pdfUrl = '/' + $(e.currentTarget).data('hash') + '/' + $(e.currentTarget).data('directory') + '/report.pdf';
                DASHBOARD.SurveyorRpt.geturl({qryobj: {qry: "resource"}, existing_tkt: true},
                function (err) {
                    console.log('error: ', err);
                },
                function (status, url) {
                    // url = window.location.origin + url.substring(0,url.lastIndexOf('?')) + pdfUrl;
                    // console.log(url);
                    window.location = url.substring(0,url.lastIndexOf('?')) + pdfUrl;
                    // window.open(url,'_blank');
                    return false;
                });
            },
            onRetrieveInstructions: function(e) {
                var that = this;
                var cid = $(e.currentTarget).data("cid");
                var job = _.findWhere(DASHBOARD.submittedJobs.models, {cid: cid});
                var url = "/" + job.get("hash") + '/instructions.json';
                DASHBOARD.SurveyorRpt.resource(url,
                function (err) {
                    alert('While retrieving instructions from ' + url + ': ' + err);
                },
                function (status, data) {
                    console.log('While retrieving instructions from ' + url + ': ' + status);
                    that.instrFileView.loadContents(cjs(data,null,2));
                    that.highLightJob(job);
                });
            },
            onViewLink: function (e) {
                var viewUrl = assets + '' + 'getReport/' + $(e.currentTarget).data('hash') + '/' + $(e.currentTarget).data('directory') + '?name=Summary';
                window.open(viewUrl,'_blank');
            },
            removeJob: function (model) {
                DASHBOARD.SurveyorRpt.updateDashboard({user: DASHBOARD.user, object: JSON.stringify(model), action:'delete'},
                    function (err) {
                        alert('While updating dashboard: ' + err);
                    },
                    function (s) {
                        console.log('While updating dashboard: ' + s);
                    });
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
                $(this.jobTable).css({width: $(this.jobTable).parent().width()});
                this.jobTable.fnAdjustColumnSizing();
                return this;
            },
            resetJobs: function () {
                var models = DASHBOARD.submittedJobs.models;
                DASHBOARD.SurveyorRpt.updateDashboard({user: DASHBOARD.user, object: JSON.stringify(models), action:'reset'},
                    function (err) {
                        alert('While updating dashboard: ' + err);
                    },
                    function (s) {
                        console.log('While updating dashboard: ' + s);
                    });
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

