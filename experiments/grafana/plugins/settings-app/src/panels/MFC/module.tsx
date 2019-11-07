import { PanelPlugin } from "@grafana/ui";
import { MFCPanel } from "./components/MFCPanel";
import { Options, defaults } from "./types";
//import { MFCLayout } from "./components/MFCLayout";

export const plugin = new PanelPlugin<Options>(MFCPanel);

//reactPanel.setEditor(MFCLayout);
plugin.setDefaults(defaults);
