import { GrafanaTheme } from "@grafana/ui";
import { TimeRange } from "@grafana/data";

export interface DataGeneratorPanelProps {
  timeRange: TimeRange;
}

export interface DataGeneratorLayoutProps {
  theme: GrafanaTheme;
  options: DataGeneratorPanelProps;
}
