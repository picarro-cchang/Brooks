// p3service.js
// Picarro p-cubed api service for javascript processes
function P3ApiService(initArgs) {
    // Initialize from args
    var anzlog_url;
    if (initArgs && initArgs["anzlog_url"]) {
        anzlog_url = initArgs["anzlog_url"];
    }
    this.anzlog_url = anzlog_url;
    
    var csp_url;
    if (initArgs && initArgs["csp_url"]) {
        csp_url = initArgs["csp_url"];
    }
    this.csp_url = csp_url;
    
    var ticket_url;
    if (initArgs && initArgs["ticket_url"]) {
        ticket_url = initArgs["ticket_url"];
    }
    this.ticket_url = ticket_url;
    
    var identity;
    if (initArgs && initArgs["identity"]) {
        identity = initArgs["identity"];
    }
    this.identity = identity;
    
    var psys;
    if (initArgs && initArgs["psys"]) {
        psys = initArgs["psys"];
    }
    this.psys = psys;
    
    var sleep_seconds;
    if (initArgs && initArgs["sleep_seconds"]) {
        sleep_seconds = initArgs["sleep_seconds"];
    }
    this.sleep_seconds = sleep_seconds;
    if (this.sleep_seconds === undefined) {
        this.sleep_seconds = 1.0;
    }
    
    var api_timeout;
    if (initArgs && initArgs["api_timeout"]) {
        api_timeout = initArgs["api_timeout"];
    }
    this.api_timeout = api_timeout;
    if (this.api_timeout === undefined) {
        this.api_timeout = 5.0;
    }
    
    var debug;
    if (initArgs && initArgs["debug"]) {
        debug = initArgs["debug"];
    }
    this.debug = debug;
    
    var rprocs;
    if (initArgs && initArgs["rprocs"]) {
        rprocs = initArgs["rprocs"];
    }
    this.rprocs = rprocs;
    
    var api_ticket = "NONE";

    var callRest = function(call_url, dtype, params, success_callback, error_callback) {
        var url;
        if (dtype === "jsonp") {
            url = call_url + "?callback=?";
            //alert("url: " + url);
            $.jsonp({
                data: $.param(params),
                url: url,
                type: "get",
                timeout: api_timeout,
                success: success_callback,
                error: error_callback
            });
        } else {
            url = call_url;
            $.ajax({contentType: "application/json",
                data: $.param(params),
                dataType: dtype,
                url: url,
                type: "get",
                timeout: api_timeout,
                success: success_callback,
                error: error_callback
                });
        }
    }
        
    // get ticket
    var getTicket = function(successFn, errorFn) {
        var ticket = "NONE";
        var qry = "issueTicket";
        var params = {
            "qry": qry
            , "sys": psys
            , "identity": identity
            , "rprocs": rprocs
        }
        var successTicket = function(json, textStatus) {
            if (json.ticket) {
                api_ticket = json.ticket;
                var fn_call_obj = {"ticket": json.ticket}
                successFn(fn_call_obj);
            }
        }
        var errorTicket = function(xOptions, textStatus) {
            //alert("we have an error");
            api_ticket = "ERROR";
            errorFn();
        }
        callRest(ticket_url, "jsonp", params, successTicket, errorTicket);
    }

    var insertTicket = function(uri) {
        var nuri
        // sometimes HLL programs try to be "helpful" and convert the < and > strings
        // into &lt; and &gt; tokens.  So we have to beware.
        nuri = uri.replace("&lt;TICKET&gt;", CSTATE.ticket);
        return nuri.replace("<TICKET>", CSTATE.ticket);
    }
    
    var get = function(reqobj, rtn_fn, err_fn) {
        log(":getting")
        var my_svc = reqobj.svc;
        var my_ver = reqobj.version;
        var my_rsc = reqobj.resource;
        var my_qryparms_obj = reqobj.qryobj;
        
        var getFn = function(tktObj) {
            var qry_url = csp_url + '/rest/' + my_svc 
            + '/' + tktObj.ticket 
            + '/' + my_ver
            + '/' + my_rsc;
            callRest(qry_url, "jsonp", my_qryparms_obj, rtn_fn, err_fn)
        }
        var badFn = function(xOptions, textStatus) {
            err_fn();
        }
        getTicket(getFn, badFn);
    };
    this.get = get;
    
    var geturl = function(reqobj, rtn_fn, err_fn) {
        var my_svc = reqobj.svc;
        var my_ver = reqobj.version;
        var my_rsc = reqobj.resource;
        var my_qryparms_obj = reqobj.qryobj;
        
        var getFn = function(tktObj) {
            var qry_url = csp_url + '/rest/' + my_svc 
            + '/' + tktObj.ticket 
            + '/' + my_ver
            + '/' + my_rsc;
            
            var sep = "?";
            for(obj in my_qryparms_obj) {
                if (my_qryparms_obj.hasOwnProperty(obj)) {
                    qry_url += sep + obj + "=" + my_qryparms_obj[obj];
                    sep = "&";
                }
            }
            
            rtn_fn(qry_url);
        }
        var badFn = function(xOptions, textStatus) {
            err_fn();
        }
        getTicket(getFn, badFn);
    };
    this.geturl = geturl;
    
    
} 

