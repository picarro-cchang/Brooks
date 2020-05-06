import { PanelPlugin } from "@grafana/ui";
import { DataGeneratorPanel } from "./src/components/DataGeneratorPanel";
import { DataGeneratorPanelProps } from "./src/types";
import { DataGeneratorService } from "./src/services/DataGeneratorService";

export const plugin = new PanelPlugin<DataGeneratorPanelProps>(
  DataGeneratorPanel
);

plugin.setDefaults(DataGeneratorService.getDefaults());
