#!/bin/bash
#
# To run code put on the analyzer with a *.deb package,
# run this script to put the config files in the right
# place.
#
cwd=$(pwd)

mv $HOME/SI2000/AppConfig $HOME/SI2000/AppConfig_
mv $HOME/SI2000/InstrConfig $HOME/SI2000/InstrConfig_

cp -r $cwd/AppConfig $HOME/SI2000
cp -r $cwd/InstrConfig/ $HOME/SI2000

