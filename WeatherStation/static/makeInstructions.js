/* Generate a report by submitting an instructions file to the P3 server and waiting for the 
components to be generated. Assemble the report and allow it to be saved */

var TIMER = {
        status: null    // time to retrieve status
    };

var CSTATE = {
        ticket: null    // Hash of instructions used as key to retrieve status, etc
    };

var CNSNT = {
        // The following is a template for the regions table. It contains the headings for the columns
        //  and an optional radioButton which can be inserted before the first column to allow a row to be
        //  selected. The key radioButtonHeading is present if the radioButton is to be included, and its value
        //  is used to label the radioButton column in the header line
        regions: {id:"regionTable",headings:['Plat','Min Lng','Max Lng','Min Lat','Max Lat','Base Image'],radioButtonHeading:'',
                  parsers:[String,parseFloat,parseFloat,parseFloat,parseFloat,String]},
        runs: {id:"runTable",headings:['Analyzer','Start Epoch','End Epoch','Path','Peaks','Wedges','Swath','Min Ampl','Max Ampl','Excl Radius','Stab Class'],radioButtonHeading:'',
                  parsers:[String,parseFloat,parseFloat,parseInt,parseInt,parseInt,parseInt,parseFloat,parseFloat,String]},
        svcurl: "/rest"
    };

var TXT = {
        addByCorners:  'Specify Region by Corner Coordinates',
        addByPlatName: 'Specify Region by Plat Name',
        addPlatOk: 'OK',
        addRegionCornersOk: 'OK',
        addRun: 'Specify Parameters of Run',
        addRunOk: 'OK',
        cancel: 'Cancel'
    };

var HBTN = {
        cancelBtn: '<div><button id="id_cancelBtn" type="button" onclick="closeModal();" class="btn primary large fullwidth">' + TXT.cancel + '</button></div>',
        addPlatOkBtn: '<div><button id="id_addPlatOkBtn" type="button" onclick="addPlatOk();" class="btn primary large fullwidth">' + TXT.addPlatOk + '</button></div>',
        addRegionCornersOkBtn: '<div><button id="id_addRegionCornersOkBtn" type="button" onclick="addRegionCornersOk();" class="btn primary large fullwidth">' + TXT.addRegionCornersOk + '</button></div>',
        addRunOkBtn: '<div><button id="id_addRunOkBtn" type="button" onclick="addRunOk();" class="btn primary large fullwidth">' + TXT.addRunOk + '</button></div>'
    };

function call_rest(call_url, method, params, success_callback, error_callback) {
    var dtype, url;
    dtype = "json";
    url = call_url + '/' + method;
    $.ajax({contentType: "application/json",
        data: $.param(params),
        dataType: dtype,
        url: url,
        type: "get",
        timeout: 60000,
        success: success_callback,
        error: error_callback
        });
}

function post_rest(call_url, method, params, success_callback, error_callback) {
    var dtype, url;
    dtype = "json";
    url = call_url + '/' + method;
    $.ajax({contentType: "application/json",
        data: $.param(params),
        dataType: dtype,
        url: url,
        type: "get",
        timeout: 60000,
        success: success_callback,
        error: error_callback
        });
}

// tableChrome NOTE: first element (index 0) in each cNarray is the "style" tag for the td div
function tableChrome(tblStyle, trStyle, c1array, c2array, c3array, c4array) {
    var tbl, i, len, body, c1sty, c2sty, c3sty, c4sty;
    tbl = '';
    body = '';
    
    c1sty = '';
    c2sty = '';
    c3sty = '';
    c4sty = '';
    
    // all passed arrays must be of same length
    if (c2array !== undefined) {
        if (c1array.length !== c2array.length) {
            return tbl;
        }
    }
    if (c3array !== undefined) {
        if (c1array.length !== c3array.length) {
            return tbl;
        }
    }
    if (c4array !== undefined) {
        if (c1array.length !== c4array.length) {
            return tbl;
        }
    }
    
    len = c1array.length;
    for (i = 0; i < len; i += 1) {
        if (i === 0) {
            c1sty = c1array[i];
            if (c2array !== undefined) {
                c2sty = c2array[i];
            }
            if (c3array !== undefined) {
                c3sty = c3array[i];
            }
            if (c4array !== undefined) {
                c4sty = c4array[i];
            }
        } else {
            body += '<tr ' + trStyle + '>';
            
            body += '<td ' + c1sty + '>' + c1array[i] + '</td>';
            if (c2array !== undefined) {
                body += '<td ' + c2sty + '>' + c2array[i] + '</td>';
            }
            if (c3array !== undefined) {
                body += '<td ' + c3sty + '>' + c3array[i] + '</td>';
            }
            if (c4array !== undefined) {
                body += '<td ' + c4sty + '>' + c4array[i] + '</td>';
            }
            
            body += '</tr>';
        }
    }
    
    tbl += '<table ' + tblStyle + '>';
    tbl += body;
    tbl += '</table>';

    return tbl;
}

