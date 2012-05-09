/* Generate a report by submitting an instructions file to the P3 server and waiting for the 
components to be generated. Assemble the report and allow it to be saved */

var TIMER = {
        status: null    // time to retrieve status
    };

var CSTATE = {
        regions: null,  // Plats to use for displaying data
        ticket: null    // Hash of instructions used as key to retrieve status, etc
    };

var CNSNT = {
        svcurl: "/rest"
    };

var TXT = {
        addPlatOk: 'OK',
        cancel: 'Cancel',
        enterRegion: 'Enter Region'
    };

var HBTN = {
        cancelBtn: '<div><button id="id_cancelBtn" type="button" onclick="closeModal();" class="btn primary large fullwidth">' + TXT.cancel + '</button></div>',
        addPlatOkBtn: '<div><button id="id_addPlatOkBtn" type="button" onclick="addPlatOk();" class="btn primary large fullwidth">' + TXT.addPlatOk + '</button></div>'
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

function popUp()
{
    var hdr='', msg='', footer='';
    var c1array, c2array, c3array;
    
    hdr += TXT.enterRegion;
    msg += '<form class="well" >';
    msg += '<fieldset>';
    msg += '    <label for="id_plat">Plat</label>';
    msg += '    <input type="text" name="plat" id="id_plat" class="span6" style="margin-top:5px;margin-bottom:5px;"/>';
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
    footer = tableChrome('style="border-spacing: 0px;"', '',  c1array, c2array, c3array);
    return setModalChrome(hdr,msg,footer);
}

function makeTable(id,contents)
{
    var i,j,row;
    var headings = contents.headings;
    var rows = contents.rows;
    var result='<table id="'+id+'"><thead><tr>';
    for (i=0;i<headings.length;i++) {
        result += '<th>' + headings[i] + '</th>';
    }
    result += '</tr></thead><tbody>';
    for (j=0;j<rows.length;j++) {
        row = rows[j];
        result += '<tr>';
        for (i=0;i<row.length;i++) {
            result += '<td>' + row[i] + '</td>';
        }
        result += '</tr>';
    }
    result += '</tbody></table>';
    return result;
}
       
function refreshRegionsTable()
{
    var regionTable = makeTable("regionTable",CSTATE.regions);
    $('#id_plats_table_div').html(regionTable);
    $('#regionTable tr').addClass('ui-widget-content');
    $('#regionTable').selectable({
        filter:'tbody tr'
    });
    /*
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
        },
        }).disableSelection();
    */
}

function add_regions() {
    $("#id_mod_change").html(popUp());
    // Note that it is only after we have added the form (generated by popUp()) to the DOM that it is possible to refer to
    //  entities such as "#id_plat" and "#id_base_image_type". More subtly, we cannot use $("form").submit(function() {return false;});
    //  in the init function to disable submission (on Enter) since at that time, there are no forms in the DOM.
    $( "#id_plat" ).autocomplete({source:"/rest/autocompletePlat",minLength:2});
    // Size of $('#id_mod_change') is not defined until its html has been inserted
    $("#id_feedback").css("left","50%").css("top","50%").css("margin-left",-$('#id_mod_change').width()/2).css("margin-top",-$('#id_mod_change').height()/2);
    $.each(['Plat image','Google map image','Google satellite image'], function(key, value) {   
         $('#id_base_image_type').append($("<option/>",{value:value}).text(value)); 
    });
    $("form").submit(function() {return false;});
}

function addPlatOk() {
    // We assume that the plat names in the JSON file are all upper case
    var plat = $("#id_plat").val();
    var base_image_type = $("#id_base_image_type").val();
    call_rest(CNSNT.svcurl, 'platCorners', {plat:plat}, 
        function (data, ts, jqXHR) {
            if ("MIN_LAT" in data) {
                CSTATE.regions.rows.push([data.PLAT,data.MIN_LONG,data.MAX_LONG,data.MIN_LAT,data.MAX_LAT,base_image_type]);
                refreshRegionsTable();
            }
            closeModal();
        },
        function (data, et, jqXHR) {
            closeModal();
        }
    );
}

function delete_regions() {
    // Find selected regions and remove them from CSTATE.regions
    var i;
    var $row = $("#regionTable > tbody > tr").filter(":last");
    for (i=CSTATE.regions.rows.length-1;i>=0;i--) {
        if ($row.hasClass("ui-selected")) CSTATE.regions.rows.splice(i,1);
        $row = $row.prev();
    }
    refreshRegionsTable();
}

function initialize(winH,winW)
{
    var row;
    var rowAsStr;
    
    $('#date').datepicker();

/*
    var regionTable = makeTable("regionTable",{headings:['Plat','Min Lng','Max Lng','Min Lat','Max Lat','Base Image'],
                                                  rows:[['45C12',-122.0967,-122.0888,37.9180,37.9275,'Google map image'],
                                                        ['45B09',-122.1194,-122.1117,37.9276,37.9369,'Google satellite image']]});
*/

/*
    row = ['45B09',-122.1194,-122.1117,37.9276,37.9369,'Google satellite image']
    rowAsStr = row.join('</td><td>');
    $('#regionTable > tbody:last').append('<tr class="ui-widget-content"><td>'+ rowAsStr +'</td></tr>');
*/
    CSTATE.regions = {headings:['Plat','Min Lng','Max Lng','Min Lat','Max Lat','Base Image'],rows:[]};
    refreshRegionsTable();
    $("#id_add_regions_button").click(add_regions);
    $("#id_delete_regions_button").click(delete_regions);
    
};
