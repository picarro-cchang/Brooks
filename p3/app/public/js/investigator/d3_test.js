	var cloudmadeUrl = 'http://{s}.tile.cloudmade.com/3eb45b95929d472d8fe4a2a5dafbd314/998/256/{z}/{x}/{y}.png',
		cloudmadeAttribution = 'Map data &copy; 2011 OpenStreetMap contributors, Imagery &copy; 2011 CloudMade',
		cloudmade = new L.TileLayer(cloudmadeUrl, {maxZoom: 18, attribution: cloudmadeAttribution});

	var map = new L.Map('map', {
		center: new L.LatLng( 47.0176,2.3427,6), 
		zoom: 5, 
		layers: [cloudmade]
	});
					
	/* Initialize the SVG layer */
	map._initPathRoot()    

	/* We simply pick up the SVG from the map object */
	var svg = d3.select("#map").select("svg"),
	g = svg.append("g");
	
	d3.json("taxa_json.json", function(collection) {
		/* Add a LatLng object to each item in the dataset */
		collection.features.forEach(function(d) {
			d.LatLng = new L.LatLng(d.geometry.coordinates[1],d.geometry.coordinates[0])
		})
  
		var feature = g.selectAll("circle")
		  .data(collection.features)
		  .enter().append("circle").attr("r", function (d) { 
		  		return d.properties.count/20 
		  	}).attr('fill','lightcoral');

       	feature.on("mouseover",function(d) { 
       		console.warn(d3.select(this)); 
            d3.select(this).transition().delay(300).
            duration(1000).attr('r',function (d){ return (d.properties.count/20)*3 }).attr('fill','yellow') 
        });

		function update() {
		  feature.attr("cx",function(d) { return map.latLngToLayerPoint(d.LatLng).x})
		  feature.attr("cy",function(d) { return map.latLngToLayerPoint(d.LatLng).y})
		  feature.attr("r",function(d) { return d.properties.count/1400*Math.pow(2,map.getZoom())})
		}
		map.on("viewreset", update);
		update();
	})