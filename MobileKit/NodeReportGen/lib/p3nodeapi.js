/* p3nodeapi.js provides a means for making P3 rest calls from node.js */
/*global console, exports, module, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
/**
 * Class to make P-Cubed API calls in Node.js
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
 * 
 */
var p3NodeApi = function(initArgs) {

    /**
     * write log to console. 
     * If last argument is "debug" then only write if debug system option is set.
     * 
     * Examples:
     *      p3nodeapi_logger("Some debug message", some_object, "debug");
     *      p3nodeapi_logger("Some Message that always displays on console");
     * 
     * @param {String or Object} 
     * @param {String or Object} 
     * @param {String} "debug" optional  
     * @return {null}
     */
    var p3nodeapi_logger = function() {
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
                    console.log(tm.toTimeString() + " p3apiservice.js " + tm.getMilliseconds(), "::: ", arguments[i]);
                }
            }
        }
    }
    this.p3nodeapi_logger = p3nodeapi_logger;

    var http = require("http");
    var https = require("https");
    var querystring = require("querystring");

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
    
    p3nodeapi_logger("p3NodeApi:", "debug");
    p3nodeapi_logger("p3NodeApi: initArgs", initArgs, "debug");
    
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
        console.log(new Error(emsg).stack);
        throw "";
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
     *                                timeout: Socket timeout.
     *                                      Optional
     *                                
     * @param {Function} errorCbFn - function(err)
     * @param {Function} successCbFn - function(<response_status_code>, <return_JSON>)
     */
    var httpRequestFn = function(request_obj, errorCbFn, successCbFn) {
        p3nodeapi_logger("httpRequestFn:", "debug");
        p3nodeapi_logger("httpRequestFn: request_obj", request_obj, "debug");
        
        var my_options = {};
        my_options["rejectUnauthorized"] = false;
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
            var rq = https;
        } else {
            var rq = http;
        };
        
        try {
            var req = rq.request(my_options, function(res) {
                var rtnstr = "";
                var rtnobj;
                res.setEncoding('utf8');
                
                res.on('data', function(chunk) {
                    
                    //console.log("");
                    //console.log("res.on data chunk", chunk);
                    //console.log("");
                    
                    rtnstr += chunk;
                })
                
                res.on('end', function() {
                    var rtnobj = rtnstr;

                    //console.log("");
                    //console.log("res.on end rtnobj", rtnobj);
                    //console.log("");
                    
                    var json_error = false;
                    if (request_obj.rtype === "json") {
                        try {
                            rtnobj = JSON.parse(rtnstr);
                        } catch(err) {
                            json_error = true;
                        }
                    } else {
                        rtnobj = rtnstr;
                    }
                    if (json_error === true) {
                        if (errorCbFn) {
                            errorCbFn(rtnstr);
                        }
                    } else {
                        successCbFn(res.statusCode, rtnobj);
                    }
                });
            });

            if (request_obj.timeout) {
                req.setTimeout(request_obj.timeout);
            }
            
            req.on('error', function(err) {
                 if (errorCbFn) {
                     errorCbFn(err);
                 }
            });
             
            if (request_obj.method === "POST") {
                req.end(request_obj.data);
            } else {
                req.end();
            }
             
        } catch(err) {
            if (errorCbFn) {
                errorCbFn(err);
            }
        };
    }; //httpRequestFn
    
    /**
     * make an httm GET request
     * 
     * @param {Object} request_obj = {host: <request_host>,
     *                                port: <request_port>,
     *                                path: <request_path>,
     *                                
     *                                host: Host to call (localhost, or
     *                                      www.google.com.....)
     *                                port: Request port. Default 80 if not
     *                                      provided. Use 443 for https.
     *                                path: Path on host (including parameters)
     *                                
     * @param {Function} errorCbFn - function(err)
     * @param {Function} successCbFn = function(<response_status_code>, <return_JSON>)
     * 
     */
    var httpGetFn = function(request_obj, errorCbFn, successCbFn) {
        p3nodeapi_logger("httpGetFn:", "debug");
        p3nodeapi_logger("httpGetFn: request_obj", request_obj, "debug");
        
        myreq = request_obj;
        myreq["method"] = "GET";
        
        httpRequestFn(myreq, errorCbFn, successCbFn);
    };
    this.httpGetFn = httpGetFn;
    
    
    /**
     * make http POST request
     * 
     * @param {Object} request_obj = {host: <request_host>,
     *                                port: <request_port>,
     *                                path: <request_path>,
     *                                data: <data_to_send>,
     *                                headers: <http_headers>}
     *                                
     *                                host: Host to call (localhost, or
     *                                      www.google.com.....)
     *                                port: Request port. Default 80 if not
     *                                      provided. Use 443 for https.
     *                                path: Path on host (including parameters)
     *                                data: Data to send.
     *                                headers: HTTP Headers.
     *                                
     * @param {Function} errorCbFn - function(err)
     * @param {Function} successCbFn - function(<response_status_code>, <return_JSON>)
     * 
     */
    var httpPostFn = function(request_obj, errorCbFn, successCbFn) {
        p3nodeapi_logger("httpPostFn:", "debug");
        p3nodeapi_logger("httpPostFn: request_obj", request_obj, "debug");
        
        myreq = request_obj;
        myreq["method"] = "POST";
        
        httpRequestFn(myreq, errorCbFn, successCbFn);
    };
    this.httpPostFn = httpPostFn;
    
    var callRest = function(rq_obj, error_callback, success_callback) {
        p3nodeapi_logger("callRest:", "debug");
        p3nodeapi_logger("callRest: path", rq_obj.path, "debug");
        p3nodeapi_logger("callRest: method", rq_obj.method, "debug");
        
        var myreq = {"host": host
                     , "port": port
                     , "path": rq_obj.path
                     , "method": rq_obj.method
                     , "rtype": "json"
                     , "timeout": api_timeout
                     };
        
        if (rq_obj.method === "POST") {
            p3nodeapi_logger("callRest: data", rq_obj.data, "debug");
            
            var mydata = {"data": JSON.stringify(rq_obj.data)};
            myreq["data"] = querystring.stringify(mydata);
            myreq["headers"] = {'Content-Length': myreq["data"].length
                                , 'Content-Type': 'application/x-www-form-urlencoded'};
        }
        
        httpRequestFn(myreq, error_callback, success_callback);
    }; //callRest
        
    // get ticket
    var getTicket = function(errorFn, successFn) {
        p3nodeapi_logger("getTicket:", "debug");
        
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
        //if (jsonp === true) {
        //    call_path += "callback=?&";
        //}
        call_path += querystring.stringify(call_parms);
        
        var ticket = "NONE";
        var successTicket = function(rtnStatus, json) {
            p3nodeapi_logger("getTicket.successTicket rtnStatus: " + rtnStatus, "debug");
            p3nodeapi_logger("getTicket.successTicket json: ", json, "debug");
            
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
        p3nodeapi_logger("post:", "debug");
        p3nodeapi_logger("post: request_obj", request_obj, "debug");
        
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
        p3nodeapi_logger("get:", "debug");
        p3nodeapi_logger("get: request_obj", request_obj, "debug");
        
        getpost("GET", request_obj, errorCbFn, successCbFn);
    }; // get
    this.get = get;
        
        
    var getpost = function(type, request_obj, errorCbFn, successCbFn) {
        p3nodeapi_logger("getpost:", "debug");
        p3nodeapi_logger("getpost: request_obj", request_obj, "debug");
        
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
        
        if (jsonp === true) {
            my_qryparms_obj['rtnOnTktError'] = "1";
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
                    //if (jsonp === true) {
                    //    if (my_qryparms_obj.indexOf("?") === -1) {
                    //        cp += "?callback=?&";
                    //    } else {
                    //        cp += "&callback=?&";
                    //    }
                    //}
                    
                } else {
                    //if (jsonp === true) {
                    //    cp += "?callback=?&";
                    //} else {
                        cp += "?"
                    //}
                    
                    cp += querystring.stringify(my_qryparms_obj);
                }
                var rest_rq = {"path": cp, "method": "GET"};
                break;
                
            case "POST":
                //if (jsonp === true) {
                //    cp += "?callback=?&";
                //}
                
                var rest_rq = {"path": cp, "method": "POST", "data": my_qryparms_obj};
                break;
            }
            return rest_rq;
        }; //buildCallRequest
        
        var tryWithInitialTicket = function(completeCbFn) {
            p3nodeapi_logger("getpost.tryWithInitialTicket:", "debug");
            
            var rest_rq = buildCallRequest(api_ticket);
            
            callRest(rest_rq
                
                // errorFn
                , function(err) {
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
                    p3nodeapi_logger("getpost.tryWithInitialTicket.callRest successFn: rcode: ", rcode, "debug");
                    
                    // 299 is equivilent to 403 ticket error (for jsonp calls)
                    if ((rcode === "299") || (rcode === 299)) {
                        
                        var tkt_error = false;
                        if (typeof(robj) === 'string') {
                            if (robj.indexOf("invalid ticket") >= 0) {
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
                            get_cntl["request_error"] = robj;
                        }
                        completeCbFn();
                        
                    } else {
                        
                        get_cntl["request_is_done"] = true;
                        get_cntl["request_rcode"] = rcode;
                        get_cntl["request_robj"] = robj;
                        completeCbFn();
                    }
                }
            );
        };// tryWithInitialTicket
        
        var getNewTicketThenGET = function(completeCbFn) {
            p3nodeapi_logger("getpost.getNewTicketThenGET:", "debug");
            
            // skip this process if request_is_done
            if (get_cntl.request_is_done === true) {
                completeCbFn();
                return;
            }
            
            var getFn = function(tktObj, doneCb) {
                p3nodeapi_logger("getpost.getNewTicketThenGET.getFn:", "debug");
                p3nodeapi_logger("getpost.getNewTicketThenGET.getFn: tktObj: "
                    , tktObj
                    , "debug");
                
                var rest_rq = buildCallRequest(tktObj.ticket);
                
                callRest(rest_rq
                    // errorCb
                    , function(err) {
                        get_cntl["request_is_done"] = true;
                        get_cntl["request_error"] = err;
                        doneCb();
                    }
                    , function(rcode, robj) {
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
                p3nodeapi_logger("getpost.getNewTicketThenGET.tktAttempt:", "debug");
                
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
            p3nodeapi_logger("getpost.finalRoutine:", "debug");
            p3nodeapi_logger("getpost.finalRoutine: get_cntl", get_cntl, "debug");
            
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
        p3nodeapi_logger("geturl:", "debug");
        p3nodeapi_logger("geturl: request_obj", request_obj, "debug");
        
        var my_svc = svc; 
        var my_ver = version; 
        var my_rsc = resource;
        var my_qryparms_obj = request_obj.qryobj;
        
        var getFn = function(tktObj) {
            var call_path = "/" + site + "/rest/" + my_svc 
            + '/' + tktObj.ticket 
            + '/' + my_ver
            + '/' + my_rsc;
            
            call_path += "?" + querystring.stringify(my_qryparms_obj);
            
            successCbFn(200, call_path);
        }
        var badFn = function(err) {
            errorCbFn(err);
        }
        getTicket(badFn, getFn);
    };
    this.geturl = geturl;
    
    
    // build resource.qry() functions for all rproc values
    var rsc, qry, rqlst;
    var resource_obj = {};
    // Assure that the resource query exists in the rpocs list
    var resource_qry_exists = false;
    var exrprocs = [];
    
    for (rqryidx in rprocs) {
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
    for (rqrystr in exrprocs) {
        rqlist = exrprocs[rqrystr].split(":");
        rsc = rqlist[0];
        qry = rqlist[1];
        if (!resource_obj.hasOwnProperty(rsc)) {
            resource_obj[rsc] = {};
        }
        var setup = function(rs,qr) {
            resource_obj[rs][qr] = function(q,e,s) {
                                        var fn, rn_req;
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
        }; // setup
        setup(rsc,qry);
    }
    
    p3nodeapi_logger("p3RestApi: exposing named resources functions", "debug");
    for (rsc in resource_obj) {
        this[rsc] = {};
        for (qry in resource_obj[rsc]) {
            this[qry] = resource_obj[rsc][qry];
        }
    }
    
}; //p3NodeApi
exports.p3NodeApi = p3NodeApi;

});
