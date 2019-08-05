import { ExampleConfigCtrl } from './legacy/config';
import { AppPlugin } from '@grafana/ui';

// Legacy exports just for update/enable and disable
export {
    ExampleConfigCtrl as ConfigCtrl,
};



export const plugin = new AppPlugin();
