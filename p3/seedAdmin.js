

var dblist = [
              "node-login"
             ];

var insdoc = { "name" : "awesomeAdmin", "email" : "admin@picarro.com", "bio" : "news", "experimentInfo" : "is good", "user" : "admin@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "country" : "USA", "date" : "April 18th 2013, 4:38:14 pm", "anz" : "FDDS2015", "anzName" : "FDDS2015", "anzIdentity" : "2999bad153a4ee48da94836ad265764f", "admin": "true"}

var ploop = function (dbname, idoc) {
    db.getSisterDB(dbname).accounts.remove({email: "admin@picarro.com"});
    db.getSisterDB(dbname).accounts.insert(idoc);
};

var i;
for (i = 0; i < dblist.length; i += 1) {
    ploop(dblist[i], insdoc);
}