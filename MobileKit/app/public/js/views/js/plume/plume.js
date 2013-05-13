// plume.js	

var plume = function(){
	var max_count = 0;
	var max_time = 1000000;
	var min_time = 0;
	var dataMin = 1000;
	var dataMax = 0;
	var plot_width = 0;
	var time_px = 0;
	var channel_index = 0;
	var series_index = 1;
	var timer;
	var last_time = 0;
	var last_value = 0;
	var container = $('#plume-container');

	var color_start = '#343dff';
	var color_middle = '#ced300';
	var color_end = '#e50012';
	var colorScaleLow;
	var colorScaleHigh;

	var heatmap;

	var init = function(){
		getDimensions();
		channel_index = 0;
		series_index = 0;
		timer = setInterval(renderNextPoint,25);
		container = $('#plume-container');
    	colorScaleLow = d3.scale.linear()
         	.domain([dataMin, dataMax/2])
         	.range([color_start, color_middle]);
       	colorScaleHigh = d3.scale.linear()
         	.domain([dataMax/2, dataMax])
         	.range([color_middle, color_end]);
         createHeatmap();
	};


	var createHeatmap = function(){
		var grad = {};
		var max = dataMax
		for(var i = 0 ; i < dataMax ; i++){
			grad[i/dataMax] = getColor(i)
		}
		log("create heatmap")
		var config = {
		    "radius": 15,
		    "element": "heatmap-container",
		    "visible": true,
		    "opacity": 95,
		    // legend: {
	     //        position: 'br',
	     //        title: 'Example Distribution'
	     //    },
		    // "gradient": grad
		    "gradient": {0: "#343dff", 0.35: "#343dff", 0.5: "#ced300", 0.8: "#e5637d", 1.0: "#e50012" }
		};
		var data = {
	        max: dataMax,
	        min:dataMin,
	        data: []
	    };
		heatmap = heatmapFactory.create(config);
		heatmap.store.setDataSet(data);
	}

	var addHeatmapElement = function(x,y,value){
		heatmap.store.addDataPoint(x,y,value);
	}

	var getDimensions = function(){
		for(var plume in plumes){
			var p = plumes[plume];
			if(p.length > max_count) max_count = p.length;
			if(p[p.length - 1][0]< max_time) max_time = p[p.length - 1][0];
			if(p[0][0] > min_time) min_time = p[0][0];
			for(var i = 0 ; i < p.length ; i++){
				// if(p[i][0] > max_time) max_time = p[i][0];
				if(p[i][1] < dataMin) dataMin = p[i][1];
				if(p[i][1] > dataMax) dataMax = p[i][1];
			}
		}
		plot_width = $('#plume-right').width();
		time_px = plot_width/max_time;

		log("max min", max_time, dataMin)
		
	}

	var getColor = function(value){
		var c;
		if(value < dataMax/2){
			c = colorScaleLow(value);
		}else{
			c = colorScaleHigh(value);
		}
		return c;
	}

	var insertPoint = function(time, value, channel){
		var el = $("<div class='plume-element'></div>")//.appendTo(container);
		// container.append(el)
		// return;
		var color_left = getColor(last_value)
		var color_right = getColor(value)
		var grad = "-moz-linear-gradient(center right, " + color_right + ", " + color_left + ")";
		var css = {
			width:((time-last_time)*time_px)/plot_width*100+.01 + "%",
			height:'25%',
			left:((last_time - min_time)*time_px)/plot_width*100 + "%",
			top:(75-channel*25) + "%",
			'background-image':grad
			// ,'background-color':color
		}
		el.css(css)
		last_time = time;
		last_value = value;
		addHeatmapElement((last_time - min_time)*time_px, 75-channel*50 + 125, (value - dataMin)*.5)
		addHeatmapElement((last_time - min_time)*time_px, 75-channel*50 + 100, value - dataMin)
		// addHeatmapElement((last_time - min_time)*time_px, 75-channel*50 + 87.5, value - dataMin)
		addHeatmapElement((last_time - min_time)*time_px, 75-channel*50 + 75, (value - dataMin)*.5)
		// log(css.width, css.left)
		// log(container, el)
	}

	var renderNextPoint = function(){
		if(channel_index <= 3){
			if(series_index >= plumes[channel_index].length){
				channel_index++;
				if(typeof plumes[channel_index] === 'undefined') {
					$('#plume-left span').show()
					clearInterval(timer)
					return;
				}
				series_index = 1;
				last_time = plumes[channel_index][0][0];
				last_value = plumes[channel_index][0][1];
			}
			if(plumes[channel_index][series_index][0] > min_time && plumes[channel_index][series_index][0] < max_time){
				insertPoint(plumes[channel_index][series_index][0], plumes[channel_index][series_index][1], channel_index)
			}			
			// log("data", plumes[channel_index][series_index][0], plumes[channel_index][series_index][1])
			series_index++;
		}else{
			log("clear timer")
			$('#plume-left span').show()
			clearInterval(timer)
		}
	}

	return {
		init:init
	};
}();

$(document).ready(function(){
	$('body').one('mousedown',function(){
		plume.init();
	})
	// plume.init()
	
})