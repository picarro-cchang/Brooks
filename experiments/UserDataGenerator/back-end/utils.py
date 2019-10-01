import trafaret as t

TRAFARET = t.Dict(
    {
        t.Key("influxdb"): t.Dict(
            {
                "database": t.String(),
                "measurements": t.List(t.String()),
                "host": t.IP,
                "port": t.Int(),
                "timeout": t.Int(),
                "retries": t.Int(),
            }
        ),
        t.Key("server"): t.Dict(
            {
                "host": t.IP,
                "port": t.Int(),
                "data_dir": t.String(),
                "file_type": t.String(),
            }
        ),
        t.Key("user_keys"): t.List(t.String()),
    }
)

