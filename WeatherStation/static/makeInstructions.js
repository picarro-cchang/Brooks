/* Generate a report by submitting an instructions file to the P3 server and waiting for the 
components to be generated. Assemble the report and allow it to be saved */

var TIMER = {
        status: null    // time to retrieve status
    };

var CSTATE = {
        ticket: null,       // Hash of instructions used as key to retrieve status, etc
        editRow: null,      // Row of table currently being edited
        reportImages: []    // Handles to composite maps in the DOM for report
    };

var CNSNT = {
        // The following is a template for the regions table. It contains the headings for the columns
        //  and an optional radioButton which can be inserted before the first column to allow a row to be
        //  selected. The key radioButtonHeading is present if the radioButton is to be included, and its value
        //  is used to label the radioButton column in the header line
        regions: {id:"regionTable",
                  keys:['name','minLng','maxLng','minLat','maxLat','baseImage'],
                  headings:['Name','Min Lng','Max Lng','Min Lat','Max Lat','Base Image'],radioButtonHeading:'',
                  parsers:[String,parseFloat,parseFloat,parseFloat,parseFloat,String],
                  form_ids:["id_name","id_min_lng","id_max_lng","id_min_lat","id_max_lat","id_base_image_type"],
                  extraHeadings:['Status']},
        runs: {id:"runTable",
                  keys:['analyzer','startEtm','endEtm','path','markerType','markerColor','wedges','swath','minAmpl','maxAmpl','exclRadius','stabClass'],
                  headings:['Analyzer','Start Epoch','End Epoch','Path','Marker Type','Marker Color','Wedges','Swath','Min Ampl','Max Ampl','Excl Radius','Stab Class'],radioButtonHeading:'',
                  parsers:[String,String,String,String,String,String,String,String,parseFloat,parseFloat,parseFloat,String],
                  form_ids:["id_analyzer","id_start_etm","id_end_etm","id_path","id_marker_type","id_marker_color","id_wedges","id_swath","id_min_ampl","id_max_ampl","id_excl_radius","id_stab_class"]},
        svcurl: "/rest"
    };

var TXT = {
        addByCorners:  'Specify Region by Corner Coordinates',
        addByPlatName: 'Specify Region by Plat Name',
        addPlatOk: 'OK',
        addRegionCornersOk: 'OK',
        editPlatOk: 'OK',
        editRegionCornersOk: 'OK',
        addRun: 'Specify Parameters of Run',
        addRunOk: 'OK',
        cancel: 'Cancel',
        editRunOk: 'OK'
    };

