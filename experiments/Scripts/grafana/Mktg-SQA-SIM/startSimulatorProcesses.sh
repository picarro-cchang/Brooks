#!/bin/bash

rootDir=$HOME/git/host/experiments
session="pigss-simulator"

# Start tmux server
tmux start-server

# Create a new sessions
tmux new-session -d -s $session

# Select main pane
tmux selectp -t 0
# Split the pane vertically
tmux splitw -v
tmux splitw -v

# Command 1 to top pane
tmux selectp -t 0
tmux send-keys "python $rootDir/LOLogger/LOLogger.py -j -v" C-m

# Command 2 to middle pane
tmux selectp -t 1
tmux send-keys "cd $rootDir/grafana/src/github.com/grafana/grafana/bin/linux-amd64/ && ./grafana-server --homepath ../../" C-m

# Command 3 to bottom pane
tmux selectp -t 2
tmux send-keys "python $rootDir/state_machine/back_end/pigss_runner.py -c pigss_sim_config.yaml" C-m

# Attach to session
tmux attach-session -t $session
