
var crypto    = require('crypto')
var MongoDB   = require('mongodb').Db;
var Server    = require('mongodb').Server;
var moment    = require('moment');
var Config =   require(__dirname + '../../config.js'),
conf = new Config();

// var dbPort     = 27017;
// var dbHost     = 'localhost';
var dbPort    = conf.mongo.dbport;
var dbHost    = '127.0.0.1';
var dbName    = 'main';

/* establish the database connection */

var db = new MongoDB(dbName, new Server(dbHost, dbPort, {auto_reconnect: true}), {w: 1});
  db.open(function(e, d){
  if (e) {
    console.log(e);
  } else{
    console.log('connected to database :: ' + dbName);
  }
});
var sharedExperiments = db.collection('investigator');

exports.getScientist = function(shorturl, callback)
{
  if(shorturl.match(/\?/)) {
    shorturl = shorturl.split('?')[0];
  }
  console.log("findOne Short url" + shorturl);
  sharedExperiments.findOne({idHash:shorturl} ,
    function(e, res) {
    if (e) callback(e)
    else callback(null, res)
  });


}

