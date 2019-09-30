#!/bin/bash -e

# Location for grafana plugins when running from source
grafanaSourcePluginDestDir=${HOME}/git/host/experiments/grafana/src/github.com/grafana/grafana/data/plugins/
# Location of custom grafana plugins in repo
pluginSourceDir=${HOME}/git/host/experiments/grafana/plugins
# List of plugins to be built
pluginList=('
    button-panel
    analyzer-graphs-app
    concentration-by-valve-app
    simpod-json-datasource
    current-values-app
    state-machine-app
    ')

# Make the grafana source plugin directory if it doesn't exist
mkdir -p ${grafanaSourcePluginDestDir}
# Remove any folders/symlinks if they exist
cd ${grafanaSourcePluginDestDir}
rm -rf *

# Create individual symlinks and build
for plugin in ${pluginList};do
    cd ${pluginSourceDir}/${plugin}
    printf "\n"; printf "Creating ${plugin} symlink"; printf "\n\n"
    ln -vs ${PWD} ${grafanaSourcePluginDestDir}/${plugin}
    printf "\n"; printf "Building ${plugin}"; printf "\n\n"
    yarn install
    yarn build
done

