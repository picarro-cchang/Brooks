#!/bin/bash

# Set up virtual network interfaces
sudo ip link delete dummy0
sudo ip link delete dummy1
sudo ip link delete dummy2
sudo ip link add dummy0 type dummy
sudo ip link add dummy1 type dummy
sudo ip link add dummy2 type dummy
sudo ip addr add 192.168.10.101/24 brd + dev dummy0
sudo ip addr add 192.168.10.102/24 brd + dev dummy1
sudo ip addr add 192.168.10.103/24 brd + dev dummy2
