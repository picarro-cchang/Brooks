var DataStore = function(){
	var my_logs = {};
	var day_logs = null;
	var middle_count;
	var max_durr = 0;

	var initArgs = {
		 "csp_url":  "https://dev.picarro.com/investigator" //"https://dev.picarro.com/node"
		, "ticket_url":  "https://dev.picarro.com/investigator/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
		, "identity":  "081ebf61998a99032c362110b0acf7df"
		, "psys":  "investigator demo"
		, "rprocs":  '["AnzMeta:byAnz", "AnzLogMeta:byEpoch", "AnzLog:byEpoch"]'
	};

	p3anzApi = new P3ApiService(initArgs);

	var default_obj = {
		log_name:"default name",
		short_name:"default_short",
		durr:0,
		lat:-1,
		lon:-1,
		length:0,
		time:new Date(),
		raw_data:[],
		decimated_data:[],
		map_data:[]
	}

	var init = function(){
	}

	var err_fn = function() {
	    var msg = 'error error';
		log(msg)
	};

	var getLogs = function(){
		return my_logs;
	}

	var getMaxDurr = function(){
		return max_durr;
	}

	var getLatestIP = function(){
		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzMeta";
		reqobj.qryobj = {
			    "qry": "byAnz"
			, 	"anz": "FDDS2015"
			,	'varList':'["PRIVATE_IP"]'
		};

		if ($('#anzName').val()){
			reqobj.qryobj.anz = $('#anzName').val();
		}


		var rtn_fn = function(json, textStatus) {
			$('div #live_view').find("a").attr("href", "http://" +  json[0]['PRIVATE_IP'] + "/investigator?prime=false&anz=CFADS2290");
		}

		p3anzApi.get(reqobj, rtn_fn, err_fn);
	}

	var getLog = function(log_name){
		if(typeof my_logs[log_name] !== undefined){
			return my_logs[log_name];
		}else{
			if(typeof my_logs[log_name + ".dat"] !== undefined){
				return my_logs[log_name + ".dat"];
			}else{
				return {};
			}
		}
	}

	var getDecimatedData = function(log_name){
		if(typeof my_logs[log_name] !== undefined){
			return my_logs[log_name].decimated_data;
		}else{
			if(typeof my_logs[log_name + ".dat"] !== undefined){
				return my_logs[log_name].decimated_data;
			}else{
				return [];
			}
		}
	}

	var getMapData = function(log_name){
		if(typeof my_logs[log_name] !== undefined){
			return my_logs[log_name].map_data;
		}else{
			if(typeof my_logs[log_name + ".dat"] !== undefined){
				return my_logs[log_name + ".dat"].map_data;
			}else{
				return [];
			}
		}
	}

	var getLogsByDay = function(){
		if (day_logs) return day_logs;
		var last_date;
		day_logs = {};
		for(var l in my_logs){
			var x=new Date();
    		var d = my_logs[l].log_name.split('-')[1];
    		var t = my_logs[l].log_name.split('-')[2];
			x.setFullYear(d.substring(0,4),d.substring(4,6) - 1,d.substring(6,8));
			x.setUTCHours(t.substring(0,2));
			x.setUTCMinutes(t.substring(2,4));
    		if(d !== last_date){
    			day_logs[d] = [];
    			last_date = d;
    		}
    		my_logs[l].time = x;
    		day_logs[d].push(my_logs[l])
		}
		return day_logs;
	}

	var setProps = function(log_name, obj){
		if(typeof my_logs[obj.log_name] === 'undefined'){
			if(typeof store.get(log_name) === 'undefined'){
				my_logs[obj.log_name] = jQuery.extend({}, default_obj);
			}else{
				my_logs[obj.log_name] = store.get(log_name);
				var this_log = my_logs[obj.log_name];
				for(var el in default_obj){
					if(typeof this_log[el] === 'undefined'){
						this_log[el] = default_obj[el];
					}
				}
			}
		}

		var my_log = my_logs[obj.log_name];

		for(var o in obj){
			my_log[o] = obj[o];
		 	my_logs[log_name][o] = obj[o];
		 	if(o === "raw_data"){

		 		// var dec = decimateLog(my_logs[log_name][o], 16);
		 		var dec = my_logs[log_name][o];
		 		var map = simplifyPath(my_logs[log_name][o], 20);
		 		my_log.decimated_data = dec;
		 		my_logs[log_name].decimated_data = dec;

				my_log.map_data = map;
		 		my_logs[log_name].map_data = map;
		 	}
		}

		my_log.short_name = log_name.split(".")[0];
		store.set(log_name, my_log);
	}

	var decimateLog = function(dataLog, interval){
		var di = [];
		var sumCh4 = 0;
		var meanElement;

		for(var i = 0 ; i < dataLog.length ; i++){
			sumCh4 += dataLog[i].CH4;
			if(i%(interval)/2 == 0){
				meanElement = dataLog[i];
			}
			if(i%interval == 0){
				meanElement.ch4 = sumCh4/interval;
				di.push(meanElement);
				sumCh4 = 0;
			}
		}
		return di;
	}

	var simplifyPath = function(points, tolerance ) {
	    var R = 6371;
	    var decimated = [];
	    var PI = Math.PI;
	    var tol = tolerance || 20;
	    var lastBearing = 0;

	    for(var i = 0 ; i < points.length - 1 ; i++){
	        var p = points[i];
	        var p2 = points[i+1];
	        var lat2 = p2.GPS_ABS_LAT;
	        var lat1= p.GPS_ABS_LAT;
	        var lon2 = p2.GPS_ABS_LONG;
	        var lon1 = p.GPS_ABS_LONG;
	        var x = (lon2-lon1) * Math.cos((lat1+lat2)/2);
	        var y = (lat2-lat1);
	        var d = Math.sqrt(x*x + y*y) * R;
	        var deltaX = lat2-lat1;
	        var deltaY = lon2-lon1;
	        var angle = Math.atan(deltaY / deltaX) * 180 / PI

	        if(d > 0 && lat1 !== 0 && lon1 !== 0){
	        	if(Math.abs(lastBearing - angle) > tol){
	        		lastBearing = angle;
	        		decimated.push([lat1, lon1])
	        	}
	        }
	    }
	    return decimated;
	};


	var getLogMeta = function(callback, callback2){

		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzLogMeta";
		reqobj.qryobj = {
				"qry": "byEpoch"
			// , 	"anz": "CFADS2290"
			, 	"anz": "FDDS2015"
			, 	'startEtm':0
			,	'varList':'["LOGNAME", "durr"]'
                        ,       'limit':2000
			, 	'reverse':'true'
		};

		if ($('#anzName').val()){
			reqobj.qryobj.anz = $('#anzName').val();
		}

		middle_count = 0;
		var rtn_fn = function(json, textStatus) {
		    if(json){
		    	var lastDate;
		    	getLatestIP();
		    	for(var i = 0; i < json.length; i++){
		    		if(json[i].LOGNAME.search("Sensor") < 0){
		    			if(json[i].durr > max_durr) max_durr = json[i].durr;
			    		setProps(json[i].LOGNAME,{
			    			log_name:json[i].LOGNAME
			    		})
			    		if(json[i].durr){
			    		  setProps(json[i].LOGNAME,{
			    			  durr:json[i].durr
			    		  })
			    		};
			    		middle_count++;
			    		getLogMiddle(json[i].LOGNAME, function(){
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


	var getLogMiddle = function(log_name, callback){
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


		var name = log_name + "_middle";

		var err_fn = function(){
			log('error');
			middle_count--;
			callback();
		}

		var rtn_fn = function(json, textStatus){
			middle_count--;
			callback();
			setProps(log_name, {
				length:json[0].row,
				lat:json[0].GPS_ABS_LAT,
				lon:json[0].GPS_ABS_LONG
			})
		}

		if(my_logs[log_name].lat === -1 && my_logs[log_name].lon === -1){
			p3anzApi.get(reqobj, rtn_fn, err_fn);
		}else{
			middle_count--;
			callback();
		}
	}


	var getLogData = function(short_name, callback){
		log_name = short_name + ".dat";

		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzLog";
		reqobj.qryobj = {
				"qry": "byEpoch"
			, 	"alog": log_name
			, 	'startEtm': 0
			, 	'decimated': 8
			,	'varList':'["CH4","GPS_ABS_LAT","GPS_ABS_LONG"]'
			, 	'limit':'25000'
		};
		/*
      ,   'decimated': 8
			,   'simplePath': true
		  you can use these two params above
		*/
		var rtn_fn = function(json, textStatus) {
			setProps(log_name, {raw_data:json} );
			callback(my_logs[log_name].raw_data, short_name);
		}

		if(my_logs[log_name].raw_data.length === 0){
			p3anzApi.get(reqobj, rtn_fn, err_fn);
		}else{
			callback(my_logs[log_name].raw_data, short_name)
		}
	}


	var getLogFile = function(short_name, callback){
		log_name = short_name + ".dat";

		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzLog";
		reqobj.qryobj = {
				  "qry": "byEpoch"
			, 	"alog": log_name
			, 	'startEtm': 0
			, 	'decimated': 8
			,	  'varList':'["CH4","GPS_ABS_LAT","GPS_ABS_LONG"]'
			, 	'limit':'25000'
			,   'rtnFmt':'file'
		};
		/*
      ,   'decimated': 8
			,   'simplePath': true
		  you can use these two params above
		*/
		var rtn_fn = function(json, textStatus) {
			setProps(log_name, {raw_data:json} );
			console.log("my_logs[log_name]" + my_logs[log_name]);
			callback(json, textStatus);
		}

		p3anzApi.geturl(reqobj, rtn_fn, err_fn);
		// if(short_name){
		// 	console.log "has short name"
		//   p3anzApi.get(reqobj, rtn_fn, err_fn);
		// }
	 //  if(my_logs[log_name].raw_data.length === 0){
	 //  	p3anzApi.get(reqobj, rtn_fn, err_fn);
	 //  }else{
	 //  	callback(my_logs[log_name].raw_data, short_name)
	 //  }
	}

	// 	var rtn_fn = function(json, textStatus) {
	// 		console.log(json);
	// 		console.log(textStatus);
	// 		setProps(log_name, {raw_data:json} );
	// 		callback(console.log("callbak!", short_name);
	// 	}

	// 	if(0 === 0){
	// 		p3anzApi.get(reqobj, rtn_fn, err_fn);
	// 	}else{
	// 		console.log(my_logs[log_name].raw_data)
	// 		callback(my_logs[log_name].raw_data, short_name)
	// 	}
	// }

	return {
		init:init,
		setProps:setProps,
		getLogsByDay:getLogsByDay,
		getLogMeta:getLogMeta,
		getLogData:getLogData,
		getDecimatedData:getDecimatedData,
		getMapData:getMapData,
		getLog:getLog,
		getMaxDurr:getMaxDurr,
		getLogFile:getLogFile
	}
}();
