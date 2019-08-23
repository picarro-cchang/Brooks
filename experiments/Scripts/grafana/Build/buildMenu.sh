#!/bin/bash -i

# This script provides a menu for Grafana builds
source ~/.bashrc
gitDir="${HOME}/git"
grafanaDir="${gitDir}/host/experiments/grafana/src/github.com/grafana/grafana"
scriptsDir="${gitDir}/host/experiments/Scripts/grafana/Build"


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
3. Make Debian Package
4. Start Grafana Server (Source)
5. Launch Chromium Browser
6. Build Grafana Front and Back-End (for Petr)
7. Exit
!

echo -n "Select an option: "
read choice

case $choice in
	1) $scriptsDir/buildFrontEnd.sh;;
	2) $scriptsDir/buildBackEnd.sh;;
	3) $scriptsDir/buildDebianPackage.sh;;
	4) gnome-terminal -- $scriptsDir/startGrafanaServer.sh;;
	5) gnome-terminal -- chromium-browser --disable-save-password-bubble --password-store=basic --start-fullscreen http://localhost:3000;;
	6) $scriptsDir/buildFrontEnd.sh && $scriptsDir/buildBackEnd.sh;;
	7) exit;;
	*) echo "\"$choice\" is not an option."; sleep 1s ;;
esac
done
