#!/bin/bash

# Download and install telegraf
if ! which telegraf 2> /dev/null; then
    wget https://dl.influxdata.com/telegraf/releases/telegraf_1.11.4-1_amd64.deb
    sudo dpkg -i telegraf_1.11.4-1_amd64.deb
fi

# Copy telegraf config file
sudo cp -r conf/telegraf.conf /etc/telegraf/telegraf.conf

# Set up influx database for telegraf
if ! influx -execute 'show databases' | grep telegraf 2> /dev/null; then
    influx -execute 'create database telegraf'
fi

# Start and enable telegraf
sudo systemctl start telegraf
sudo systemctl enable telegraf

