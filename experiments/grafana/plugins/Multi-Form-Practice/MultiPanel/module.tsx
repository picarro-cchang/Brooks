import { PanelPlugin } from "@grafana/ui";
import { MyPanel } from "./components/MyPanel";
import { ExtraOptions, defaults } from "./types";
import { MyPanelEditor } from "./components/MyPanelEditor";

export const plugin = new PanelPlugin<ExtraOptions>(MyPanel);

plugin.setEditor(MyPanelEditor);
plugin.setDefaults(defaults);