function closeModal() {
    $("#id_mod_change").html("");
}

function setModalChrome(hdr, msg, click) {
    var modalChrome = "";
    modalChrome = '<div class="modal" style="position: relative; top: auto; left: auto; margin: 0 auto; z-index: 1">';
    modalChrome += '<div class="modal-header">';
    modalChrome += '<h3>' + hdr + '</h3>';
    modalChrome += '</div>';
    modalChrome += '<div class="modal-body">';
    modalChrome += msg;
    modalChrome += '</div>';
    modalChrome += '<div class="modal-footer">';
    modalChrome += click;
    modalChrome += '</div>';
    modalChrome += '</div>';
    return modalChrome;
}

function makeEmptyTable(template)
{
    var i, j, row, headings = template.headings, result='', id = template.id;
    if (template.hasOwnProperty('radioButtonHeading')) {
        result += '<table id="'+id+'" class="withRadioButton"><thead><tr>';
        result += '<th>' + template.radioButtonHeading + '</th>';
    } else {
        result += '<table id="'+id+'"><thead><tr>';
    }
    for (i=0;i<headings.length;i++) {
        result += '<th>' + headings[i] + '</th>';
    }
    result += '</tr></thead><tbody></tbody></table>';
    return result;
}

function addToTable(template,data)
{
    var newRow='', s1, s2, duplicate=false;
    if (template.hasOwnProperty('radioButtonHeading')) {
        newRow += '<td><input type="radio" name="' + template.id + '"/></td>';
    }
    $.each(data,function(index,value){ newRow += '<td>' + value + '</td>'; });
    // Check if the new row is already in the table, returning false if it is
    $('#' + template.id + ' > tbody tr').each( function(index,tableRow) { 
        // We need to check equality of newRow and an existing row in the table. However, if there is a radioButton,
        // the first <td></td> item should be ignored
        if (template.hasOwnProperty('radioButtonHeading')) {
            s1 = newRow.substring(newRow.indexOf("</td>")+5);
            s2 = tableRow.innerHTML.substring(tableRow.innerHTML.indexOf("</td>")+5);
            if (s1 === s2) duplicate=true;
        } else {
            if (newRow === tableRow.innerHTML) duplicate=true;
        }
    });
    if (duplicate) return false;
    // Add the row to the table and return true
    $('#' + template.id + ' > tbody:last').append('<tr>' + newRow + '</tr>');
    return true;
}

function tableAsStruct(template)
{
    var result = [];
    var temp, i;
    $('#' + template.id + ' > tbody tr').each( function(ir,row) {
        temp = []; 
        $(this).children('td').each( function(ic,col) {
            if (!(template.hasOwnProperty('radioButtonHeading') && ic==0)) {
                temp.push(template.parsers[temp.length](col.innerHTML));
            }
        });
        result.push(temp);
    })
    alert(JSON.stringify(result));
}

function hideTips()
{
    $("#id_tips").hide();
}

function showTips(text)
{
    $("#id_tips").html(text).show();
}

// ============================================================================
//  Adding region by plat name
// ============================================================================

