function draw_map()
{
    var testloc = new google.maps.LatLng(38.005, -122.130);
    var imageBounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(38.0022,-122.1346),
        new google.maps.LatLng(38.0116,-122.1269));
    var myOptions = {
      zoom: 16,
      center: testloc,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    var map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
    var oldmap = new google.maps.GroundOverlay(
        "/static/43F07.jpg",
        imageBounds);
    oldmap.setMap(map);
    
    /* 
	var triangle1Coords = [
        new google.maps.LatLng(38.0022, -122.1346),
        new google.maps.LatLng(38.1022, -122.1346),
        new google.maps.LatLng(38.1022, -122.1280)
    ];
    var triangle2Coords = [
        new google.maps.LatLng(38.1022, -122.1280),
        new google.maps.LatLng(38.1022, -122.1346),
        new google.maps.LatLng(38.2022, -122.1346)
    ];

    bermudaTriangle = new google.maps.Polygon({
        paths: triangle1Coords,
        strokeColor: "#FF0000",
        strokeOpacity: 0.35,
        strokeWeight: 0,
        fillColor: "#FF0000",
        fillOpacity: 0.35
    });

    bermudaTriangle.setMap(map);
    bermudaTriangle.getPaths().push(new google.maps.MVCArray(triangle2Coords));
    */
    
    var marker = new google.maps.Marker({
      position: testloc,
      map: map,
      title:"Hello World!"
    });    
};

function initialize(winH,winW)
{
    draw_map();
};
