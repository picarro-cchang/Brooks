import { URL, DEFAULT_DATA_GENERATOR_PROPS } from '../../constants';
import { API } from './API';
import { DataGeneratorPanelProps } from '../../types';

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
    getAnalyzers: () => {
      return API.get(URL.GET_ANALYZERS)
    },
    getPorts: () => {
      return API.post(URL.GET_PORTS)
    },
    getFile: (fileName: string) => {
      const url = URL.GET_FILE + '?name=' + fileName;
      return API.get(url);      
    },
    generateFile: (params: any) => {
      let url = URL.GENERATE_FILE + '?';
      const { from, to, keys, analyzers, ports } = params;

      for (const key of keys) {
        url += `keys=${key['value']}&`;
      }
      for (const analyzer of analyzers) {
        url += `analyzer=${analyzer['value']}&`;
      }
      for (const port of ports) {
        url += `port=${port['value']}&`;
      }

      url += `from=${from}`;
      url += `&to=${to}`;
      return API.get(url);
    },
  };
})();
