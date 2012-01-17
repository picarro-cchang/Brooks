var TIMER = {
    refresh : null,
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

var graph = new Image();
var lastTime = null;
var theCanvas;
var context;

graph.addEventListener('load',drawScreen,false);

function refreshImage()
{
    var name = "mygraph";
    call_rest("/rest","mostRecentImage",{name:name},
        function (data, status, jqXHR) {
            if (lastTime === data.result.when) { // No need to draw
                TIMER.refresh = setTimeout(refreshImage,500);
            }
            else {
                lastTime = data.result.when;
                graph.src = "/rest/getImage?name=" + name + "#e" + new Date().getTime();    
            }
        }
    )
};

function drawScreen()
{
    context.drawImage(graph,0,0);
    TIMER.refresh = setTimeout(refreshImage,500);
};

function initialize(winH,winW)
{
    theCanvas = document.getElementById("canvas");
    context = theCanvas.getContext("2d");
    refreshImage();
    // alert('Window size: ' + winW + 'x' + winH);
};
