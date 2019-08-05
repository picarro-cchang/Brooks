import {
    GrafanaTheme,
} from '@grafana/ui';

export interface NetworkOptions {
    networkType: string;
    ip: string;
    gateway: string;
    netmask: string;
    dns: string;
    applyEnabled: boolean;
    undoEnabled: boolean;
}

export const defaults: NetworkOptions = {
    networkType: '',
    ip: '',
    gateway: '',
    netmask: '',
    dns: '',
    applyEnabled: false,
    undoEnabled: false,
};

export interface NetworkProps {
    options: NetworkOptions;
    theme: GrafanaTheme;
}

const host = 'http://localhost:';
const port = '3030';
export const getRoute = host + port + '/get_network_settings';
export const postRoute = host + port + '/set_network_settings';
