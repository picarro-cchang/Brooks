#!/bin/bash

gitDir="${HOME}/git"
grafanaDir="${gitDir}/host/experiments/grafana/src/github.com/grafana/grafana"

# Build Grafana Debian Package
cd $grafanaDir
yarn install --pure-lockfile
go run build.go pkg-deb
