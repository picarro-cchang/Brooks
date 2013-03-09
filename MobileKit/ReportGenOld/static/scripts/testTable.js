
function boolToIcon(value) {
    var name = (value) ? ("icon-ok") : ("icon-remove");
    return (undefined !== value) ? '<i class="' + name + '"></i>' : '';
}

function makeColorPatch(value) {
    var result = '<div style="width:15px;height:15px;border:1px solid #000;margin:0 auto;';
    result += 'background-color:' + value + ';"></div>';
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

function validate(eidByKey, template, container, onSuccess) {
    var numRe = /^[+\-]?([0-9]+\.?[0-9]*|(\.[0-9]+))$/;
    if (!numRe.test($("#" + eidByKey.H4).val())) {
        tableFuncs.addError(eidByKey.H4, "Number required");
        tableFuncs.addTip(container, "Please try again");
    }
    else {
        onSuccess();
    }
}

var template = {id: "test-table",
                vf: validate, 
                layout: [
    {key: "H1", width: "15%", th: "Heading 1", tf: String, eid: "id_H1", cf: String},
    {key: "H2", width: "15%", th: "Heading 2", tf: boolToIcon, eid: "id_H2",
      ef: function (s, b) {
            $(s).val(String(b));
        }, cf: function (s) {   return s === "true"; 
                            }
        },
    {key: "H3", width: "15%", th: "Heading 3", tf: makeColorPatch, eid: "id_H3", cf: String},
    {key: "H4", width: "15%", th: "Heading 4", tf: parseFloat, eid: "id_H4", cf: parseFloat},
    {key: "C", width: "15%", th: "Comments", tf: processComments, tfParams: {fieldWidth: 12},
        eid: "id_C", cf: String},
    {width: "5%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
    {width: "5%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton},
    {key: "S", width: "15%", th: "Status", omit: true}
]};


var tableData = [
    {"H1": "Row1_1", "H2": true, "H3": "#00FF00", "H4": 1.0, "C": "Row1_Comments and more"},
    {"H1": "Row2_1", "H2": true, "H3": "#FF0000", "H4": 4.0, "C": "Row2_Comments and more", "S": "Status"},
    {"H1": "Row3_1", "H2": false, "H3": "#0000FF", "H4": 9.0, "C": "Row3_Comments and more"}
];

// Row used to initialize form on insert
var initRow = {"H1": "First", "H2": true, "H3": "#FFFFFF", "H4": 1.0, "C": "Comments"};

function editTableChrome()
{
    var header, body, footer;
    var controlClass = "input-large";
    header = '<div class="modal-header"><h3>Data Row</h3></div>';
    body   = '<div class="modal-body">';
    body += '<form id="id_edit_form" class="form-horizontal"><fieldset>';
    body += tableFuncs.editControl("Heading 1", tableFuncs.makeInput("id_H1", {"class": controlClass, "placeholder": "Some text"}));
    body += tableFuncs.editControl("Heading 2", tableFuncs.makeSelect("id_H2", {"class": controlClass}, {"true": "Yes", "false": "No"}));
    body += tableFuncs.editControl("Heading 3", tableFuncs.makeSelect("id_H3", {"class": controlClass},
            {"#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red", 
             "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow", "#FFFFFF": "white" }));
    body += tableFuncs.editControl("Heading 4", tableFuncs.makeInput("id_H4", {"class": controlClass, "placeholder": "Height"}));
    body += tableFuncs.editControl("Comments", tableFuncs.makeTextArea("id_C", {"class": controlClass}));
    body += '</fieldset></form></div>';
    footer = '<div class="modal-footer">';
    footer += '<p class="validate_tips alert alert-error hide"></p>';
    footer += '<button class="btn btn-primary btn-ok">OK</button>';
    footer += '<button class="btn btn-cancel">Cancel</button>';
    footer += '</div>';
    return header + body + footer;
}

function beforeShow() {}

function setupRadioControlGroup(params)
{
    var result = '';
    result += '<div class="control-group" id="' + params.control_group_id + '">';
    result += '<label class="control-label" for="' + params.control_div_id + '">';
    result += params.label + '</label>';
    result += '<div class="controls">';
    result += '<div id="' + params.control_div_id + '" class="btn-group" data-toggle="buttons-radio">';
    $.each(params.buttons, function (i, v) {
        result += '<button id="' + v.id + '"   class="btn btn-large">' + v.caption + '</button>';
    });
    result += '</div></div></div>';
    return result;
}


function makeWeatherForm(resultFunc, init) {
    /* Makes a weather selection form in the modal box "myModal". There are currently three questions, where the
     * second question depends on the first
     * 
     * Day (0) or Night (1)
     * If Day:   Strong sunlight (0), moderate sunlight (1) or weak sunlight (2)
     * If Night: <50% cloud cover (0), >50% cloud cover (1)
     * Calm (0), light wind (1) or strong wind (2)
     * 
     * The user selects the appropriate options, and the result is returned as a 3 element array. 
     * e.g. [0,1,2] = Day, moderate sunlight, strong wind
     *      [1,0,1] = Night, <50% cloud cover, light wind
     * 
     * The initial settings of the buttons in the form can be specified using init, which must be a valid 
     *  3-element array
     *  
     * After a successful selection has been made, the function "resultFunc" is called. This function has a
     * single parameter which is the 3-element array of the selections. 
     *  */
    var weatherFormTemplate = [{label: "<h4>Survey time</h4>",
        control_div_id: "id_day_night", 
        control_group_id: "id_day_night_group",
        buttons: [{id: "id_day", caption: "Day"},
                  {id: "id_night", caption: "Night"}]},
       {label: "<h4>Sunlight</h4>",
        control_div_id: "id_sunlight",
        control_group_id: "id_sunlight_group",
        buttons: [{id: "id_strong_sunlight", caption: "Strong"},
                  {id: "id_moderate_sunlight", caption: "Moderate"},
                  {id: "id_weak_sunlight", caption: "Weak"}]},
       {label: "<h4>Cloud</h4>",
        control_div_id: "id_cloud",
        control_group_id: "id_cloud_group",
        buttons: [{id: "id_less50_cloud", caption: "&lt;50%"},
                  {id: "id_more50_cloud", caption: "&gt;50%"}]},
       {label: "<h4>Wind</h4>",
        control_div_id: "id_wind",
        control_group_id: "id_wind_group",
        buttons: [{id: "id_calm_wind", caption: "Calm"},
                  {id: "id_light_wind", caption: "Light"},
                  {id: "id_strong_wind", caption: "Strong"}]}];                              

    function addError(field_id, message) {
        var id = "#" + field_id;
        if ($(id).next('.help-inline').length === 0) {
            $(id).after('<span class="help-inline">' + message + '</span>');
            $(id).parents("div .control-group").addClass("error");
        }
        $(id).on('focus keypress click', function () {
            $(this).next('.help-inline').fadeOut("fast", function () {
                $(this).remove();
            });
            $(this).parents('.control-group').removeClass('error');
        });
    }
    
    function getSelected(field_id) {
        var selection = [];
        var id = "#" + field_id;
        $(id).find("button").each(function (i) {
            if ($(this).hasClass("active")) selection.push(i);
        });
        if (selection.length === 0) {
            addError(field_id,"Please select an option");
        }
        return selection;
    }
    
    var header = "", body = "", footer = "";
    header += '<div class="modal-header">';
    header += '<h3>Select Weather Conditions</h3>';
    header += '</div>';
    
    body += '<div class="modal-body">';
    body += '<form id="id_weather_form" class="form-horizontal">';
    body += '<fieldset>';
    $.each(weatherFormTemplate, function (i, v) {
        body += setupRadioControlGroup(v);
    });
    body += '</fieldset>';
    body += '</form>';
    body += '</div>';

    footer += '<div class="modal-footer">';
    footer += '<a href="#" id="id_stab" class="btn btn-primary">OK</a>';
    footer += '</div>';
    $("#myModal").html(header + body + footer);

    if (undefined !== init) {
        $("#"+weatherFormTemplate[0].buttons[init[0]].id).button("toggle");
        switch (init[0]) {
        case 0:
            $("#"+weatherFormTemplate[1].buttons[init[1]].id).button("toggle");
            $("#id_sunlight_group").removeClass("hide");
            $("#id_cloud_group").addClass("hide");
            break;
        case 1:
            $("#"+weatherFormTemplate[2].buttons[init[1]].id).button("toggle");
            $("#id_sunlight_group").addClass("hide");
            $("#id_cloud_group").removeClass("hide");        
            break;
        }
        $("#"+weatherFormTemplate[3].buttons[init[2]].id).button("toggle");        
    }
    
    $("#id_day").on("click", function (e) {
        $("#id_sunlight_group").removeClass("hide");
        $("#id_cloud_group").addClass("hide");
    });
    $("#id_night").on("click", function (e) {
        $("#id_sunlight_group").addClass("hide");
        $("#id_cloud_group").removeClass("hide");        
    });
    $("#id_stab").on("click", function (e) {
        var c, s, result = [];
        var dn = getSelected("id_day_night");
        var w  = getSelected("id_wind");
        
        if (dn.length > 0) {
            result.push(dn[0]);
            if (dn[0] === 0) { // Day selected
                s = getSelected("id_sunlight");
                if (s.length > 0) result.push(s[0]);
            }
            else {  // Night selected
                c = getSelected("id_cloud");
                if (c.length > 0) result.push(c[0]);
            }
        }
        
        if (w.length > 0) result.push(w[0]);

        if (result.length === 3) {
            $("#myModal").modal("hide");
            if (undefined !== resultFunc) resultFunc(result);
        }
    });
}

var bar = ['<div id="id_cavity_p_bar" class="progress progress-success">' +
           '<div id="id_cavity_p_prog" class="bar" style="width:20%;"><span id="id_cavity_p_val" class="ui-label"><b>20.0</b></span></div>' +
           '</div>',
           '<div id="id_cavity_t_bar" class="progress progress-warning">' +
           '<div id="id_cavity_t_prog" class="bar" style="width:30%;"><span id="id_cavity_t_val" class="ui-label"><b>30.0</b></span></div>' +
           '</div>', 
           '<div id="id_wb_t_bar" class="progress progress-danger">' +
          '<div id="id_wb_t_prog" class="bar" style="width:40%;"><span id="id_wb_t_val" class="ui-label"><b>40.0</b></span></div>' +
          '</div>'];


function updateBar(id_sp, id_val, id_prog, id_bar, sp, val) {
    var unit, prog, barClass;
    if (sp !== null) {
        barClass = "progress progress-success";
        if (id_sp ==  '#id_cavity_p_sp') {
            unit = 'Torr';
            if (Math.abs(val-sp) > 5.0) {
                barClass = "progress progress-warning";
            }
            prog = 100.0*Math.exp(-Math.abs(0.05*(val-sp)/5.0));
        } else {
            unit = 'C';
            if (Math.abs(val-sp) > 0.3) {
                barClass = "progress progress-warning";
            }
            prog = 100.0*Math.exp(-Math.abs(0.05*(val-sp)/0.3));
        }
        $(id_sp).html("<h5>" + sp.toFixed(1) + " " + unit + "</h5>");
        $(id_val).html("<b>" + val.toFixed(1) + "</b>");
        $(id_prog).attr("style", "width:" + prog + "%")
        $(id_bar).attr("class", barClass);
    } else {
        $(id_sp).html("<h5> Unavailable </h5>");
        $(id_val).html("");
        $(id_prog).attr("style", "width:100%")
        $(id_bar).attr("class", "progress progress-error");
    }
    
}

function setupBars() {
    updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", 140.0, 150.0);
    updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", 45.0, 44.8);
    updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", 45.0, 25.0);    
}

function updateProgress() {
    var cavity_p_val, cavity_p_sp, cavity_t_val, cavity_t_sp, wb_t_val, wb_t_sp;
    if (!CSTATE.getting_warming_status) {
        CSTATE.getting_warming_status = true;
        var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
        call_rest(CNSNT.svcurl, "driverRpc", dtype, {"func": "getWarmingState", "args": "[]"},
                function (data, ts, jqXHR) {
                if (data.result.value !== undefined) {
                    cavity_p_val = data.result.value['CavityPressure'][0];
                    cavity_p_sp = data.result.value['CavityPressure'][1];
                    cavity_t_val = data.result.value['CavityTemperature'][0];
                    cavity_t_sp = data.result.value['CavityTemperature'][1];
                    wb_t_val = data.result.value['WarmBoxTemperature'][0];
                    wb_t_sp = data.result.value['WarmBoxTemperature'][1];
                    updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", cavity_p_sp, cavity_p_val);
                    updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", cavity_t_sp, cavity_t_val);
                    updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", wb_t_sp, wb_t_val);
                } else {
                    updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", null, 0.0);
                    updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", null, 0.0);
                    updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", null, 0.0);
                }
                CSTATE.getting_warming_status = false;
            },
            function (jqXHR, ts, et) {
                $("#errors").html(jqXHR.responseText);
                updateBar("#id_cavity_p_sp", "#id_cavity_p_val", "#id_cavity_p_prog", "#id_cavity_p_bar", null, 0.0);
                updateBar("#id_cavity_t_sp", "#id_cavity_t_val", "#id_cavity_t_prog", "#id_cavity_t_bar", null, 0.0);
                updateBar("#id_wb_t_sp", "#id_wb_t_val", "#id_wb_t_prog", "#id_wb_t_bar", null, 0.0);
                CSTATE.getting_warming_status = false;
            }
            );
    }
    if (!CSTATE.end_warming_status){
        TIMER.progress = setTimeout(updateProgress, CNSNT.progressUpdatePeriod);
    }
}


function initialize(winH, winW) {
    var container = $("#myModal");
    $("#id_jsTable").html(tableFuncs.makeTable(tableData, template));
    $("#id_jsTable table").addClass("table table-condensed table-striped");
    $("#id_jsTable table tbody").addClass("sortable");
    $(".sortable").sortable({helper: tableFuncs.sortableHelper});
    $("#id_jsTable tbody").on("click", "a.table-delete-row", function (e) {
        $(e.currentTarget).closest("tr").remove();
    });
    $("#id_jsTable table").on("click", "a.table-clear", function (e) {
        $(e.currentTarget).closest("table").find("tbody").empty();
    });
    $("#id_jsTable tbody").on("click", "a.table-edit-row", function (e) {
        tableFuncs.editRow($(e.currentTarget).closest("tr"), template, container, editTableChrome, beforeShow);
    });
    $("#id_jsTable table").on("click", "a.table-new-row", function (e) {
        tableFuncs.insertRow(e, template, container, editTableChrome, beforeShow, initRow);
    });
    makeWeatherForm(function (result) {
        alert(JSON.stringify(result));
    }, [1, 1, 0]);
    $("#id_progress_expt").html(bar.join("\n"));
    setupBars();
}

