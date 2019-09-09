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


# Start simulators
python mysim.py dummy0 '{"chassis": "4123", "analyzer": "AMADS", "analyzer_num": "3001", "species": ["NH3", "HF", "H2O"], "source": "analyze_AMADS_LCT", "mode": "AMADS_LCT_mode", "interval": 1.1}' 192.168.10.101 &
python mysim.py dummy1 '{"chassis": "4357", "analyzer": "SBDS", "analyzer_num": "3002", "species": ["HCl", "H2O"], "source": "analyze_SADS", "mode": "HCl_mode", "interval": 1.2}' 192.168.10.102 &
python mysim.py dummy2 '{"chassis": "4532", "analyzer": "BFADS", "analyzer_num": "3003", "species": ["H2S", "HDO"], "source": "analyze_BFADS", "mode": "BFADS_mode", "interval": 1.3}' 192.168.10.103 &

