/* Generate a report by submitting an instructions file to the P3 server and waiting for the 
components to be generated. Assemble the report and allow it to be saved */

var TIMER = {
        status: null,   // time to retrieve status
    };

var CSTATE = {
        ticket: null,  // Hash of instructions used as key to retrieve status, etc
    };
    
var CNSNT = {
        svcurl: "/rest",
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

function onLoad() {
    $('#instructions').val('');
    $('#status').val('');
    $('#instrUpload').fileupload({
        dataType: 'json',
        dropZone: $("#instructions"),
        formData: { 'extra':'info' },
        done: function (e, data) {
            $.each(data.result, function (index, item) {
                $("#instructions").val(item.contents);
                CSTATE.ticket = item.ticket;
                TIMER.status = setTimeout(statusTimer, 1000);
                $('<p/>').text(index + ' Ticket: ' + CSTATE.ticket).appendTo(document.body);
            });
        }
    });
}

function statusTimer() {
    params = { "ticket":CSTATE.ticket }
    call_rest(CNSNT.svcurl, "getReportStatus", params, 
        function (data, ts, jqXHR) {
            var done = true;
            $("#status").val('')
            $.each(data.files,function(fName,contents) {
                $("#status").val($("#status").val() + fName + 
                "\n" + JSON.stringify(contents,null,2) + "\n");
                if ("end" in contents) done = false;
            });
            if (!done) TIMER.status = setTimeout(statusTimer, 1000);
        },
        function (data, et, jqXHR) {
            TIMER.status = setTimeout(statusTimer, 1000);
        }
    );
}

$(onLoad);    

function initialize(winH,winW)
{
    // theCanvas = document.getElementById("canvas");
    // context = theCanvas.getContext("2d");
    // refreshImage();
    // alert('Window size: ' + winW + 'x' + winH);
};
