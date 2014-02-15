set anzName=%1
set listen-path=C:/UserData/AnalyzerServer/%anzName%*.dat
set data-type=dat   
set psys=sqa   
set identity=JyBFc7jMyncFXiiYuTyvyoBFz99yjpG0
set lines=500

set ticket-url="https://p3.picarro.com/sqa/rest/sec/dummy/1.0/Admin/"
set ip-req-url="https://p3.picarro.com/sqa/rest/gdu/<TICKET>/1.0/AnzMeta/"  
set push-url="https://p3.picarro.com/sqa/rest/gdu/<TICKET>/1.0/AnzLog/"
set log-meta-url="https://p3.picarro.com/sqa/rest/gdu/<TICKET>/1.0/AnzLogMeta/"

python DatEchoP3.py --listen-path=%listen-path% --data-type=%data-type% --log-metadata-url=%log-meta-url% --ticket-url=%ticket-url% --ip-req-url=%ip-req-url% --push-url=%push-url% --sys=%psys% --identity=%identity% --nbr-lines=%lines% --history-range 3000 --analyzer-name %anzName%
