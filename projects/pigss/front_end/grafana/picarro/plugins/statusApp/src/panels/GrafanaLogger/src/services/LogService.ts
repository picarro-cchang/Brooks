import { DEFAULT_LOG_PROPS, GET_LOGS_URL } from '../constants';
import { API } from './API';

export const LogService = (() => {
  return {
    getDefaults: () => {
      return DEFAULT_LOG_PROPS;
    },
    getLogs: (params: any) => {
      let url = GET_LOGS_URL + '?';
      const { rowid, level, limit, start, end, interval } = params;
      
      url += `rowid=${rowid}`;
      url += `&limit=${limit}`;
      url += `&start=${start}`;
      url += `&end=${end}`;
      url += `&interval=${interval}`;
      url += `&${level.map((i, j) => { return `level=${i}`}).join('&')}`;

      return API.get(url)
    }
  };
})();
