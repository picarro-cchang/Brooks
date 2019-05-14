#!/bin/bash

# Sleep a bit before starting so the customer can see the
# Picarro logo on the desktop wallpaper
sleep 5
#cd /home/picarro/git/host/src/main/python/Host/Supervisor
xterm -iconic -e /home/picarro/bin/launchSimulation.sh

sleep 5
#shutdown -P "now"

