import { UserDataAppConfigCtrl } from './legacy/config';
// @ts-ignore
import { AppPlugin } from '@grafana/ui';
// @ts-ignore

// Legacy exports just for update/enable and disable
export { UserDataAppConfigCtrl as ConfigCtrl };

export let plugin = new AppPlugin();
