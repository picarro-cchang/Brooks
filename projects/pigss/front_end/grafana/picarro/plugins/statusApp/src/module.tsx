import { StatusAppConfigCtrl } from "./legacy/config";
import { AppPlugin } from "@grafana/ui";

// Legacy exports just for update/enable and disable
export { StatusAppConfigCtrl as ConfigCtrl };

export const plugin = new AppPlugin();
