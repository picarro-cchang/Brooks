sudo git pull -f && sudo kill -9 $(ps aux | grep 'node app.js' | awk '{print $2}') && sudo bash ./run_production.sh

# for python.. 
# sudo touch /var/log/investigator_flask.log && chmod 0777 /var/log/investigator_flask.log
# sudo python ../MobileKit/AnalyzerServer/analyzerServer.py >> /var/log/investigator_flask.log 2>&1 &
