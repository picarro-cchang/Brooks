#!/bin/bash

# This script provides a menu for Grafana builds

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
4. Exit
!

echo -n "Select an option: "
read choice

case $choice in
	1) ./buildFrontEnd.sh;;
	2) ./buildBackEnd.sh;;
	3) ./buildDebianPackage.sh;;
	4) exit;;
	*) echo "\"$choice\" is not an option."; sleep 1s ;;
esac
done
