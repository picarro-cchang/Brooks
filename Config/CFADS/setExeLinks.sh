#!/bin/bash
#
# To run code put on the analyzer with a *.deb package,
# run this script to put the config files in the right
# place.
#
cwd=$(pwd)

mv $HOME/I2000/AppConfig $HOME/I2000/AppConfig_
mv $HOME/I2000/InstrConfig $HOME/I2000/InstrConfig_

cp -r $cwd/AppConfig $HOME/I2000
cp -r $cwd/InstrConfig/ $HOME/I2000

