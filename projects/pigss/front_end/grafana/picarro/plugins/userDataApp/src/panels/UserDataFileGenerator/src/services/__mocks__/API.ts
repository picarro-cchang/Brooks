import {URL} from '../../constants'
import { dateTime } from '@grafana/data';

export const API = {
    get(url: string) {
      switch(url) {
        case URL.GET_SAVED_FILES: {
          const data = {"files": ["pigss-ms-02-05-2020_121737-02-05-2020_131737.csv", "pigss-ms-02-05-2020_121814-02-05-2020_131814.csv"]}
          return data
        }
        case URL.GET_FIELD_KEYS: {
          const keys = {"keys": ["CavityPressure", "WarmBoxTemp", "HCl", "H2O", "SO2", "CH4"]}
          return keys
        }
        case URL.GET_ANALYZERS: {
          const analyzers = {"analyzers": ["AMADS3001", "AMSADS3003", "BFADS3003", "SBDS3002", "UADS3003"]}
          return analyzers
        }
        case URL.GET_FILE + '?name=': {
          // return new Promise((resolve) => {
          // resolve([["time","analyzer","valve_pos","WarmBoxTemp","CavityTemp"], 
          //   ["1580936855480","AMSADS3003","18","45","80"],
          //   ["1580936854180","AMSADS3003","18","45","80"],
          //   ["1580936852880","AMSADS3003","18","45","80"]])
          // });
          const data = [["time","analyzer","valve_pos","WarmBoxTemp","CavityTemp"], 
            ["1580936855480","AMSADS3003","18","45","80"],
            ["1580936854180","AMSADS3003","18","45","80"],
            ["1580936852880","AMSADS3003","18","45","80"]]
          return data
        }
        case URL.GENERATE_FILE + '?keys=CavityTemp&analyzer=AMSADS3003&port=2&from=&to=': {
          const data = {"filename": "pigss-ms-02-13-2020_061135-02-13-2020_121135.csv"}
          return data
        }
      }
    },
    post(url: string, data: object={}) {
      const ports = [{"text": "2: Bank 1 Ch. 2", "value": "2"}, {"text": "4: Bank 1 Ch. 4", "value": "4"}, {"text": "6: Bank 1 Ch. 6", "value": "6"}, {"text": "8: Bank 1 Ch. 8", "value": "8"}, {"text": "18: Bank 3 Ch. 2", "value": "18"}, {"text": "20: Bank 3 Ch. 4", "value": "20"}, {"text": "22: Bank 3 Ch. 6", "value": "22"}, {"text": "24: Bank 3 Ch. 8", "value": "24"}, {"text": "26: Bank 4 Ch. 2", "value": "26"}, {"text": "28: Bank 4 Ch. 4", "value": "28"}, {"text": "30: Bank 4 Ch. 6", "value": "30"}, {"text": "32: Bank 4 Ch. 8", "value": "32"}]
      return ports
      // return new Promise((resolve) => resolve([{"text": "2: Bank 1 Ch. 2", "value": "2"}, {"text": "4: Bank 1 Ch. 4", "value": "4"}, {"text": "6: Bank 1 Ch. 6", "value": "6"}, {"text": "8: Bank 1 Ch. 8", "value": "8"}, {"text": "18: Bank 3 Ch. 2", "value": "18"}, {"text": "20: Bank 3 Ch. 4", "value": "20"}, {"text": "22: Bank 3 Ch. 6", "value": "22"}, {"text": "24: Bank 3 Ch. 8", "value": "24"}, {"text": "26: Bank 4 Ch. 2", "value": "26"}, {"text": "28: Bank 4 Ch. 4", "value": "28"}, {"text": "30: Bank 4 Ch. 6", "value": "30"}, {"text": "32: Bank 4 Ch. 8", "value": "32"}]))
    },
  };
