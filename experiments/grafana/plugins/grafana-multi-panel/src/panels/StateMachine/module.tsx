import { PanelPlugin } from "@grafana/ui";
import { Main } from "./components/Main";
//import { Options, defaults } from "./types";
//import { ImagePanelEditor } from "./components/ImagePanelEditor";

export const plugin = new PanelPlugin(Main);

//reactPanel.setEditor(ImagePanelEditor);
//reactPanel.setDefaults(defaults);
