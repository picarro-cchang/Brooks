# Pure JSX Grafana Plugin

### Currently working
* @grafana/ui imports
* User Changeable Grafana Theme
* Grafana CSS using div classNames
* Webpack with JS Loaders
***
### Currently not working
* Grafana Select Component

***

### Usage
#### Clone this repository:
```bash
mkdir -p ~/git && cd ~/git
git clone -b <branch> https://github.com/picarro/I2000-Host.git
```
#### Symlink the project directory to the Grafana plugin directory

Standalone binary:
```bash
$ ln -s /home/$USER/git/picarro-networking-plugin-jsx /home/$USER/Downloads/grafana-6.0.1/data/plugins/picarro-networking-plugin-jsx
```
Debian binary:
```bash
$ sudo ln -s /home/$USER/git/picarro-networking-plugin-jsx /var/lib/grafana/data/plugin/picarro-networking-plugin-jsx
```
#### Build the project:
```bash
$ npm run build
```
#### Start the Grafana Server

#### Start the Flask Server:
```bash
$ python /home/$USER/git/picarro-networking-plugin-jsx/src/flask_server.py
```
#### Open your browser to http://localhost:3000
#### Import the plug-in
#### Profit

