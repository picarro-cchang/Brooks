#!/bin/bash

gitDir="${HOME}/git"
grafanaDir="${gitDir}/host/experiments/grafana/src/github.com/grafana/grafana"

# Build Grafana front-end
cd $grafanaDir
yarn install --pure-lockfile
yarn build
