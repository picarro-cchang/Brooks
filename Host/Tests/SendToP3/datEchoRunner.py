import os
import subprocess
import sys

if __name__ == "__main__":
	if len(sys.argv)<2:
		fname = raw_input("Name of data file from analyzer? ")
	else:
		fname = sys.argv[1]
	abs_name = os.path.abspath(fname)
	base,name = os.path.split(abs_name)
	anz = name.split("-")[0]
	print anz
	
	dat_type="dat"   
	psys="google"   
	identity="N7boCjtBEcKwzzrzJHLTiDjmPFc1LchhXQBxQLvd"
	lines="1000"
	history_range="365"
	ticket_url="https://p3.picarro.com/google/rest/sec/dummy/1.0/Admin/"
	log_metadata_url="https://p3.picarro.com/google/rest/gdu/<TICKET>/1.0/AnzLogMeta/"
	ip_req_url="https://p3.picarro.com/google/rest/gdu/<TICKET>/1.0/AnzMeta/"  
	push_url="https://p3.picarro.com/google/rest/gdu/<TICKET>/1.0/AnzLog/"

	subprocess.call(["DatEchoP3.exe", 
					 "--listen-path", abs_name, 
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
