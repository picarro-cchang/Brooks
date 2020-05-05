import { PanelPlugin } from "@grafana/ui";
import { PlanInformationPanelLayout } from "./components/PlanInformationPanelLayout";

export const plugin = new PanelPlugin(PlanInformationPanelLayout);
