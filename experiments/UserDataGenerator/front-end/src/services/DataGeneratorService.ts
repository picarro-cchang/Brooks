import { URL, DEFAULT_DATA_GENERATOR_PROPS } from './../constants';
import { API } from './API';
import { DataGeneratorPanelProps } from 'types';

export const DataGeneratorService = (() => {
  return {
    getDefaults: () => {
      return DEFAULT_DATA_GENERATOR_PROPS as DataGeneratorPanelProps;
    },
    getSavedFiles: () => {
      return API.get(URL.GET_SAVED_FILES);
    },
    getKeys: () => {
      return API.get(URL.GET_FIELD_KEYS);
    },
    getFile: (fileName: string) => {
      const url = URL.GET_FILE + '?name=' + fileName;
      return API.get(url);
    },
    generateFile: (params: any) => {
      // http://localhost:8010/api/generatefile
      // url eg http://localhost:8010/api/generatefile?keys=CO2&keys=NH3&keys=H2O&keys=CH4&from=1569609759914&to=1569619183402
      let url = URL.GENERATE_FILE + '?';
      const { from, to, keys } = params;

      for (let key of keys) {
        url += `keys=${key['value']}&`;
      }

      url += `from=${from}`;
      url += `&to=${to}`;
      return API.get(url);
    },
  };
})();
