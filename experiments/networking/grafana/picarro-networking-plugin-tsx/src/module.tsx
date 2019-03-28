import { ReactPanelPlugin } from '@grafana/ui';
import { NetworkPanel } from './components/Network/NetworkPanel';
import { NetworkPanelEditor } from './components/Network/NetworkPanelEditor';
import { defaults, NetworkOptions } from './types';
const request = require('sync-request');

const url = 'http://localhost:3030/get_network_settings';
setDefaults();

export const reactPanel = new ReactPanelPlugin<NetworkOptions>(NetworkPanel);

reactPanel.setEditor(NetworkPanelEditor);
reactPanel.setDefaults(defaults);

function setDefaults () {
    let res = request('GET', url);
    if (res.statusCode == 200) {
        let data = JSON.parse(res.getBody());
        defaults.networkType = data['networkType'];
        defaults.ip = data['ip'];
        defaults.gateway = data['gateway'];
        defaults.netmask = data['netmask'];
        defaults.dns = data['dns'];
    } else {
        alert('Error! GET request failed for Network Settings: defaults')
    }
}
