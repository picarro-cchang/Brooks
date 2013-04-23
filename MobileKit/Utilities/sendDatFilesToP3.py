from glob import glob
import os
import subprocess

if __name__ == "__main__":
    dname = raw_input("Directory name with data files? ")
    lpath = os.path.join(dname, "*_Minimal.dat")
    fnames = glob(lpath)
    if len(fnames) > 0:
        fname = fnames[0]
        abs_name = os.path.abspath(fname)
        base, name = os.path.split(abs_name)
        anz = name.split("-")[0]

    dat_type = "dat"
    psys = "google"
    identity = "N7boCjtBEcKwzzrzJHLTiDjmPFc1LchhXQBxQLvd"
    lines = "500"
    history_range = "365"
    ticket_url = "https://p3.picarro.com/google/rest/sec/dummy/1.0/Admin/"
    log_metadata_url = "https://p3.picarro.com/google/rest/gdu/<TICKET>/1.0/AnzLogMeta/"
    ip_req_url = "https://p3.picarro.com/google/rest/gdu/<TICKET>/1.0/AnzMeta/"
    push_url = "https://p3.picarro.com/google/rest/gdu/<TICKET>/1.0/AnzLog/"

    subprocess.call(["DatEchoP3.exe",
                     "--listen-path", lpath,
                     "--data-type", dat_type,
                     "--analyzer-name", anz,
                     "--log-metadata-url", log_metadata_url,
                     "--ticket-url", ticket_url,
                     "--ip-req-url", ip_req_url,
                     "--push-url", push_url,
                     "--sys", psys,
                     "--identity", identity,
                     "--history-range", history_range,
                     "-c", "50601",
                     "--nbr-lines", lines])
