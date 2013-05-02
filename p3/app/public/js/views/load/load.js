var load = function(){
	var middle_count;

	var global_count = 0;

	var loop_me = true;

	var initArgs = {
		 "csp_url":  "https://10.200.2.78:8081/node" //"https://dev.picarro.com/node"
		, "ticket_url":  "https://10.200.2.78:8081/node/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
		, "identity":  "1de860aa77bbc0c64b47193822547d27"
		, "psys":  "investigatorj"
		, "rprocs":  '["AnzLog:byEpoch","AnzLogMeta:byEpoch", "AnzLog:byEpoch"]'
	};
	
	var shareUrl = "https://dev.picarro.com/short/url"

	var p3anzApi = new P3ApiService(initArgs);

	var init = function(){
		$('#btn_start').click(function(){
			loop_me = true;
			startRound()
		})
		$('#btn_stop').click(stopRound)
	}

	var startRound = function(){
		log("start", loop_me)
		if(loop_me){
			load_one(
				function(){log("callback1")},
				function(){
					setTimeout(startRound, 5);
					log("callback2")
				}
			)
		}
	}

	var stopRound = function(){
		log("stopping")
		loop_me = false;
	}

	var err_fn = function(){
		log("error")
	}

	var loadTwo = function(log_name, callback){
		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzLog";
		reqobj.qryobj = {
				"qry": "byEpoch"
			, 	"alog": log_name
			, 	'startEtm':0
			, 	'limit':1
			,	'varList':'["CH4","GPS_ABS_LAT","GPS_ABS_LONG"]'
			, 	'reverse':'true'
		};

		var err_fn = function(){
			log('error');
			middle_count--;
			callback();
		}

		var rtn_fn = function(json, textStatus){
			middle_count--;
			$('#global_count').html(global_count++)
			callback();
			// log("return two")
		}
		// rtn_fn()

		// return;

		if(!loop_me){
			rtn_fn();
		}

		p3anzApi.get(reqobj, rtn_fn, err_fn);
	}

	var load_one = function(callback, callback2){
		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzLogMeta";
		reqobj.qryobj = {
				"qry": "byEpoch"
			, 	"anz": "CFADS2290"
			, 	'startEtm':0
			,	'varList':'["LOGNAME", "durr"]'
			, 	'reverse':'true'
		};

		middle_count = 0;

		var rtn_fn = function(json, textStatus) {
		    if(json){ 	
		    	for(var i = 0; i < json.length; i++){
		    		if(json[i].LOGNAME.search("Sensor") < 0){
			    		middle_count++;
			    		loadTwo(json[i].LOGNAME, function(){
			    			setTimeout(function(){
								if(middle_count === 0){
									middle_count = -1;
				    				callback2();
				    			}
			    			},100)			    			
			    		});
			    	}
		    	}
		    }
		    callback();
		    return;
		};
		p3anzApi.get(reqobj, rtn_fn, err_fn);
	}

	return {
		init:init
	}
}();

$(document).ready(function(){
	console.log("test")
	load.init();
})