/**
 * Empty ALL PCubed data from a PCubed "main_" database;
 */

var cnames, i, len, cn, dbname, nxt_list;

dbname = db.getName();

// only clear the collections if we are "main_"
if (dbname.indexOf("main") === 0) {
    cnames = [
        "analyzer"
        , "analyzer_analysis_logs"
        , "analyzer_analysis_logs_list"
        , "analyzer_dat_logs"
        , "analyzer_dat_logs_list"
        , "analyzer_fov_logs"
        , "analyzer_fov_logs_list"
        , "analyzer_log_notes"
        , "analyzer_peak_logs"
        , "analyzer_peak_logs_list"
        , "counters"
        , "generic_dat_logs"
        , "generic_dat_logs_list"
        , "immutable_names"
        , "lrt_meta"
        , "process_status"
//	, "system.indexes"
    ];

    // empty standard PCubed collections;
    len = cnames.length;
    for (i = 0; i < len; i += 1) {
        cn = cnames[i];
        print('db.' + cn + '.remove();');
        db[cn].remove();
    }

    // initialize the immutable_names counter
    nxt_list = db.counters.distinct('next');
    if (nxt_list.length === 0) {
        db.counters.insert({_id: "immutable_names", next: 0});
    }

    // drop LRT collections
    cnames = db.getCollectionNames();
    len = cnames.length;
    for (var i = 0; i < len; i += 1) {
        cn = cnames[i];

        if (  cn.indexOf('fov_') === 0  ) {
            print('db.' + cn + '.drop();');
            db[cn].drop();
        } else {
            if (cn !== "lrt_meta") {
                if (  cn.indexOf('lrt_') === 0  ) {
                    print('db.' + cn + '.drop();');
                    db[cn].drop();
                }
            }
        }

    };
    print(dbname + " has been cleared of all end_user (main_) data.");
} else {
    print(dbname + " is not a PCubed main_ database. Exiting the process without making any changes.");
}

