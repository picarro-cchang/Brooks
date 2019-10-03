import { DEFAULT_LOG_PROPS } from '../constants';

export const LogService = (() => {
  return {
    getDefaults: () => {
      return DEFAULT_LOG_PROPS;
    },
  };
})();
