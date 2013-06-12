REM Start reportServer and reportProxy for developing reportGeneration code
start node reportServer.js -n -s configs\site_config_node_with_pge -r\temp\Pge
start node reportProxy.js -s configs\site_config_node_with_pge
