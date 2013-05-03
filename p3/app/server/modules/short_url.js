
var crypto    = require('crypto')
var MongoDB   = require('mongodb').Db;
var Server    = require('mongodb').Server;
var moment    = require('moment');
var ReplSet   = require('mongodb').ReplSetServers;
var Config    = require(__dirname + '../../config.js'),
conf = new Config();

// var dbPort     = 27017;
// var dbHost     = 'localhost';
var dbPort    = conf.mongo.dbport;
var dbHost    = '127.0.0.1';
var dbName    = 'node-login';

/* establish the database connection */
var db; 
console.log(dbPort);
console.log(conf.mongo.replSet);
if (conf.mongo.replSet) {
  console.log('using replica set!!')
  var replOptions = {};
  var replSet = new ReplSet( [
    new Server( "127.0.0.1", dbPort[0]),
    new Server( "127.0.0.1", dbPort[1]),
    new Server( "127.0.0.1", dbPort[2])
  ],
    replOptions
  );
  db = new MongoDB(dbName, replSet);
} else {
  console.log('not using repl set!')
  db = new MongoDB(dbName, new Server(dbHost, dbPort, {auto_reconnect: true}), {w: 1});
}

var sharedExperiments = db.collection('investigator');

exports.getScientist = function(shorturl, callback)
{
  console.log("findOne Short url of before splitting/matching" + shorturl);
  if(shorturl.match(/\?/)) {
    shorturl = shorturl.split('?')[0];
  }
  console.log("findOne Short url of " + shorturl);
  sharedExperiments.findOne({idHash:shorturl} , function(e, o) {
    if (o){
      console.log("Success: found the scientsit!");
      callback(o);
    } else{
      console.log("Error: no scientist found... :( ");
      callback(null);
    }
  });


}

