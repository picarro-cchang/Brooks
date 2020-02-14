import React, { PureComponent } from 'react';
import { TimeRange, dateTime, dateMath, TimeFragment } from '@grafana/data';
import 'jest-styled-components';
import "jest-fetch-mock"
import { DataGeneratorService } from "./../services/DataGeneratorService";
jest.mock('./../services/API.ts')
describe("DataFileGeneratorService", () => {
    it("getDefaults", () => {
        const timeRange = {
            from: dateTime().subtract(6, 'h'),
            to: dateTime(),
            raw: {from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment}
        }
        const time = DataGeneratorService.getDefaults()
        const raw = time.timeRange.raw
        expect(raw).toEqual(timeRange.raw)
    });

    it("getSavedFiles", () => {
        const response = DataGeneratorService.getSavedFiles()
        expect(response).toEqual({"files": ["pigss-ms-02-05-2020_121737-02-05-2020_131737.csv", "pigss-ms-02-05-2020_121814-02-05-2020_131814.csv"]})
    });

    it("getKeys", () => {
        const response = DataGeneratorService.getKeys()
        const mockKeys = {"keys": ["CavityPressure", "WarmBoxTemp", "HCl", "H2O", "SO2", "CH4"]}
        expect(response).toEqual(mockKeys)
    });

    it("getAnalyzers", async () => {
        const response = DataGeneratorService.getAnalyzers()
        const mockKeys = {"analyzers": ["AMADS3001", "AMSADS3003", "BFADS3003", "SBDS3002", "UADS3003"]}
        expect(response).toEqual(mockKeys)
    });

    it("getPorts", async () => {
        const response = DataGeneratorService.getPorts()
        const mockKeys = [{"text": "2: Bank 1 Ch. 2", "value": "2"}, {"text": "4: Bank 1 Ch. 4", "value": "4"}, {"text": "6: Bank 1 Ch. 6", "value": "6"}, {"text": "8: Bank 1 Ch. 8", "value": "8"}, {"text": "18: Bank 3 Ch. 2", "value": "18"}, {"text": "20: Bank 3 Ch. 4", "value": "20"}, {"text": "22: Bank 3 Ch. 6", "value": "22"}, {"text": "24: Bank 3 Ch. 8", "value": "24"}, {"text": "26: Bank 4 Ch. 2", "value": "26"}, {"text": "28: Bank 4 Ch. 4", "value": "28"}, {"text": "30: Bank 4 Ch. 6", "value": "30"}, {"text": "32: Bank 4 Ch. 8", "value": "32"}]
        expect(response).toEqual(mockKeys)
    });

    it("getPorts", async () => {
        const response = DataGeneratorService.getFile("file-name")
        const mockKeys =  [
            ["time","analyzer","valve_pos","WarmBoxTemp","CavityTemp"], 
            ["1580936855480","AMSADS3003","18","45","80"],
            ["1580936854180","AMSADS3003","18","45","80"],
            ["1580936852880","AMSADS3003","18","45","80"]
          ]
        expect(response).toEqual(mockKeys)
    });

    it("getPorts", async () => {
        const params = {
            from: "",
            to: "",
            keys: "", 
            analyzers: "",
            ports: ""
        }
        const response = DataGeneratorService.generateFile(params)
        const mockKeys = {"filename": "pigss-ms-02-13-2020_061135-02-13-2020_121135.csv"}
        expect(response).toEqual(mockKeys)
    });
});
