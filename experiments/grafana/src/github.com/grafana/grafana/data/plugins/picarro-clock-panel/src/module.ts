import { PanelCtrl } from 'grafana/app/plugins/sdk';
import moment from 'moment';
import _ from 'lodash';
import './css/clock-panel.css';

class ClockCtrl extends PanelCtrl {
  static templateUrl = 'partials/module.html';
  panelDefaults = {
    refreshSettings: {
      syncWithDashboard: false,
    },
    dateSettings: {
      showDate: false,
      fontSize: '20px',
      fontWeight: 'normal',
      dateFormat: 'D-MMM-YYYY',
    },
    timeSettings: {
      fontSize: '60px',
      fontWeight: 'normal',
      customFormat: 'HH:mm:ss',
    },
  };
  nextTickPromise: any;
  date: string;
  time: string;

  /** @ngInject */
  constructor($scope, $injector) {
    super($scope, $injector);
    _.defaultsDeep(this.panel, this.panelDefaults);

    this.events.on('init-edit-mode', () => this.onInitEditMode());
    this.events.on('panel-teardown', () => this.onPanelTeardown());
    this.events.on('panel-initialized', () => this.render());
    this.events.on('component-did-mount', () => this.render());
    this.events.on('refresh', () => this.updateClock());
    this.events.on('render', () => this.updateClock());

    this.updateClock();
  }

  onInitEditMode() {
    this.addEditorTab('Options', 'public/plugins/' + this.pluginId + '/partials/options.html', 2);
    this.addEditorTab('Refresh', 'public/plugins/' + this.pluginId + '/partials/refresh.html', 2);
  }

  onPanelTeardown() {
    this.$timeout.cancel(this.nextTickPromise);
  }

  updateClock() {
    this.$timeout.cancel(this.nextTickPromise);
    this.renderTime();

    if (!this.panel.refreshSettings.syncWithDashboard) {
      this.nextTickPromise = this.$timeout(() => this.updateClock(), 1000);
    }
  }

  renderTime() {
    let now = moment();
    this.date = now.format(this.panel.dateSettings.dateFormat);
    this.time = now.format(this.panel.timeSettings.customFormat);
  }
}

export { ClockCtrl as PanelCtrl };
