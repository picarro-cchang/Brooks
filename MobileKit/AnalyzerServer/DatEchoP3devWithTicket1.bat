set listen-path="C:/UserData/AnalyzerServer/*DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat"
set data-type=dat   
set psys=APITEST   
set identity=85490338d7412a6d31e99ef58bce5de6
set lines=500

set ticket-url="https://dev.picarro.com/dev/rest/sec/dummy/1.0/Admin/"
set ip-req-url="https://dev.picarro.com/dev/rest/gdu/<TICKET>/1.0/AnzMeta/"  
set push-url="https://dev.picarro.com/dev/rest/gdu/<TICKET>/1.0/AnzLog/"
set log-meta-url="https://dev.picarro.com/dev/rest/gdu/<TICKET>/1.0/AnzLogMeta/"

python DatEchoP3.py --listen-path=%listen-path% --data-type=%data-type% --log-metadata-url=%log-meta-url% --ticket-url=%ticket-url% --ip-req-url=%ip-req-url% --push-url=%push-url% --sys=%psys% --identity=%identity% --nbr-lines=%lines% --history-range 365 --analyzer-name DEMO2000
