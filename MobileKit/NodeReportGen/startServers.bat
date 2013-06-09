REM Start reportServer and reportProxy for developing reportGeneration code
start node reportServer.js -n -s configs\site_config_node_with_stage -r\temp\ReportGen
start node reportProxy.js -s configs\site_config_node_with_stage
