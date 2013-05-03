sudo git pull -f && sudo kill -9 $(ps aux | grep 'node app.js' | awk '{print $2}') && sudo bash ./run_production.sh
