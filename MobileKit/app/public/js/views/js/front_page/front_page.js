
var FrontPage = function(){
	var day_logs = {};
	var log_logs = {};
	var max_durr = 0;
	var log_map;
	var min_lat = 1000;
	var max_lat = -1000;
	var min_lon = 1000;
	var max_lon = -1000;
	var markers = {};
	var geocoder;
	var selected_circles;
	var mapG;
	var mapSVG;
	var accordion_opening;
	var current_path;
	var popup;
	var path_bounds;

	var map_filter_active = false;
	var map_filter_bounds;
	var map_filter_hash = {};

	var center_map_flag = false;
	var follow_timeout;

	var car_marker;

	var last_hover_name;

	var DS = DataStore;

	// var initArgs = {
	// 	 "csp_url":  "https://p3.picarro.com/nonda" //"https://dev.picarro.com/node"
	// 	, "ticket_url":  "https://p3.picarro.com/nonda/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
	// 	, "identity":  "d430013c9527c25525ec032bed2130f2"
	// 	, "psys":  "INVESTIGATOR"
	// 	, "rprocs":  '["AnzMeta:byAnz", "AnzLogMeta:byEpoch", "AnzLog:byEpoch"]'
	// };


// {"identity":"081ebf61998a99032c362110b0acf7df","sys":"investigator demo"}
	// var initArgs = {
	// 	 "csp_url":  "https://10.200.2.100:8081" //"https://dev.picarro.com/node"
	// 	, "ticket_url":  "https://localhost:8081/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
	// 	, "identity":  "TSGwBhGFSdC350bozBQ6HqgiT4bEYF7BPzBauH69"
	// 	, "psys":  "investigator"
	// 	, "rprocs":  '["AnzMeta:byAnz", "AnzLogMeta:byEpoch", "AnzLog:byEpoch"]'
	// };

	var initArgs = {
		 "csp_url":  "https://10.200.2.100:8081/node" //"https://dev.picarro.com/node"
		, "ticket_url":  "https://10.200.2.100:8081/node/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
		, "identity":  "85490338d7412a6d31e99ef58bce5dPM"
		, "psys":  "SUPERADMIN"
		, "rprocs":  '["AnzMeta:byAnz", "AnzLogMeta:byEpoch", "AnzLog:byEpoch"]'
	};
	
	// var initArgs = {
	// 	 "csp_url":  "https://10.200.2.78:8081/node" //"https://dev.picarro.com/node"
	// 	, "ticket_url":  "https://10.200.2.78:8081/node/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
	// 	, "identity":  "1de860aa77bbc0c64b47193822547d27"
	// 	, "psys":  "investigatorj"
	// 	, "rprocs":  '["AnzLog:byEpoch","AnzLogMeta:byEpoch", "AnzLog:byEpoch"]'
	// };

	var shareUrl = "https://dev.picarro.com/short/url"

	p3anzApi = new P3ApiService(initArgs);

	var init = function(){
		DS.getLogMeta(function(){
			renderDays();
		},function(){
			renderMarkers();
		});
		initMap();
		$('#accordion2').css({height:$(window).height() -100});
		geocoder = new google.maps.Geocoder();
	}

	var err_fn = function() {
	    var msg = 'error error';
		log(msg)
	};

	var shareLog = function(log_name, baseline){
		log("sharing log", log_name)
		var this_log = DS.getLog(log_name);
		log(this_log.decimated_data[0])
		var data = {
			scientist:"Bob Ross",
			anz_log:log_name,
			baseline:baseline
		}
		$.ajax({
		  url: shareUrl,
		  type:"POST",
		  data: data,
		  data_type:"JSON"
		}).done(function(d) {
			var url = "http://dev.picarro.com/public_url?s=" + d.short_url.split("/")[2]
			$('.share-input').val(url)
			$('#share_url').append("<a href=" + url + " target='_blank'><i class='icon-search'></i></a>")
		}).error(function(){
			var shorty = 'dev.picarro.com/short/cubakrwl8fr'
			var url = "http://dev.picarro.com/public_url?s=" + shorty.split("/")[2];
			$('#share_url').append("<a href=" + url + " target='_blank'><i class='icon-search'></i></a>")
			$('.share-input').val(url)
		});
	}

	var launchInvestigate = function(){
		var log_name = $(this).attr("id").split("$")[1] + ".dat";
		window.location = "/investigator?prime=false&alog=" + log_name + "&anz=" + 'CFADS2206';
	}

	var launchModal = function(){
		$('#myModal').modal('show')
		var log_name = $(this).attr("id").split("$")[1] + ".dat";
		var baseline = 0;

		var this_log = DS.getLog(log_name);
		var queue = this_log.decimated_data;

	    var data = [
	    	{
	    		label:"Ch4",
	    		data:[]
	    	}
	    ]

	    for(var i = 0 ; i < queue.length ; i++){
	    	if(queue[i].CH4 > .5){
	    		data[0].data.push([queue[i].EPOCH_TIME, queue[i].CH4])
	    	}    		
	    }

	    var options = {
	        series: {
	            lines: { show: true },
	            points: { show: false },
	            color:'#ff0d08'
	        },
	        crosshair: {
				mode: "y",
				color:'#0024ff'
			},
	        legend: { show:false },
	        xaxis: { time: 0 , show:false },
	        yaxis: { show:true, autoscaleMargin: 0.1 },
	        selection: { mode: "x" },
	        grid: { hoverable: true, clickable: true }
	    };

	    var placeholder = $("#modal-chart");
	    placeholder.show();

	    var modal_plot = $.plot(placeholder, data, options);

	   	$('#modal-chart').append("<div id='modal-value'>0</div>")
	   	var clicked = false;

	    placeholder.bind("plothover", function (event, pos) {
	    	if(clicked) return;
	    	var offset =   pos.pageY - $('#modal-chart').offset().top
	    	$('#modal-value').css({top:offset}).html(Math.round(pos.y *1000)/1000)
	    })
	    placeholder.bind("plotclick", function (event, pos) {
	    	clicked = true;
	    	var offset =   pos.pageY - $('#modal-chart').offset().top
	    	baseline = pos.y;
	    	$('#modal-value').css({top:offset}).html(Math.round(pos.y *1000)/1000)
	    })

	    $('#btn_modal_share').on("click", function(){
	    	shareLog(log_name, baseline);
	    })
	}


	var initMap = function(){
		log_map = L.map('map_container', {maxZoom:18}).setView([40.54654795, -75.588032833], 13);
		log_map._initPathRoot() 
		var mapquestUrl = 'http://{s}.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png',
        subDomains = ['otile1','otile2','otile3','otile4'],
        mapquestAttrib = '<a href="http://open.mapquest.co.uk" target="_blank">MapQuest</a>, <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>.'
        var mapquest = new L.TileLayer(mapquestUrl, {maxZoom: 24, attribution: mapquestAttrib, subdomains: subDomains});
        mapquest.addTo(log_map);

		mapSVG = d3.select('#map_container').select('svg');
    	mapG = mapSVG.append("g").attr("id", "amazingViz");

    	log_map.on("moveend", function(){
			filterByMap();
		});
		log_map.on("zoomend", function(){
			filterByMap();
		});

		log_map.on("viewreset", redrawSVG);

		 var greenIcon = L.icon({
            iconUrl: '/static/images/crosshair.png',
            shadowUrl: '/static/images/crosshair.png',

            iconSize:     [65, 65], // size of the icon
            shadowSize:   [0, 0], // size of the shadow
            iconAnchor:   [32, 32], // point of the icon which will correspond to marker's location
            shadowAnchor: [0, 0],  // the same for the shadow
            popupAnchor:  [0, 0] // point from which the popup should open relative to the iconAnchor
        });
        car_marker = L.marker([0,0], {icon: greenIcon}).addTo(log_map);
	}

	var filterByMap = function(){
		map_filter_active = false;
		map_filter_bounds = log_map.getBounds();
		map_filter_hash = {};

		return;
		
		for(var my_log in log_logs){
			var data = log_logs[my_log].json;
			if(data.GPS_ABS_LAT >= map_filter_bounds._southWest.lat && data.GPS_ABS_LAT <= map_filter_bounds._northEast.lat){
				if(data.GPS_ABS_LONG >= map_filter_bounds._southWest.lng && data.GPS_ABS_LONG <= map_filter_bounds._northEast.lng){
					map_filter_hash[log_logs[my_log].log_name.split(".")[0]] = true;
				}
			}			
		}

		if(map_filter_active){
			renderDays();
		}
	}

	var redrawSVG = function(){
		selected_circles = mapG.selectAll("image")
		
		selected_circles.attr("x",function(d) { 
			return log_map.latLngToLayerPoint(d.LatLng).x - 16
		})
		selected_circles.attr("y",function(d) { 
			return log_map.latLngToLayerPoint(d.LatLng).y - 32
		})
		selected_circles.attr("r",function(d) { 
			return 5
		})

	  	selected_circles.attr("fill", function(d) { 
	  		return '#0000ff';
  		})
	  	selected_circles.attr('opacity',function(d){
		  	return 1;
	  	})

	  	redrawPath();
	}

	var plotLog = function(name){
		var dlog = DS.getDecimatedData(name + ".dat");

		var queue = dlog;
		var this_log = []

	    var data = [
	    	{
	    		label:"Ch4",
	    		data:[]
	    	}
	    ]

	    for(var i = 0 ; i < queue.length ; i++){
    		data[0].data.push([queue[i].EPOCH_TIME, queue[i].CH4])
    		this_log.push([queue[i].EPOCH_TIME,queue[i].GPS_ABS_LAT,queue[i].GPS_ABS_LONG, queue[i].CH4])
	    }

		
	    var options = {
	        series: {
	            lines: { show: true },
	            points: { show: false },
	            color:'#ff0d08'
	        },
	        crosshair: {
				mode: "x",
				color:'#0024ff'
			},
	        legend: { show:false },
	        xaxis: { time: 0 , show:false },
	        yaxis: { show:true, autoscaleMargin: 0.0 },
	        selection: { mode: "x" },
	        grid: { hoverable: true, clickable: false }
	    };



	    var placeholder = $("#flot_" + name);

	    placeholder.parent().find(".chart_loading").remove();

	    if(placeholder.find('.flot-base').length > 0) return;

	    placeholder.show();


	    var time_plot = $.plot(placeholder, data, options);

		var getClosestValues = function(a, x) {
		    var lo = 0, hi = a.length-1;
		    while (hi - lo > 1) {
		        var mid = Math.round((lo + hi)/2);
		        if (a[mid][0] <= x) {
		            lo = mid;
		        } else {
		            hi = mid;
		        }
		    }
		    if (a[lo][0] == x) hi = lo;
		    return [a[lo] , a[hi]];
		}

		var follow_car = true;

		placeholder.bind("plothover", function (event, pos) {
			var position = getClosestValues(this_log, pos.x);
			var pos = position[0];
			var pos2 = position[1];

			var R = 6371;
		    var PI = Math.PI;

	        var lat2 = pos2[1];
	        var lat1= pos[1];
	        var lon2 = pos2[2];
	        var lon1 = pos[2];
	        var x = (lon2-lon1) * Math.cos((lat1+lat2)/2);
	        var y = (lat2-lat1);
	        var d = Math.sqrt(x*x + y*y) * R;
	        var deltaX = lat2-lat1;
	        var deltaY = lon2-lon1;
	        var angle = Math.atan(deltaY / deltaX) * 180 / PI;

			GoogleEarth.updatePlacemark(pos[1], pos[2], pos[3], angle)
			car_marker.setLatLng([pos[1], pos[2]])
			if(popup){
				log_map.removeLayer(popup);
			}
			if(follow_car){
		    	var xy = log_map.latLngToContainerPoint([pos[1],pos[2]]);
		    	if(xy.x < 200 || xy.x > $('#map_container').width() || xy.y < 0 || xy.y > $('#map_container').height()){
		    		var lat = pos[1];
		    		var lon = pos[2];
		    		
		    		if(follow_timeout) clearTimeout(follow_timeout)
		    		// follow_car = false;
		    		setTimeout(function(){
		    			log_map.panTo([lat,lon]);
		    			follow_car = true;
		    		},250)
		    	}
		    }
	    })

	    placeholder.bind("mouseout", function (event, pos) {
	    	// popup.openOn(log_map);
	    })

	    placeholder.bind("plotselected", function (event, ranges) {
	    	selectedMinTime = ranges.xaxis.from;
	    	selectedMaxTime = ranges.xaxis.to;

	    	center_map_flag = true;

	    	setTimeout(function(){
	    		center_map_flag = false;
	    	},500)
			
			var min = getClosestValues(this_log, selectedMinTime)
			var max = getClosestValues(this_log, selectedMaxTime)
			// center_map_flag = true;
			centerMapOnSelection(min[1], max[1], min[2], max[2])
	    });
	}

	var centerMapOnSelection = function(minLat, maxLat, minLon, maxLon){
	  	log_map.fitBounds([
			[minLat, minLon],
			[maxLat, minLon]
		]);
	}

	var scalePath = function(poly_log){
		var bounds = log_map.getBounds();
		var size = log_map.getSize();
		var base_lat = bounds._southWest.lat;
		var base_lon = bounds._southWest.lng;
		var xscale = (bounds._northEast.lng - bounds._southWest.lng);
		var yscale = (bounds._northEast.lat - bounds._southWest.lat);

		var local_min_lat = 1000;
		var local_max_lat = -1000;
		var local_min_lon = 1000;
		var local_max_lon = -1000;

		var geo_path = [];

		for(var i = 0 ; i < poly_log.length ; i++){
			if(poly_log[i][0] < local_min_lat && poly_log[i][0] !== 0) local_min_lat = poly_log[i][0];
			if(poly_log[i][0] > local_max_lat && poly_log[i][0] !== 0) local_max_lat = poly_log[i][0];
			if(poly_log[i][1] < local_min_lon && poly_log[i][1] !== 0) local_min_lon = poly_log[i][1];
			if(poly_log[i][1] > local_max_lon && poly_log[i][1] !== 0) local_max_lon = poly_log[i][1];
			geo_path.push({
				x:log_map.latLngToLayerPoint([poly_log[i][0],poly_log[i][1]]).x,
				y:log_map.latLngToLayerPoint([poly_log[i][0],poly_log[i][1]]).y
			})
		}

		return {bounds:{
			min_lat:local_min_lat,
			max_lat:local_max_lat,
			min_lon:local_min_lon,
			max_lon:local_max_lon
		},path:geo_path};		
	}

	var redrawPath = function(){
		startTimer("draw line")
		if(!current_path) return;
		var data2 = scalePath(current_path)

		path_bounds = data2.bounds;

		$('path').remove();

		var lineFunction = d3.svg.line()
		    .x(function(d) { return d.x; })
		    .y(function(d) { return d.y; })
		    .interpolate("linear");

		var lineGraph = mapSVG.append("path")
			.attr("d", lineFunction(data2.path))
			.attr("stroke", "red")
			.attr("stroke-width", 4)
			.attr("fill", "none");
		stopTimer("draw line");
	}

	var decimateMap = function(name){
		startTimer("decimatemap")

		current_path = DS.getMapData(name + ".dat");
		var decimated_path = DS.getDecimatedData(name + ".dat");

		stopTimer("decimatemap")
		
		redrawPath();
		log_map.fitBounds([
			[path_bounds.min_lat, path_bounds.min_lon],
			[path_bounds.max_lat, path_bounds.max_lon]
		]);		
		// return;

		GoogleEarth.setView((path_bounds.min_lat+path_bounds.max_lat)/2, (path_bounds.min_lon+path_bounds.max_lon)/2);


		setTimeout(function(){
			GoogleEarth.renderLog(decimated_path)
		},350)
		return;
		
	} 	

	var showCached = function(){
		log("show cached")
		return;
		var day_logs = DS.getLogsByDay();
		var day = day_logs[$(this).data('day')];
		for(var i = 0 ; i < day.length ; i++){
			var cache = store.get(day[i].short_name);
			if(cache){
				plotLog(cache.dlog, day[i].short_name)
			}
		}
	}

	var secondsToString = function(seconds) {
		var numhours = Math.floor(((seconds % 31536000) % 86400) / 3600);
		var numminutes = Math.floor((((seconds % 31536000) % 86400) % 3600) / 60);
		var numseconds = (((seconds % 31536000) % 86400) % 3600) % 60;
		if(numminutes < 10) numminutes = "0" + numminutes
		return numhours + "hrs " + numminutes + "mins";
	}

	var renderDays = function(){
		var dom = [];
		var day_logs = DS.getLogsByDay();
		var max_durr = DS.getMaxDurr();
		for(var day in day_logs){			
			var logs = day_logs[day];			
			var x=new Date();

			x.setFullYear(day.substring(0,4),day.substring(4,6) - 1,day.substring(6,8));
			var title = dateFormat(x, "dddd, mmmm dS, yyyy")// + " : " + logs.length; 
	        dom.push('<div class="accordion-group">')
	        	dom.push('<div class="accordion-heading">')
	        		dom.push('<a class="accordion-toggle" data-toggle="collapse" data-day="' + day + '" data-parent="#accordion2" href="#collapse_' + day + '">' + title + "<span class='log_count'></span></a>")
	        	dom.push('</div>')
	        	dom.push('<div id="collapse_' + day + '" class="accordion-body collapse">')
	        		dom.push('<div class="accordion-inner">')	        		

						for(var i = 0 ; i < logs.length ; i++){
							if(!map_filter_active || map_filter_hash[logs[i].short_name]){
								dom.push('<div class="log-wrapper" data-name="' + logs[i].short_name + '" >')
								dom.push('<h5><a class="btn btn-small" href="#"><i class="icon-plus"></i><i class="icon-minus"></i></a>' + logs[i].short_name.split('-')[0] + ' : ' + dateFormat(logs[i].time,"UTC:hh:MM TT") + ' : ')	
								dom.push('<span> ' + secondsToString(logs[i].durr) + '</span></h5>')
								dom.push('<div class="bar-wrapper"><div class="progress progress-info"><div class="bar" style="width: ' + logs[i].durr/max_durr*100 + '%;"></div></div></div>')
								dom.push('<div class="log-content">')
									dom.push('<img src="/static/images/public_url/loading.gif" class="chart_loading"></img>')
									dom.push('<div class="mini-flot" id="flot_' + logs[i].short_name + '"></div>')
									
									dom.push('<hr/>')
									dom.push('<div class="launch-modal btn btn-primary" id="modal$' + logs[i].short_name + '">Share</div>')
									dom.push('<div class="launch-investigate btn btn-primary" id="investigate$' + logs[i].short_name + '">Investigate</div>')
								dom.push('</div>')
								dom.push('<hr class="list-hr"/>')								
								dom.push('</div>')
							}								
						}

					dom.push('</div>')
				dom.push('</div>')	
			dom.push('</div>')	
		}
		$('#accordion2').html(dom.join(''));
		$('.accordion-body').each(function(){
			var len = $(this).find(".log-wrapper").length;
			if(len > 0){
				$(this).parent().find(".log_count").html(" : " + len)
			}else{
				$(this).parent().remove()
			}
		})
		$('#accordion2').on('click', '.log-wrapper', function(){
			// return;
			// var my_name = name;
			var my_data = $(this).data('name');
			setTimeout(function(){
				DS.getLogData(my_data, function(data, name){
					plotLog(name);
					decimateMap(name);
				})
			},1)
			
		})
		$('.accordion-toggle').one('click', showCached);
		$('.accordion-body').on("show", function(){
			log("show accordion")
			var day = $(this).attr("id").split("_")[1]
			accordion_opening = true;
			renderMarkers(day)
		})
		$('.accordion-body').on("hidden", function(){
			if(!accordion_opening){
				accordion_opening = false;
				renderMarkers();
			}			
		})
		$('.accordion-body').on("shown", function(){
			setTimeout(function(){
				accordion_opening = false;
			},100)			
		})
		$('.log-wrapper').on("mouseover", hoverLog)
		$('.launch-modal').on("click", launchModal)
		$('.launch-investigate').on("click", launchInvestigate)
		$('.log-wrapper h5').on("click", function(){
			if($(this).hasClass("toggle-open")){
				$(this).removeClass("toggle-open");
				$(this).parent().find(".log-content").animate({height:0})
			}else{
				$(this).addClass("toggle-open");
				$(this).parent().find(".log-content").animate({height:186})
			}
		})
	}

	var hoverLog = function(e){
		// log("!!!!!! before monday")
		return;
		var name = $(this).data("name")
		if(name === last_hover_name) return;
		last_hover_name = name;
		popup = L.popup({offset:new L.Point(0, -32), autoPan:false})
		    .setLatLng([log_logs[name].json.GPS_ABS_LAT, log_logs[name].json.GPS_ABS_LONG])
		    .setContent(name)
		    .openOn(log_map);
	}

	var selectMarker = function(e,t){
		var lat = t.getLatLng().lat;
		var lon = t.getLatLng().lng;
		var latlng = new google.maps.LatLng(lat, lon);

	    geocoder.geocode({'latLng': latlng}, function(results, status) {
			if (status == google.maps.GeocoderStatus.OK) {
				if (results[1]) {
					var addr = results[1].address_components[2].long_name + " " + results[1].address_components[3].short_name;
					log(addr);
				}
			} else {
				log("Geocoder failed due to: " + status);
			}
	    });
		var me = $('div [data-name="' + $(e.target._icon).data("my_name") + '"]');

		var grandad = me.parent().parent();
		 $('.accordion-body').each(function(){
		 	if($(this).hasClass("in") && $(this)[0] !== grandad[0]){
		 		$(this).collapse("hide");
		 	}
	 	})

		if(!grandad.hasClass("in")){
			grandad.collapse("show");
		}

		$('.log-wrapper').removeClass("selected")
		me.addClass("selected");

		var scrollToMe = function(){
			$('#accordion2').animate({
	         scrollTop: me.position().top
	     	}, 500)
		}

		grandad.one('shown', scrollToMe)
	}

	var clearMarkers = function(){
		$('.map_marker').remove();
		if(popup){
			log_map.removeLayer(popup)
		}		
	}

	var renderMarkers = function(this_day){
		clearMarkers();

		var today = false;
		var hidden = true;

		$('.accordion-body').each(function(){
		 	if($(this).hasClass("in")) hidden = false;
		})

		min_lat = 1000;
		max_lat = -1000;
		min_lon = 1000;
		max_lon = -1000;

		var geodata = {
			"type": "FeatureCollection",
			"features": []
		};

		if(accordion_opening){
			hidden = false;
		}		

		var day_logs = DS.getLogsByDay();

		for(var day in day_logs){
			for(var i = 0 ; i < day_logs[day].length ; i++){
				if(day == this_day || hidden){
					var this_log = day_logs[day][i]
					if(this_log){
						var this_name = this_log.short_name;
						if(this_log.lat < min_lat && this_log.lat !== 0) min_lat = this_log.lat;
						if(this_log.lat > max_lat && this_log.lat !== 0) max_lat = this_log.lat;
						if(this_log.lon < min_lon && this_log.lon !== 0) min_lon = this_log.lon;
						if(this_log.lon > max_lon && this_log.lon !== 0) max_lon = this_log.lon;

						if(this_log.lat !== 0 && this_log.lon !== 0){
							geodata.features.push({
						        "type": "Circle",
						        "geometry": {
						            "coordinates": [ this_log.lon,this_log.lat ]
						        },
						        "properties": {
						            "name":this_name
						        },
						        "LatLng":new L.LatLng(this_log.lat ,this_log.lon)
						    })
						}
					}
				}
			}
		}

		selected_circles = mapG.selectAll("circle")

		selected_circles
			.data(geodata.features)
			.enter()
		  	.append("svg:image")
			.attr("xlink:href", "/static/images/marker-icon.png")
			.attr("width", 32)
			.attr("height", 32)
			.attr("x",function(d) { 
				return log_map.latLngToLayerPoint(d.LatLng).x
			})
			.attr("y",function(d) { 
				return log_map.latLngToLayerPoint(d.LatLng).y
			})
			.attr("class", "map_marker")
			.attr("data-name", function(d) { 
				return d.properties.name.split(".")[0]
			})
			.attr("id", function(d) { 
				return "marker_" + d.properties.name.split(".")[0]
			})

		$('.map_marker').on("mouseover", hoverLog)

		log_map.fitBounds([
			[min_lat, min_lon],
			[max_lat, max_lon]
		]);	

		redrawSVG();
	}

	return{init:init}
}();

$(document).ready(function(){
	FrontPage.init()
})




	

