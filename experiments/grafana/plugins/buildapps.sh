cd ${HOME}/git/host/experiments/grafana/plugins/button-panel
yarn install
yarn build
cd ../concentration-by-valve-app
yarn install
yarn build
cd ../grafana-multi-panel
yarn install 
yarn build
cd ../simpod-json-datasource
yarn install
yarn build
cd ../summary-app
yarn install
yarn build
cd ../../../grafana_api/provisioning/apps
python load_apps.py

