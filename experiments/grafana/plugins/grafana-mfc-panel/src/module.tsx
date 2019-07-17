import { ReactPanelPlugin } from "@grafana/ui";
import { MFCPanel } from "./components/MFCPanel";
import { Options, defaults } from "./types";
//import { MFCLayout } from "./components/MFCLayout";

export const reactPanel = new ReactPanelPlugin<Options>(MFCPanel);

//reactPanel.setEditor(MFCLayout);
reactPanel.setDefaults(defaults);
