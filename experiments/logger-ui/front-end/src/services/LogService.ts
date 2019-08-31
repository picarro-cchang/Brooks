import { LoggerGetLogsAPI, DEFAULT_LOG_PROPS } from '../constants';

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
      return DEFAULT_LOG_PROPS;
    },
    getLogs: getLogs,
  };
})();
