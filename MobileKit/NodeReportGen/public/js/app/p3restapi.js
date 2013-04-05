/* jshint undef:true, unused:true, laxcomma:true, -W014, -W069, -W083 */
/*globals console, define, setTimeout */
define(['jquery', 'jquery.jsonp'],
function ($) {
    'use strict';
    /**
 * Class to make P-Cubed REST API calls in JavaScript.js
 *   expects jquery-1.7.2+
 *           jquery.jsonp-2.3.0+
 * 
 * @param {Object} initArgs = {host: <API_service_host>,
 *                             port: <port_for_host>,
 *                             site: <site>,
 *                             identity: <auth_identity_string>,
 *                             psys: <auth_picarro_sys_string>,
 *                             rprocs: <rprocs_string>,
 *                             svc: <service>,
 *                             version: <version>,
 *                             resource: <resource>,
 *                             max_auth_attempts: <max_auth_attempts>,
 *                             sleep_seconds: <seconds_to_sleep_int>,
 *                             api_timeout: <seconds_for_timout_int>,
 *                             jsonp: <make_jsonp_call_boolean>,
 *                             debug: <debug_boolean>,
 *                             }
 *                                
 *                             host: Host for API service. Example:
 *                                   dev.picarro.com
 *                                   Required.
 *                             port: Request port. Default 80 if not
 *                                   provided. Use 443 for https.
 *                             site: API site. Example: dev
 *                                   Required.
 *                             identity: Security Authentication identity
 *                                   Required
 *                             psys: Picarro System Name
 *                                   Required
 *                             svc: Service for requested resource. 
 *                                   Required
 *                             version: Version for the requested resource.
 *                                   Default 1.0 if not provided.
 *                             resource: Requested resource.
 *                                   Required
 *                             rprocs: Requested Resource Processes. This is
 *                                   a JSON list of strings, or a string 
 *                                   representation of a JSON 
 *                                   string list. Example:
 *                                   ["AnzMeta:byAnz", "AnzMeta:data"] --OR--
 *                                   '["AnzMeta:byAnz", "AnzMeta:data"]'.
 *                                   All resources must belong to the same
 *                                   service. If you need access to multiple
 *                                   services, or multiple versions for a
 *                                   resource service you must instantiate 
 *                                   additional classes for the addition 
 *                                   services or versions.
 *                                   Required.
 *                             max_auth_attempts: Max number of attempts to
 *                                   get a valid ticket before error.
 *                                   Defaults to 5 attempts.
 *                             sleep_seconds: Seconds to sleep between 
 *                                   failed authentication requests.
 *                                   Defaults to 1 second.
 *                             api_timeout: Seconds to wait for API request
 *                                   before issuing timeout error.
 *                                   Defaults to 5 seconds.
 *                             jsonp: Make Cross Domain (JSONP) call Boolean.
 *                                   Defaults to false.
 * 
 */
var p3RestApi = function(initArgs) {
    /**
     * write log to console. 
     * If last argument is "debug" then only write if debug system option is set.
     * 
     * Examples:
     *      p3restapi_logger("Some debug message", some_object, "debug");
     *      p3restapi_logger("Some Message that always displays on console");
     * 
     * @param {String or Object} 
     * @param {String or Object} 
     * @param {String} "debug" optional  
     * @return {null}
     */
    var p3restapi_logger = function() {
        var i, len, printMe
        len = arguments.length;
        
        printMe = true;
        
        if (len > 0) {
            if (arguments[len-1] === "debug") {
                if (debug !== true) {
                    printMe = false;
                }
            }
        }
        
        if (printMe === true) {
            var tm = new Date()
            for(i = 0; i < len; i += 1) {
                if (arguments[i] !== "debug") {
                    try {
                        if (typeof(arguments[i]) === "object") {
                            var objparse = function(obj) {
                                var ostr = "{";
                                var osep = "";
                                
                                for(var ky in obj) {
                                    if (obj.hasOwnProperty(ky)) {
                                        var nobj = obj[ky];
                                        ostr += osep + ky + ": ";
                                        osep = ", ";
                                        
                                        switch(typeof(nobj)) {
                                        case "object":
                                            if (nobj instanceof Array) {
                                                ostr += "[";
                                                var nstr = "";
                                                
                                                for(var idx in nobj) {
                                                    if (nobj.hasOwnProperty(idx)) {
                                                        var nval = nobj[idx];
                                                        
                                                        switch(typeof(nval)) {
                                                        case "object":
                                                            ostr += nstr + objparse(nval);
                                                            break;
                                                            
                                                        case "string":
                                                            ostr += nstr + "'" + nval + "'";
                                                            break;
                                                            
                                                        default:
                                                            ostr += nstr + nval;
                                                            break;
                                                        }                                                    
                                                    }
                                                    nstr = ", ";
                                                }
                                                
                                                ostr += "]";
                                            } else {
                                                ostr += objparse(nobj);
                                            }
                                            break;
                                            
                                        case "string":
                                            ostr += "'" + nobj + "'";
                                            break;
                                            
                                        default:
                                            ostr += nobj;
                                            break;
                                        }
                                    }
                                }
                                ostr += "}";
                                return ostr;
                            }
                            var str = objparse(arguments[i]);
                            
                        } else {
                            var str = arguments[i];
                        }
                    } catch(err) {
                        var str = arguments[i];
                    }
                    
                    console.log(tm.toTimeString() + " p3restapi.js " + tm.getMilliseconds(), "::: ", str);
                }
            }
        }
    }
    this.p3restapi_logger = p3restapi_logger;

    var NONE = "NONE";
    this.NONE = NONE;
    var ERROR = "ERROR";
    this.ERROR = ERROR;
    
    // Initialize from args
    var host;
    if (initArgs && initArgs["host"]) {
        host = initArgs["host"];
    }
    this.host = host;
    var port;
    if (initArgs && initArgs["port"]) {
        port = initArgs["port"];
    }
    this.port = port;
    
    var site;
    if (initArgs && initArgs["site"]) {
        site = initArgs["site"];
    }
    this.site = site;
    
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
    
    
    var rprocs;
    if (initArgs && initArgs["rprocs"]) {
        rprocs = initArgs["rprocs"];
    }
    if (typeof(rprocs) === 'string') {
        rprocs = JSON.parse(rprocs);
    }
    this.rprocs = rprocs;
    
    var svc;
    if (initArgs && initArgs["svc"]) {
        svc = initArgs["svc"];
    }
    this.svc = svc;
    
    var version;
    if (initArgs && initArgs["version"]) {
        version = initArgs["version"];
    }
    if (version === undefined) {
        version = "1.0";
    }
    this.version = version;

    var resource;
    if (initArgs && initArgs["resource"]) {
        resource = initArgs["resource"];
    }
    this.resource = resource;
    
    var max_auth_attempts;
    if (initArgs && initArgs["max_auth_attempts"]) {
        max_auth_attempts = initArgs["max_auth_attempts"];
    }
    if (max_auth_attempts === undefined) {
        max_auth_attempts = 5.0;
    }
    this.max_auth_attempts = max_auth_attempts;
    
    var sleep_seconds;
    if (initArgs && initArgs["sleep_seconds"]) {
        sleep_seconds = initArgs["sleep_seconds"];
    }
    if (sleep_seconds === undefined) {
        sleep_seconds = 1.0;
    }
    this.sleep_seconds = sleep_seconds;
    
    var api_timeout;
    if (initArgs && initArgs["api_timeout"]) {
        api_timeout = initArgs["api_timeout"];
    }
    if (api_timeout === undefined) {
        api_timeout = 5.0;
    }
    this.api_timeout = api_timeout;
    var api_timeout_mili = api_timeout * 1000;
    this.api_timeout_mili = api_timeout_mili;

    var jsonp;
    if (initArgs && initArgs["jsonp"]) {
        jsonp = initArgs["jsonp"];
    }
    if (jsonp !== true) {
        jsonp = false;
    }
    this.jsonp = jsonp;
    
    var debug;
    if (initArgs && initArgs["debug"]) {
        debug = initArgs["debug"];
    }
    this.debug = debug;
    
    var api_ticket = NONE;
    
    p3restapi_logger("p3RestApi:", "debug");
    p3restapi_logger("p3RestApi: initArgs", initArgs, "debug");
    
    var missing_required = false;
    var emsg = "";
    var esep = "";
    if (!host) {
        emsg += esep + "host is required.";
        esep = "\n";
        missing_required = true;
    }
    if (!site) {
        emsg += esep + "site is required.";
        esep = "\n";
        missing_required = true;
    }
    if (!identity) {
        emsg += esep + "identity is required.";
        esep = "\n";
        missing_required = true;
    }
    if (!psys) {
        emsg += esep + "psys is required.";
        esep = "\n";
        missing_required = true;
    }
    if (!svc) {
        emsg += esep + "svc is required.";
        esep = "\n";
        missing_required = true;
    }
    if (!resource) {
        emsg += esep + "resource is required.";
        esep = "\n";
        missing_required = true;
    }
    if (!rprocs) {
        emsg += esep + "rprocs is required.";
        esep = "\n";
        missing_required = true;
    }
    if (missing_required === true) {
        throw(new Error(emsg).stack);
    }

    
    /**
     * make http request
     * 
     * @param {Object} request_obj = {host: <http_host>,
     *                                port: <request_port>,
     *                                path: <request_path>,
     *                                method: <html_method>,
     *                                data: <data_to_send>,
     *                                headers: <http_header>,
     *                                rtype: <return_type>,
     *                                jsonp: <jsonp_boolean>,
     *                                timeout: <socket_timeout>,
     *                                }
     *                                
     *                                host: Host to call (localhost, or
     *                                      www.google.com.....)
     *                                port: Request port. Default 80 if not
     *                                      provided. Use 443 for https.
     *                                path: Path on host (including parameters)
     *                                method: POST or GET
     *                                data: Data to send. Required for POST
     *                                      otherwise ignored.
     *                                headers: HTTP header
     *                                      Required for POST
     *                                rtype: Return Data Type expected
     *                                      json or string. Defaut string
     *                                jsonp: Make a jsonp request
     *                                      Boolean. Defaut false
     *                                timeout: Socket timeout.
     *                                      Optional
     *                                
     * @param {Function} errorCbFn - function(err)
     * @param {Function} successCbFn - function(<response_status_code>, <return_JSON>)
     */
    var httpRequestFn = function(request_obj, errorCbFn, successCbFn) {
        p3restapi_logger("httpRequestFn:", "debug");
        p3restapi_logger("httpRequestFn: request_obj", request_obj, "debug");
        
        var my_options = {};
        my_options["host"] = request_obj.host;
        
        if (request_obj.hasOwnProperty("port")) {
            my_options["port"] = request_obj.port;
        } else {
            my_options["port"] = 80;
        }
        
        my_options["path"] = request_obj.path;
        my_options["method"] = request_obj.method;
        
        if (request_obj.hasOwnProperty("headers")) {
            my_options["headers"] = request_obj.headers;
        }
        
        if (my_options.port === 443) {
            var url = "https://" 
                + my_options.host 
                + my_options.path;
        } else {
            var url = "http://" 
                + my_options.host 
                + ":" + my_options.port 
                + my_options.path;
        };
        
        // use jquery.jsonp for jsonp  otherwise use ajax
        if (request_obj.jsonp === true) {
            var errorFn = function(xOptions, status_str) {
                if (errorCbFn) {
                    errorCbFn(status_str);
                }
            }; // errorFn
            
            var successFn = function(rtn_json, status_str, xOptions) {
                if (successCbFn) {
                    successCbFn(200, rtn_json); // Fake 200
                }
            }; // successFn
            
            if (my_options.method === "POST") {
                $.jsonp({data: $.param(request_obj.data)
                    , url: url
                    , type: "POST"
                    , timeout: request_obj.timeout
                    , success: successFn
                    , error: errorFn
                    });
            } else {
                $.jsonp({url: url //, data: data
                    , type: "GET"
                    , timeout: request_obj.timeout
                    , success: successFn
                    , error: errorFn
                    });
            };
            
        } else {
            var errorFn = function(jqXHR, status, err) {
                // N.B. It is important to send jqXHR.responseText since this contains the
                // "invalid ticket" string which we test for
                if (errorCbFn) {
                    errorCbFn(jqXHR.status + ' ' + jqXHR.statusText + ' ' + jqXHR.responseText);
                }
            }; // errorFn
            
            var successFn = function(rtn_data, status, jqXHR) {
                var json_error = false, rtnobj;
                try {
                    rtnobj = JSON.parse(rtn_data);
                } catch(err) {
                    json_error = true;
                }
                if (json_error === false) {
                    if (successCbFn) {
                        successCbFn(status, rtnobj);
                    }
                } else {
                    if (errorCbFn) {
                        errorCbFn(rtn_data);
                    }
                }
            }; // successFn
            
            if (my_options.method === "POST") {
                $.ajax({contentType: "application/json"
                    , data: $.param(request_obj.data)
                    , dataType: "text"
                    , url: url
                    , type: "POST"
                    , timeout: request_obj.timeout
                    , success: successFn
                    , error: errorFn
                    });
            } else {
                $.ajax({contentType: "application/json"
                    , dataType: "text"
                    , url: url
                    , type: "GET"
                    , timeout: request_obj.timeout
                    , success: successFn
                    , error: errorFn
                    });
            };
        }
    }; //httpRequestFn
    
    var callRest = function(rq_obj, error_callback, success_callback) {
        p3restapi_logger("callRest:", "debug");
        p3restapi_logger("callRest: path", rq_obj.path, "debug");
        p3restapi_logger("callRest: method", rq_obj.method, "debug");
        
        var myreq = {"host": host
                     , "port": port
                     , "path": rq_obj.path
                     , "method": rq_obj.method
                     , "rtype": "json"
                     , "timeout": api_timeout_mili
                     , "jsonp": jsonp
                     };
        
        if (rq_obj.method === "POST") {
            p3restapi_logger("callRest: data", rq_obj.data, "debug");
            
            var mydata = {"data": JSON.stringify(rq_obj.data)};
            myreq["data"] = $.param(mydata);
            myreq["headers"] = {'Content-Length': myreq["data"].length
                                , 'Content-Type': 'application/x-www-form-urlencoded'};
        }
        
        httpRequestFn(myreq, error_callback, success_callback);
    }; //callRest
        
    // get ticket
    var getTicket = function(errorFn, successFn) {
        p3restapi_logger("getTicket:", "debug");
        
        var call_path = "";
        var call_parms = {};
        call_parms["qry"] = "issueTicket";
        call_parms["sys"] = psys;
        call_parms["identity"] = identity;
        
        if (typeof(rprocs) === 'string') {
            call_parms["rprocs"] = rprocs;
        } else {
            call_parms["rprocs"] = JSON.stringify(rprocs);
        }
        
        call_path += "/" + site + "/rest/sec/dummy/1.0/Admin?";
        if (jsonp === true) {
            call_path += "callback=?&";
        }
        call_path += $.param(call_parms);
        
        var ticket = "NONE";
        var successTicket = function(rtnStatus, json) {
            p3restapi_logger("getTicket.successTicket rtnStatus: " + rtnStatus, "debug");
            p3restapi_logger("getTicket.successTicket json: ", json, "debug");
            
            if (json.ticket) {
                api_ticket = json.ticket;
                var fn_call_obj = {"ticket": json.ticket}
                successFn(fn_call_obj);
            } else {
                var eobj = {};
                eobj.msg = "ERROR No Ticket Returned";
                eobj.rtn = json;
                errorFn(eobj);
            }
        }
        var errorTicket = function(err) {
            p3restapi_logger("getTicket.errorTicket err: ", err, "debug");
            
            api_ticket = ERROR;
            errorFn(err);
        }
        callRest({"path": call_path, "method": "GET"}, errorTicket, successTicket);
    }; //getTicket

    /**
     * P-Cubed get REST request
     * 
     * @param {Object} request_obj   - {"dataobj: <api_data_object>",
     *                                  "existing_tkt: <use_existing_tkt>"}
     *                                  
     *                                  dataobj: The data for the post. This is
     *                                       the object that will be sent in 
     *                                       the "data" portion of the HTTP 
     *                                       POST. Most P-Cubed POST requests
     *                                       take a list of insert documents 
     *                                       as the dataobj. Example:
     *                                       [<document_1>, <document_2>, ...]
     *                                  existing_tkt: If true, try to use
     *                                       the existing authentication
     *                                       ticket first.
     *                                       Optional.
     *                                       If ommited it will be true.
     *                                        
     * @param {Function} errorCbFn   - function(err)
     * @param {Function} successCbFn - function(<response_status_code>, <return_JSON>)
     */
    var post = function(request_obj, errorCbFn, successCbFn) {
        p3restapi_logger("post:", "debug");
        p3restapi_logger("post: request_obj", request_obj, "debug");
        
        getpost("POST", request_obj, errorCbFn, successCbFn);
    };
    this.post = post;
    
    /**
     * P-Cubed get REST request
     * 
     * @param {Object} request_obj   - {"qryobj: <api_query_object>",
     *                                  "existing_tkt: <use_existing_tkt>"}
     *                                  
     *                                  qryobj: The resource query and 
     *                                       requested parameters. Example:
     *                                       {"qry": "byAnz", "limit": 5}
     *                                  existing_tkt: If true, try to use
     *                                       the existing authentication
     *                                       ticket first.
     *                                       Optional.
     *                                       If ommited it will be true.
     *                                        
     * @param {Function} errorCbFn   - function(err)
     * @param {Function} successCbFn - function(<response_status_code>, <return_JSON>)
     */
    var get = function(request_obj, errorCbFn, successCbFn) {
        p3restapi_logger("get:", "debug");
        p3restapi_logger("get: request_obj", request_obj, "debug");
        
        getpost("GET", request_obj, errorCbFn, successCbFn);
    }; // get
    this.get = get;
        
        
    var getpost = function(type, request_obj, errorCbFn, successCbFn) {
        p3restapi_logger("getpost:", "debug");
        p3restapi_logger("getpost: request_obj", request_obj, "debug");
        
        var my_svc = svc; 
        var my_ver = version; 
        var my_rsc = resource;
        
        switch(type) {
        case "GET":
            var my_qryparms_obj = request_obj.qryobj;
            break;
        case "POST":
            var my_qryparms_obj = request_obj.dataobj;
            break;
        }
        
        if (request_obj.hasOwnProperty("existing_tkt")) {
            var my_existing_tkt = request_obj.existing_tkt;
        } else {
            var my_existing_tkt = true;
        }
        
        var get_cntl = {"fn_list": []};
        
        var buildCallRequest = function(tkt) {
            var rest_rq = {};
            var cp = "/" + site + "/rest/" + my_svc 
            + '/' + tkt 
            + '/' + my_ver
            + '/' + my_rsc;

            switch(type) {
            case "GET":
                if (typeof(my_qryparms_obj) === 'string') {
                    cp += my_qryparms_obj;
                    if (jsonp === true) {
                        if (my_qryparms_obj.indexOf("?") === -1) {
                            cp += "?callback=?&";
                        } else {
                            cp += "&callback=?&";
                        }
                    }
                    
                } else {
                    if (jsonp === true) {
                        cp += "?callback=?&";
                    } else {
                        cp += "?"
                    }
                    
                    cp += $.param(my_qryparms_obj);
                }
                var rest_rq = {"path": cp, "method": "GET"};
                break;
                
            case "POST":
                if (jsonp === true) {
                    cp += "?callback=?&";
                }
                
                var rest_rq = {"path": cp, "method": "POST", "data": my_qryparms_obj};
                break;
            }
            return rest_rq;
        } 
        
        var tryWithInitialTicket = function(completeCbFn) {
            p3restapi_logger("getpost.tryWithInitialTicket:", "debug");
            
            var rest_rq = buildCallRequest(api_ticket);
            
            callRest(rest_rq
                
                // errorFn
                , function(err) {
                    p3restapi_logger("getpost.tryWithInitialTicket.callRest errorFn:", "debug");
                
                    var tkt_error = false;
                    if (typeof(err) === 'string') {
                        if (err.indexOf("invalid ticket") >= 0) {
                            tkt_error = true
                        }
                    } else {
                        try {
                            var estr = JSON.stringify(err);
                            if (estr.indexOf("invalid ticket") >= 0) {
                                tkt_error = true
                            }
                        } catch(e) {
                            tkt_error = false;
                        }
                    }
                    if (tkt_error === false) {
                        get_cntl["request_is_done"] = true;
                        get_cntl["request_error"] = err;
                    }
                    completeCbFn();
                }
            
                // SuccessFn
                , function(rcode, robj) {
                    p3restapi_logger("getpost.tryWithInitialTicket.callRest successFn:", "debug");
                    
                    get_cntl["request_is_done"] = true;
                    get_cntl["request_rcode"] = rcode;
                    get_cntl["request_robj"] = robj;
                    completeCbFn();
                }
            );
        };// tryWithInitialTicket
        
        var getNewTicketThenGET = function(completeCbFn) {
            p3restapi_logger("getpost.getNewTicketThenGET:", "debug");
            
            // skip this process if request_is_done
            if (get_cntl.request_is_done === true) {
                completeCbFn();
                return;
            }
            
            var getFn = function(tktObj, doneCb) {
                p3restapi_logger("getpost.getNewTicketThenGET.getFn:", "debug");
                p3restapi_logger("getpost.getNewTicketThenGET.getFn: tktObj: "
                    , tktObj
                    , "debug");
                
                var rest_rq = buildCallRequest(tktObj.ticket);
                
                callRest(rest_rq
                    // errorCb
                    , function(err) {
                        p3restapi_logger("getpost.getNewTicketThenGET.getFn.callRest errorCb:", "debug");
                        
                        get_cntl["request_is_done"] = true;
                        get_cntl["request_error"] = err;
                        doneCb();
                    }
                    , function(rcode, robj) {
                        p3restapi_logger("getpost.getNewTicketThenGET.getFn.callRest successFn:", "debug");
                        
                        get_cntl["request_is_done"] = true;
                        get_cntl["request_rcode"] = rcode;
                        get_cntl["request_robj"] = robj;
                        doneCb();
                    });
            }
            
            var tkt_cntl = {"max": max_auth_attempts
                            , "err": null
                            , "acount": 0 // attempt counter
                            , "ecount": 0 // error counter
                            , "OK": false};
            
            var tktAttempt = function() {
                p3restapi_logger("getpost.getNewTicketThenGET.tktAttempt:", "debug");
                
                // if this is an error retry, pause before the retry
                if (tkt_cntl.ecount >= 1) {
                    var sleep_mili = sleep_seconds * 1000;
                } else {
                    var sleep_mili = 0;
                }
                
                tkt_cntl.acount += 1;
                getTicket(
                    
                    // errorFn
                    function(err) {
                        tkt_cntl.ecount += 1;
                        tkt_cntl.err = err;
                        
                        // we have an error, so retry
                        if (tkt_cntl.acount < tkt_cntl.max) {
                            setTimeout(function() {tktAttempt()}, sleep_mili);
                            
                        } else {
                            
                            // finished with all retry attempts,
                            get_cntl["request_is_done"] = true;
                            if (tkt_cntl.err) {
                                get_cntl["request_error"] = tkt_cntl.err;
                            } else {
                                get_cntl["request_error"] = {"msg": "Authentication error. Cannot get ticket"};
                            }
                            completeCbFn();
                        }
                    }
                
                    // successFn (call return)
                    , function(tktObj) {
                        tkt_cntl.OK = true;
                        getFn(tktObj, completeCbFn)
                    }
                );
            }; // tktAttempt
            tktAttempt();
        }; //getNewTicketThenGET
        
        var finalRoutine = function() {
            p3restapi_logger("getpost.finalRoutine:", "debug");
            p3restapi_logger("getpost.finalRoutine: get_cntl", get_cntl, "debug");
            
            if (get_cntl.hasOwnProperty("request_robj")) {
                if (successCbFn) {
                    successCbFn(get_cntl.request_rcode, get_cntl.request_robj);
                }
            } else {
                if (errorCbFn) {
                    errorCbFn(get_cntl.request_error);
                }
            }
        }; // finalRoutine
        
        // try to use existing ticket first
        if ((my_existing_tkt === true) && (api_ticket !== NONE) && (api_ticket !== ERROR)) {
            get_cntl["fn_list"].push(tryWithInitialTicket);
        }
        get_cntl["fn_list"].push(getNewTicketThenGET);
        get_cntl["fn_list"].push(finalRoutine);
        
        var singleThread = function(nextFn) {
            if (nextFn) {
                nextFn(function() {
                    return singleThread(get_cntl["fn_list"].shift());
                }); 
            }
        }
        
        // startThe list of processes
        singleThread(get_cntl["fn_list"].shift());
        
    }; //getpost
    
    /**
     * generate P-Cubed REST path string with valid ticket
     * 
     * @param {Object} request_obj   - {"qryobj: <api_query_object>",
     *                                  "existing_tkt: <use_existing_tkt>"}
     *                                  
     *                                  qryobj: The resource query and 
     *                                       requested parameters. Example:
     *                                       {"qry": "byAnz", "limit": 5}
     *                                        
     * @param {Function} errorCbFn   - function(err)
     * @param {Function} successCbFn - function(200, <path_string>)
     */
    var geturl = function(request_obj, errorCbFn, successCbFn) {
        p3restapi_logger("geturl:", "debug");
        p3restapi_logger("geturl: request_obj", request_obj, "debug");
        
        var my_svc = svc; 
        var my_ver = version; 
        var my_rsc = resource;
        var my_qryparms_obj = request_obj.qryobj;
        
        var getFn = function(tktObj) {
            var call_path = "/" + site + "/rest/" + my_svc 
            + '/' + tktObj.ticket 
            + '/' + my_ver
            + '/' + my_rsc;
            
            call_path += "?" + $.param(my_qryparms_obj);
            
            successCbFn(200, call_path);
        }
        var badFn = function(err) {
            errorCbFn(err);
        }
        getTicket(badFn, getFn);
    };
    this.geturl = geturl;
    
    
    // build resource.qry() functions for all rproc values
    var rsc, qry, rqlist;
    var resource_obj = {};
    
    // Assure that the resource query exists in the rpocs list
    var resource_qry_exists = false;
    var exrprocs = [];
    
    for (var rqryidx in rprocs) {
        rqlist = rprocs[rqryidx].split(":");
        if (rqlist[1] === "resource") {
            resource_qry_exists = true;
        };
        exrprocs.push(rprocs[rqryidx]);
    }
    if (resource_qry_exists !== true) {
        exrprocs.push(resource + ":resource");
    }
    
    // build the qry functions
    for (rqryidx in exrprocs) {
        rqlist = exrprocs[rqryidx].split(":");
        rsc = rqlist[0];
        qry = rqlist[1];
        if (!resource_obj.hasOwnProperty(rsc)) {
            resource_obj[rsc] = {};
        }
        var setup = function(rs,qr) {
            resource_obj[rs][qr] = function(q,e,s) {
                                        var fn, fn_req;
                                        switch(qr) {
                                        case "data":
                                            fn_req = {"dataobj": q, "existing_tkt": true};
                                            fn = post;
                                            break
                                            
                                        case "resource":
                                            fn_req = {"qryobj": q, "existing_tkt": true};
                                            fn = get;
                                            break
                                            
                                        default:
                                            q["qry"] = qr; 
                                            fn_req = {"qryobj": q, "existing_tkt": true};
                                            fn = get;
                                            break;
                                        }
                                        fn(fn_req,e,s);
                                    };
        }
        setup(rsc,qry);
    }
    
    p3restapi_logger("p3RestApi: exposing named resources functions", "debug");
    for (rsc in resource_obj) {
        for (qry in resource_obj[rsc]) {
            p3restapi_logger("p3RestApi: exposing " + rsc + "." + qry + "({<parms>})", "debug");
            this[qry] = resource_obj[rsc][qry];
        }
    }
    
    }; //p3RestApi

    return {p3RestApi: p3RestApi};
});


