import {
  GrafanaTheme,
} from '@grafana/ui';

export interface HelloOptions {
  worldString: string;
}

export const defaults: HelloOptions = {
  worldString: 'World',
};

export interface HelloProps {
  options: HelloOptions;
  theme: GrafanaTheme;
};
