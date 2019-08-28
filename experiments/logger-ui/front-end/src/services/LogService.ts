import { TimeFragment, dateTime } from '@grafana/data';
import { LoggerGetLogsAPI } from '../constants/API';
import { LogProps } from 'components/types';

export const LogService = (() => {
  function getLogs(query = '') {
    const url = LoggerGetLogsAPI + query;
    console.log('url', url);
    return fetch(url, {
      method: 'GET',
    }).then(response => {
      if (!response.ok) {
        throw Error('Network GET request failed');
      }
      console.log('Response to GET', response);
      return response;
    });
  }

  return {
    getDefaults: () => {
      const defaults: LogProps = {
        level: '10',
        limit: 20,
        date: {
          from: dateTime(),
          to: dateTime(),
          raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment }
        },
        data: [[]],
      };
      return defaults;
    },
    getLogs: getLogs,
  };
})();
