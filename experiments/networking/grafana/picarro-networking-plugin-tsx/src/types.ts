import {
  GrafanaTheme,
} from '@grafana/ui';

export interface NetworkOptions {
  networkType: string;
  ip: string;
  gateway: string;
  netmask: string;
  dns: string;
  btnEnabled: boolean;
}

export const defaults: NetworkOptions = {
  networkType: '',
  ip: '',
  gateway: '',
  netmask: '',
  dns: '',
  btnEnabled: false,
};

export interface NetworkProps {
  options: NetworkOptions;
  theme: GrafanaTheme;
};