function add_regions_by_name() {
    $("#id_mod_change").html(add_regions_by_name_chrome());
    // Note that it is only after we have added the form (generated by add_regions_by_name_chrome()) to the DOM that it is possible to refer to
    //  entities such as "#id_plat" and "#id_base_image_type". More subtly, we cannot use $("form").submit(function() {return false;});
    //  in the init function to disable submission (on Enter) since at that time, there are no forms in the DOM.
    $( "#id_plat" ).autocomplete({source:"/rest/autocompletePlat",minLength:2}).focus();
    // Size of $('#id_mod_change') is not defined until its html has been inserted
    $("#id_feedback").css("left","50%").css("top","50%").css("margin-left",-$('#id_mod_change').width()/2).css("margin-top",-$('#id_mod_change').height()/2);
    $.each(['Plat image','Google map image','Google satellite image'], function(key, value) {   
         $('#id_base_image_type').append($("<option/>",{value:value}).text(value)); 
    });
    hideTips();
    $("#id_mod_change input, #id_mod_change select").keyup(function(event) { if (event.which == 13) { addPlatOk(); } } )
    $("form").submit(function() {return false;});
}

function add_regions_by_name_chrome()
{
    var hdr='', msg='', footer='';
    var c1array, c2array, c3array;
    
    hdr += TXT.addByPlatName;
    
    msg += '<p id="id_tips" class="validateTips ui-state-highlight"></p>'
    msg += '<form class="well" >';
    msg += '<fieldset>';
    msg += '    <label for="id_plat">Plat</label>';
    msg += '    <input type="text" name="plat" id="id_plat" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_base_image_type">Base Image Type</label>';
    msg += '    <select name="map_type" id="id_base_image_type" class="span6" style="margin-top:5px;margin-bottom:5px;"></select>';
    msg += '</fieldset>';
    msg += '</form>';
    
    c1array = [];
    c2array = [];
    c3array = [];
    c1array.push('style="border-style: none; width: 50%;"');
    c2array.push('style="border-style: none; width: 25%;"');
    c3array.push('style="border-style: none; width: 25%;"');
    c1array.push('');
    c2array.push(HBTN.addPlatOkBtn);
    c3array.push(HBTN.cancelBtn);
    footer = tableChrome('style="border-spacing: 0px; margin-bottom: 0"', '',  c1array, c2array, c3array);
    return setModalChrome(hdr,msg,footer);
}

