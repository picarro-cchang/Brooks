#!/bin/bash

# This script provides a menu for Grafana builds

gitDir="${HOME}/git"
grafanaDir="${gitDir}/host/experiments/grafana/src/github.com/grafana/grafana"

while : # Loop forever
do
clear
cat << !
			     *********************
			     *                   *
			     *  Grafana   Build  *
                             *      Scripts      *
			     *                   *
			     *********************
1. Build Front-End
2. Build Back-End
3. Build Debian Package
4. Start Grafana Server (Source)
5. Launch Chromium Browser
6. Exit
!

echo -n "Select an option: "
read choice

case $choice in
	1) ./buildFrontEnd.sh;;
	2) ./buildBackEnd.sh;;
	3) ./buildDebianPackage.sh;;
	4) ./startGrafanaServer.sh; sleep 1s; clear;;
	5) chromium-browser --start-fullscreen http://localhost:3000;;
	6) exit;;
	*) echo "\"$choice\" is not an option."; sleep 1s ;;
esac
done
