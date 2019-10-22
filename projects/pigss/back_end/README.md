# Configuration File Paths in the PiGSS backend

Plan files are stored in the directory `$HOME/.config/pigss/plan_files` in files with the `.pln` extension. Currently this directory is not configurable.

The back-end software is started using:

`python pigss_runner.py --config <config_file>.yaml`

The program looks for the specified YAML configuration file in the following directories in order:

 * The directory specified by the environmental variable PIGSS_CONFIG
 * The directory $HOME/.config/pigss
 * The directory containing the file pigss_runner.py

Within the YAML configuration file, the entry ["Configuration"]["RpcTunnel"]["config_file"] specifies the JSON-formatted file which allows a number of separate RPC endpoints to be accessed through a single port. The JSON file is searched for in the following directories in order:

 * The directory specified by the environmental variable PIGSS_CONFIG
 * The directory $HOME/.config/pigss
 * The directory containing the YAML configuration file

When running in simulation mode, the details of the simulated devices connected to the serial ports (the piglets, MFC and the relay boards) are enumerated using a program called `sim_serial_mapper`. This returns information from the file `sim_serial_map.json` which is searched for in the following directories in order:

 * The directory specified by the environmental variable PIGSS_CONFIG
 * The directory $HOME/.config/pigss
 * The directory containing the file `sim_serial_mapper.py`