function addPlatOk() {
    // We assume that the plat names in the JSON file are all upper case
    var plat = $("#id_plat").val();
    var base_image_type = $("#id_base_image_type").val();
    call_rest(CNSNT.svcurl, 'platCorners', {plat:plat}, 
        function (data, ts, jqXHR) {
            if ("MIN_LAT" in data) {
                if (addToTable(CNSNT.regions,[data.PLAT,data.MIN_LONG,data.MAX_LONG,data.MIN_LAT,data.MAX_LAT,base_image_type])) {
                    closeModal();
                } else {
                    showTips("Duplicate row");
                }
            }
            else {
                $("#id_plat").addClass("ui-state-error");
                showTips("Invalid plat name");
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

function add_regions_by_corners() {
    $("#id_mod_change").html(add_regions_by_corners_chrome());
    // Note that it is only after we have added the form (generated by add_regions_by_corners_chrome()) to the DOM that it is possible to refer to
    //  entities such as "#id_plat" and "#id_base_image_type". More subtly, we cannot use $("form").submit(function() {return false;});
    //  in the init function to disable submission (on Enter) since at that time, there are no forms in the DOM.
    $( "#id_name" ).focus();
    // Size of $('#id_mod_change') is not defined until its html has been inserted
    $("#id_feedback").css("left","50%").css("top","50%").css("margin-left",-$('#id_mod_change').width()/2).css("margin-top",-$('#id_mod_change').height()/2);
    $.each(['Google map image','Google satellite image'], function(key, value) {   
         $('#id_base_image_type').append($("<option/>",{value:value}).text(value)); 
    });
    hideTips();
    $("#id_mod_change input, #id_mod_change select").keyup(function(event) { if (event.which == 13) { addRegionCornersOk(); } } )
    $("form").submit(function() {return false;});
}

function add_regions_by_corners_chrome()
{
    var hdr='', msg='', footer='';
    var c1array, c2array, c3array;
    
    hdr += TXT.addByCorners;
    
    msg += '<p id="id_tips" class="validateTips ui-state-highlight"></p>'
    msg += '<form class="well" >';
    msg += '<fieldset>';
    msg += '    <label for="id_name">Name</label>';
    msg += '    <input type="text" name="name" id="id_name" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_min_lng">Minimum longitude</label>';
    msg += '    <input type="text" name="min_lng" id="id_min_lng" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_max_lng">Maximum longitude</label>';
    msg += '    <input type="text" name="max_lng" id="id_max_lng" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_min_lat">Minimum latitude</label>';
    msg += '    <input type="text" name="min_lat" id="id_min_lat" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_max_lat">Maximum latitude</label>';
    msg += '    <input type="text" name="max_lat" id="id_max_lat" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_base_image_type">Base Image Type</label>';
    msg += '    <select name="map_type" id="id_base_image_type" class="span6" style="margin-top:5px;margin-bottom:5px;"></select>';
    msg += '</fieldset>';
    msg += '</form>';
    
    c1array = [];
    c2array = [];
    c3array = [];
    c1array.push('style="border-style: none; width: 50%;"');
    c2array.push('style="border-style: none; width: 25%;"');
    c3array.push('style="border-style: none; width: 25%;"');
    c1array.push('');
    c2array.push(HBTN.addRegionCornersOkBtn);
    c3array.push(HBTN.cancelBtn);
    footer = tableChrome('style="border-spacing: 0px; margin-bottom: 0"', '',  c1array, c2array, c3array);
    return setModalChrome(hdr,msg,footer);
}

function addRegionCornersOk() {
    // We assume that the plat names in the JSON file are all upper case
    var name   = $.trim($("#id_name").val());
    var minLng = parseFloat($("#id_min_lng").val());
    var maxLng = parseFloat($("#id_max_lng").val());
    var minLat = parseFloat($("#id_min_lat").val());
    var maxLat = parseFloat($("#id_max_lat").val());
    var base_image_type = $("#id_base_image_type").val();
    var errors = [];
    
    if (name.length < 3) {
        $("#id_name").addClass("ui-state-error");
        errors.push("Name should have >=3 characters");
    }
    name = '[' + name.toUpperCase() + ']';
    
    // Check validity of corner values
    if (minLng>=maxLng || (maxLng-minLng)>1.0 || minLng<-180.0 || maxLng>180.0 || isNaN(minLng) || isNaN(maxLng)) {
        $("#id_min_lng, #id_max_lng").addClass("ui-state-error");
        errors.push("Invalid longitude boundaries");
    }
    if (minLat>=maxLat || (maxLat-minLat)>1.0 || minLat<-90.0 || maxLat>90.0 || isNaN(minLat) || isNaN(maxLat)) {
        $("#id_min_lat, #id_max_lat").addClass("ui-state-error");
        errors.push("Invalid latitude boundaries");
    }
    if (errors.length > 0) {
        showTips(errors.join(", "));
    } else {
        if (addToTable(CNSNT.regions,[name,minLng,maxLng,minLat,maxLat,base_image_type])) {
            closeModal();
        } else {
            showTips("Duplicate row");
        }
    }
}

// ============================================================================
//  Adding run
// ============================================================================

function add_run() {
    $("#id_mod_change").html(add_run_chrome());
    // Note that it is only after we have added the form (generated by add_regions_by_corners_chrome()) to the DOM that it is possible to refer to
    //  entities such as "#id_plat" and "#id_base_image_type". More subtly, we cannot use $("form").submit(function() {return false;});
    //  in the init function to disable submission (on Enter) since at that time, there are no forms in the DOM.
    // Size of $('#id_mod_change') is not defined until its html has been inserted
    $("#id_feedback").css("left","50%").css("top","50%").css("margin-left",-$('#id_mod_change').width()/2).css("margin-top",-$('#id_mod_change').height()/2);
    /*
    $( "#id_name" ).focus();
    $.each(['Google map image','Google satellite image'], function(key, value) {   
         $('#id_base_image_type').append($("<option/>",{value:value}).text(value)); 
    });
    $("#id_mod_change input, #id_mod_change select").keyup(function(event) { if (event.which == 13) { addRegionCornersOk(); } } )
    */
    hideTips();
    $("form").submit(function() {return false;});
}

function add_run_chrome()
{
    var hdr='', msg='', footer='';
    var c1array, c2array, c3array;
    
    hdr += TXT.addRun;
    
    msg += '<p id="id_tips" class="validateTips ui-state-highlight"></p>'
    msg += '<form class="well" >';
    msg += '<fieldset>';
    msg += '    <label for="id_analyzer">Analyzer</label>';
    msg += '    <input type="text" name="analyzer" id="id_analyzer" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_start_etm">Start Epoch Time</label>';
    msg += '    <input type="text" name="start_etm" id="id_start_etm" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_end_etm">End Epoch Time</label>';
    msg += '    <input type="text" name="end_etm" id="id_end_etm" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_path">Show Path</label>';
    msg += '    <input type="text" name="path" id="id_path" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_peaks">Show Peaks</label>';
    msg += '    <input type="text" name="peaks" id="id_peaks" class="span6" onfocus="$(this).removeClass(\'ui-state-error\')" style="margin-top:5px;margin-bottom:5px;"/>';
    msg += '    <label for="id_wedges">Show Wedges</label>';
    msg += '    <input name="wedges" id="id_wedges" class="span6" style="margin-top:5px;margin-bottom:5px;"></input>';
    msg += '    <label for="id_swath">Show Swath</label>';
    msg += '    <input name="swath" id="id_swath" class="span6" style="margin-top:5px;margin-bottom:5px;"></input>';
    msg += '    <label for="id_min_ampl">Minimum Amplitude</label>';
    msg += '    <input name="min_ampl" id="id_min_ampl" class="span6" style="margin-top:5px;margin-bottom:5px;"></input>';
    msg += '    <label for="id_max_ampl">Maximum Amplitude</label>';
    msg += '    <input name="max_ampl" id="id_max_ampl" class="span6" style="margin-top:5px;margin-bottom:5px;"></input>';
    msg += '    <label for="id_excl_radius">Exclusion Radius</label>';
    msg += '    <input name="excl_radius" id="id_excl_radius" class="span6" style="margin-top:5px;margin-bottom:5px;"></input>';
    msg += '    <label for="id_stab_class">Stability Class</label>';
    msg += '    <input name="stab_class" id="id_stab_class" class="span6" style="margin-top:5px;margin-bottom:5px;"></input>';
    msg += '</fieldset>';
    msg += '</form>';
    
    c1array = [];
    c2array = [];
    c3array = [];
    c1array.push('style="border-style: none; width: 50%;"');
    c2array.push('style="border-style: none; width: 25%;"');
    c3array.push('style="border-style: none; width: 25%;"');
    c1array.push('');
    c2array.push(HBTN.addRunOkBtn);
    c3array.push(HBTN.cancelBtn);
    footer = tableChrome('style="border-spacing: 0px; margin-bottom: 0"', '',  c1array, c2array, c3array);
    return setModalChrome(hdr,msg,footer);
}


// ============================================================================
// ============================================================================

function initialize(winH,winW)
{
    var regionTable;
    
    $('#date').datepicker();
    regionTable = makeEmptyTable(CNSNT.regions);
    $('#id_plats_table_div').html(regionTable);
    $('#regionTable tbody').sortable({helper: function(e, tr)
        {
            var $originals = tr.children();
            var $helper = tr.clone();
            $helper.children().each(function(index)
                {
                  // Set helper cell sizes to match the original sizes
                  $(this).width($originals.eq(index).width())
                });
            return $helper;
        }
        }).disableSelection();

    runsTable = makeEmptyTable(CNSNT.runs);
    $('#id_runs_table_div').html(runsTable);
        
    $("#id_add_by_name_button").click(add_regions_by_name);
    $("#id_add_by_corners_button").click(add_regions_by_corners);
    $("#id_delete_region_button").click(function(){ $("#regionTable input:radio[name=regionTable]:checked").closest("tr").remove(); });
    $("#id_clear_all_regions_button").click(function(){ $("#regionTable tbody tr").remove(); });
    $("#id_show_as_json_button").click(function(){ tableAsStruct(CNSNT.regions); });

    $("#id_add_run_button").click(add_run);
    $("#id_delete_run_button").click(function(){ $("#runTable input:radio[name=runTable]:checked").closest("tr").remove(); });
    $("#id_edit_run_button").click(function(){ edit_run($("#runTable input:radio[name=runTable]:checked").closest("tr")); });
    $("#id_clear_all_runs_button").click(function(){ $("#runTable tbody tr").remove(); });

}
