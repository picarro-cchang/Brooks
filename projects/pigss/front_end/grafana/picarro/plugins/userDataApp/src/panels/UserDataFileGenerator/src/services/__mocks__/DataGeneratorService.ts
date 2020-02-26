import { URL, DEFAULT_DATA_GENERATOR_PROPS } from "../../constants";
import { API } from "./API";
import { DataGeneratorPanelProps } from "../../types";

export const DataGeneratorService = (() => {
  return {
    getDefaults: () => {
      return DEFAULT_DATA_GENERATOR_PROPS as DataGeneratorPanelProps;
    },
    getSavedFiles: () => {
      const response = API.get(URL.GET_SAVED_FILES);
      return Promise.resolve(new Response(JSON.stringify(response)));
    },
    getKeys: () => {
      const keys = API.get(URL.GET_FIELD_KEYS);
      return Promise.resolve(new Response(JSON.stringify(keys)));
    },
    getAnalyzers: () => {
      const analyzers = API.get(URL.GET_ANALYZERS);
      return Promise.resolve(new Response(JSON.stringify(analyzers)));
    },
    getPorts: () => {
      const ports = API.post(URL.GET_PORTS);
      return Promise.resolve(new Response(JSON.stringify(ports)));
    },
    getFile: (fileName: string) => {
      const url = URL.GET_FILE + "?name=" + fileName;
      const response = API.get(url);
      return Promise.resolve(new Response(JSON.stringify(response)));
    },
    generateFile: (params: any) => {
      let url = URL.GENERATE_FILE + "?";
      const { from, to, keys, analyzers, ports } = params;

      for (const key of keys) {
        url += `keys=${key.value}&`;
      }
      for (const analyzer of analyzers) {
        url += `analyzer=${analyzer.value}&`;
      }
      for (const port of ports) {
        url += `port=${port.value}&`;
      }

      url += `from=`;
      url += `&to=`;
      const response = API.get(url);
      return Promise.resolve(new Response(JSON.stringify(response)));
    }
  };
})();
