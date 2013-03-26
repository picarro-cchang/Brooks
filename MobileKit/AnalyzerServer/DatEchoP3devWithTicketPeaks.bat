set file-path="R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120323\OUT\FCDS2006-20120323-020431Z-DataLog_User_Minimal.peaks"
set data-type=peaks
set psys=APITEST   
set identity=85490338d7412a6d31e99ef58bce5de6
set lines=1000

set ticket-url="https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
set ip-req-url="https://dev.picarro.com/node/rest/gdu/<TICKET>/1.0/AnzMeta/"  
set push-url="https://dev.picarro.com/node/rest/gdu/<TICKET>/1.0/AnzLog/"

python DatEchoP3.py --file-path=%file-path% --data-type=%data-type% --ticket-url=%ticket-url% --ip-req-url=%ip-req-url% --push-url=%push-url% --sys=%psys% --identity=%identity% --nbr-lines=%lines% --replace 


rem Data files from Sacramento comparison

set file-path="R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120323\OUT\FCDS2006-20120323-020431Z-DataLog_User_Minimal.peaks"
set file-path="R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120401\OUT\FCDS2006-20120401-095924Z-DataLog_User_Minimal.peaks"
set file-path="R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120410\OUT\FCDS2003-20120410-035159Z-DataLog_User_Minimal.peaks"
set file-path="R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120407\OUT\FCDS2003-20120407-042604Z-DataLog_User_Minimal.peaks"
set file-path="R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120407\OUT\FCDS2003-20120407-053754Z-DataLog_User_Minimal.peaks"
set file-path="R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120407\OUT\FCDS2003-20120407-064816Z-DataLog_User_Minimal.peaks"
set file-path="R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120407\OUT\FCDS2003-20120407-072125Z-DataLog_User_Minimal.peaks"
set file-path="R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120407\OUT\FCDS2006-20120407-102214Z-DataLog_User_Minimal.peaks"