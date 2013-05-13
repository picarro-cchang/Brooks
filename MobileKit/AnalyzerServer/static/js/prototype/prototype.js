log("proto")

var PI = Math.PI;

var skews = {
  30:[2,2,2,2,2.1,2.2,2.3,2.4,2.5,2.6,2.7,2.8,2],
  50:[2,2,2,2.2,2.4,2.6,2.8,2,2,2,2,2,2],
  70:[2,2,2,2.1,2.2,2.3,2.4,2.6,2.8,2.2,2.1,2,2],
  90:[2,2,2,2.2,2.4,2.6,2.8,2.6,2.4,2.2,2,2,2],
  110:[2,2,2,2,2,2,2.8,2.6,2.4,2.2,2,2,2],
  130:[2,2,2.1,2.2,2.8,2.6,2.4,2.3,2.2,2.1,2.05,2,2],
  150:[2,2.8,2.7,2.6,2.5,2.4,2.3,2.2,2.1,2,2,2,2]
}

var compositeTypes = [
  'source-over','source-in','source-out','source-atop',
  'destination-over','destination-in','destination-out',
  'destination-atop','lighter','darker','copy','xor'
];

var temp = function(){
	var colorScale = d3.scale.log()
         	.domain([2, 2.6])
         	.range(["#fcff00", "#ff0404"]);

    var this_canvas0;
	var ctx0;
	var this_canvas1;
	var ctx1;

	var testData = [
		{
			ch4:2,
			bearing:PI/2,
			speed:24,
			x:50,
			y:200
		},
		{
			ch4:2.2,
			bearing:PI/2,
			speed:30,
			x:100,
			y:200
		},
		{
			ch4:2.6,
			bearing:PI/2,
			speed:30,
			x:150,
			y:200
		},
		{
			ch4:2.7,
			bearing:PI/2,
			speed:30,
			x:200,
			y:200
		},
		{
			ch4:2,
			bearing:PI/2,
			speed:24,
			x:250,
			y:200
		}
	]

	var init = function(){
		log("init")
		this_canvas0 = document.getElementById('canvas0');
		ctx0 = this_canvas0.getContext('2d');
		this_canvas1 = document.getElementById('canvas1');
		ctx1 = this_canvas1.getContext('2d');
		startTimer("test")
		for(var n = 0 ; n < 10 ; n++){
			drawArcs()
		}
		stopTimer("test")
	}

	var drawArcs = function(){
		ctx0.clearRect(0,0,1000,500)
		ctx1.clearRect(0,0,1000,500)

		for(var i = 0 ; i < testData.length ; i++){
			var minBearing = testData[i].bearing - .2;
			var maxBearing = testData[i].bearing + .2;
			var num = 250;

			var spacing = 20;
			ctx0.beginPath()
			ctx0.arc(testData[i].x,testData[i].y,5,minBearing,maxBearing, false); // outer (filled)
			ctx0.arc(testData[i].x,testData[i].y,num,maxBearing,minBearing, true); // outer (unfills it)
			ctx0.fillStyle = colorScale(testData[i].ch4);
			ctx0.globalAlpha = 0.2;
			ctx0.fill();	
			// if(i == 1){
			// 	ctx0.globalCompositeOperation = compositeTypes[11];
			// }	
			
		}
		// return;

		for(var i = 0 ; i < 1 ; i++){

			var minBearing = testData[i].bearing - .2;
			var maxBearing = testData[i].bearing + .2;
			var num = 250;

			var spacing = 20;
			ctx1.globalCompositeOperation = compositeTypes[0];
			ctx1.globalAlpha = 1;
			ctx1.beginPath()
			ctx1.arc(testData[i].x,testData[i].y,5,minBearing,maxBearing, false); // outer (filled)
			ctx1.arc(testData[i].x,testData[i].y,num,maxBearing,minBearing, true); // outer (unfills it)
			ctx1.fillStyle = colorScale(testData[i].ch4);
			ctx1.fill();
			ctx1.globalAlpha = 1;
			ctx1.beginPath()
			ctx1.arc(testData[i+2].x,testData[i+2].y,5,minBearing,maxBearing, false); // outer (filled)
			ctx1.arc(testData[i+2].x,testData[i+2].y,num,maxBearing,minBearing, true); // outer (unfills it)
			ctx1.fillStyle = colorScale(testData[i+2].ch4);
			ctx1.fill();
			// 1: only overlapping - color of second
			// 2: subtract second from first - color of second
			// 5: only overlapping - color of first
			// 6: subtract first from second - color of first
			// 11: only non overlapping - keep colors
			ctx1.globalCompositeOperation = compositeTypes[1];
			ctx1.beginPath()
			ctx1.arc(testData[i+1].x,testData[i+1].y,5,minBearing,maxBearing, false); // outer (filled)
			ctx1.arc(testData[i+1].x,testData[i+1].y,num,maxBearing,minBearing, true); 
			ctx1.fillStyle = colorScale(testData[i+1].ch4);
			ctx1.fill();
		}

	}


	return{
		init:init
	}
}();

$(document).ready(function(){
	temp.init();
})