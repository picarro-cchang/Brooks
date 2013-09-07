

var dblist = [
              "login_investigator"
             ];

var insdocs = [
  { "organization": "picarro", "name" : "Patrick Franz", "email" : "pfranz@picarro.com", "bio" : "Patrick is a hactivist and he is awesome at managing.", "experimentInfo" : "Leak Chaser - Like storm chaser but more hardcore and not yet on TV", "user" : "pfranz@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "date" : "April 19th 2013, 1:42:11 am", "anz" : "FDDS2015", "anzName" : "FDDS2015", "anzIdentity" : "2999bad153a4ee48da94836ad265764f" },
  { "organization": "picarro", "name" : "Joshua Montross", "email" : "jmontross@picarro.com", "bio" : "Joshua is a hactivist and he is awesome at managing.", "experimentInfo" : "Leak Chaser - Like storm chaser but more hardcore and not yet on TV", "user" : "jmontross@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "date" : "April 19th 2013, 1:42:11 am", "anz" : "FDDS2015", "anzName" : "FDDS2015", "anzIdentity" : "2999bad153a4ee48da94836ad265764f" },
  { "organization": "picarro", "name" : "Ben Huffman", "email" : "bhuffman@picarro.com", "bio" : "Ben is a hactivist and he is awesome at managing.", "experimentInfo" : "Leak Chaser - Like storm chaser but more hardcore and not yet on TV", "user" : "bhuffman@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "date" : "April 19th 2013, 1:42:11 am", "anz" : "FDDS2015", "anzName" : "FDDS2015", "anzIdentity" : "2999bad153a4ee48da94836ad265764f" },
  { "organization": "picarro", "name" : "Sirron Davis", "email" : "sdavis@picarro.com", "bio" : "Sirron is a hactivist and he is awesome at managing.", "experimentInfo" : "Leak Chaser - Like storm chaser but more hardcore and not yet on TV", "user" : "sdavis@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "date" : "April 19th 2013, 1:42:11 am", "anz" : "FDDS2015", "anzName" : "FDDS2015", "anzIdentity" : "2999bad153a4ee48da94836ad265764f" },
  { "organization": "picarro", "name" : "Sze Tan", "email" : "sze@picarro.com", "bio" : "Sze is a hactivist and he is awesome at managing.", "experimentInfo" : "Leak Chaser - Like storm chaser but more hardcore and not yet on TV", "user" : "sdavis@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "date" : "April 19th 2013, 1:42:11 am", "anz" : "FDDS2015", "anzName" : "FDDS2015", "anzIdentity" : "2999bad153a4ee48da94836ad265764f" },
  { "organization": "picarro", "name" : "Subra", "email" : "ssankar@picarro.com", "bio" : "Subra Sankar is a hactivist and he is awesome at managing.", "experimentInfo" : "Leak Chaser - Like storm chaser but more hardcore and not yet on TV", "user" : "ssankar@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "date" : "April 19th 2013, 1:42:11 am", "anz" : "FDDS2015", "anzName" : "FDDS2015", "anzIdentity" : "2999bad153a4ee48da94836ad265764f" },
  { "organization": "picarro", "name" : "Tracy Tsai", "email" : "ttsai@picarro.com", "bio" : "Tracy is a hactivist and he is awesome at managing.", "experimentInfo" : "Leak Chaser - Like storm chaser but more hardcore and not yet on TV", "user" : "ttsai@picarro.com", "pass" : "wDbqR0WD9A8f8005805d89481a4c2b0228e4dfe601", "date" : "April 19th 2013, 1:42:11 am", "anz" : "CFADS2206", "anzName" : "TracyCFADS2206", "anzIdentity" : "a6e245cc6e1adaa56dbfe39d4c1c38b8" }
]

var ploop = function (dbname, idoc) {
    db.getSisterDB(dbname).accounts.remove({email: idoc["email"]});
    db.getSisterDB(dbname).accounts.insert(idoc);
};

var i;
for (i = 0; i < insdocs.length; i += 1) {
    ploop(dblist[0], insdocs[i]);
}