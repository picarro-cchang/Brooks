import {
  GrafanaTheme,
} from '@grafana/ui';

export interface ValvePanelOptions {
  numberOfValves: number;
  buttonsPerRow: number;
};

export const defaults: ValvePanelOptions = {
  numberOfValves: 16,
  buttonsPerRow: 6
};

export interface LayoutProps {
  width: number;
  height: number;
  options: ValvePanelOptions;
  theme: GrafanaTheme;
  onInterpolate: (value: string, format?: string) => string;
};