var HBTN = {
        cancelBtn: '<button id="id_cancelBtn" type="button" onclick="closeModal();" class="btn btn-primary">' + TXT.cancel + '</button>',
        addPlatOkBtn: '<button id="id_addPlatOkBtn" type="button" onclick="addOrEditPlatOk(false);" class="btn btn-primary">' + TXT.addPlatOk + '</button>',
        addRegionCornersOkBtn: '<button id="id_addRegionCornersOkBtn" type="button" onclick="addOrEditRegionCornersOk(false);" class="btn btn-primary">' + TXT.addRegionCornersOk + '</button>',
        editPlatOkBtn: '<button id="id_editPlatOkBtn" type="button" onclick="addOrEditPlatOk(true);" class="btn btn-primary">' + TXT.editPlatOk + '</button>',
        editRegionCornersOkBtn: '<button id="id_editRegionCornersOkBtn" type="button" onclick="addOrEditRegionCornersOk(true);" class="btn btn-primary">' + TXT.editRegionCornersOk + '</button>',
        addRunOkBtn: '<button id="id_addRunOkBtn" type="button" onclick="addOrEditRunOk(false);" class="btn btn-primary">' + TXT.addRunOk + '</button>',
        editRunOkBtn: '<button id="id_editRunOkBtn" type="button" onclick="addOrEditRunOk(true);" class="btn btn-primary">' + TXT.editRunOk + '</button>'
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
//  Modal box utilities
// ============================================================================
function closeModal() {
    $("#id_modal").html("");
    $("#id_modal").modal("hide").removeClass("modal");
}

function hideTips()
{
    $(".validate_tips").hide();
}

function showTips(text)
{
    $(".validate_tips").html(text).show();
}

// ============================================================================
//  Table handling utilities
// ============================================================================

function makeEmptyTable(template)
{
    var i, j, row, headings = template.headings, result='', id = template.id;
    if (template.hasOwnProperty('radioButtonHeading')) {
        result += '<table id="'+id+'" class="table table-striped withRadioButton"><thead><tr>';
        result += '<th>' + template.radioButtonHeading + '</th>';
    } else {
        result += '<table id="'+id+'"><thead><tr>';
    }
    for (i=0;i<headings.length;i++) {
        result += '<th>' + headings[i] + '</th>';
    }
    if (template.hasOwnProperty('extraHeadings')) {
        for (i=0;i<template.extraHeadings.length;i++) {
            result += '<th>' + template.extraHeadings[i] + '</th>';
        }
    }
    result += '</tr></thead><tbody></tbody></table>';
    return result;
}

function clearTable(template)
{
    $("#" + template.id + " tbody tr").remove();
}

function setCell(template,row,col,value)
{
    $('#' + template.id + ' > tbody tr:eq(' + row + ') td:eq(' + col + ')').html(value)
}

function getRowItems(row)
{
    var items = [];
    $.each($(row).children(),
        function(index,value){ 
            items.push($(value).html()); 
        });
    return items;
}

function makeRowAndCheck(template,data)
// Use the template to make a row using the specified data and
//  check that the row is not already in the table. Return the
//  row on success, or false if the row is a duplicate.
{
    var newRow='', duplicate=false;
    
    if (template.hasOwnProperty('radioButtonHeading')) {
        newRow += '<td><input type="radio" name="' + template.id + '"/></td>';
    }
    $.each(data,function(index,value){ newRow += '<td>' + value + '</td>'; });
    // Fill up extra fields with blanks
    if (template.hasOwnProperty('extraHeadings')) {
        $.each(template.extraHeadings,function(index,value){ newRow += '<td>' + '</td>'; });
    }
    // Check if the new row is already in the table, returning false if it is
    $('#' + template.id + ' > tbody tr').each( function(index,tableRow) { 
        var i, start, end, same = true;
        var oldItemList, newItemList;
        // We need to check equality of newRow and an existing row in the table. However, if there is a radioButton,
        // the first <td></td> item should be ignored
        oldItemList = getRowItems(tableRow);
        newItemList = getRowItems('<tr>' + newRow + '</tr>');
        start = 0;
        if (template.hasOwnProperty('radioButtonHeading')) start += 1;
        end = start + template.headings.length;
        for (i=start;i<end;i++) {
            if (oldItemList[i] !== newItemList[i]) {
                same = false;
                break;
            }
        }
        duplicate = duplicate || same;
    });
    if (duplicate) return false;
    return newRow;
}

function addToTable(template,data) {
    newRow = makeRowAndCheck(template,data);
    if (newRow) {
        $('#' + template.id + ' > tbody:last').append('<tr>' + newRow + '</tr>');
    }
    return newRow;
}

function tableAsStruct(template)
{
    var result = [];
    var i, temp;
    $('#' + template.id + ' > tbody tr').each( function(ir,row) {
        temp = {};
        i = 0;
        $(this).children('td').each( function(ic,col) {
            if (i<template.headings.length && !(template.hasOwnProperty('radioButtonHeading') && ic==0)) {
                temp[template.keys[i]] = template.parsers[i](col.innerHTML);
                i += 1;
            }
        });
        result.push(temp);
    })
    return result;
}

function tableRow(template,row)
{
    var temp=[], i=0;
    $(row).children('td').each( function(ic,col) {
        if (i<template.headings.length && !(template.hasOwnProperty('radioButtonHeading') && ic==0)) {
            temp.push(col.innerHTML);
            i += 1;
        }
    });
    return temp;
}

// ============================================================================
//  Adding region by plat name
// ============================================================================

function addError(field_id,message) {
    var id = "#" + field_id;
    if ($(id).next('.help-inline').length == 0) {
        $(id).after('<span class="help-inline">' + message + '</span>');
        $(id).parents("div .control-group").addClass("error")
    }
    $(id).bind('focus keypress', function(){
        $(this).next('.help-inline').fadeOut("fast", function(){
            $(this).remove();
        });
        $(this).parents('.control-group').removeClass('error');
    });
}

function addTip(form_id,message) {
    showTips(message);
    $("#" + form_id + " input,#" + form_id + " select").bind('focus keypress', function(){
        $(".validate_tips").fadeOut("fast");
    });
}

function addRegionsByName() {
    $('#id_modal').addClass("modal").html(addOrEditRegionsByNameChrome(HBTN.addPlatOkBtn))
    setupRegionsByNameForm();
    $("#id_modal input, #id_modal select").keyup(function(event) { if (event.which == 13) { addOrEditPlatOk(false); } } )
    $("#id_modal").modal();
}

function setupRegionsByNameForm() {
    // Note that it is only after we have added the form (generated by addRegionsByNameChrome()) to the DOM that it is possible to refer to
    //  entities such as "#id_name" and "#id_base_image_type". More subtly, we cannot use $("form").submit(function() {return false;});
    //  in the init function to disable submission (on Enter) since at that time, there are no forms in the DOM.    
    $( "#id_name" ).typeahead({ajax:{url:"/rest/autocompletePlat",triggerLength:2,method:"get",timeout:100},items:20}).focus();
    $.each(['Plat image','Google map image','Google satellite image'], function(key, value) {   
         $('#id_base_image_type').append($("<option/>",{value:value}).text(value)); 
    });
    hideTips();
    $("form").submit(function() {return false;});    
}

function addOrEditRegionsByNameChrome(okButton)
{
    var hdr='', msg='', footer='';
    
    hdr += '<div class="modal-header">';
    hdr += '<h3>' + TXT.addByPlatName + '</h3>';
    hdr += '</div>';
    
    msg += '<div class="modal-body">'
    msg += '<form id="id_regions_by_name_form" class="form-horizontal" >';
    msg += '<fieldset>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_name">Plat</label>';
    msg += '    <div class="controls">';
    msg += '        <input type="text" name="plat" id="id_name" class="input-xlarge typeahead" data-provide="typeahead"/>';
    msg += '    </div>';
    msg += '</div>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_base_image_type">Base Image Type</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="map_type" id="id_base_image_type" class="input-xlarge"></select>';
    msg += '    </div>';
    msg += '</div>';

    msg += '</fieldset>';
    msg += '</form>';
    // msg += '<p class="validate_tips alert alert-error"></p>'
    msg += '</div>';
    
    footer += '<div class="modal-footer">'
    footer += '<p class="validate_tips alert alert-error"></p>'
    footer += okButton;
    footer += HBTN.cancelBtn;
    footer += '</div>'
    return hdr + msg + footer;
}

function addOrEditPlatOk(editFlag) {
    // We assume that the plat names in the JSON file are all upper case
    var plat = $("#id_name").val();
    var base_image_type = $("#id_base_image_type").val();
    call_rest(CNSNT.svcurl, 'platCorners', {plat:plat}, 
        function (data, ts, jqXHR) {
            var rowDat;
            if ("MIN_LAT" in data) {
                rowDat = [data.PLAT,data.MIN_LONG,data.MAX_LONG,data.MIN_LAT,data.MAX_LAT,base_image_type]
                newRow = makeRowAndCheck(CNSNT.regions,rowDat);
                if (newRow) {
                    if (editFlag) {
                        $(CSTATE.editRow).replaceWith('<tr class="editRow">' + newRow + '</tr>');
                        $(".editRow input:radio").prop("checked",true);
                        $(".editRow").removeClass("editRow");
                    }
                    else {
                        $('#' + CNSNT.regions.id + ' > tbody:last').append('<tr>' + newRow + '</tr>');
                    }
                    closeModal();
                } else {
                    addTip("id_regions_by_name_form","Duplicate row");
                }
            }
            else {
                addError("id_name","Bad plat name");
            }
        },
        function (data, et, jqXHR) {
            closeModal();
        }
    );
}
// ============================================================================
//  Adding region by corners
// ============================================================================

function addRegionsByCorners() {
    $('#id_modal').addClass("modal").html(addOrEditRegionsByCornersChrome(HBTN.addRegionCornersOkBtn));
    setupRegionsByCornersForm();
    $("#id_modal input, #id_modal select").keyup(function(event) { if (event.which == 13) { addOrEditRegionCornersOk(false); } } )
    $("#id_modal").modal();
}

function setupRegionsByCornersForm() {
    // Note that it is only after we have added the form (generated by addRegionsByCorners_chrome()) to the DOM that it is possible to refer to
    //  entities such as "#id_name" and "#id_base_image_type". More subtly, we cannot use $("form").submit(function() {return false;});
    //  in the init function to disable submission (on Enter) since at that time, there are no forms in the DOM.
    $.each(['Google map image','Google satellite image'], function(key, value) {   
         $('#id_base_image_type').append($("<option/>",{value:value}).text(value)); 
    });
    hideTips();
    $("form").submit(function() {return false;});
}

function addOrEditRegionsByCornersChrome(okButton)
{
    var hdr='', msg='', footer='';
    
    hdr += '<div class="modal-header">';
    hdr += '<h3>' + TXT.addByCorners + '</h3>';
    hdr += '</div>';
    
    msg += '<div class="modal-body">'
    msg += '<form class="form-horizontal" id="id_regions_by_corners_form">';
    msg += '<fieldset>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_name">Name</label>';
    msg += '    <div class="controls">';
    msg += '        <input type="text" name="name" id="id_name" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_min_lng">Minimum longitude</label>';
    msg += '    <div class="controls">';
    msg += '        <input type="text" name="min_lng" id="id_min_lng" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_max_lng">Maximum longitude</label>';
    msg += '    <div class="controls">';
    msg += '        <input type="text" name="max_lng" id="id_max_lng" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_min_lat">Minimum latitude</label>';
    msg += '    <div class="controls">';
    msg += '        <input type="text" name="min_lat" id="id_min_lat" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_max_lat">Maximum latitude</label>';
    msg += '    <div class="controls">';
    msg += '        <input type="text" name="max_lat" id="id_max_lat" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_base_image_type">Base Image Type</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="map_type" id="id_base_image_type" class="input-xlarge"></select>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '</fieldset>';
    msg += '</form>';
    msg += '<p class="validate_tips alert alert-error"></p>'
    msg += '</div>';
    
    footer += '<div class="modal-footer">'
    footer += okButton;
    footer += HBTN.cancelBtn;
    footer += '</div>'
    return hdr + msg + footer;
}

function addOrEditRegionCornersOk(editFlag) {
    // We assume that the plat names in the JSON file are all upper case
    var name   = $.trim($("#id_name").val());
    var minLng = parseFloat($("#id_min_lng").val());
    var maxLng = parseFloat($("#id_max_lng").val());
    var minLat = parseFloat($("#id_min_lat").val());
    var maxLat = parseFloat($("#id_max_lat").val());
    var base_image_type = $("#id_base_image_type").val();
    var rowDat, anyErrors = false;
    
    if (name.length < 3) {
        addError("id_name","Name should have >=3 characters");
        anyErrors = true;
    }
    name = '[' + name.toUpperCase() + ']';
    
    // Check validity of corner values
    if (minLng>=maxLng || (maxLng-minLng)>1.0 || minLng<-180.0 || maxLng>180.0 || isNaN(minLng) || isNaN(maxLng)) {
        addError("id_min_lng","Bad longitude range");
        addError("id_max_lng","Bad longitude range");
        anyErrors = true;
    }
    if (minLat>=maxLat || (maxLat-minLat)>1.0 || minLat<-90.0 || maxLat>90.0 || isNaN(minLat) || isNaN(maxLat)) {
        addError("id_min_lat","Bad latitude range");
        addError("id_max_lat","Bad latitude range");
        anyErrors = true;
    }

    if (!anyErrors) {
        rowDat = [name,minLng,maxLng,minLat,maxLat,base_image_type];
        newRow = makeRowAndCheck(CNSNT.regions,rowDat);
        if (newRow) {
            if (editFlag) {
                $(CSTATE.editRow).replaceWith('<tr class="editRow">' + newRow + '</tr>');
                $(".editRow input:radio").prop("checked",true);
                $(".editRow").removeClass("editRow");
            }
            else {
                $('#' + CNSNT.regions.id + ' > tbody:last').append('<tr>' + newRow + '</tr>');
            }
            closeModal();
        } 
        else {
            addTip("id_regions_by_corners_form","Duplicate row");
        }
    }
}

// ============================================================================
//  Edit a region
// ============================================================================

function editRegion(row)
{
    var fields = CNSNT.regions.form_ids;
    var values = tableRow(CNSNT.regions,row);
    var name, fieldDict = {};
    if (values.length === 0) {
        alert('Please select a row to edit');
        return;
    }
    CSTATE.editRow = row;
    for (i=0;i<fields.length;i++) {
        fieldDict[fields[i]] = values[i];
    }
    name = fieldDict["id_name"];
    
    if (name.charAt(0)==="[" && name.charAt(name.length-1)==="]") {
        fieldDict["id_name"] = name.substring(1,name.length-1);
        $('#id_modal').addClass("modal").html(addOrEditRegionsByCornersChrome(HBTN.editRegionCornersOkBtn));
        setupRegionsByCornersForm();
        $("#id_modal input, #id_modal select").keyup(function(event) { if (event.which == 13) { addOrEditRegionCornersOk(true); } } )        
        setFormFields("id_regions_by_corners_form",fieldDict);
    }
    else {
        $('#id_modal').addClass("modal").html(addOrEditRegionsByNameChrome(HBTN.editPlatOkBtn));
        setupRegionsByNameForm();
        $("#id_modal input, #id_modal select").keyup(function(event) { if (event.which == 13) { addOrEditPlatOk(true); } } )
        setFormFields("id_regions_by_name_form",fieldDict);
    }
    $("#id_modal").modal();
}

// ============================================================================
//  Adding run
// ============================================================================

function setupRunForm() {
    // Note that it is only after we have added the form (generated by addOrEditRegionsByCornersChrome()) to the DOM that it is possible to refer to
    //  entities such as "#id_path" and "#id_wedges". More subtly, we cannot use $("form").submit(function() {return false;});
    //  in the init function to disable submission (on Enter) since at that time, there are no forms in the DOM.
    setOptions('id_path',['No','Yes']);
    setOptions('id_marker_type', ['None','Concentration','Rank']);
    setOptions('id_marker_color', ['Red','Green','Blue','Yellow','Magenta','Cyan']);
    setOptions('id_wedges',['No','Yes','Red','Green','Blue','Yellow','Magenta','Cyan']);
    setOptions('id_swath', ['No','Yes','Red','Green','Blue','Yellow','Magenta','Cyan']);
    setOptions('id_min_ampl',['0.03','0.05','0.1','0.2','0.5','1.0']);
    setOptions('id_max_ampl',['','0.05','0.1','0.2','0.5','1.0']);
    setOptions('id_excl_radius',['0','10','20','30','50']);
    setOptions('id_stab_class',['A','B','C','D','E','F']);
    $.datetimeEntry.setDefaults({spinnerImage: null, datetimeFormat: 'Y-O-D  H:M', show24Hours:true});
    $('input.datetimeRange').datetimeEntry({beforeShow:datetimeRange});
    $( "#id_analyzer" ).focus();
    hideTips();
    $("form").submit(function() {return false;});
}


function addRun() {
    $('#id_modal').addClass("modal").html(addOrEditRunChrome(HBTN.addRunOkBtn));
    setupRunForm();
    $("#id_modal input, #id_modal select").keyup(function(event) { if (event.which == 13) { addOrEditRunOk(false); } } )
    setFormFields("id_run_form",{id_analyzer:"FCDS2008", id_path:'Yes', id_wedges:'Yes', id_min_ampl:'0.05', id_stab_class:'D', id_excl_radius:'30'})
    $("#id_modal").modal();
}

function datetimeRange(input) {
    return {minDatetime: (input.id=='id_end_etm'   ? $('#id_start_etm').datetimeEntry('getDatetime'):null),
            maxDatetime: (input.id=='id_start_etm' ? $('#id_end_etm').datetimeEntry('getDatetime'):null)};
}

function addOrEditRunChrome(okButton)
{
    var hdr='', msg='', footer='';
    
    hdr += '<div class="modal-header">';
    hdr += '<h3>' + TXT.addRun + '</h3>';
    hdr += '</div>';
    
    msg += '<div class="modal-body" style="max-height:550px;">'
    msg += '<form id="id_run_form" class="form-horizontal" >';
    msg += '<fieldset>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_analyzer">Analyzer</label>';
    msg += '    <div class="controls">';
    msg += '        <input type="text" name="analyzer" id="id_analyzer" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_start_etm">Start Epoch Time</label>';
    msg += '    <div class="controls">';
    msg += '        <input id="id_start_etm" class="datetimeRange input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_end_etm">End Epoch Time</label>';
    msg += '    <div class="controls">';
    msg += '        <input id="id_end_etm" class="datetimeRange input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';

    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_path">Show Path</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="path" id="id_path" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_marker_type">Marker Type</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="marker_type" id="id_marker_type" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_marker_color">Marker Color</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="marker_color" id="id_marker_color" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_wedges">Show Wedges</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="wedges" id="id_wedges" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_swath">Show Swath</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="swath" id="id_swath" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_min_ampl">Minimum Amplitude</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="min_ampl" id="id_min_ampl" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_max_ampl">Maximum Amplitude</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="max_ampl" id="id_max_ampl" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_excl_radius">Exclusion Radius</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="excl_radius" id="id_excl_radius" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    
    msg += '<div class="control-group">';
    msg += '    <label class="control-label" for="id_stab_class">Stability Class</label>';
    msg += '    <div class="controls">';
    msg += '        <select name="stab_class" id="id_stab_class" class="input-xlarge"/>';
    msg += '    </div>';
    msg += '</div>';
    msg += '</fieldset>';
    msg += '</form>';
    msg += '<p class="validate_tips alert alert-error"></p>'
    msg += '</div>';
    
    footer += '<div class="modal-footer">'
    footer += okButton;
    footer += HBTN.cancelBtn;
    footer += '</div>'
    return hdr + msg + footer;
}

function addOrEditRunOk(editFlag) {
    var template = CNSNT.runs;
    var fields = template.form_ids;
    var i, data = [], newRow = '';
    
    for (i=0;i<fields.length;i++) {
        data.push($("#"+fields[i]).val());
    }
    newRow = makeRowAndCheck(CNSNT.runs,data);
    if (newRow) {
        if (editFlag) {
            $(CSTATE.editRow).replaceWith('<tr class="editRow">' + newRow + '</tr>');
            $(".editRow input:radio").prop("checked",true);
            $(".editRow").removeClass("editRow");
        }
        else {
            $('#' + CNSNT.runs.id + ' > tbody:last').append('<tr>' + newRow + '</tr>');
        }
        closeModal();
    } 
    else {
        addTip("id_run_form","Duplicate row");
    }
}

function editRun(row)
{
    var fields = CNSNT.runs.form_ids;
    var values = tableRow(CNSNT.runs,row);
    var fieldDict = {};
    if (values.length === 0) {
        alert('Please select a row to edit');
        return;
    }
    CSTATE.editRow = row;
    for (i=0;i<fields.length;i++) {
        fieldDict[fields[i]] = values[i];
    }
    $('#id_modal').addClass("modal").html(addOrEditRunChrome(HBTN.editRunOkBtn));
    setupRunForm();
    $("#id_modal input, #id_modal select").keyup(function(event) { if (event.which == 13) { addOrEditRunOk(true); } } )
    setFormFields("id_run_form",fieldDict);
    $("#id_modal").modal();
}

function setFormFields(formId,fieldDict)
/* Set the fields in the specified form according to the contents of fieldDict.
The keys in fieldDict are the ids of the various elements of the form */
{
    for (key in fieldDict) {
        if (fieldDict.hasOwnProperty(key)) {
            $('#' + formId + ' #' + key).val(fieldDict[key])  
        }
    }
}

function setOptions(selectId,optionList)
/* Set the list of options for the specified select element */
{
    $.each(optionList, function(key, value) {   
         $('#'+selectId).append($("<option/>",{value:value}).text(value)); 
    });
}

// ============================================================================
// Make instructions from tables
// ============================================================================
function makeJsonInstructions()
{
    var result1 = tableAsStruct(CNSNT.regions);
    var result2 = tableAsStruct(CNSNT.runs);
    var result = JSON.stringify({regions:result1,runs:result2},null,"    ") + '\n'; 
    return result;
}

function fillTableFromInstructions(template,instrList)
{
    var i,j,irow,row;
    $("#" + template.id + " tbody tr").remove();
    for (j=0;j<instrList.length;j++) {
        irow = instrList[j];
        row = [];
        for (i=0;i<template.keys.length;i++) {
            if (irow.hasOwnProperty(template.keys[i]) && irow[template.keys[i]] !== null) {
                row.push(irow[template.keys[i]]);
            } else {
                row.push('');
            }
        }
        addToTable(template,row);
    }
}

// ============================================================================
//  Routines to handle opening of instructions file
// ============================================================================
function updateTables(contents) {
    $("#id_instructions").val(contents);
    instrDict = JSON.parse(contents);
    if (instrDict.hasOwnProperty("regions")) {
        fillTableFromInstructions(CNSNT.regions,instrDict.regions);
    }
    if (instrDict.hasOwnProperty("runs")) {
        fillTableFromInstructions(CNSNT.runs,instrDict.runs);
    }
}

function readerOnLoad(theFile) {
    return function(e) {
        var instrDict, contents = e.target.result, lines;
        // Do simple validation to reject malformed files quickly
        try {
            lines = contents.split('\n',1024);
            lines.shift();
            JSON.parse(lines.join('\n'));
        }
        catch (e) {
            alert("Invalid instructions file");
            return;
        }
        call_rest(CNSNT.svcurl, 'validate', {contents:contents}, 
            function (data, ts, jqXHR) {
                var contents;
                if (data.hasOwnProperty("error")) {
                    alert("Invalid instructions file");
                }
                else {
                    var contents = data.contents;
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
    for (var i = 0, f; f = files[i]; i++) {
        reader = new FileReader();
        // Set up the reader to read a text file
        $("#id_instr_upload_name").val(f.name)
        reader.readAsText(f);
        reader.onload = readerOnLoad(f);
    }
}

function handleFileDrop(evt) {
    evt.stopPropagation();
    evt.preventDefault();
    var files = evt.dataTransfer.files; // FileList object.
    if (files.length > 1) alert('Cannot process more than one file');
    else {
        for (var i = 0, f; f = files[i]; i++) {
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
    call_rest(CNSNT.svcurl,"instrUpload", {contents:instr}, 
        function (data, ts, jqXHR) {
            var fname = $("#id_instr_upload_name").val();
            CSTATE.reportImages = [];
            CSTATE.ticket = data.ticket;
            $(window.location).attr('href','/makeInstructions?' + $.param({ticket:data.ticket,fname:fname}));
            // $("#id_results_container img").remove();
            // TIMER.status = setTimeout(statusTimer, 1000);
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
    var key, region, words, s, t, url, statByRegion = {};
    for (key in statusDict) {
        words = key.split('.');
        if (words[0] === 'composite') {
            region = parseInt(words[1]);
            if (!statByRegion.hasOwnProperty(region)) statByRegion[region] = "";
            if ("done" in statusDict[key]) {
                statByRegion[region] += "C";
            }
        }
        else if (words[0] === 'baseMap') {
            region = parseInt(words[1]);
            if (!statByRegion.hasOwnProperty(region)) statByRegion[region] = "";
            if ("done" in statusDict[key]) {
                statByRegion[region] += "B";
            }
        }
        else if (words[0] === 'pathMap') {
            region = parseInt(words[1]);
            if (!statByRegion.hasOwnProperty(region)) statByRegion[region] = "";
            if ("done" in statusDict[key][0]) {
                statByRegion[region] += "P";
            }
            if ("done" in statusDict[key][1]) {
                statByRegion[region] += "W";
            }
        }
        else if (words[0] === 'markerMap') {
            region = parseInt(words[1]);
            if (!statByRegion.hasOwnProperty(region)) statByRegion[region] = "";
            if ("done" in statusDict[key][0]) {
                statByRegion[region] += "M";
            }
            if ("done" in statusDict[key][1]) {
                statByRegion[region] += "S";
            }
        }
    }
    for (region in statByRegion) {
        s = statByRegion[region];
        url = CNSNT.svcurl+"/getComposite?"+$.param({ticket:CSTATE.ticket,region:region})
        taburl = CNSNT.svcurl+"/getReport?"+$.param({ticket:CSTATE.ticket,region:region})
        if (s.indexOf("C") >= 0) {
            t = '<b>Done <a href="' + url + '" target="_blank"> Open</a><a href="';
            t += taburl + '" target="_blank"> Report</a> </b>';
        }
        else t = "Processing" + "..........".substring(0,s.length);
        setCell(CNSNT.regions,region,7,t);
    }
}

function statusTimer()
{
    params = { "ticket":CSTATE.ticket }
    call_rest(CNSNT.svcurl, "getReportStatus", params, 
        function (data, ts, jqXHR) {
            var done = true;
            $("#id_status").val('')
            $.each(data.files,function(fName,contents) {
                $("#id_status").val($("#id_status").val() + fName + 
                "\n" + JSON.stringify(contents,null,2) + "\n");
                processStatus(contents);
                if (!("end" in contents)) done = false;
            });
            if (!done) {
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

// ============================================================================
// ============================================================================
function sortableHelper(e,tr) {
    var $originals = tr.children();
    var $helper = tr.clone();
    $helper.children().each(function(index)
        {
          // Set helper cell sizes to match the original sizes
          $(this).width($originals.eq(index).width())
        });
    return $helper;
}

function initialize(winH,winW)
{
    var contents, dropZone, name, regionTable, runsTable, ticket;
    
    regionTable = makeEmptyTable(CNSNT.regions);
    $('#id_regions_table_div').html(regionTable);
    $('#regionTable tbody').addClass('sortable').sortable({helper:sortableHelper}).disableSelection();

    runsTable = makeEmptyTable(CNSNT.runs);
    $('#id_runs_table_div').html(runsTable);
    $('#runTable tbody').addClass('sortable').sortable({helper:sortableHelper}).disableSelection();
        
    $("#id_add_by_name_button").click(addRegionsByName);
    $("#id_add_by_corners_button").click(addRegionsByCorners);
    $("#id_delete_region_button").click(function(){ $("#regionTable input:radio[name=regionTable]:checked").closest("tr").remove(); });
    $("#id_edit_region_button").click(function(){ editRegion($("#regionTable input:radio[name=regionTable]:checked").closest("tr")); });
    $("#id_clear_all_regions_button").click(function(){ clearTable(CNSNT.regions); });

    $("#id_add_run_button").click(addRun);
    $("#id_delete_run_button").click(function(){ $("#runTable input:radio[name=runTable]:checked").closest("tr").remove(); });
    $("#id_edit_run_button").click(function(){ editRun($("#runTable input:radio[name=runTable]:checked").closest("tr")); });
    $("#id_clear_all_runs_button").click(function(){ clearTable(CNSNT.runs); });
    
    $("#id_instr_upload_name").val('');
    $("#id_instr_upload").change( function(e){ handleFileSelect(e); });
    // Setup the dnd listeners.
    dropZone = document.getElementById('id_instructions');
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
        $("#id_instructions").val(instr);
        $("#id_instr_upload_name").val(name);
    });
    
    $("#id_make_report").click(function(e){ makeReport(); e.preventDefault(); }); 
    ticket = $("#id_hidden_ticket").text();
    contents = $("#id_hidden_contents").text();
    name = $("#id_hidden_name").text();
    $('#id_instructions').val(contents);
    $("#id_instr_upload_name").val(name);
    if (contents) {
        $(".sortable").sortable('disable');
        updateTables(contents);
        CSTATE.ticket = ticket;
        TIMER.status = setTimeout(statusTimer, 1000);
    }
    $('#id_status').val('');
}
