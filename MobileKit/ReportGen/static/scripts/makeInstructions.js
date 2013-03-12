/* Generate a report by submitting an instructions file to the P3 server and waiting for the 
components to be generated. Assemble the report and allow it to be saved */

var TIMER = {
        status: null    // time to retrieve status
    };

var CSTATE = {
        ticket: null,       // Hash of instructions used as key to retrieve status, etc
        progress: 0,        // Row of table currently being edited
        reportImages: [],   // Handles to composite maps in the DOM for report
        
    };

var CNSNT = {
        regions: null,
        runs: null,
        svcurl: "/rest",
        mapTypes: {"plat": "Plat", "map": "Google Map", "satellite": "Google Satellite" }
    };

var TXT = {
        addMarker: 'Specify Marker',
        addRegion: 'Specify Region',
        addRun: 'Specify Parameters of Run',
        cancel: 'Cancel',
        ok: 'OK'
    };

function call_rest(call_url, method, params, success_callback, error_callback) {
    var dtype, url;
    dtype = "json";
    url = call_url + '/' + method;
    $.ajax({contentType: "application/json",
        data: $.param(params),
        dataType: dtype,
        url: url,
        type: "GET",
        timeout: 60000,
        success: success_callback,
        error: error_callback
        });
}

function zeroPad(num, places) {
  var zero = places - num.toString().length + 1;
  return Array(+(zero > 0 && zero)).join("0") + num;
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
// ============================================================================
//  Error handling for table forms
// ============================================================================

function addError(field_id, message) {
    var id = "#" + field_id;
    if ($(id).next('.help-inline').length === 0) {
        $(id).after('<span class="help-inline">' + message + '</span>');
        $(id).parents("div .control-group").addClass("error");
    }
    $(id).bind('focus keypress', function () {
        $(this).next('.help-inline').fadeOut("fast", function () {
            $(this).remove();
        });
        $(this).parents('.control-group').removeClass('error');
    });
}

function addTip(form_id, message) {
    $(".validate_tips").html(message).show();
    $("#" + form_id + " input,#" + form_id + " select").bind('focus keypress', function () {
        $(".validate_tips").fadeOut("fast");
    });
}

// ============================================================================
// Make instructions from tables
// ============================================================================
function makeJsonInstructions()
{
    var result1 = tableFuncs.getTableData(CNSNT.regions);
    var result2 = tableFuncs.getTableData(CNSNT.runs);
    var result3 = tableFuncs.getTableData(CNSNT.markers);
    var result = JSON.stringify({regions: result1, runs: result2, markers: result3}, null, "    ") + '\n'; 
    return result;
}

// ============================================================================
//  Routines to handle opening of instructions file
// ============================================================================
function styleRegionsTable() {
    $("#id_regions_table_div table").addClass("table table-condensed table-striped table-fmt1");
    $("#id_regions_table_div tbody").addClass("sortable");
    $(".sortable").sortable({helper: tableFuncs.sortableHelper});
}

function styleRunsTable() {
    $("#id_runs_table_div table").addClass("table table-condensed table-striped table-fmt1");
    $("#id_runs_table_div tbody").addClass("sortable");
    $(".sortable").sortable({helper: tableFuncs.sortableHelper});
}

function styleMarkersTable() {
    $("#id_markers_table_div table").addClass("table table-condensed table-striped table-fmt1");
    $("#id_markers_table_div tbody").addClass("sortable");
    $(".sortable").sortable({helper: tableFuncs.sortableHelper});
}

function updateTables(contents) {
    var i, instrDict;
    // $("#id_instructions").val(contents);
    instrDict = JSON.parse(contents);
    if (instrDict.hasOwnProperty("regions")) {
        $("#" + CNSNT.regions.id).replaceWith(tableFuncs.makeTable(instrDict.regions, CNSNT.regions));
        styleRegionsTable();
    }
    if (instrDict.hasOwnProperty("runs")) {
        // Fill up default values
        for (i=0; i<instrDict.runs.length; i++) {
            if (!instrDict.runs[i].hasOwnProperty("path")) {
                instrDict.runs[i].path = true;
            }
        }
        $("#" + CNSNT.runs.id).replaceWith(tableFuncs.makeTable(instrDict.runs, CNSNT.runs));
        styleRunsTable();
    }
    if (instrDict.hasOwnProperty("markers")) {
        $("#" + CNSNT.markers.id).replaceWith(tableFuncs.makeTable(instrDict.markers, CNSNT.markers));
        styleMarkersTable();
    }
}

function readerOnLoad(theFile) {
    return function (e) {
        var contents = e.target.result, lines;
        // Do simple validation to reject malformed files quickly
        try {
            lines = contents.split('\n', 1024);
            lines.shift();
            JSON.parse(lines.join('\n'));
        }
        catch (err) {
            alert("Invalid instructions file");
            return;
        }
        call_rest(CNSNT.svcurl, 'validate', {contents: contents}, 
            function (data, ts, jqXHR) {
                var contents;
                if (data.hasOwnProperty("error")) {
                    alert("Invalid instructions file");
                }
                else {
                    contents = data.contents;
                    updateTables(contents);
                }
            },
            function (data, et, jqXHR) {
            }
        );
    }
}

function handleFileSelect(evt) {
    var files = evt.target.files; // FileList object
    var reader;
    for (var i = 0, f; undefined !== (f = files[i]); i++) {
        reader = new FileReader();
        // Set up the reader to read a text file
        $("#id_instr_upload_name").val(f.name);
        reader.readAsText(f);
        reader.onload = readerOnLoad(f);
    }
}

function handleFileDrop(evt) {
    var reader;
    evt.stopPropagation();
    evt.preventDefault();
    var files = evt.dataTransfer.files; // FileList object.
    if (files.length > 1) alert('Cannot process more than one file');
    else {
        for (var i = 0, f; undefined !== (f = files[i]); i++) {
            $("#id_instr_upload_name").val(f.name);
            reader = new FileReader();
            // Set up the reader to read a text file
            reader.readAsText(f);
            reader.onload = readerOnLoad(f);
        }
    }
}

function handleDragOver(evt) {
    evt.stopPropagation();
    evt.preventDefault();
    evt.dataTransfer.dropEffect = 'copy'; // Explicitly show this is a copy.
}

// ============================================================================
// Making report
// ============================================================================

function makeReport() {
    var instr = makeJsonInstructions();
    call_rest(CNSNT.svcurl, "instrUpload", {contents: instr}, 
        function (data, ts, jqXHR) {
            var fname = $("#id_instr_upload_name").val();
            CSTATE.reportImages = [];
            CSTATE.ticket = data.ticket;
            $(window.location).attr('href', '/report?' + $.param({ticket: data.ticket, fname: fname}));
        },
        function (data, et, jqXHR) {
        }
    );
}

function processStatus(statusDict)
/* Go through the status of the composite maps and as each
   becomes done, create an image to add to the results section.
   This will later produce some metadata describing the image as 
   well as the PNG file */
{
    var e, region, row, words, s, t, url, statByRegion = {}, taburl;

    function updateStatByRegion(region,sd,stage) {
        if (!statByRegion.hasOwnProperty(region)) {
            statByRegion[region] = {stages:"", error: false};
        }
        if (sd.hasOwnProperty("done")) statByRegion[region].stages += stage;
        if (sd.hasOwnProperty("error")) statByRegion[region].error = true;
    }

    for (var key in statusDict) {
        if (statusDict.hasOwnProperty(key)) {
            words = key.split('.');
            if (words[0] === 'report') {
                region = parseInt(words[1], 10);
                updateStatByRegion(region,statusDict[key],"R");
            }
            else if (words[0] === 'composite') {
                region = parseInt(words[1], 10);
                updateStatByRegion(region,statusDict[key],"C");
            }
            else if (words[0] === 'baseMap') {
                region = parseInt(words[1], 10);
                updateStatByRegion(region,statusDict[key],"B");
            }
            else if (words[0] === 'pathMap') {
                region = parseInt(words[1], 10);
                updateStatByRegion(region,statusDict[key][0],"P");
                updateStatByRegion(region,statusDict[key][1],"W");
            }
            else if (words[0] === 'markerMap') {
                region = parseInt(words[1], 10);
                updateStatByRegion(region,statusDict[key][0],"M");
                updateStatByRegion(region,statusDict[key][1],"S");
            }
        }
    }
    for (region in statByRegion) {
        row = tableFuncs.getRowByIndex(region,CNSNT.regions);
        name = tableFuncs.getRowData(row,CNSNT.regions).name;
        if (statByRegion.hasOwnProperty(region)) {
            s = statByRegion[region].stages;
            e = statByRegion[region].error;
            pdfurl = CNSNT.svcurl + "/getPDF?" + $.param({ticket: CSTATE.ticket, region: region});
            xmlurl = CNSNT.svcurl + "/getXML?" + $.param({ticket: CSTATE.ticket, region: region});
            taburl = CNSNT.svcurl + "/getReport?" + $.param({ticket: CSTATE.ticket, region: region, name:name});
            if (e) {
                t = "<b>Error, see detailed status</b>"
                tableFuncs.setCell(row, "status", t, CNSNT.regions);
            }
            else if (s.indexOf("R") >= 0) {
                t = '<b>Done <a href="' + pdfurl + '"> PDF</a><a href="';
                t += xmlurl + '"> Excel</a><a href="';
                t += taburl + '" target="_blank"> View</a> </b>';
                tableFuncs.setCell(row, "status", t, CNSNT.regions);
            }
            else {
                t =  '<div class="progress progress-striped" style="width:50%;margin:0 auto;">';
                t += '<div id="regionBar" class="bar" style="margin-left:';
                t += CSTATE.progress + '%;width:20%;"></div></div>';
                CSTATE.progress = (CSTATE.progress + 20) % 100;
                tableFuncs.setCell(row, "status", t, CNSNT.regions);
            }
        }
    }
}

function formatStatus(contents)
{
    var i, k, keys=[], result=[];
    for (k in contents) {
        keys.push(k);
    }
    keys.sort();
    for (i=0; i<keys.length; i++) {
        result.push('"' + keys[i] +'": ' + JSON.stringify(contents[keys[i]]));
    }
    return result.join("\n");
}

function statusTimer()
{
    params = { "ticket":CSTATE.ticket };
    call_rest(CNSNT.svcurl, "getReportStatus", params, 
        function (data, ts, jqXHR) {
            var done = true;
            var allContents = "";
            $.each(data.files,function(fName,contents) {
                allContents += formatStatus(contents)
                processStatus(contents);
                if (!("end" in contents)) done = false;
            });
            if ("" !== allContents) {
                $("#id_status").val(allContents + "\n");
            }
            if (!done) {
                $(".sortable").sortable('disable');
                TIMER.status = setTimeout(statusTimer, 1000);
            }
            else {
                $(".sortable").sortable('enable');
            }
        },
        function (data, et, jqXHR) {
            TIMER.status = setTimeout(statusTimer, 1000);
        }
    );
}

//=============================================================================
// Edit Regions
//=============================================================================

CNSNT.regions = {id: "regionTable", layout: [
    {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
    {key: "baseType", width: "10%", th: "Type", tf: function (t) { return CNSNT.mapTypes[t]; }, eid: "id_base_type", cf: String},
    {key: "name", width: "10%", th: "Name", tf: String, eid: "id_name", cf: String},
    {key: "swCorner", width: "15%", th: "SW Corner", tf: floatsToString, eid: "id_sw_corner", cf: parseFloats, 
        ef: function (s, b) {
            s.val(floatsToString(b));
        }},
    {key: "neCorner", width: "15%", th: "NE Corner", tf: floatsToString, eid: "id_ne_corner", cf: parseFloats,
        ef: function (s, b) {
            s.val(floatsToString(b));
        }},
    {key: "comments", width: "20%", th: "Comments", tf: processComments, tfParams: {fieldWidth: 25}, 
        eid: "id_comments", cf: String},
    {key: "status", width: "26%", th: "Status", omit: true},
    {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
],
    vf: function (eidByKey, template, container, onSuccess) {
    return validateRegion(eidByKey, template, container, onSuccess); 
}};

function editRegionsChrome()
{
    var header, body, footer;
    var controlClass = "input-large", optClass = "input-corners";
    header = '<div class="modal-header"><h3>' + TXT.addRegion + '</h3></div>';
    body   = '<div class="modal-body">';
    body += '<form class="form-horizontal"><fieldset>';
    body += tableFuncs.editControl("Region Type", tableFuncs.makeSelect("id_base_type", {"class": controlClass}, CNSNT.mapTypes));
    body += tableFuncs.editControl("Name", tableFuncs.makeInput("id_name", {"class": controlClass, 
            "data-provide":"typeahead", "placeholder": "Name of region or plat"}));
    body += tableFuncs.editControl("SW Corner", tableFuncs.makeInput("id_sw_corner", 
            {"class": controlClass + " " + optClass, "placeholder": "Latitude, Longitude"}));
    body += tableFuncs.editControl("NE Corner", tableFuncs.makeInput("id_ne_corner", 
            {"class": controlClass + " " + optClass, "placeholder": "Latitude, Longitude"}));
    body += tableFuncs.editControl("Comments", tableFuncs.makeTextArea("id_comments", {"class": controlClass}));
    body += '</fieldset></form></div>';
    footer = '<div class="modal-footer">';
    footer += '<p class="validate_tips alert alert-error hide"></p>';
    footer += '<button class="btn btn-primary btn-ok">' + TXT.ok + '</button>';
    footer += '<button class="btn btn-cancel">' + TXT.cancel + '</button>';
    footer += '</div>';
    return header + body + footer;
}

function beforeRegionsShow()
{
    var customize = function (type) {
        if (type == "plat") {
            $(".input-corners").closest(".control-group").hide();
            $("#id_name").typeahead({ajax:{url:"/rest/autocompletePlat",triggerLength:2,
                method:"get",timeout:100},items:20});
            $(".typeahead").addClass('dropdown-menu');
        }
        else {
            $(".typeahead").removeClass('dropdown-menu');
            $(".input-corners").closest(".control-group").show();
        }
    };
    customize($("#id_base_type").val()); 

    $("#id_base_type").on("change",function () {
        customize($("#id_base_type").val()); 
    });
}

function validateRegion(eidByKey,template,container,onSuccess) {
    var nameRe = /^(\w|\d){3,16}$/;
    var cornerRe = /^([+\-]?([0-9]+\.?[0-9]*|(\.[0-9]+)))\s*,\s*([+\-]?([0-9]+\.?[0-9]*|(\.[0-9]+)))$/;
    var numErr = 0;
    var name = $("#"+eidByKey["name"]).val();
    var type = $("#"+eidByKey["baseType"]).val();
    var neCorner, swCorner, neArray = [], swArray = [], okCorners = 0;
    
    if (type === "plat") {
        call_rest(CNSNT.svcurl, 'platCorners', {"plat":name}, 
        function (data, ts, jqXHR) {
            if (data.hasOwnProperty("MIN_LAT")) {
                $("#"+eidByKey["swCorner"]).val("" + data.MIN_LAT + "," + data.MIN_LONG);
                $("#"+eidByKey["neCorner"]).val("" + data.MAX_LAT + "," + data.MAX_LONG);
                onSuccess();    
            }
            else {
                tableFuncs.addError(eidByKey["name"], "Unknown plat");
                return;
            }
        });
    }
    else {
        swCorner = $("#"+eidByKey["swCorner"]).val();
        neCorner = $("#"+eidByKey["neCorner"]).val();    
        /* Verify that the name of the region is valid */
        if (!nameRe.test(name)) {
            tableFuncs.addError(eidByKey["name"], "Invalid name");
            numErr++;
        }
        if (!cornerRe.test(swCorner)) {
            tableFuncs.addError(eidByKey["swCorner"], "Invalid corner");
            numErr++;        
        }
        else {
            swArray = parseFloats(swCorner);
            okCorners++;
        }
        if (!cornerRe.test(neCorner)) {
            tableFuncs.addError(eidByKey["neCorner"], "Invalid corner");
            numErr++;
        }
        else {
            neArray = parseFloats(neCorner);
            okCorners++;
        }
        /* Verify that the corner coordinates make sense */
        if (okCorners == 2) {
            if (neArray[0]<=swArray[0] || swArray[0]<-90.0  || neArray[0]>90.0  || neArray[0]-swArray[0]>1.0 ||
                neArray[1]<=swArray[1] || swArray[1]<-180.0 || neArray[1]>180.0 || neArray[1]-swArray[1]>1.0) {
                tableFuncs.addTip(container, "Bad corner coordinates");
                numErr++;
            }
        }
        if (numErr == 0) onSuccess();
    }
}

//=============================================================================
// Edit Runs
//=============================================================================

CNSNT.runs = {id: "runTable", layout: [
    {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
    {key: "analyzer", width: "12%", th: "Analyzer", tf: String, eid: "id_analyzer", cf: String},
    {key: "startEtm", width: "12%", th: "Start Epoch", tf: String, eid: "id_start_etm", cf: String},
    {key: "endEtm", width: "12%", th: "End Epoch", tf: String, eid: "id_end_etm", cf: String},
    {key: "path", width: "5%", th: "Path", tf: boolToIcon, eid: "id_path",
      ef: function (s, b) { $(s).val(String(b)); }, cf: function (s) { return s === "true"; }},
    {key: "marker", width: "5%", th: "Markers", tf: makeColorPatch, eid: "id_marker", cf: String},
    {key: "wedges", width: "5%", th: "Wedges", tf: makeColorPatch, eid: "id_wedges", cf: String},
    {key: "swath", width: "5%", th: "Swath", tf: makeColorPatch, eid: "id_swath", cf: String},
    {key: "minAmpl", width: "5%", th: "Min Ampl", tf: parseFloat, eid: "id_min_ampl", cf: parseFloat},
    {key: "exclRadius", width: "5%", th: "Excl Radius", tf: parseFloat, eid: "id_excl_radius", cf: parseFloat},
    {key: "stabClass", width: "5%", th: "Stab Class", tf: String, eid: "id_stab_class", cf: String},
    {key: "comments", width: "25%", th: "Comments", tf: processComments, tfParams: {fieldWidth: 25}, 
        eid: "id_comments", cf: String},
    {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
],
vf: function (eidByKey, template, container, onSuccess) {
    return validateRun(eidByKey, template, container, onSuccess); 
}};

function editRunsChrome()
{
    var header, body, footer;
    var controlClass = "input-large";
    header = '<div class="modal-header"><h3>' + TXT.addRun + '</h3></div>';
    body   = '<div class="modal-body">';
    body += '<form class="form-horizontal"><fieldset>';
    body += tableFuncs.editControl("Analyzer", tableFuncs.makeInput("id_analyzer", {"class": controlClass, 
            "placeholder": "Name of analyzer"}));
    body += tableFuncs.editControl("Start Epoch Time", tableFuncs.makeInput("id_start_etm", 
            {"class": controlClass + " datetimeRange", "placeholder": "YYYY-MM-DD HH:MM"}));
    body += tableFuncs.editControl("End Epoch Time", tableFuncs.makeInput("id_end_etm", 
            {"class": controlClass + " datetimeRange", "placeholder": "YYYY-MM-DD HH:MM"}));
    body += tableFuncs.editControl("Path", tableFuncs.makeSelect("id_path", {"class": controlClass}, {"true": "Yes", "false": "No"}));
    body += tableFuncs.editControl("Markers", tableFuncs.makeSelect("id_marker", {"class": controlClass},
            {"None": "None", "#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red", 
             "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
    body += tableFuncs.editControl("Wedges", tableFuncs.makeSelect("id_wedges", {"class": controlClass},
            {"None": "None", "#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red", 
             "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
    body += tableFuncs.editControl("Swath", tableFuncs.makeSelect("id_swath", {"class": controlClass},
            {"None": "None", "#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red", 
             "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
    body += tableFuncs.editControl("Min Amplitude", tableFuncs.makeSelect("id_min_ampl", {"class": controlClass},
            {"0.03": "0.03", "0.05": "0.05", "0.1": "0.1", "0.2": "0.2", 
             "0.5": "0.5", "1.0": "1.0" }));
    body += tableFuncs.editControl("Exclusion radius", tableFuncs.makeSelect("id_excl_radius", {"class": controlClass},
            {"0": "0", "10": "10", "20": "20", "30": "30", "50": "50" }));
    body += tableFuncs.editControl("Stability Class", tableFuncs.makeSelect("id_stab_class", {"class": controlClass},
            {"*": "*: Use reported weather data", "A": "A: Very Unstable", "B": "B: Unstable", 
             "C": "C: Slightly Unstable", "D": "D: Neutral", "E": "E: Slightly Stable", "F": "F: Stable" }));
    body += tableFuncs.editControl("Comments", tableFuncs.makeTextArea("id_comments", {"class": controlClass}));
    body += '</fieldset></form></div>';
    footer = '<div class="modal-footer">';
    footer += '<p class="validate_tips alert alert-error hide"></p>';
    footer += '<button class="btn btn-primary btn-ok">' + TXT.ok + '</button>';
    footer += '<button class="btn btn-cancel">' + TXT.cancel + '</button>';
    footer += '</div>';
    return header + body + footer;
}

function beforeRunsShow()
{
    var GMToffset = new Date().getTimezoneOffset()*60;
    function datetimeRange(input) {
        if ("" === $('#id_end_etm').val()) $('#id_end_etm').datetimeEntry('setDatetime',GMToffset); 
        return {minDatetime: (input.id=='id_end_etm'   ? $('#id_start_etm').datetimeEntry('getDatetime'): null),
                maxDatetime: (input.id=='id_start_etm' ? $('#id_end_etm').datetimeEntry('getDatetime'): GMToffset )};
    }
    $.datetimeEntry.setDefaults({spinnerImage: null, datetimeFormat: 'Y-O-D  H:M', show24Hours: true });
    $('input.datetimeRange').datetimeEntry({beforeShow:datetimeRange});
}

var initRunRow = {"analyzer": "FCDS2008", "path":true, "marker": "#FFFF00", "wedges": "#0000FF", "swath": "#00FF00", "minAmpl": 0.1, 
        "exclRadius": 10, "stabClass": "*"};

function validateRun(eidByKey,template,container,onSuccess) {
    var numErr = 0;
    var startEtm = $("#"+eidByKey["startEtm"]).val();
    var endEtm= $("#"+eidByKey["endEtm"]).val();
    if ("" === startEtm) {
        tableFuncs.addError(eidByKey["startEtm"], "Invalid start epoch");
        numErr++;        
    }
    if ("" === endEtm) {
        tableFuncs.addError(eidByKey["endEtm"], "Invalid end epoch");
        numErr++;        
    }
    if (numErr == 0) {
        onSuccess();
    }
}

//=============================================================================
//Edit Additional Markers
//=============================================================================

CNSNT.markers = {id: "markersTable", layout: [
                     {width: "2%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
                     {key: "label", width: "10%", th: "Label", tf: String, eid: "id_label", cf: String},
                     {key: "location", width: "15%", th: "Location", tf: floatsToString, eid: "id_location", cf: parseFloats, 
                         ef: function (s, b) {
                             s.val(floatsToString(b));
                         }},                         
                     {key: "color", width: "5%", th: "Color", tf: makeColorPatch, eid: "id_color", cf: String},
                     {key: "comments", width: "66%", th: "Comments", tf: processComments, tfParams: {fieldWidth: 35}, 
                         eid: "id_comments", cf: String},
                     {width: "2%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton}
                 ],
                     vf: function (eidByKey, template, container, onSuccess) {
                     return validateMarkers(eidByKey, template, container, onSuccess); 
                 }};

function editMarkersChrome()
{
    var header, body, footer;
    var controlClass = "input-large", optClass = "input-corners";
    header = '<div class="modal-header"><h3>' + TXT.addMarker + '</h3></div>';
    body   = '<div class="modal-body">';
    body += '<form class="form-horizontal"><fieldset>';
    body += tableFuncs.editControl("Label", tableFuncs.makeInput("id_label", {"class": controlClass, 
            "placeholder": "Marker label"}));
    body += tableFuncs.editControl("Location", tableFuncs.makeInput("id_location", 
            {"class": controlClass + " " + optClass, "placeholder": "Latitude, Longitude"}));
    body += tableFuncs.editControl("Color", tableFuncs.makeSelect("id_color", {"class": controlClass},
            {"#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red", 
             "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow" }));
    body += tableFuncs.editControl("Comments", tableFuncs.makeTextArea("id_comments", {"class": controlClass}));
    body += '</fieldset></form></div>';
    footer = '<div class="modal-footer">';
    footer += '<p class="validate_tips alert alert-error hide"></p>';
    footer += '<button class="btn btn-primary btn-ok">' + TXT.ok + '</button>';
    footer += '<button class="btn btn-cancel">' + TXT.cancel + '</button>';
    footer += '</div>';
    return header + body + footer;
}

function beforeMarkersShow()
{
}

function  validateMarkers(eidByKey,template,container,onSuccess) {
    var labelRe = /^(\w|\d){1,4}$/;
    var locationRe = /^([+\-]?([0-9]+\.?[0-9]*|(\.[0-9]+)))\s*,\s*([+\-]?([0-9]+\.?[0-9]*|(\.[0-9]+)))$/;
    var numErr = 0;
    var label = $("#"+eidByKey["label"]).val();
    var location, locationArray = [], okLocation = 0;
    
    location = $("#"+eidByKey["location"]).val();
    /* Verify that the label is valid */
    if (!labelRe.test(label)) {
        tableFuncs.addError(eidByKey["label"], "Invalid label");
        numErr++;
    }
    if (!locationRe.test(location)) {
        tableFuncs.addError(eidByKey["location"], "Invalid location");
        numErr++;        
    }
    else {
        locationArray = parseFloats(location);
        okLocation++;
    }
    /* Verify that the location coordinates make sense */
    if (okLocation) {
        if (locationArray[0]<-90.0  || locationArray[0]>90.0  ||
            locationArray[1]<-180.0 || locationArray[1]>180.0 ) {
            tableFuncs.addTip(container, "Bad location coordinates");
            numErr++;
        }
    }
    if (numErr == 0) onSuccess();
}

//=============================================================================
// Initialize
//=============================================================================

function initialize(winH,winW)
{
    var contents, dropZone, name, ticket;
    var container = $("#id_modal");
    
    $("#id_regions_table_div").html(tableFuncs.makeTable({}, CNSNT.regions));
    styleRegionsTable();
    $("#id_regions_table_div").on("click", "tbody a.table-delete-row", function (e) {
        $(e.currentTarget).closest("tr").remove();
    });
    $("#id_regions_table_div").on("click", "table a.table-clear", function (e) {
        $(e.currentTarget).closest("table").find("tbody").empty();
    });
    $("#id_regions_table_div").on("click", "tbody a.table-edit-row", function (e) {
        tableFuncs.editRow($(e.currentTarget).closest("tr"), CNSNT.regions, container, editRegionsChrome, beforeRegionsShow);
    });
    $("#id_regions_table_div").on("click", "table a.table-new-row", function (e) {
        tableFuncs.insertRow(e, CNSNT.regions, container, editRegionsChrome, beforeRegionsShow);
    });
    
    $("#id_runs_table_div").html(tableFuncs.makeTable({}, CNSNT.runs));
    styleRunsTable();    
    $("#id_runs_table_div").on("click", "tbody a.table-delete-row", function (e) {
        $(e.currentTarget).closest("tr").remove();
    });
    $("#id_runs_table_div").on("click", "table a.table-clear", function (e) {
        $(e.currentTarget).closest("table").find("tbody").empty();
    });
    $("#id_runs_table_div").on("click", "tbody a.table-edit-row", function (e) {
        tableFuncs.editRow($(e.currentTarget).closest("tr"), CNSNT.runs, container, editRunsChrome, beforeRunsShow);
    });
    $("#id_runs_table_div").on("click", "table a.table-new-row", function (e) {
        tableFuncs.insertRow(e, CNSNT.runs, container, editRunsChrome, beforeRunsShow, initRunRow);
    });        

    $("#id_markers_table_div").html(tableFuncs.makeTable({}, CNSNT.markers));
    styleMarkersTable();    
    $("#id_markers_table_div").on("click", "tbody a.table-delete-row", function (e) {
        $(e.currentTarget).closest("tr").remove();
    });
    $("#id_markers_table_div").on("click", "table a.table-clear", function (e) {
        $(e.currentTarget).closest("table").find("tbody").empty();
    });
    $("#id_markers_table_div").on("click", "tbody a.table-edit-row", function (e) {
        tableFuncs.editRow($(e.currentTarget).closest("tr"), CNSNT.markers, container, editMarkersChrome, beforeMarkersShow);
    });
    $("#id_markers_table_div").on("click", "table a.table-new-row", function (e) {
        tableFuncs.insertRow(e, CNSNT.markers, container, editMarkersChrome, beforeMarkersShow);
    });        
    
    $("#id_instr_upload_name").val('');
    $("#id_instr_upload").change( function(e){ handleFileSelect(e); });
    // Setup the dnd listeners.
    dropZone = document.getElementById("id_instr_upload_name");
    dropZone.addEventListener('dragover', handleDragOver, false);
    dropZone.addEventListener('drop', handleFileDrop, false);

    $("#id_save_instructions").click(function(e){ 
        var instr = makeJsonInstructions();
        var d = new Date();
        var name = "instructions_" + zeroPad(d.getUTCFullYear(),4) + zeroPad(d.getUTCMonth()+1,2) + zeroPad(d.getUTCDate(),2) +
                   "T" + zeroPad(d.getUTCHours(),2) + zeroPad(d.getUTCMinutes(),2) + zeroPad(d.getUTCSeconds(),2) + '.json';
        $.generateFile({
                    filename    : name,
                    content     : instr,
                    script      : CNSNT.svcurl + '/download'
        });
        e.preventDefault();
        // $("#id_instructions").val(instr);
        $("#id_instr_upload_name").val(name);
    });
    
    $("#id_make_report").click(function(e) { 
        $(".sortable").sortable('disable');
        makeReport(); 
        e.preventDefault(); 
    });
    
    ticket = $("#id_hidden_ticket").text();
    contents = $("#id_hidden_contents").text();
    name = $("#id_hidden_name").text();
    // $('#id_instructions').val(contents);
    $("#id_instr_upload_name").val(name);
    if (contents) {
        $(".sortable").sortable('disable');
        updateTables(contents);
        CSTATE.ticket = ticket;
        TIMER.status = setTimeout(statusTimer, 1000);
    }
    $('#id_status').val('');
    $('#id_show_hide_status').on('click',function () {
        $('#id_status').toggleClass("hide");
        if ($('#id_status').hasClass("hide")) $('#id_show_hide_status').html("Show detailed status");
        else $('#id_show_hide_status').html("Hide detailed status");
    });
}
