var PublicUrl = function(){
	var sizeScale;
	var lineStringPlacemark;
	var p3anzApi;
	var baseline = 1.8;

	var map_log;

	var initArgs = {
		 "csp_url":  "https://dev.picarro.com/investigator" //"https://dev.picarro.com/node"
		, "ticket_url":  "https://dev.picarro.com/investigator/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
		, "identity":  "081ebf61998a99032c362110b0acf7df"
		, "psys":  "investigator demo"
		, "rprocs":  '["AnzLog:byEpoch"]'
	};

// hackety - give me anz fdds2015
 //  initArgs = {
	// 	 "csp_url":  "https://dev.picarro.com/investigator" //"https://dev.picarro.com/node"
	// 	, "ticket_url":  "https://dev.picarro.com/investigator/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
	// 	, "identity":  "2999bad153a4ee48da94836ad265764f"
	// 	, "psys":  "FDDS2015"
	// 	, "rprocs":  '["AnzLog:byEpoch"]'
	// };


	var fake_data = {
		scientist:"Ben",
		anz_log:"CFADS2206-20130221-232538Z-DataLog_User_Minimal.dat",
		map_data:[
			{GPS_ABS_LAT:29,GPS_ABS_LONG:-69, CH4:2},
			{GPS_ABS_LAT:27,GPS_ABS_LONG:-71, CH4:4},
			{GPS_ABS_LAT:26,GPS_ABS_LONG:-69, CH4:3},
			{GPS_ABS_LAT:25,GPS_ABS_LONG:-71, CH4:2},
			{GPS_ABS_LAT:24,GPS_ABS_LONG:-69, CH4:4},
			{GPS_ABS_LAT:23,GPS_ABS_LONG:-71, CH4:2}
		]
	}

	var init = function(){
		var key = getURLParameter("s");
		getLogdata(key);
		p3anzApi = new P3ApiService(initArgs);
	}

	function getURLParameter(name) {
	    return decodeURI(
	        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
	    );
	}

	var getLogdata = function(key){
		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzLog";
		reqobj.qryobj = {
				"qry": "byEpoch"
			, 	"alog": "temp" 
			, 	'startEtm': 0
			, 	'decimated': 16
			// , 	'simplePath':true
			,	'varList':'["CH4","GPS_ABS_LAT","GPS_ABS_LONG"]'
			, 	'limit':'25000'
		};



		var err_fn = function(){
			log("error")
		}

		var rtn_fn = function(json, textStatus) {
			setView(json[0].GPS_ABS_LAT, json[0].GPS_ABS_LONG);
			map_log = json;
			renderLog()
		}


		var first_trip = function(){

		}

		$.ajax({
		  dataType:"jsonp",
		  url: "http://dev.picarro.com/short/" + key + "?callback=?",
		  type: "get",
		  jsonp: 'callback',
		  success: function(json){
		  	if(json && json !== "[]"){
		  		var mylog = JSON.parse(json)[0].anz_log;
			  	reqobj.qryobj.alog = mylog
			  	baseline = JSON.parse(json)[0].baseline;
		  	 	p3anzApi.get(reqobj, rtn_fn, err_fn);
		  	}		  	
		  },
		  error: function(data){
		  	log("error", data)
		  }
		});
	}

	var setView = function(lat, lon, height, angle){
		var h = height || 5000;
		var a = angle || 0;
		var ge = gi;
		var la = ge.createLookAt('');
		// double 	latitude,
		// double 	longitude,
		// double 	altitude,
		// KmlAltitudeModeEnum 	altitudeMode,
		// double 	heading,
		// double 	tilt,
		// double 	range
		la.set(lat, lon, h/2, ge.ALTITUDE_RELATIVE_TO_GROUND, a - 90, 66.213, h*3 + 800);
		ge.getView().setAbstractView(la);
		var center = new google.maps.LatLng(lat,lon)
		var marker = new google.maps.Marker({position:center})
		marker.setMap(google_map);
		google_map.setCenter(center); 
	}

	var renderLog = function(){
		var dlog = map_log;
		var ge = gi;
		if(lineStringPlacemark){
			ge.getFeatures().removeChild(lineStringPlacemark);
		}

		// https://dev.picarro.com/investigator/rest/gdu/ab0f2d9f9a4e3b19d612b954f3d038a2/1.0/AnzLog?callback=_jqjsp&qry=byEpoch&alog=CFADS2206-20130222-215646Z-DataLog_User_Minimal.dat&startEtm=0&limit=1&varList=%5B%22CH4%22%2C%22GPS_ABS_LAT%22%2C%22GPS_ABS_LONG%22%5D&reverse=true&_1363030052421=
		
		// Create the placemark.
		lineStringPlacemark = ge.createPlacemark('');

		// Create the LineString; set it to extend down to the ground
		// and set the altitude mode.
		var lineString = ge.createLineString('');
		lineStringPlacemark.setGeometry(lineString);
		lineString.setExtrude(true);
		lineString.setAltitudeMode(ge.ALTITUDE_RELATIVE_TO_GROUND);

		var min = 1000;
		var max = 0;

		for(var i = 0 ; i < dlog.length ; i++){
			if(dlog[i].CH4 < min) min = dlog[i].CH4;
			if(dlog[i].CH4 > max) max = dlog[i].CH4;
		}


		sizeScale = d3.scale.pow().domain([baseline,max]).range([100,5000])

		for(var i = 0 ; i < dlog.length ; i++){
			var ch4 = sizeScale(dlog[i].CH4);
			lineString.getCoordinates().pushLatLngAlt(dlog[i].GPS_ABS_LAT,dlog[i].GPS_ABS_LONG, ch4);
		}

		// return;

		// Create a style and set width and color of line.
		lineStringPlacemark.setStyleSelector(ge.createStyle(''));
		var lineStyle = lineStringPlacemark.getStyleSelector().getLineStyle();
		lineStyle.setWidth(3);
		lineStyle.getColor().set('7fff0000'); 
		var polyStyle = lineStringPlacemark.getStyleSelector().getPolyStyle();
		polyStyle.getColor().set('7fff0000');  // aabbggrr format

		// Add the feature to Earth.
		ge.getFeatures().appendChild(lineStringPlacemark);
	}

	return {
		init:init,
		renderLog:renderLog
	}	
}();

$(document).ready(function(){
	 // console.log("why was public_url.init commented out?");
	 // PublicUrl.init();
})

