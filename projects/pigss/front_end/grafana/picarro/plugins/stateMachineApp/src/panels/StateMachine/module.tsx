import { PanelPlugin } from "@grafana/ui";
import { Main } from "./components/Main";

// @ts-ignore
export const plugin = new PanelPlugin(Main);

