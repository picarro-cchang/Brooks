import { ReactPanelPlugin } from "@grafana/ui";
import { Main } from "./components/Main";
//import { Options, defaults } from "./types";
//import { ImagePanelEditor } from "./components/ImagePanelEditor";

export const reactPanel = new ReactPanelPlugin(Main);

//reactPanel.setEditor(ImagePanelEditor);
//reactPanel.setDefaults(defaults);
