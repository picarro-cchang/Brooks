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
            $.each(data,function(layerName,layerUrl) {
                // $("<h2>"+layerName+"</h2><img src='"+layerUrl+"' alt='"+layerName+"'/>").appendTo(document.body);
                image = new Image();
                image.src = layerUrl;
                w = image.width;
                h = image.height;
                $("#canvasesdiv").css('height',h+'px').css('width',w+'px');
                if (layerName == 'baseMap') {
                    layer = document.getElementById("layer1");
                    ctx = layer.getContext("2d");
                    $("#layer1").attr('height',h+'px').attr('width',w+'px');
                    ctx.drawImage(image,0,0);
                }
                else if (layerName == 'pathMap') {
                    layer = document.getElementById("layer2");
                    ctx = layer.getContext("2d");
                    $("#layer2").attr('height',h+'px').attr('width',w+'px');
                    ctx.drawImage(image,0,0);
                }
                else if (layerName == 'peaksMap') {
                    layer = document.getElementById("layer3");
                    ctx = layer.getContext("2d");
                    $("#layer3").attr('height',h+'px').attr('width',w+'px');
                    ctx.drawImage(image,0,0);
                }
                else if (layerName == 'wedgesMap') {
                    layer = document.getElementById("layer4");
                    ctx = layer.getContext("2d");
                    $("#layer4").attr('height',h+'px').attr('width',w+'px');
                    ctx.drawImage(image,0,0);
                }
            });
        },
        function (data, et, jqXHR) {
        }
    );
}

function initialize(winH,winW)
{
}
