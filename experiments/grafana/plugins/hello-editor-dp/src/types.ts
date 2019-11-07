import { GrafanaTheme } from '@grafana/ui';

export interface HelloOptions {
  name: string;
}

export const defaults: HelloOptions = {
  name: 'World',
};

export interface HelloProps {
  options: HelloOptions;
  theme: GrafanaTheme;
}
