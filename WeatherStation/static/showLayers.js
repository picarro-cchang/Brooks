/* Show layers associated with a specified ticket */
    
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

function showLayers(ticket) {
    params = { "ticket":ticket }
    call_rest(CNSNT.svcurl,'getLayerUrls',params,
        function (data, ts, jqXHR) {
            var composite = document.getElementById("composite");
            var ctxOut = composite.getContext("2d");
            var nLayers = 0;
            var canvases = {};
            $.each(data,function(layerName,layerUrl) {
                // $("<h2>"+layerName+"</h2><img src='"+layerUrl+"' alt='"+layerName+"'/>").appendTo(document.body);
                var image = new Image();
                image.onload = function() {
                    var c, ctx, w, h;
                    w = image.width;
                    h = image.height;
                    $("#canvasesdiv").css('height',h+'px').css('width',w+'px');
                    c = document.createElement('canvas');
                    ctx = c.getContext("2d");
                    c.id = layerName;
                    c.height = h; 
                    c.width = w;
                    ctx.drawImage(image,0,0);
                    canvases[layerName] = c;
                    nLayers++;
                    if (nLayers == 4) {
                        $("#composite").attr('height',h+'px').attr('width',w+'px');
                        ctxOut.drawImage(c,0,0);
                        ctxOut.drawImage(canvases['baseMap'],0,0);
                        ctxOut.drawImage(canvases['pathMap'],0,0);
                        ctxOut.drawImage(canvases['wedgesMap'],0,0);
                        ctxOut.drawImage(canvases['peaksMap'],0,0);
                    }
                };
                image.src = layerUrl;
            });
        },
        function (data, et, jqXHR) {
        }
    );
}

function initialize(winH,winW)
{
}
