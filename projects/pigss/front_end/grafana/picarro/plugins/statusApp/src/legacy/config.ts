import { PluginMeta } from "@grafana/ui";

export class StatusAppConfigCtrl {
  appEditCtrl: any;
  appModel: PluginMeta;

  /** @ngInject */
  constructor($scope: any, $injector: any) {
    this.appModel.enabled = true;
    this.appEditCtrl.setPostUpdateHook(this.postUpdate.bind(this));

    // Make sure it has a JSON Data spot
    if (!this.appModel) {
      this.appModel = {} as PluginMeta;
    }

    // Required until we get the types sorted on appModel :(
    const appModel = this.appModel as any;
    if (!appModel.jsonData) {
      appModel.jsonData = {};
    }
  }

  postUpdate() {
    if (!this.appModel.enabled) {
      return;
    }
  }
}
