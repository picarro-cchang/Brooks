var GoogleEarth = function(){
	var lineStringPlacemark;
	var sizeScale;
	var marker;

	var init = function(){
		log("ge  init")
		initPlacemark();
	}

	var initPlacemark = function(){
		// Create the placemark.
		marker = ge.createPlacemark('');


		// Set the placemark's location.  
		var point = ge.createPoint('');
		point.setAltitudeMode(ge.ALTITUDE_RELATIVE_TO_GROUND);
		point.setLatitude(12.345);
		point.setLongitude(54.321);
		point.setAltitude(100);
		marker.setGeometry(point);
		var icon = ge.createIcon('');
		icon.setHref('http://dev.picarro.com/static/images/red_arrow.png');
		var style = ge.createStyle(''); //create a new style
		style.getIconStyle().setIcon(icon); //apply the icon to the style
		marker.setStyleSelector(style); //apply the style to the placemark

		// Add the placemark to Earth.
		ge.getFeatures().appendChild(marker);
	}

	var updatePlacemark = function(lat,lon,ch4, angle){
		var angle = angle || 0;
		setView(lat, lon, sizeScale(ch4), angle)
		var point = ge.createPoint('');
		point.setLatitude(lat);
		point.setLongitude(lon);
		point.setAltitude(sizeScale(ch4)); //in meters 
		point.setAltitudeMode(ge.ALTITUDE_RELATIVE_TO_SEA_FLOOR); 
		marker.setGeometry(point);
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
	}

	var renderLog = function(dlog){
		startTimer("renderLog2")
		var ge = gi;
		if(lineStringPlacemark){
			ge.getFeatures().removeChild(lineStringPlacemark);
		}
		
		// Create the placemark.
		lineStringPlacemark = ge.createPlacemark('');

		// Create the LineString; set it to extend down to the ground
		// and set the altitude mode.
		var lineString = ge.createLineString('');
		

		var min = 1000;
		var max = 0;

		for(var i = 0 ; i < dlog.length ; i++){
			if(dlog[i].CH4 < min && dlog[i].CH4 > 1) min = dlog[i].CH4;
			if(dlog[i].CH4 > max) max = dlog[i].CH4;
		}

		var baseline = 1.8;

		sizeScale = d3.scale.pow().domain([min,max]).range([10,4000])

		for(var i = 0 ; i < dlog.length ; i++){
			var ch4 = sizeScale(dlog[i].CH4);
			lineString.getCoordinates().pushLatLngAlt(dlog[i].GPS_ABS_LAT,dlog[i].GPS_ABS_LONG, ch4);
		}

		lineStringPlacemark.setGeometry(lineString);
		lineString.setExtrude(true);
		lineString.setAltitudeMode(ge.ALTITUDE_RELATIVE_TO_GROUND);

		stopTimer("renderLog2")

		// Create a style and set width and color of line.
		lineStringPlacemark.setStyleSelector(ge.createStyle(''));
		var lineStyle = lineStringPlacemark.getStyleSelector().getLineStyle();
		lineStyle.setWidth(3);
		lineStyle.getColor().set('70000fff'); 
		var polyStyle = lineStringPlacemark.getStyleSelector().getPolyStyle();
		polyStyle.getColor().set('70000fff');  // aabbggrr format

		// Add the feature to Earth.
		ge.getFeatures().appendChild(lineStringPlacemark);
	}

	return{
		init:init,
		setView:setView,
		renderLog:renderLog,
		updatePlacemark:updatePlacemark
	}
}();
