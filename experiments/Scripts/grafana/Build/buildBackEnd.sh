#!/bin/bash

gitDir="${HOME}/git"
grafanaDir="${gitDir}/host/experiments/grafana/src/github.com/grafana/grafana"

# Build Grafana back-end
cd $grafanaDir
go run build.go setup
go run build.go build
