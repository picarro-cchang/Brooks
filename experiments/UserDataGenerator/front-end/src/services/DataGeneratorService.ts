import { DEFAULT_DATA_GENERATOR_PROPS } from './../constants';

export const DataGeneratorService = (() => {
  return {
    getDefaults: () => {
      return DEFAULT_DATA_GENERATOR_PROPS;
    },
  };
})();
