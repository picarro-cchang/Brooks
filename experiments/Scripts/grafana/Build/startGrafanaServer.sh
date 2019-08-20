#!/bin/bash

gitDir="${HOME}/git"
grafanaDir="${gitDir}/host/experiments/grafana/src/github.com/grafana/grafana"

cd $grafanaDir
bin/linux-amd64/grafana-server &
