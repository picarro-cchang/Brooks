import React, { PureComponent } from "react";
import { TimeRange, dateTime, dateMath, TimeFragment } from "@grafana/data";
import "jest-styled-components";
import "jest-fetch-mock";
import { DataGeneratorService } from "./../services/DataGeneratorService";

jest.mock("./../services/API.ts");

describe("DataFileGeneratorService", () => {
  it("getDefaults", () => {
    const timeRange = {
      from: dateTime().subtract(6, "h"),
      to: dateTime(),
      raw: { from: "now-6h" as TimeFragment, to: "now" as TimeFragment }
    };
    const time = DataGeneratorService.getDefaults();
    const raw = time.timeRange.raw;
    expect(raw).toEqual(timeRange.raw);
  });

  it("getSavedFiles", () => {
    const files = DataGeneratorService.getSavedFiles();
    expect(files).toEqual({
      files: [
        "pigss-ms-02-05-2020_121737-02-05-2020_131737.csv",
        "pigss-ms-02-05-2020_121814-02-05-2020_131814.csv"
      ]
    });
  });

  it("getKeys", () => {
    const mockKeys = {
      keys: ["CavityPressure", "WarmBoxTemp", "HCl", "H2O", "SO2", "CH4"]
    };
    const keys = DataGeneratorService.getKeys();
    expect(keys).toEqual(mockKeys);
  });

  it("getAnalyzers", () => {
    const mockAnalyzers = {
      analyzers: [
        "SI2306",
        "SI2108",
        "SI3401",
        "BFADS",
        "SI5450"
      ]
    };
    const analyzers = DataGeneratorService.getAnalyzers();
    expect(mockAnalyzers).toEqual(analyzers);
  });

  it("getPorts", () => {
    const mockPorts = [
      { text: "2: Bank 1 Ch. 2", value: "2" },
      { text: "4: Bank 1 Ch. 4", value: "4" },
      { text: "6: Bank 1 Ch. 6", value: "6" },
      { text: "8: Bank 1 Ch. 8", value: "8" },
      { text: "18: Bank 3 Ch. 2", value: "18" },
      { text: "20: Bank 3 Ch. 4", value: "20" },
      { text: "22: Bank 3 Ch. 6", value: "22" },
      { text: "24: Bank 3 Ch. 8", value: "24" },
      { text: "26: Bank 4 Ch. 2", value: "26" },
      { text: "28: Bank 4 Ch. 4", value: "28" },
      { text: "30: Bank 4 Ch. 6", value: "30" },
      { text: "32: Bank 4 Ch. 8", value: "32" }
    ];
    const ports = DataGeneratorService.getPorts();
    expect(ports).toEqual(mockPorts);
  });

  it("getFile", async () => {
    const mockKeys = [
      ["time", "analyzer", "valve_pos", "WarmBoxTemp", "CavityTemp"],
      ["1580936855480", "SI2306", "18", "45", "80"],
      ["1580936854180", "SI2306", "18", "45", "80"],
      ["1580936852880", "SI2306", "18", "45", "80"]
    ];
    const response = await DataGeneratorService.getFile("");
    expect(response).toEqual(mockKeys);
  });

  it("generateFile", async () => {
    const params = {
      from: "",
      to: "",
      keys: [{ value: "CavityTemp", label: "CavityTemp" }],
      analyzers: [{ value: "SI2306", label: "SI2306" }],
      ports: [{ value: "2", label: "2" }],
      isProcessedData: false
    };
    const mockKeys = {
      filename: "pigss-ms-02-13-2020_061135-02-13-2020_121135.csv"
    };
    const response = await DataGeneratorService.generateFile(params);
    expect(response).toEqual(mockKeys);
  });
});
