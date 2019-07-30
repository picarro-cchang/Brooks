import { PanelPlugin } from "@grafana/ui";
import { MyPanel } from "./components/MyPanel";
import { ExtraOptions, defaults } from "./types";
import { MyPanelEditor } from "./components/MyPanelEditor";

export const reactPanel = new PanelPlugin<ExtraOptions>(MyPanel);

reactPanel.setEditor(MyPanelEditor);
reactPanel.setDefaults(defaults);
