import { dateTime } from '@grafana/data';
// import { LoggerGetColumnsAPI } from '../constants/API';
import { LogProps } from 'components/types';

export const LogService = (() => {
  function getLogs() {
    return [];
  }

  return {
    getDefaults: () => {
      const defaults: LogProps = {
        level: '10',
        limit: 20,
        date: { from: dateTime(), to: dateTime(), raw: { from: dateTime(), to: dateTime() } },
        data: [[]],
      };
      return defaults;
    },
    getLogs: getLogs,
  };
})();
