import { dateTime } from '@grafana/data';
// import { LoggerGetColumnsAPI } from '../constants/API';
import { TableOptions } from 'components/DataTable/types';

export const LogService = (() => {
  function getLogs() {
    return [];
  }

  return {
    getDefaults: () => {
      const defaults: TableOptions = {
        thead: ['Time', 'Client', 'LogMessage', 'Level'],
        level: '10',
        limit: 20,
        date: { from: dateTime(), to: dateTime(), raw: { from: dateTime(), to: dateTime() } },
      };
      return defaults;
    },
    getLogs: getLogs,
  };
})();
