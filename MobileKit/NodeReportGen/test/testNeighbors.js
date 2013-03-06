/*global console, describe, before, it, require  */

'use strict';
require("should");
var bs = require("../lib/bisect");
var gh = require("../lib/geohash");
var bisect_right = bs.bisect_right;
var bisect_left = bs.bisect_left;
var insort_right = bs.insort_right;
var insort_left = bs.insort_left;

var RTD = 180.0/Math.PI;
var DTR = Math.PI/180.0;
var rEarth = 6371000;

function shuffle ( myArray ) {
  var i = myArray.length, j, tempi, tempj;
  if ( i === 0 ) return false;
  while ( --i ) {
     j = Math.floor( Math.random() * ( i + 1 ) );
     tempi = myArray[i];
     myArray[i] = myArray[j];
     myArray[j] = tempi;
   }
}

function haversine(lng1, lat1, lng2, lat2) {
    /* Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) */
    lng1 = DTR * lng1;
    lat1 = DTR * lat1;
    lng2 = DTR * lng2;
    lat2 = DTR * lat2;
    // haversine formula
    var dlng = lng2 - lng1;
    var dlat = lat2 - lat1;
    var dx = Math.sin(dlng/2);
    var dy = Math.sin(dlat/2);
    var a = dy * dy + Math.cos(lat1) * Math.cos(lat2) * dx * dx;
    var c = 2 * Math.asin(Math.sqrt(a));
    return rEarth * c;
}

describe('knownPoints', function() {
    var locations = [];
    var latPerm = [], lngPerm = [];
    var lat0 = 37.396014;
    var lng0 = -121.984325;
    var n = 20;
    var m = 20;
    var d = 7.0;    // Distance between points in meters

    function neighbors(location, maxDist) {
        // Returns indices in locations which lie within maxDist of location
        var closest = [];
        var inRangeLat = {}, inRangeBoth = {};
        var deltaLat = RTD * maxDist / rEarth;
        var deltaLng = deltaLat / Math.cos(DTR * location.lat);
        var latSort = [], lngSort = [];
        var i;
        for (i=0; i<locations.length; i++) {
            latSort.push(locations[latPerm[i]].lat);
            lngSort.push(locations[lngPerm[i]].lng);
        }
        // Get points which are close to location in both lat and lng
        i = bisect_left(latSort, location.lat - deltaLat);
        while (i<latSort.length && latSort[i] <= location.lat + deltaLat) {
            inRangeLat[latPerm[i]] = true;
            i += 1;
        }
        i = bisect_left(lngSort, location.lng - deltaLng);
        while (i<lngSort.length && lngSort[i] <= location.lng + deltaLng) {
            if (inRangeLat[lngPerm[i]]) inRangeBoth[lngPerm[i]] = true;
            i += 1;
        }
        
        for (var k in inRangeBoth) {
            if (inRangeBoth.hasOwnProperty(k)) {
                var dist = haversine(location.lng, location.lat,
                                     locations[k].lng, locations[k].lat);
                if (dist <= maxDist) closest.push({"index": +k, "dist": dist});
            }
        }
        closest.sort(function(j,k) { return j.dist - k.dist; });
        return closest;
    }

    before(function () {
        var dlat = RTD * d / rEarth;
        var dlng = dlat / Math.cos(DTR * lat0);
        var i, j;
        for (i=-m; i<=m; i++) {
            var lat = lat0 + i*dlat;
            for (j=-n; j<=n; j++) {
                var lng = lng0 + j*dlng;
                locations.push({"lat": lat, "lng": lng, "geohash": gh.encodeGeoHash(lat,lng), "row":i, "col":j});
            }
        }
        shuffle(locations);
        // Compute permutation vectors in order of latitude and of longitude
        for (i=0; i<locations.length; i++) {
            latPerm.push(i);
            lngPerm.push(i);
        }
        latPerm.sort(function(j,k) { return locations[j].lat - locations[k].lat; });
        lngPerm.sort(function(j,k) { return locations[j].lng - locations[k].lng; });
    });

    describe('#check points', function () {
        it('should have correct number of points', function () {
            locations.length.should.equal((2*m+1)*(2*n+1));
        });
        it('should have correct point spacing', function () {
            for (var i=0; i<locations.length; i++) {
                var loci = locations[i];
                for (var j=0; j<locations.length; j++) {
                    var locj = locations[j];
                    var dist = haversine(loci.lng, loci.lat, locj.lng, locj.lat);
                    var dy = (loci.row-locj.row)*d;
                    var dx = (loci.col-locj.col)*d;
                    (dist - Math.sqrt(dx*dx + dy*dy)).should.be.below(0.01);
                }
            }
        });
    });

    describe('#lat permutation', function () {
        it('should indicate ascending order of latitudes', function () {
            for (var i=1; i<locations.length; i++) {
                (locations[latPerm[i-1]].lat).should.not.be.above(locations[latPerm[i]].lat);
            }
        });
    });

    describe('#lng permutation', function () {
        it('should indicate ascending order of longitudes', function () {
            for (var i=1; i<locations.length; i++) {
                (locations[lngPerm[i-1]].lng).should.not.be.above(locations[lngPerm[i]].lng);
            }
        });
    });

    describe('#find closest', function () {
        it('should have correct number of points', function () {
            var nPoints = [];
            var maxDist = 30.0;
            for (var i=0; i<locations.length; i++) {
                if ((Math.abs(locations[i].row) < m - maxDist/d - 1) &&
                    (Math.abs(locations[i].col) < n - maxDist/d - 1))
                nPoints.push(neighbors(locations[i], maxDist).length);
            }
            nPoints.every(function (x) { return x === nPoints[0]; }).should.be.true;
            Math.abs(nPoints[0]-Math.PI*(maxDist/d)*(maxDist/d)).should.be.below(4);
        });
    });
});
