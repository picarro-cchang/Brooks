import { URL } from './../constants';
import { API } from './API';


export const DataGeneratorService = (() => {
  return {
    getDefaults: () => {
      return {};
    },
    getSavedFiles: () => {
      return API.get(URL.GET_SAVED_FILES);
    },
    getFile: (fileName: string) => {
      const url = URL.GET_FILE + '?name=' + fileName;
      return API.getFile(url);
    }
  };
})();
