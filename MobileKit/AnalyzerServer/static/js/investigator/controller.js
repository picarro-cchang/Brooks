var mapmaster = mapmaster || {};

var tp;

var locationFilter;

               
mapmaster.Controller = function(){
	var CNSNT = mapmaster.CNSNT;
	var TXT = mapmaster.TXT;
	var CSTATE = mapmaster.CSTATE;
	var HBTN = mapmaster.HBTN;
	var LBTNS = mapmaster.LBTNS;
	var COOKIE_NAMES = mapmaster.COOKIE_NAMES;

	if(getURLParameter("prime") === "false"){
		CNSNT.prime_view = false;
	    CNSNT.resturl = "https://dev.picarro.com/investigator/rest";
	    CNSNT.resource_AnzLog = "gdu/<TICKET>/1.0/AnzLog";
	    CNSNT.resource_Admin = "sec/dummy/1.0/Admin"; 

	    var initArgs = {
			 "csp_url":  "https://dev.picarro.com/investigator" //"https://dev.picarro.com/node"
			, "ticket_url":  "https://dev.picarro.com/investigator/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
			, "identity":  "TSGwBhGFSdC350bozBQ6HqgiT4bEYF7BPzBauH69"
			, "psys":  "investigator"
			, "rprocs":  '["AnzMeta:byAnz","AnzLogMeta:byEpoch", "AnzLogNote:byEpoch", "AnzLog:byPos", "AnzLogNote:dataIns"]'
		};

	    var p3anzApi = new P3ApiService(initArgs);
	}else{
		CSTATE.prime_view = true;
	}
	

	var dataCount = 0;
	var path_queue = [];
	var path_data = [];
	var mapSVG;
	var mapG;
	var mapSVGInit = false;
	var geodata = {};
	var geoCollection = [geodata,geodata];
	var decimated = {};
	var decimate_level = 4;
	var decimate_level_zoom = 2;
	var map_decimation = 1;
	var chart_decimation = 1;

	var dataMin = 10000;
	var dataMax = 0;

	var last_flot = 0;

	var svgMin = 0;
	var svgPow = 0.5;

	var selectedMinTime = 0;
	var selectedMaxTime = 10000000000000000000;

	var selected_circles;

	var ignore_plot_below = 1.5;

	var temp_render_count = 10000;
	var map_threshold = 1;

	var minLat = 1000;
	var maxLat = -1000;
	var minLon = 1000;
	var maxLon = -1000;	

	var minSelLat = 1000;
	var maxSelLat = -1000;
	var minSelLon = 1000;
	var maxSelLon = -1000;

	var wind_visible = false;
	var follow_car = false;

	var map_zooming = false;
	var data_pause_current = false;
	var data_pause = false;

	var center_map_flag = true;

	var time_plot;
	var realtime_plot;
	var plot_init = false;

	var view_filter = false;
	var time_filter = false;

	var pulsingUp = true;
	var pulseMultiplier = 1;

	var lastColor = 'Reds';

	var colorStart = '#25ff00';
	var colorEnd = '#ff0014';
	// var colorArray = [colorStart,colorEnd]
	var colorArray = ["#2D823F","#3CA448","#87C543","#F0E927","#F9CF1A","#F89921","#CC5021","#ED1C24"]

	var quantize = d3.scale.quantile().domain([2, 2.8]).range(d3.range(9));

	var highlited_temp;

	var temp_count = 0;
	var control_panels = ['setting', 'map'];

	var transition_time = 300;

	var realtime_threshold = 0;

	var last_circle_rendered = 0;

	var dom_holder;
	var dom_holder2;
	var dom_parent;

	var last_decimation_level = 0;

	var coverageLayer;

	var tile_points = [];

	var image_overlay;

	var last_queue = 0;

	var MyCustomLayer;
	var layer0;
	var canvas;
	var canvas_wind;

	var hack_offset_x = 0;
	var hack_offset_y = 0;

	var valve_mask = 0.0;

	var isotopic_layer;

	var isotopics = [];

	var min_plot = 0;
	var max_plot = 0;

	var dtype = "Json";

	var captureState = "IDLE";
	var cancelStates =   ['TRIGGERED','INACTIVE','CANCELLING'];
	var switchStates =   ['ARMED','TRIGGER_PENDING'];

	var analysisInfo = [];

	var saveDataPoint = function(name, diff){
		log("Profile", name, diff);
	};

	var createReport = function(){
		// log("creating report");
	};

    /**
     * Instruments a method to have profiling calls.
     * @param {String} name The name of the report for the function.
     * @param {Function} method The function to instrument.
     * @return {Function} An instrumented version of the function.
     * @method instrument
     * @static
     */

	CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
	  if (w < 2 * r) r = w / 2;
	  if (h < 2 * r) r = h / 2;
	  this.beginPath();
	  this.moveTo(x+r, y);
	  this.arcTo(x+w, y,   x+w, y+h, r);
	  this.arcTo(x+w, y+h, x,   y+h, r);
	  this.arcTo(x,   y+h, x,   y,   r);
	  this.arcTo(x,   y,   x+w, y,   r);
	  this.closePath();
	  return this;
	}

	var instrument = function(name, method){
        //create instrumented version of function
        var newMethod = function () {
            var start = new Date(),
                retval = method.apply(this, arguments),
                stop = new Date();
            
            saveDataPoint(name, stop-start);
            return retval;                
        };     

        //copy the function properties over
        $.extend( method, newMethod);
        
        //assign prototype and flag as being profiled
        newMethod.prototype = method.prototype;
        
        //create the report
        createReport(name);

        //return the new method
        return newMethod;
    };

    var addThreeZeros = function(num){
    	var val = Math.round(num*1000)/1000
	    if(val % 1 == 0){
	    	val = val + ".000";
	    }else if(val*10 % 1 == 0){
	    	val = val + "00";
	    }else if(val*100 % 1 == 0){
	    	val = val + "0";
	    }
	    return val
    }

	var initialize = function(winH, winW) {
		//secure ping (to assure browsers can see secure site)
		$("#id_content_spacer").html('<img src="' + CNSNT.resturl + '/pimg' + '"/>');
		getTicket(initialize_gdu);
		$('#tmp_insert_btn').click(function(){
			insertQueue();
		});

		$('#color_select').change(function(){			
			lastColor = $(this).val();
			d3.select('#map2_canvas').select('svg').attr("class", lastColor);
		});

		$("#id_legend_canvas").on('click', '.legend-wrapper', function(){
			map_threshold = $(this).data('size');
			svgMin = map_threshold;
			plotFlot(decimated['int' + decimate_level]);
			redrawCanvas();
		});

		$(window).resize(function() {
			resize_map();
		});

		$('#btn_car_controls').tappable(toggleCarControls);
		$('#btn_iso_controls').tappable(toggleCaptureControls);
		$('#btn_wind_controls').tappable(toggleWind);
		$('#btn_cursor_controls').tappable(toggleCursor);
		$('#btn_chart_controls').tappable(toggleChart);
		$('#btn_legend_controls').tappable(toggleLegend);
		$('#btn_pause_controls').tappable(togglePause);
		
		$('#btn_map_controls').tappable(function(){togglePane('map', 'setting');});
		$('#btn_setting_controls, #setting_controls .control-close').tappable(function(){togglePane('setting', 'map');});
		// showPanel('setting');
		$('#car_signal-top').tappable(setSignalTop)	;
		$('#car_signal-front').tappable(setSignalFront);
		$('#btn_capture_manual').tappable(startCaptureManual);
		$('#btn_capture_trigger').tappable(startCaptureTrigger);

		$('.settings-btn-wrapper').tappable(toggleSwitch);
		// $('#btn_reference_new').tappable(toggleReference);
		// $('#btn_restart').tappable(restartLog);
		// $('#btn_shutdown').tappable(shutdownAnalyzer);
		// $('#btn_reference_gas').tappable(toggleReference);

		// $('#btn_map_controls').tappable(function(){
		// 	confirm("yo")
		// })

      	$('#btn_close_weather, #modal_restart_log .btn-close').on("click", function(){
			$('#btn_restart').removeClass("locked");
			$('#btn_restart').trigger("click");
		})
      	$('#modal_shutdown_analyzer .btn-close').on("click", function(){
			$('#btn_shutdown').removeClass("locked");
			$('#btn_shutdown').trigger("click");
		})

      	// togglePane('map', 'setting');

		initSignal();


		insertQueue = instrument("insertQueue", insertQueue);
		// decimateQueue = instrument("decimateQueue", decimateQueue);
		// redrawCanvas = instrument("redrawCanvas", redrawCanvas);
		domHide = instrument("domHide", domHide);
		domShow = instrument("domShow", domShow);
		// drawWindRose = instrument("drawWindRose", drawWindRose);


        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }

        // !!!!!! Remove for push
        // setInterval(getCaptureState,2000)

        getAnalysis();
	};

	var resetMap = function(){
		path_data = [];
		path_queue = [];
		CSTATE.firstData = true;
		CSTATE.clearConcMarkers = true;

		insertQueue();
		plotFlot();
	}

	var domHide = function(){
        // dom_parent = $('.leaflet-overlay-pane');

        // $('.leaflet-overlay-pane').find('#canvas_bubbles')
        dom_holder = $('.leaflet-overlay-pane').find('#canvas_bubbles').css({top:-2000});
        dom_holder2 = $('.leaflet-overlay-pane').find('#canvas_wind').css({top:-2000});
	};

	var domShow = function(){
		// dom_holder.css({alpha:1})
		// dom_holder2.css({alpha:1})
		// dom_parent.append(dom_holder);
		// dom_parent.append(dom_holder2);
	};

	var toggleCarControls = function(){
		$('#car_controls').show();
		if($('#car_controls').hasClass('locked')){
			return;
		}
		if($('#car_controls').hasClass('selected')){
			$('#pageFooter').removeClass("grayscale")
			$('#btn_car_controls').removeClass('selected');
			$('#car_controls').removeClass('selected');
			$('#car_controls').css({bottom:0}).animate({bottom:-130}, transition_time);
		}else{
			$('#pageFooter').addClass("grayscale")
			$('#btn_car_controls').addClass('selected');
			$('#car_controls').addClass('selected');
			$('#car_controls').css({bottom:-130}).animate({bottom:0}, transition_time);
		}
	}

	var toggleCaptureControls = function(){
		$('#capture_controls').show();
		if($('#capture_controls').hasClass('locked')){
			return;
		}
		if($('#capture_controls').hasClass('selected')){
			$('#pageFooter').removeClass("grayscale")
			$('#btn_capture_controls').removeClass('selected');
			$('#capture_controls').removeClass('selected');
			$('#capture_controls').css({bottom:0}).animate({bottom:-130}, transition_time);
		}else{
			$('#pageFooter').addClass("grayscale")
			$('#btn_capture_controls').addClass('selected');
			$('#capture_controls').addClass('selected');
			$('#capture_controls').css({bottom:-130}).animate({bottom:0}, transition_time);
		}
	}

	var toggleSwitch = function(){
		if($(this).hasClass('locked')){
			return;
		}
		if($(this).attr("ID") === "btn_reference_new"){
			toggleReference();
		}
		if($(this).hasClass('selected')){
			$(this).removeClass('selected');
			$(this).find('.switch_handle').css({left:60}).animate({left:2}, transition_time);
			$(this).find('.left_text').animate({opacity:1});
			$(this).find('.right_text').animate({opacity:0.5});	
	
		}else{
			$(this).addClass('selected');
			$(this).find('.switch_handle').css({left:2}).animate({left:60}, transition_time);
			$(this).find('.left_text').animate({opacity:0.5});
			$(this).find('.right_text').animate({opacity:1});
			if($(this).attr("ID") === "btn_shutdown"){
				shutdownAnalyzer();
			}
			if($(this).attr("ID") === "btn_restart"){
				restartLog();
			}	
		}
	};

	var toggleLegend = function(){
		if($('.icon-legend').hasClass('selected')){
			$('.icon-legend').removeClass('selected');
			$('#legend-controls').animate({left:-50}, transition_time);		
		}else{
			$('.icon-legend').addClass('selected');
			$('#legend-controls').animate({left:4}, transition_time);			
		}
	};

	var togglePause = function(){
		if($('.icon-pause').hasClass('selected')){
			$('.icon-pause').removeClass('selected');
			data_pause = true;
		}else{
			$('.icon-pause').addClass('selected');
			data_pause = false;	
		}
	};

	var confirmCancalCapture = function(){
		if (confirm("Cancel Capture?")==true){
			$('#btn_capture_manual').removeClass("selected");
			$('#btn_capture_trigger').removeClass("selected");
			setTimeout(function(){
				toggleCaptureControls();
				$('#btn_iso_controls').removeClass('selected')
			},700)
			var err_fn = function(err){
	        	log("error Cancel")
	        }
			var success_fn = function(data){
	        	log(data)
	        }
		  	call_rest(CNSNT.svcurl, "cancelIsotopicCapture", dtype,{},  success_fn, err_fn);
	  	}
	}

	var startCaptureManual = function(){
		if($('#btn_capture_manual').hasClass("selected") || cancelStates.indexOf(captureState) >= 0){
			confirmCancalCapture();
		}else{
			if(switchStates.indexOf(captureState) >= 0){
				$('#btn_capture_trigger').removeClass("selected");
			}
			var err_fn = function(err){
	        	log("error Capture Manual")
	        }
			var success_fn = function(data){
	        	log(data)
	        }
			$('#btn_capture_manual').addClass("selected");
			setTimeout(function(){
				toggleCaptureControls();
				$('#btn_iso_controls').addClass('selected')
			},1000)
			call_rest(CNSNT.svcurl, "startManualIsotopicCapture", dtype,{},  success_fn, err_fn);
		}
	};

	var startCaptureTrigger = function(){
        if($('#btn_capture_trigger').hasClass("selected") || $('#btn_capture_manual').hasClass("selected") || cancelStates.indexOf(captureState) >= 0){
			confirmCancalCapture();
		}else{
			var err_fn = function(err){
	        	log("error Capture Trigger")
	        }
			var success_fn = function(data){
	        	log(data)
	        }
			$('#btn_capture_trigger').addClass("selected")
			setTimeout(function(){
				toggleCaptureControls();
				$('#btn_iso_controls').addClass('selected')
			},1000)
			call_rest(CNSNT.svcurl, "startTriggeredIsotopicCapture", dtype,{},  success_fn, err_fn);
		}
	};

	var getCaptureState = function(){
		var err_fn = function(err){
        	log("error Capture Trigger")
        }
		var success_fn = function(data){
        	log(data.result)
        	captureState = data.result;
        }
		call_rest(CNSNT.svcurl, "getIsotopicCaptureState", dtype,{},  success_fn, err_fn);

	}


	var setReferenceIso = function(){
        var err_fn = function(err){
        	log("error Reference top")
        }
		var success_fn = function(data){
        	log(data)
        }

		call_rest(CNSNT.svcurl, "setCurrentReference", dtype,{reference:"ISOTOPIC"},  success_fn, err_fn);	
	};

	var setReferenceConc = function(){
        var err_fn = function(err){
        	log("error Reference front")
        }
		var success_fn = function(data){
        	log(data)
        }

		call_rest(CNSNT.svcurl, "setCurrentReference", dtype,{reference:"CONCENTRATION"}, success_fn, err_fn);
	};

	var initReference = function(){
        var err_fn = function(err){
        	log("error init")
        }
		var success_fn = function(data){
			// When first valued received, switch on value and set mast state.
        	log(data)
        }

		call_rest(CNSNT.svcurl, "getCurrentReference",dtype, {},  success_fn, err_fn);
	}

	var toggleReference = function(){
		if($('#btn_reference').hasClass("selected")){
			setReferenceConc();
		}else{
			setReferenceIso();
		}
	}

	var setSignalTop = function(){
		$('#car_signal-front').removeClass('selected');
		$('#car_signal-top').addClass('selected');
		setTimeout(function(){
			toggleCarControls();
		},750)

        var err_fn = function(err){
        	log("error signal top")
        }
		var success_fn = function(data){
        	log(data)
        }

		call_rest(CNSNT.svcurl, "setCurrentInlet",  dtype, {inlet:"MAST"},success_fn, err_fn);	
	};

	var setSignalFront = function(){
		$('#car_signal-top').removeClass('selected');
		$('#car_signal-front').addClass('selected');
		setTimeout(function(){
			toggleCarControls();
		},750)

        var err_fn = function(err){
        	log("error signal front")
        }
		var success_fn = function(data){
        	log(data)
        }

		call_rest(CNSNT.svcurl, "setCurrentInlet", dtype, {inlet:"BUMPER"}, success_fn, err_fn);
	};

	var initSignal = function(){
        var err_fn = function(err){
        	log("error init")
        }
		var success_fn = function(data){
			// When first valued received, switch on value and set mast state.
        	log(data)
        }

		call_rest(CNSNT.svcurl, "getCurrentInlet", dtype,{}, success_fn, err_fn);
	}

	var clearControls = function(){
		$('.icon-car').removeClass('selected');
		$('.icon-map').removeClass('selected');
		$('.icon-setting').removeClass('selected');
	};

	var hidePanels = function(){
		for(var i = 0 ; i < control_panels.length ; i++){
			var pane = $('#' + control_panels[i] + "_controls");
			if(pane.is(':animated') || control_panels[i] == 'map'){
				// pane.hide();
			}else{
				if(pane.is(':visible')){
					var p = pane;
					// pane.animate({opacity:0}, 200, function(){
					// 	p.hide();
					// });
					pane.css({left:'0%'}).css({left:'-100%'}, transition_time, function(){
						p.hide();
					});
				}				
			}			
			$('.icon-' + control_panels[i]).addClass('selected');
		}
		clearControls();
	};

	var showPanel = function(which){
		hidePanels();
		if(which !== 'map'){
			// $('#' + which + "_controls").show().css({opacity:0}).animate({opacity:1}, 500);
			$('#' + which + "_controls").show().css({left:'100%'}).css({left:'0'}, transition_time);
		}else{
			$('#' + which + "_controls").show();
		}		
		$('.icon-' + which).addClass('selected');
	};

	var toggleChart = function(){
		if($('.icon-chart').hasClass('selected')){
			$('.icon-chart').removeClass('selected');
			$('#map2_flot, #map_realtime_flot, #realtime_display').animate({bottom:'-20%'}, transition_time, function(){
				$('#map2_canvas').css({height:'100%'});
			});		
		}else{
			$('.icon-chart').addClass('selected');
			$('#map2_flot, #map_realtime_flot, #realtime_display').animate({bottom:'0%'}, transition_time, function(){
				$('#map2_canvas').css({height:'80%'});
			});			
		}
	};

	var toggleWind = function(){
		if($('.icon-wind').hasClass('selected')){
			$('.icon-wind').removeClass('selected');
			wind_visible = false;
			$('line').remove();
		}else{
			$('.icon-wind').addClass('selected');
			wind_visible = true;
		}
		redrawCanvas();
	};

	var toggleCursor = function(){
		if($('.icon-cursor').hasClass('selected')){
			$('.icon-cursor').removeClass('selected');
			follow_car = false;
		}else{
			$('.icon-cursor').addClass('selected');
			follow_car = true;
		}
	};

	var togglePane = function(which, alternate){
		if($('.icon-' + which).hasClass('selected')){
			$('.icon-' + which).removeClass('selected');
			showPanel(alternate);
		}else{
			$('.icon-' + which).addClass('selected');
			showPanel(which);
		}
	};

	var restartLog = function(){
		if($('#btn_restart').hasClass("selected")){
			if(!$('#btn_restart').hasClass("locked")){
				$('#btn_restart').addClass("locked");

				var c = window.confirm("Restart Log?")
				if(c){
					var dtype = "json";
			        if (CNSNT.prime_view === true) {
			            dtype = "jsonp";
			        }
			        var success_fn = function(){
			        	$('#btn_restart').removeClass("locked");
						$('#btn_restart').trigger("click");
			        }
			        var err_fn = function(){

			        }
					call_rest(CNSNT.svcurl, "", dtype, {}, success_fn, err_fn);
				 	resetMap();
			        setTimeout(function(){
						$('#btn_restart').removeClass("locked");
						$('#btn_restart').trigger("click");
					},1000)

					setTimeout(function(){
						togglePane('map', 'setting')
					},2000)
				}else{
					$('#btn_restart').removeClass('selected');
					$('#btn_restart').removeClass("locked");
					$('#btn_restart').find('.switch_handle').css({left:2}).animate({left:60}, transition_time);
					$('#btn_restart').find('.left_text').animate({opacity:0.5});
					$('#btn_restart').find('.right_text').animate({opacity:1});
				}
			}
		}
	}

	var shutdownAnalyzer = function(){
		if($('#btn_shutdown').hasClass("selected")){
			if(!$('#btn_shutdown').hasClass("locked")){
				$('#btn_shutdown').addClass("locked");
				var c = window.confirm("Shutdown Analyzer?")
				if(c){
					var dtype = "json";
			        if (CNSNT.prime_view === true) {
			            dtype = "jsonp";
			        }
			        var success_fn = function(){

			        }
			        var err_fn = function(){

			        }
			        call_rest(CNSNT.svcurl, "shutdownAnalyzer", dtype, {}, success_fn, err_fn);
				}else{
					$('#btn_shutdown').removeClass('selected');
					$('#btn_shutdown').removeClass("locked");
					$('#btn_shutdown').find('.switch_handle').css({left:2}).animate({left:60}, transition_time);
					$('#btn_shutdown').find('.left_text').animate({opacity:0.5});
					$('#btn_shutdown').find('.right_text').animate({opacity:1});
				}
				// $('#modal_shutdown_analyzer').modal('show')
			}
		}
	}

	var drawWindRose = function(){
		var ball = new Image;
		ball.src    = '/static/images/arrow.png';
		var steps = 15;
		var avgSteps = 0;
		var begin = path_data.length - 1 - steps;
		var end = path_data.length - 1;
		if(begin < 0) begin = 0;

		var arrow_canvas = document.getElementById('canvas_rose_arrow');
		var sprite = document.getElementById("canvas_rose_sprite");
		var ctx_arrow = arrow_canvas.getContext('2d');
		var this_canvas = document.getElementById('canvas_rose');
		var ctx = this_canvas.getContext('2d');
		ctx.clearRect(0,0,200,200);
		ctx_arrow.clearRect(0,0,240,240);
		var colorScale = d3.scale.log()
         	.domain([1, 4])
         	.range(["#fcff00", "#ff0404"]);

        var avg = 0;
        var avgE = 0;
        var avgN = 0;

		for(var i = begin ; i < end ; i++){
			var speed = Math.sqrt(path_data[i].pdata.windE*path_data[i].pdata.windE + path_data[i].pdata.windN * path_data[i].pdata.windN);
			var num = i - begin;
			var bearingRad = Math.atan2(path_data[i].pdata.windE,path_data[i].pdata.windN) - Math.PI/2;
			avg = avg + bearingRad + Math.PI *2;
			if(Math.abs(path_data[i].pdata.windE) > 0){
				avgE = avgE + path_data[i].pdata.windE;
				avgN = avgN + path_data[i].pdata.windN;
				avgSteps++;
			}			
			
			var minBearing = bearingRad - .2;
			var maxBearing = bearingRad + .2;
			var spacing = 100/steps;

			ctx.beginPath()
			ctx.arc(100,100,num*spacing,minBearing,maxBearing, false); // outer (filled)
			ctx.arc(100,100,num*spacing+spacing,maxBearing,minBearing, true); // outer (unfills it)
			ctx.fillStyle = colorScale(speed + 1);			

			ctx.fill();
			if(i == end - 1){
			 	var bw = ball.width/2;
				var bh = ball.height/2;
				var x = 120;
				var y = 120;

				var myBearing = Math.atan2(avgE/avgSteps,avgN/avgSteps) + Math.PI*3/2;

				log(speed, colorScale(2))

				ctx_arrow.translate(x,y);
				ctx_arrow.rotate(myBearing);
				ctx_arrow.drawImage( ball, -bw, -bh );
				ctx_arrow.rotate(-myBearing);                      // The shading shouldn't be rotated
				ctx_arrow.translate(-x,-y);
				ctx.beginPath();
				ctx.fillStyle="rgba(255,255,255,.8)";
				ctx.arc(180,20,19,0,2*Math.PI, true); // outer (unfills it)
				ctx.stroke();
				ctx.fill();
				ctx.font="18px Helvetica Neue";
				ctx.textAlign = 'center';
				ctx.fillStyle="#000";
				if(!isNaN(speed)){
					ctx.fillText(Math.floor(speed*10,1)/10,180,23);
				}			
				ctx.font="11px Helvetica Neue";	
				ctx.fillText("m/s",180,33);
			}
		}
	}

	var thresholdListener = function(){
		map_threshold = parseFloat($(this).data("size"),10);
		drawLegend();
		redrawCanvas();
		// log($(this).data("size"))
	}

	var drawLegend = function(){

		var dmin = dataMin;

		if(dataMax <= 0 || dataMin >= 10000) return;

		var vals = [];
		var interval = (dataMax - dmin)/colorArray.length;

		for(var i = 0 ; i < colorArray.length ; i++){
			vals.push(dmin + i * interval);
		}

		var sizeScale = d3.scale.pow().clamp(true).exponent(svgPow).domain([dmin,dataMax]).range([3,(9 + svgPow*2)])
    	var colorScale = d3.scale.log()
         	.domain(vals)
         	.range(colorArray);

	    var legendCanvas = $("#legend-controls > .legend-controls-inner");
	    if(typeof time_plot === 'undefined'){
	    	return;
	    } 
 		var min = dmin;
 		var max = dataMax;

 		var concList = [];

 		var inc = (max-min)/8;
 		var offset = 25;
 		legendCanvas.html('')
 		var offCount = 0;

 		for(var i = 0 ; i < 8 ; i++){
 			var s =addThreeZeros(inc*i+min)
 			if(s%1 == 0) s = s + ".0"
 			var size = sizeScale(inc*i+min) * 2;
 			var label = $("<div class='legend-wrapper' data-size='" + s + "'><span class='legend-label' data-size='" + s + "'>" + s + "</span></div>");
 			var circle = $("<div class='legend-wrapper' data-size='" + s + "'><span class='legend-circle' style='height:" + size + "px;width:" + size + "px;' data-size='" + s + "'></span></div>");
 			label.css({top:(offCount++/16)*90 + '%'});
 			circle.css({
 				top:(offCount++/16)*92 + '%',
 				left:23,
 				'margin-left':size/2*-1
 			});

 			if((parseFloat(s,10)) > map_threshold){
 				circle.find(".legend-circle").css({
	 				'background-color':colorScale(inc*i+min)
	 			})
 			}else{
 				circle.find(".legend-circle").css({
	 				'background-color':"#aaa"
	 			})
 			}
 			
 			if(s <= svgMin){
 				circle.find('span').css({'background-color':'#aaa'});
 			}
 			legendCanvas.append(label);
 			legendCanvas.append(circle);
 			
 			$(circle).on("click", thresholdListener)
 			$(circle).find(".legend-wrapper").on("click", thresholdListener)
 			$(label).on("click", thresholdListener)
 			$(label).find(".legend-wrapper").on("click", thresholdListener)
 		}
	}

	var centerMapOnSelection = function(){
		if(!center_map_flag) return;
	  	CSTATE.map2.fitBounds([
			[minLat, minLon],
			[maxLat, maxLon]
		]);
		center_map_flag = false;
	}


	var initPlot = function(){
		if(plot_init){
			return;
		}else{
			plot_init = true;
		}

		var placeholder = $("#map2_flot");

	    placeholder.bind("plotselected", function (event, ranges) {
	    	selectedMinTime = ranges.xaxis.from;
	    	selectedMaxTime = ranges.xaxis.to;

	    	log(selectedMinTime, selectedMaxTime)
			
			center_map_flag = true;
			time_filter = true;
			
	    	insertQueue();	 	
	    });

	    placeholder.bind("plotunselected", function (event, ranges) {
	    	selectedMinTime = 0;
	    	selectedMaxTime = 10000000000000000000;
	    	time_filter = false;
	    	center_map_flag = true;
	    	insertQueue();
	    	centerMapOnSelection();	    	
	    });

	    placeholder.bind("plotunselected", function (event) {
	        $("#selection").text("");
	    });

	    $(window).resize(function() {	
			plotRealtime();
			plotFlot();
		})

	}

	var plotRealtime = function(){
		var min = 0;
		if(path_data.length > 100){
			min = path_data.length - 100;
		}

		if(path_data.length - last_flot > 128){
			plotFlot();
			last_flot = path_data.length;
		}
		var queue = path_data.slice(min, path_data.length)

		realtime_threshold = queue[0].etm;

	    var data = [
	    	{
	    		label:"Ch4",
	    		color:"#4e73ff",
	    		data:[]
	    	},
	    	{
	    		label:"Ch4",
	    		color:"red",
	    		data:[]
	    	}
	    ]

	    var under = true;
	    if(follow_car){
	    	var xy = CSTATE.map2.latLngToContainerPoint([queue[queue.length - 1].pdata.lat,queue[queue.length - 1].pdata.lon ]);
	    	if(xy.x < 200 || xy.x > $('#map2_canvas').width() - 200 || xy.y < 100 || xy.y > $('#map2_canvas').height() - 100){
	    		CSTATE.map2.panTo([queue[queue.length - 1].pdata.lat,queue[queue.length - 1].pdata.lon ])
	    	}
	    }
	    
	    CSTATE.carMarker.setLatLng([queue[queue.length - 1].pdata.lat,queue[queue.length - 1].pdata.lon ])

	    var ch4 = queue[queue.length - 1].pdata.ch4;
	    var val = addThreeZeros(ch4)
	    var pos = (ch4 - dataMin)/(dataMax - dataMin)*100 + 3
	    if(pos > 90) pos = 90;
	    if(pos < 10) pos = 10;
	    $('#realtime_num')
	    	.html(val)
	    	.animate({
	    		bottom:pos + "%"
	    	})

	    for(var i = 0 ; i < queue.length - 1 ; i++){
	    	var qi = queue[i];
	    	var qi1 = queue[i+1];
	    	if(qi.pdata.ch4 > ignore_plot_below){	    		
	    		if(qi.pdata.lat > minSelLat && qi.pdata.lat < maxSelLat && qi.pdata.lon > minSelLon && qi.pdata.lon < maxSelLon){
					data[1].data.push([qi.etm, qi.pdata.ch4])
					if(!under){					
						data[0].data.push([qi1.etm, qi1.pdata.ch4])	
						data[0].data.push(null)
						data[1].data.push(null)
						under = true;
					} 
	    		}else{
	    			data[0].data.push([qi.etm, qi.pdata.ch4])
	    			if(under){
	    				data[1].data.push([qi1.etm, qi1.pdata.ch4])
						data[0].data.push(null)
						data[1].data.push(null)						
						under = false;
					} 
	    		}	    	

	    	}	    	
	    }

	    var options = {
	        series: {
	            lines: { show: true },
	            points: { show: false },
	            color:'#ff0d08'
	        },
	        legend: { show:false },
	        xaxis: { time: 0 , show:false },
	        yaxis: { 
        		show:true, 
        		autoscaleMargin: 0.0 ,
        		max:dataMax,
        		min:dataMin
        	},
	        selection: { mode: "x" }
	    };

	    var placeholder = $("#map_realtime_flot");

	    realtime_plot = $.plot(placeholder, data, options);
	}

	var plotFlot = function(){
		// return;
		var queue = [];
		decimateQueue(chart_decimation, 100000);
		queue = decimated['int' + chart_decimation];
		
	    var data = [
	    	{
	    		label:"Ch4",
	    		color:"#4e73ff",
	    		data:[]
	    	},
	    	{
	    		label:"Ch4",
	    		color:"red",
	    		data:[]
	    	}
	    ]

	    var under = true;

	    for(var i = 0 ; i < queue.length ; i++){
	    	var qi = queue[i];
	    	var qi1 = queue[i+1]
	    	if(qi.pdata.ch4 > ignore_plot_below && qi.etm < realtime_threshold){	
	    		if(qi.pdata.lat > minSelLat && qi.pdata.lat < maxSelLat && qi.pdata.lon > minSelLon && qi.pdata.lon < maxSelLon){
					data[1].data.push([qi.etm, qi.pdata.ch4])
					if(!under){						
						data[0].data.push([qi1.etm, qi1.pdata.ch4])
						data[0].data.push(null)
						data[1].data.push(null)
						under = true;
					} 
	    		}else{
	    			data[0].data.push([qi.etm, qi.pdata.ch4])
	    			if(under){
						data[0].data.push(null)
						data[1].data.push([qi1.etm, qi1.pdata.ch4])
						data[1].data.push(null)						
						under = false;
					} 
	    		}	    
	    	}	    	
	    }

	    min_plot = queue[0].etm;
	    max_plot = queue[queue.length - 1].etm;

	    

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
	        yaxis: { 
	        	show:true, 
	        	autoscaleMargin: 0.0,
	        	max:dataMax,
        		min:dataMin 
        	},
	        selection: { mode: "x" }
	    };

	    var placeholder = $("#map2_flot");

	    time_plot = $.plot(placeholder, data, options);

	    var axes = time_plot.getAxes();
 		var min = axes.yaxis.min;
 		var max = axes.yaxis.max;

 		initPlot();
		if(selectedMinTime > 0){
			time_plot.setSelection({ xaxis: { from: selectedMinTime, to: selectedMaxTime } }, true)
		}

		
	    $("#range_slider").slider({
			min:min,
			max:max,
			step:.01,
			value:max,
			orientation: "vertical",	    	
		  change: function( event, ui ) {
			svgMin = (max - $( "#range_slider" ).slider( "option", "value" )) + min;
			redrawCanvas();
			// plotFlot(decimated['int' + decimate_level])
		  },	    	
		  slide: function( event, ui ) {
		  	svgMin = (max - $( "#range_slider" ).slider( "option", "value" )) + min;
		  	map_threshold = svgMin;
		  	redrawCanvas();
		  }
		});
		drawLegend();

		isotopic_layer = $("<div id='isotopic_layer'>ISO</div>")
    	$('#map2_flot .flot-base').after("<div id='isotopic_layer'>ISO</div>");
    	drawIsotopics();
	}

	var locationFilterListener = function(e){
		minSelLat = CSTATE.map2.getBounds()._southWest.lat;
		maxSelLat = CSTATE.map2.getBounds()._northEast.lat;
		minSelLon = CSTATE.map2.getBounds()._southWest.lng;
		maxSelLon = CSTATE.map2.getBounds()._northEast.lng;	

		plotFlot(decimated['int' + 4]);
	}

	var initMap = function(){
		$('#concPlot2').hide();
		CSTATE.map2._initPathRoot() 
		mapSVG = d3.select('#map2_canvas').select('svg').attr("class", lastColor);
    	mapG = mapSVG.append("g").attr("id", "amazingViz");

    	canvas = document.getElementById('canvas_bubbles');
    	canvas_wind = document.getElementById('canvas_wind');
    	canvas_extras = document.getElementById('canvas_extras');

  //   	var imageUrl = canvas.toDataURL(),
	 //    	imageBounds = CSTATE.map2.getBounds();

		// image_overlay = L.imageOverlay(imageUrl, imageBounds)

		// image_overlay.addTo(CSTATE.map2);



		MyCustomLayer = L.Class.extend({

		    initialize: function (latlng) {
		        // save position of the layer or any options from the constructor
		        this._latlng = latlng;
		    },

		    onAdd: function (map) {
		        this._map = map;

		        // create a DOM element and put it into one of the map panes
		        this._el = document.getElementById('canvas_bubbles');
		        map.getPanes().overlayPane.appendChild(this._el);
		        this._el2 = document.getElementById('canvas_wind');
		        map.getPanes().overlayPane.appendChild(this._el2);
		        this._el3 = document.getElementById('canvas_extras');
		        map.getPanes().overlayPane.appendChild(this._el3);

		        // add a viewreset event listener for updating layer's position, do the latter
		        map.on('viewreset', this._reset, this);
		        map.on('moveend', this._reset, this);
		        this._reset();
		    },

		    onRemove: function (map) {
		        // remove layer's DOM elements and listeners
		        // map.getPanes().overlayPane.removeChild(this._el);
		        map.off('viewreset', this._reset, this);
		    },

		    _reset: function () {
		    	hack_offset_x = this._map.latLngToLayerPoint(this._map.getBounds()._southWest).x;
		    	hack_offset_y = this._map.latLngToLayerPoint(this._map.getBounds()._northEast).y;
		    	$(this._el).css({top:hack_offset_y,left:hack_offset_x})
		    	$(this._el2).css({top:hack_offset_y,left:hack_offset_x})
		    	$(this._el3).css({top:hack_offset_y,left:hack_offset_x})
		    }
		});

	
		layer0 = new MyCustomLayer(CSTATE.map2.getPixelOrigin())

		CSTATE.map2.addLayer(layer0);


    	mapSVGInit = true;

    	selected_circles = mapG.selectAll("circle")
    	selected_lines = mapG.selectAll("line")

		CSTATE.map2.on("viewreset", redrawCanvas);
		CSTATE.map2.on("viewreset", locationFilterListener);
		CSTATE.map2.on("moveend", locationFilterListener);

		CSTATE.map2.on("movestart", function(){
			map_zooming = true;			
			data_pause = true;
		});

		CSTATE.map2.on("moveend", function(){
			map_zooming = false;

			if($('#btn_pause_controls').hasClass("selected")){
				data_pause = false;
			}else{
				data_pause = true;
			}
			insertQueue();
		});

		CSTATE.map2.on("zoomstart", function(){
			map_zooming = true;
			data_pause = true;
			domHide()
		});

		CSTATE.map2.on("zoomend", function(){
			domShow();
			map_zooming = false;
			if($('#btn_pause_controls').hasClass("selected")){
				data_pause = true;
			}else{
				data_pause = false;
			}
			calcDecimationLevel();
			if(map_decimation !== last_decimation_level || view_filter){
				last_decimation_level = map_decimation;
				// startTimer("remove")
				$('circle').remove();
				$('line').remove();
				// stopTimer("remove")
				insertQueue();
			}
			redrawCanvas();

		});
    	
    	var big = [];
	}


	var redrawCanvas = function(){
		minLat = 1000;
		maxLat = -1000;
		minLon = 1000;
		maxLon = -1000;

		var myQueue = decimated['int' + map_decimation];
		
		if(myQueue.length > 500){
			view_filter = true;
			minMapLat = CSTATE.map2.getBounds()._southWest.lat;
			maxMapLat = CSTATE.map2.getBounds()._northEast.lat;
			minMapLon = CSTATE.map2.getBounds()._southWest.lng;
			maxMapLon = CSTATE.map2.getBounds()._northEast.lng;	
		}

		if(map_decimation !== last_decimation_level){
			last_decimation_level = map_decimation;
			$('circle').remove();
			$('line').remove();
		}

		geodata = {
			"type": "FeatureCollection",
			"features": []
		};
		
		if(!mapSVGInit){
			initMap();
		}

		var thisQueue = myQueue;

		var valve0 = 1;

		tile_points = []
		isotopics = [{start:0,end:0}]
		for(var i = 0 ; i < thisQueue.length ; i++){
			if(view_filter){
				var on_plot = false;
				if(thisQueue[i].pdata.lat > minMapLat && thisQueue[i].pdata.lat < maxMapLat){
					if(thisQueue[i].pdata.lon > minMapLon && thisQueue[i].pdata.lon < maxMapLon){
						on_plot = true;
					}
				}
				tile_points.push([thisQueue[i].pdata.lat,thisQueue[i].pdata.lon, thisQueue[i].pdata.ch4, thisQueue[i].pdata.windE,thisQueue[i].pdata.windN, thisQueue[i].etm, on_plot, parseInt(thisQueue[i].pdata.ValveMask) & 0x1])

			}else{
				tile_points.push([thisQueue[i].pdata.lat,thisQueue[i].pdata.lon, thisQueue[i].pdata.ch4, thisQueue[i].pdata.windE,thisQueue[i].pdata.windN, thisQueue[i].etm, true, parseInt(thisQueue[i].pdata.ValveMask) & 0x1])
			}		
			if(thisQueue[i].pdata.ch4 > dataMax) dataMax = thisQueue[i].pdata.ch4;
			if(thisQueue[i].pdata.ch4 < dataMin) dataMin = thisQueue[i].pdata.ch4;

			if(thisQueue[i].pdata.ValveMask !== valve_mask){
				valve_mask = thisQueue[i].pdata.ValveMask;
				if((parseInt(thisQueue[i].pdata.ValveMask) & 0x1) > 0){
					isotopics[0].start = thisQueue[i].etm;			
				}
				if((parseInt(thisQueue[i].pdata.ValveMask) & 0x1) === 0 && isotopics.length >= 1){
					isotopics[0].end = thisQueue[i].etm;
					isotopics.unshift({start:0,end:0})
				}				
			}
		}
		if(isotopics[0].end === 0){
			isotopics[0].end = thisQueue[thisQueue.length - 1].etm;
		}
		last_queue = thisQueue.length;

		var width = CSTATE.map2.getPixelBounds().max.x - CSTATE.map2.getPixelOrigin().x - hack_offset_x;
		var height = CSTATE.map2.getPixelBounds().max.y - CSTATE.map2.getPixelOrigin().y - hack_offset_y;

		$(canvas).attr({width:width,height:height})
		$(canvas_wind).attr({width:width,height:height})
		$(canvas_extras).attr({width:width,height:height})

	    var ctx = canvas.getContext('2d');
	    var ctx_wind = canvas_wind.getContext('2d');
	    var ctx_extras = canvas_extras.getContext('2d');

	    var radius = 12;

	    var dmin = dataMin;

		if (map_threshold > dataMin){
			dmin = map_threshold;
		}

		var sizeScale = d3.scale.pow().clamp(true).exponent(svgPow).domain([dmin,dataMax]).range([3,10 + svgPow*2])

		var min = map_threshold || ignore_plot_below;


        var vals = [];
		var interval = (dataMax - dmin)/colorArray.length;

		for(var i = 0 ; i < colorArray.length ; i++){
			vals.push(dmin + i * interval);
		}

    	var colorScale = d3.scale.log()
         	.domain(vals)
         	.range(colorArray);

        var ini = 0; 
        var out = 0; 

        tile_points.sort(function(a, b) {return a[2] - b[2]})

		for (var i = 0; i < tile_points.length; i++) {
			var plotMe = function(){
				// var point = new L.LatLng(tile_points[i][0], tile_points[i][1]);

		        // // actual coordinates to tile pixel
		        var p = CSTATE.map2.latLngToLayerPoint([tile_points[i][0], tile_points[i][1]]);

		        // // // point to draw
		        var x = Math.floor(p.x) - hack_offset_x;
		        var y = Math.floor(p.y) - hack_offset_y;
		        

		        if(tile_points[i][2] < dataMin){
		        	tile_points[i][2] = dataMin;	        	
		        }

		        ctx.beginPath();
	        	ctx.arc(x, y, sizeScale(tile_points[i][2]), 0, 2 * Math.PI, false);
	        	if(tile_points[i][2] > map_threshold){   
	        		if(tile_points[i][7] > 0){
	        			ctx.fillStyle = "#0000ff";
	        		}else{
						ctx.fillStyle = colorScale(tile_points[i][2]);
	        		}    		
	        		
		        	ctx.globalAlpha = 0.8;

			        if(wind_visible){
						var bearingRad = Math.atan2(tile_points[i][3],tile_points[i][4]) - Math.PI/2;
						ctx_wind.beginPath();
						ctx_wind.moveTo(x, y);
						var len = sizeScale(tile_points[i][2]) * 3;
						var x2 = len*Math.cos(bearingRad)
						var y2 = len*Math.sin(bearingRad);
						ctx_wind.lineTo(x + x2, y + y2);
						ctx_wind.lineWidth = 2;
						ctx_wind.strokeStyle = colorScale(tile_points[i][2]);
						ctx_wind.stroke();
			        }
	        	}else{
	        		ctx.fillStyle = "#aaa";
		        	ctx.globalAlpha = 1;
	        	}

	        	ctx.fill();	  
			}

			if(time_filter){
				if(tile_points[i][5] >= selectedMinTime && tile_points[i][5] <= selectedMaxTime){
					if(tile_points[i][0] > maxLat) maxLat = tile_points[i][0];
					if(tile_points[i][0] < minLat) minLat = tile_points[i][0];
					if(tile_points[i][1] > maxLon) maxLon = tile_points[i][1];
					if(tile_points[i][1] < minLon) minLon = tile_points[i][1];
					if(tile_points[i][6]){
						plotMe();
					}					
				}
			}else{
				if(tile_points[i][0] > maxLat) maxLat = tile_points[i][0];
				if(tile_points[i][0] < minLat) minLat = tile_points[i][0];
				if(tile_points[i][1] > maxLon) maxLon = tile_points[i][1];
				if(tile_points[i][1] < minLon) minLon = tile_points[i][1];
				plotMe();
			}	                    
	    }

	    var ctx = canvas.getContext('2d');
	    var forceDirect = function(){
    	 	for(var i = 0 ; i < analysisInfo.length ; i++){
    	 		var p = CSTATE.map2.latLngToLayerPoint([analysisInfo[i].GPS_ABS_LAT, analysisInfo[i].GPS_ABS_LONG]);
		        analysisInfo[i].x = Math.floor(p.x) - hack_offset_x;
		        analysisInfo[i].y = Math.floor(p.y) - hack_offset_y;
		        for(var n = 0 ; n < analysisInfo.length - 1 ; n++){
		        	var pa = CSTATE.map2.latLngToLayerPoint([analysisInfo[n].GPS_ABS_LAT, analysisInfo[n].GPS_ABS_LONG]);
			        var xa = Math.floor(pa.x) - hack_offset_x;
			        var ya = Math.floor(pa.y) - hack_offset_y;
			        if(Math.abs(analysisInfo[i].y-ya) >= 0 && Math.abs(analysisInfo[i].y-ya) < 20 && i !== n){
			        	analysisInfo[i].y += 20;
			        }
		        }
	    	}
	    }

	    forceDirect();
	   
		for(var i = 0 ; i < analysisInfo.length ; i++){
	        var p = CSTATE.map2.latLngToLayerPoint([analysisInfo[i].GPS_ABS_LAT, analysisInfo[i].GPS_ABS_LONG]);
	        var x = Math.floor(p.x) - hack_offset_x;
	        var y = Math.floor(p.y) - hack_offset_y;

	 		ctx.beginPath();
	 		ctx.globalAlpha = 1;
			ctx.roundRect(analysisInfo[i].x, analysisInfo[i].y, 100, 20, 5).stroke();
			ctx.fillStyle = "#000000";
			ctx.fill();
			ctx.beginPath();
			ctx.fillStyle = "#ffffff";
			ctx.font = "bold 16px Arial";
			ctx.fillText(analysisInfo[i].DELTA + "+/-" + analysisInfo[i].UNCERTAINTY,analysisInfo[i].x + 2, analysisInfo[i].y + 16);
		}

		if(time_filter){
			ctx_extras.beginPath();
			ctx_extras.fillStyle = 'rgba(0, 0, 0,0.25)';

		 	var p = CSTATE.map2.latLngToLayerPoint([minLat,minLon]);
		 	var p2 = CSTATE.map2.latLngToLayerPoint([maxLat,maxLon]);

	        var x = Math.floor(p.x) - hack_offset_x;
	        var y = Math.floor(p.y) - hack_offset_y;
	        var x2 = Math.floor(p2.x) - hack_offset_x;
	        var y2 = Math.floor(p2.y) - hack_offset_y;
			ctx_extras.fillRect(x - 1000,y2 - 1000,x2 - x + 2000,y-y2 + 2000 );
			var pad = 10;
			ctx_extras.strokeRect(x - pad,y2 - pad,x2 - x + 2*pad,y-y2 + 2*pad);
			ctx_extras.clearRect(x - pad,y2 - pad,x2 - x + 2*pad,y-y2 + 2*pad);
		}

	    centerMapOnSelection();
	}

	var drawIsotopics = function(){
		if(min_plot == 0) return;
		var plot_end = time_plot.pointOffset({ x: max_plot, y:2 }).left;
		$('#isotopic_layer').html("");
		for(var i = 0 ; i < isotopics.length ; i++){
			var begin = time_plot.pointOffset({ x: isotopics[i].start, y:2 }).left;
			var end = time_plot.pointOffset({ x: isotopics[i].end, y:2 }).left;
			if(end > plot_end) end = plot_end;
			if(begin > 15 && end < 5000){
				var dom = $("<div class='iso-display'></div>")
				$('#isotopic_layer').append(dom)
				dom.css({
					left:begin,
					width:end - begin
				})
			}
		}
	}

	var appendQueue = function(){
		drawWindRose()
		if(data_pause) return;
		for(var i = 0 ; i < path_queue.length ; i++){
			path_data.push(path_queue[i]);
			if(path_queue[i].pdata.ch4 > dataMax) dataMax = path_queue[i].pdata.ch4;
			if(path_queue[i].pdata.ch4 < dataMin) dataMin = path_queue[i].pdata.ch4;
		}
		path_queue = [];
		insertQueue();
		plotRealtime();
	}

	var insertQueue = function(){	


		view_filter = false;

		var count = 100000;

		if(path_data.length == 0) return;

		map_decimation = decimate_level;
		calcDecimationLevel();
		decimateQueue(map_decimation, count);

		redrawCanvas();
		drawLegend();
		return;
	}


	var calcDecimationLevel = function(){
		var value = CSTATE.map2.getZoom();
		var result;

		switch (true){
			case (value > 17):
				map_decimation = 1;
			break;
			case ((value <= 17) && (value > 15)):
				map_decimation = 4;
			break;
			case (value <= 15):
				map_decimation = 8;
			break;
			default:
				map_decimation = 8;
			break;
		}

		switch (true){
			case (path_data.length < 1000):
				map_decimation = 1;
				chart_decimation = 1;
			break;
			case ((path_data.length >= 1000) && (path_data.length < 2000)):
				chart_decimation = 4;
			break;
			case ((path_data.length >= 2000) && (path_data.length < 8000)):
				chart_decimation = 4;
			break;
			default:
				chart_decimation = 16;
			break;
		}


		if(selectedMinTime > 0 && selectedMaxTime < 10000000000000000000){
			map_decimation = 1;
		}

		return map_decimation;
	}


	var decimateQueue = function(interval, count){
		// startTimer('decimate');
		// var polyList = [];
		decimated['int' + interval] = [];
		var di = decimated['int' + interval];
		var sumCh4 = 0;
		var sumWindN = 0;
		var sumWindE = 0;
		var meanElement;
		var max = 0;
		var firstMax = 0;
		if(path_data.length < count){
			max = path_data.length - 1;
		}else{			
			max = count;
		}

		if(max > 16){
			firstMax = max - 16;
		}

		if(interval == 1){
			for(var n = 0 ; n < path_data.length ; n++){
				var temp = {
					etm:path_data[n].etm,
					pdata:{
						ch4:path_data[n].pdata.ch4,
						windN:path_data[n].pdata.windN,
						windE:path_data[n].pdata.windE,
						lat:path_data[n].pdata.lat,
						lon:path_data[n].pdata.lon,
						ValveMask:path_data[n].pdata.ValveMask
					}
				}
				di.push(temp);
			}
			return;
		}

		var peakCh4 = 0;
		var valleyCh4 = 10000;

		for(var i = 0 ; i < firstMax ; i++){
			sumCh4 += path_data[i].pdata.ch4;

			if(path_data[i].pdata.ch4 > peakCh4) peakCh4 = path_data[i].pdata.ch4;
			if(path_data[i].pdata.ch4 < valleyCh4) valleyCh4 = path_data[i].pdata.ch4;

			if(path_data[i].pdata.windN) sumWindN += path_data[i].pdata.windN;
			if(path_data[i].pdata.windE) sumWindE += path_data[i].pdata.windE;
			if(i%(interval)/2 == 0){
				meanElement = path_data[i];
			}
			if(i%interval == 0 && i > 0){
				var avgCh4 = sumCh4/interval;
				if(Math.abs(peakCh4 - avgCh4) > Math.abs(valleyCh4 - avgCh4)){
					avgCh4 = peakCh4;
				}else{
					avgCh4 = valleyCh4;
				}
				var temp = {
					etm:meanElement.etm,
					pdata:{
						ch4:avgCh4,
						windN:sumWindN/interval,
						windE:sumWindE/interval,
						lat:meanElement.pdata.lat,
						lon:meanElement.pdata.lon,
						ValveMask:meanElement.pdata.ValveMask						
					}
				}
				peakCh4 = 0;
				valleyCh4 = 10000;
				di.push(temp);
				sumCh4 = 0;
				sumWindN = 0;
				sumWindE = 0;
				// polyList.push([meanElement.pdata.lat, meanElement.pdata.lon])
			}			
		}

		if(max > firstMax && max > 0){
			for(var n = firstMax ; n < max ; n++){
				var temp = {
					etm:path_data[n].etm,
					pdata:{
						ch4:path_data[n].pdata.ch4,
						windN:path_data[n].pdata.windN,
						windE:path_data[n].pdata.windE,
						lat:path_data[n].pdata.lat,
						lon:path_data[n].pdata.lon,
						ValveMask:path_data[n].pdata.ValveMask
					}
				}
				di.push(temp);
			}
		}
		
		// stopTimer('decimate', interval)
	}

	var queuePath = function(pdata, etm){
		// floor data at 1.7
		if(pdata.ch4 < 1.7) {
			log(pdata.ch4)
			return;
		}
		var pathObj = {
			pdata:pdata, 
			etm:etm
		}
		path_queue.push(pathObj);
	}

	var getAnalysis = function(){
		analysisInfo = [];
		var dtype = "json";
        if (CNSNT.prime_view === true) {
            dtype = "jsonp";
        }
		params = {name:"",startRow:0,minAmp:0};
		var errorData = function(a,b){
			log("error error", a)
		} 
		var successData = function(data,b){
			if(data.result){
				var r = data.result;
				for(var i = 0 ; i < r.nextRow; i++){
					if(!isNaN(r.GPS_ABS_LONG[i])){
						analysisInfo.push({
							GPS_ABS_LONG:r.GPS_ABS_LONG[i],
							GPS_ABS_LAT:r.GPS_ABS_LAT[i],
							DELTA:r.DELTA[i],
							UNCERTAINTY:r.UNCERTAINTY[i]
						})
					}
				}
			}
		}
        call_rest(CNSNT.svcurl, "getAnalysis", dtype, params, successData, errorData);
	}

	var getData = function() {
		var init = false;
	    var successData = function(data) {
	        var resultWasReturned, newTimestring, newFit, newInst, i, clr, pdata, weatherCode;
	        var restart;

	        CSTATE.net_abort_count = 0;
	        // restoreModalDiv();
	        resultWasReturned = false;
	        if (data.result) {
	        	// log('DATA RESULT', data.result)
	            if (data.result.filename) {
	                if (CSTATE.lastDataFilename === data.result.filename) {
	                    if (data.result.GPS_ABS_LAT) {
	                        if (data.result.GPS_ABS_LONG) {
	                            resultWasReturned = true;
	                        }
	                    }
	                } else {
	                    initialize_map();
	                    CSTATE.startPos = null;
	                    CSTATE.methaneHistory = [];
	                    CSTATE.posHistory = [];
	                    // resetLeakPosition();
	                    // clearAnalysisNoteMarkers();
	                }
	                CSTATE.lastDataFilename = data.result.filename;
	                // CSTATE.lastPeakFilename = CSTATE.lastDataFilename.replace(".dat", ".peaks");
	                // CSTATE.lastAnalysisFilename = CSTATE.lastDataFilename.replace(".dat", ".analysis");
	            } else {
	                // alert("data and data.result: ", JSON.stringify(data.result));
	            }
	        } else {
	        	// log('no data result')
	            if (data && (data.indexOf("ERROR: invalid ticket") !== -1)) {
	                getTicket();
	                statCheck();
	                setGduTimer('dat');
	                return;
	            }
	        }

	        // log('resultWasReturned', resultWasReturned)

	        if (resultWasReturned) {
	            var resetClear = false;
	            if (CSTATE.clearConcMarkers) {
	                CSTATE.clearConcMarkers = false;
	                resetClear = true;
	            }
	            if (resetClear) {
	                CSTATE.startPos = null;
	            } else {
	            	// log('result')

	                var pos, startPos = CSTATE.startPos == null ? 0 : CSTATE.startPos;
	                CSTATE.startPos = data.result.lastPos;
	                if (data.result.EPOCH_TIME) {
	                	// log('epoch time')
	                    if (data.result.EPOCH_TIME.length > 0) {
	                        newTimestring = timeStringFromEtm(data.result.EPOCH_TIME[data.result.EPOCH_TIME.length - 1]);
	                        if (CSTATE.lastTimestring !== newTimestring) {
	                            dte = new Date();
	                            CSTATE.laststreamtime = dte.getTime();
	                            $("#placeholder").html("<h4>" + newTimestring + "</h4>");
	                            CSTATE.lastTimestring = newTimestring;
	                        }
	                    }

	                    n = data.result.CH4.length;

	                    restart = false;
                        if (n > 1) {
                            CSTATE.methaneHistory = CSTATE.methaneHistory.concat(data.result.CH4.slice(1));
                            for (pos=startPos+1; pos<startPos+data.result.CH4.length; pos++) CSTATE.posHistory.push(pos);
                            if (CSTATE.methaneHistory.length >= CNSNT.histMax) {
                                CSTATE.posHistory.splice(0, CSTATE.methaneHistory.length - CNSNT.histMax);
                                CSTATE.methaneHistory.splice(0, CSTATE.methaneHistory.length - CNSNT.histMax);
                            }

                           	for (i = 1; i < n; i += 1) {
		                            pdata = {
                                    lat: data.result.GPS_ABS_LAT[i],
                                    lon: data.result.GPS_ABS_LONG[i],
                                    etm: data.result.EPOCH_TIME[i],
                                    ch4: data.result.CH4[i],
                                    ValveMask:data.result.ValveMask[i]
                                };

                                if ('WIND_E' in data.result) pdata['windE'] = data.result.WIND_E[i];
                                if ('WIND_N' in data.result) pdata['windN'] = data.result.WIND_N[i];
                                if ('WIND_DIR_SDEV' in data.result) pdata['windDirSdev'] = data.result.WIND_DIR_SDEV[i];
                                
                                queuePath(pdata, data.result.EPOCH_TIME[i]);
                            }
                            if(n > 0){
                            	appendQueue();
                            }

                            $('#tmp_queue_len').html(path_data.length)
                        }
	                }
	            }
	        }

	        // if(!resultWasReturned){
	        // 	setGduTimer('fast');
	        // }
            // log('timer data', TIMER.data)
	        statCheck();
	        if (resultWasReturned) {
	        	var n = data.result.CH4.length;
	        	if(n < CSTATE.getDataLimit){
	        		setGduTimer('longDat');
	        	}else{
	        		setGduTimer('fast');
	        	}
	        }else{
	        	setGduTimer('fast');
	        }

	        // if (CNSNT.prime_view) {
	        //     if (TIMER.mode === null) {
	        //         setGduTimer('mode');
	        //     }
	        //     if (TIMER.periph === null) {
	        //         setGduTimer('periph');
	        //     }
	        // }

	        // if (TIMER.analysis === null) {
	        //     setGduTimer('analysis');
	        // }
	        // if (TIMER.peakAndWind === null) {
	        //     setGduTimer('peakAndWind');
	        // }
	    }

	    var  errorData = function(xOptions, textStatus) {
	        CSTATE.net_abort_count += 1;
	        if (CSTATE.net_abort_count >= 4) {
	            //alert("HERE in errorData");
	            $("#id_modal").html(modalNetWarning());
	            $("id_warningCloseBtn").focus();
	        }
	        $("#errors").html("");
	        statCheck();
	        setGduTimer('dat');
	    }

	    if (CSTATE.ticket !== "WAITING") {
	        // CSTATE.alog = "CFADS2290-20130323-020423Z-DataLog_User_Minimal.dat"
	        // CNSNT.prime_view = false;
	        switch(CNSNT.prime_view) {
	        case false:
	            ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
	            resource = CNSNT.resource_AnzLog; //"gdu/<TICKET>/1.0/AnzLog"
	            resource = insertTicket(resource);
	            var lmt = CSTATE.getDataLimit;
	            if (CSTATE.firstData === true) {
	                lmt = 1;
	                CSTATE.firstData = false;
	                CSTATE.startPos = 0;
	            }

	            params = {
	                "qry": "byPos"
	                , "alog": CSTATE.alog
	                , "startPos": CSTATE.startPos
	                , "gmtOffset": CNSNT.gmt_offset
	                , 'varList': '["GPS_ABS_LAT","GPS_ABS_LONG","GPS_FIT","CH4","ValveMask", "INST_STATUS", "WIND_N", "WIND_E", "WIND_DIR_SDEV","CAR_SPEED"]'
	                , "limit": CSTATE.getDataLimit
	                , "doclist": "true"
	                , "insFilename": "true"
	                , "timeStrings": "true"
	                , "insNextLastPos": "true"
	                , "rtnOnTktError": "1"
	            };
	            //alert("ruri: " + ruri + "  resource: " + resource);
	            call_rest(ruri, resource, "jsonp", params, successData, errorData);
	            break;

	        default:
	            var dtype = "json";
	            if (CNSNT.prime_view === true) {
	                dtype = "jsonp";
	            }
	            var limit = 0;
	            if(CSTATE.firstData){
	            	limit = CSTATE.seedDataLimit ;
	            	CSTATE.firstData = false;
	            }else{
	            	limit = CSTATE.getDataLimit;
	            }

	            params = {'limit': limit, 'startPos': CSTATE.startPos, 'alog': CSTATE.alog, 'gmtOffset': CNSNT.gmt_offset,
	                        'varList': '["GPS_ABS_LAT","GPS_ABS_LONG","CH4","ValveMask","WIND_N","WIND_E","WIND_DIR_SDEV"]'};
	            call_rest(CNSNT.svcurl, "getData", dtype, params, successData, errorData);
	            break;
	        }
	    } else {
	        setGduTimer('dat');
	    }
	}

	var getLogMeta = function(callback){
		var anz = getURLParameter("anz");
		var reqobj = {};
		reqobj.svc = "gdu";
		reqobj.version = "1.0";
		reqobj.resource = "AnzLogMeta";
		reqobj.qryobj = {
				"qry": "byEpoch"
			, 	"anz": anz
			, 	'startEtm':0
			,	'varList':'["LOGNAME"]'
			, 	'reverse':'true'
		};

		var err_fn = function(){
			log("error")
		}

		var rtn_fn = function(json, textStatus) {
		    if(json){
		    	CSTATE.alog = json[0].LOGNAME;
		    }
		    callback();
		    return;
		};

		p3anzApi.get(reqobj, rtn_fn, err_fn);
	}


	var getTicket = function(initialFn, expt) {
	    var params, ruri, resource;
	    if (CSTATE.ticket !== "WAITING") {
	        var successTicket = function(json, textStatus) {
	            CSTATE.net_abort_count = 0;
	            if (json.ticket) {
	                CSTATE.ticket = json.ticket
	                if (CSTATE.initialFnIsRun === false) {
		                if(CSTATE.prime_view){		
			                    if (initialFn) {
			                        initialFn(winH, winW);
			                    }
			                    CSTATE.initialFnIsRun = true;			                
		                }else{
		                	CSTATE.initialFnIsRun = true;	
		                	if(getURLParameter("alog") !== "null" ){
		                		CSTATE.alog = getURLParameter("alog");
		                		initialFn(winH, winW);
		                	}else{
		                		getLogMeta(initialFn);
		                	}		                	
		                }
	                }	                
	            }
	        }

	        var successTicketExport = function(json, textStatus) {
	            var rui, resource, tkt, fmt;
	            var ifn = expt;
	            var alog = ifn.replace("export:", "");
	            var ltype = "dat";
	            if (alog.indexOf(".analysis") !== -1) {
	                ltype = "analysis";
	            } else {
	                if (alog.indexOf(".peaks") !== -1) {
	                    ltype = "peaks";
	                } else {
	                    if (alog.indexOf(".notes") !== -1) {
	                        ltype = "notes";
	                    }
	                }
	            }
	            if (json.ticket) {
	                tkt = json.ticket;
	                ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
	                if (ltype === "notes") {
	                    resource = CNSNT.resource_AnzLogNote;
	                } else {
	                    resource = CNSNT.resource_AnzLog; //"gdu/<TICKET>/1.0/AnzLogMeta"
	                }
	                resource = resource.replace("&lt;TICKET&gt;", tkt);
	                resource = resource.replace("<TICKET>", tkt);

                    expturl = ruri + "/" + resource
                    + "?qry=byPos&alog=" + alog
                    + "&logtype=" + ltype
                    + "&startPos=0&rtnFmt=" + CSTATE.exportClass
                    + "&limit=all";


	                switch(ltype) {
			            case "dat":
			                $('#id_exptLogBtn').html(TXT.download_concs);
			                $('#id_exptLogBtn').redraw;
			                break;

			            case "peaks":
			                $('#id_exptPeakBtn').html(TXT.download_peaks);
			                $('#id_exptPeakBtn').redraw;
			                break;
	                }
	                window.location = expturl;
	                //alert("expturl: " + expturl);
	            }
	        }
	        var errorTicket = function(xOptions, textStatus) {
	            //alert("we have an error");
	            CSTATE.ticket = "ERROR";
	            alert("Ticket error. Please refresh the page. \nIf the error continues, contact Customer Support.");
	        }
	        var errorTicketExport = function(xOptions, textStatus) {
	            alert("Ticket error. Please refresh the page. \nIf the error continues, contact Customer Support.")
	        }
	        if (expt && expt.indexOf("export") !== -1)  {
	            var sTicketFn = successTicketExport;
	            var eTicketFn = errorTicketExport;
	        } else {
	            CSTATE.ticket = "WAITING";
	            var sTicketFn = successTicket;
	            var eTicketFn = errorTicket;
	        }
	        ruri = CNSNT.resturl; //"https://ubuntuhost64:3000/node/rest"
	        // resource = CNSNT.resource_Admin; //"sec/abcdefg/1.0/Admin"
	         //"sec/abcdefg/1.0/Admin"
	        // https://dev.picarro.com/investigator/rest/sec/dummy/1.0/Admin/?callback=_jqjsp&qry=issueTicket&sys=investigator+demo&identity=081ebf61998a99032c362110b0acf7df&rprocs=%5B%22AnzMeta%3AbyAnz%22%2C+%22AnzLogMeta%3AbyEpoch%22%2C+%22AnzLog%3AbyEpoch%22%5D&_1365029825747=
	        
	        if(CNSNT.prime_view){
				params = {"qry":"issueTicket"
		            , "sys": CNSNT.sys
		            , "identity": CNSNT.identity
		            , "rprocs": '["AnzMeta:byAnz","AnzLogMeta:byEpoch", "AnzLogNote:byEpoch", "AnzLog:byPos", "AnzLogNote:dataIns"]'
		        }
		        resource = CNSNT.resource_Admin;
	        }else{
	        	params = {"qry":"issueTicket"
		            , "identity":  "TSGwBhGFSdC350bozBQ6HqgiT4bEYF7BPzBauH69"
					, "sys":  "investigator"
					, "rprocs":  '["AnzMeta:byAnz","AnzLogMeta:byEpoch", "AnzLogNote:byEpoch", "AnzLog:byPos", "AnzLogNote:dataIns"]'
		        }
		        resource = "sec/dummy/1.0/Admin";
	        }
	        resource = insertTicket(resource);
	        
	        call_rest(ruri, resource, "jsonp", params, sTicketFn, eTicketFn);
	    }
	}

		// stats
	var isArray = function (obj) {
		return Object.prototype.toString.call(obj) === "[object Array]";
	}
	var getNumWithSetDec = function( num, numOfDec ){
		var pow10s = Math.pow( 10, numOfDec || 0 );
		return ( numOfDec ) ? Math.round( pow10s * num ) / pow10s : num;
	}
	var getAverageFromNumArr = function( numArr, numOfDec ){
		if( !isArray( numArr ) ){ return false;	}
		var i = numArr.length, 
			sum = 0;
		while( i-- ){
			sum += numArr[ i ];
		}
		return getNumWithSetDec( (sum / numArr.length ), numOfDec );
	}
	var getVariance = function( numArr, numOfDec ){
		if( !isArray(numArr) ){ return false; }
		var avg = getAverageFromNumArr( numArr, numOfDec ), 
			i = numArr.length,
			v = 0;
	 
		while( i-- ){
			v += Math.pow( (numArr[ i ] - avg), 2 );
		}
		v /= numArr.length;
		return getNumWithSetDec( v, numOfDec );
	}
	var getStandardDeviation = function( numArr, numOfDec ){
		if( !isArray(numArr) ){ return false; }
		var stdDev = Math.sqrt( getVariance( numArr, numOfDec ) );
		return getNumWithSetDec( stdDev, numOfDec );
	};

	return{
		initialize:initialize,
		getData:getData,
		insertQueue:insertQueue
	}
}();



	// var plotFlot_histo = function(){
	// 	return;
	// 	if(!decimated['int' + decimate_level]){
	// 		decimateQueue(decimate_level, temp_render_count);
	// 	}

	// 	var numBars = 32;
	//     var axes = time_plot.getAxes();
 // 		var min = axes.yaxis.min;
 // 		var max = axes.yaxis.max;
 // 		var inc = Math.floor((max-min)/numBars*100)/100;
 // 		var bins = {};

 //  		var queue = decimated['int' + decimate_level]

	// 	var data = [
	//     	{
	//     		label:"Histo",
	//     		data:[]
	//     	}
	//     ]

	//     for(var c = 0 ; c < numBars ; c++){
	//     	var myBin = Math.round(inc*c*100)/100;
	//     	bins[myBin] = 0;
	//     }



	//     for(var i = 0 ; i < queue.length ; i++){
	//     	if(queue[i].pdata.ch4 > ignore_plot_below){
	//     		var ch = (queue[i].pdata.ch4 - min) - (queue[i].pdata.ch4 - min)%inc;
	// 	    	ch = Math.round(ch*100)/100;
	// 	    	bins[ch]++;
	//     	}
	//     }

	// 	var d = []
	//  	var col = 0;
	//     // var data = [];
	//     for(var b in bins){
	//     	var bbin = Math.floor((parseFloat(b) + min)*100)/100;
	//     	var obj = {
	//     		label:bbin,
	//     		data:[[bbin, bins[b]]]
	//     	}
	    	
	//     	data[0].data.push([bbin,bins[b]])
	//     	// d.push(obj)
	//     }

	//     function MyFormatter(v, xaxis) {
	// 	    return " ";
	//   	}

	//     var options = {
	//         series: {
	//             bars: {
	//                  show: true,
	//                  barWidth: inc*.75,
	//                  align: 'center'
	//              },
	//             points: { show: false },
	//             color:'#ff0d08'
	//         },
	//         xaxis: { decimal: 0 }
	//     };
	//     var placeholder = $("#map2_histo");

	//     var histo_plot = $.plot(placeholder, data, options);

	//     $('#map2_histo .legend').hide();
	// }
