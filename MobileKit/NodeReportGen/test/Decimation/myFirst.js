var databaseUrl = "admin_pfranz";
var collections = ["systems", "users"];
var MongoClient = require('mongodb').MongoClient;

MongoClient.connect("mongodb://localhost:27017/admin_pfranz", function (err, db) {
    if (err) {
        console.log("Error: " + err.message);
    }
    else {
        console.log("We are connected");
        db.collectionNames(function (err, items) {
            if (err) console.log("Error: " + err.message);
            else {
                console.log(items);
            }
        });

        var collection = db.collection('users');
        /*
        collection.find().toArray(function (err, users) {
            if (err) console.log("Error: " + err.message);
            else {
                console.log(users);
                process.exit();
            }
        });
*/
        var stream = collection.find().stream();
        stream.on("data", function(item) {
            console.log(item);
        });
        stream.on("end", function(item) {
            console.log("All done");
            process.exit();
        });


    }
});

/*
db.users.find({}, function (err, users) {
    if (err) console.log("Error: " + err.message);
    else {
        users.forEach(function (user) {
            console.log(user);
        });
        process.exit();
    }
});
*/
