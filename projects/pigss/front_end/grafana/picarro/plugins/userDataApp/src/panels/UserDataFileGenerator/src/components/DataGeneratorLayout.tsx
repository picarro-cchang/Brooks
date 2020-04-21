import React, { PureComponent, Fragment } from "react";
import { TimeRange, dateTime, dateMath } from "@grafana/data";
import {
  TimePicker,
  FormLabel,
  PanelOptionsGroup,
  Select,
  Button,
  Switch
} from "@grafana/ui";

import { notifyError, notifySuccess } from "../utils/Notifications";
import { DataGeneratorLayoutProps } from "../types";
import { DEFAULT_TIME_OPTIONS } from "../constants";
import { DataGeneratorService } from "../services/DataGeneratorService";

import "./Layout.css";

interface Props extends DataGeneratorLayoutProps {}

const labelWidth_6 = 6;
const labelWidth_7 = 7;
const selectWidth = 12;

export default class DataGeneratorLayout extends PureComponent<Props, any> {
  constructor(props: Props) {
    super(props);
    this.state = {
      timeRange: this.props.options.timeRange,
      keys: [],
      keyOptions: [{ value: "All", label: "All" }],
      analyzers: [],
      analyzerOptions: [{ value: "All", label: "All" }],
      ports: [],
      portOptions: [{ value: "All", label: "All" }],
      files: [],
      isProcessedData: true,
    };
  }

  // Code to download the file
  downloadData = (blob: any, fileName: string) => {
    const a = document.createElement("a");

    document.getElementById("file-list").appendChild(a);
    // @ts-ignore
    a.style = "display: none";
    const url = window.URL.createObjectURL(blob);
    a.href = url;
    a.download = fileName;
    a.click();
    notifySuccess(`File successfully downloaded in Downloads folder.`);
    window.URL.revokeObjectURL(url);
  };

  generateFile = () => {
    const { timeRange, keys, analyzers, ports, isProcessedData } = this.state;
    const { from, to } = {
      from: dateMath.parse(timeRange.raw.from),
      to: dateMath.parse(timeRange.raw.to),
      raw: timeRange.raw
    } as TimeRange;

    // @ts-ignore
    const fromTime = from._d.getTime();
    // @ts-ignore
    const toTime = to._d.getTime();

    if (fromTime === toTime || keys.length === 0) {
      notifyError("Invalid Query parameters");
      return;
    }

    const queryParams = {
      ports,
      from: fromTime * 1000000,
      to: toTime * 1000000,
      keys,
      analyzers,
      isProcessedData
    };

    // Call generate file api
    DataGeneratorService.generateFile(queryParams).then((response: any) => {
      response.json().then((data: any) => {
        // call getFile to download the data
        if (data.filename !== undefined) {
          this.getFileNames();
          this.getFile(data.filename);
        } else {
          if (data !== undefined && data.hasOwnProperty("message")) {
            notifyError(data.message);
          }
        }
      });
    });
  };

  getFile = (fileName: string) => {
    DataGeneratorService.getFile(fileName).then((response: any) => {
      response.blob().then((data: any) => {
        this.downloadData(data, fileName);
      });
    });
  };

  getFileNames = () => {
    // Get file names
    DataGeneratorService.getSavedFiles().then((response: any) => {
      response.json().then((files: any) => {
        this.setState(() => {
          return files;
        });
      });
    });
  };

  onDateChange = (timeRange: TimeRange) => {
    this.setState({ timeRange });
  };

  onKeysChange = (keys: any) => {
    if (!keys.length) {
      this.setState({ keys: [] });
      return;
    }
    for (const key of keys) {
      if (key.value === "All") {
        this.setState(() => {
          return {
            keys: this.state.keyOptions.filter(x => x.value !== "All")
          };
        });
        break;
      }
      this.setState(() => {
        return { keys };
      });
    }
  };

  onAnalyzersChange = (analyzers: any) => {
    if (!analyzers.length) {
      this.setState({ analyzers: [] });
      return;
    }

    for (const analyzer of analyzers) {
      if (analyzer.value === "All") {
        this.setState(() => {
          return {
            analyzers: this.state.analyzerOptions.filter(x => x.value !== "All")
          };
        });
        break;
      }
      this.setState(() => {
        return { analyzers };
      });
    }
  };

  onPortsChange = (ports: any) => {
    if (!ports.length) {
      this.setState({ ports: [] });
      return;
    }

    for (const port of ports) {
      if (port.value === "All") {
        this.setState(() => {
          return {
            ports: this.state.portOptions.filter(x => x.value !== "All")
          };
        });
        break;
      }
      this.setState(() => {
        return { ports };
      });
    }
  };

  onProcessedDataSwitchChange = (checked: boolean) => {
    this.setState({isProcessedData: checked})
  }

  componentWillMount() {
    // Get file names
    this.getFileNames();

    // Get Key Options
    DataGeneratorService.getKeys().then((response: any) => {
      response.json().then((data: any) => {
        const keyOptions = data.keys.map((x: string) => {
          return {
            value: x,
            label: x
          };
        });
        this.setState({
          keyOptions: [...this.state.keyOptions, ...keyOptions]
        });
      });
    });

    // Get Analyzer Options
    DataGeneratorService.getAnalyzers().then((response: any) => {
      response.json().then((data: any) => {
        const analyzerOptions = data.analyzers.map((x: string) => {
          return {
            value: x,
            label: x
          };
        });
        this.setState({
          analyzerOptions: [...this.state.analyzerOptions, ...analyzerOptions]
        });
      });
    });

    // Get Port Options
    DataGeneratorService.getPorts().then((response: any) => {
      response.json().then((data: any) => {
        const portOptions = data.map((x: any) => {
          return {
            value: x.value,
            label: x.text
          };
        });
        this.setState({
          portOptions: [...this.state.portOptions, ...portOptions]
        });
      });
    });
  }

  render() {
    const {
      files,
      timeRange,
      keyOptions,
      analyzerOptions,
      portOptions
    } = this.state;

    const styleObj = {
      overflow: "scroll !important",
      height: "inherit"
    };

    if (typeof timeRange.from === "string") {
      timeRange.from = dateTime(timeRange.from);
    }
    if (typeof timeRange.to === "string") {
      timeRange.to = dateTime(timeRange.to);
    }

    const fileItems = files.map((fn: string, i: number) => {
      return (
        <li
          key={fn}
          className="file-item"
          value={fn}
          onClick={() => this.getFile(fn)}
        >
          {fn}
        </li>
      );
    });

    return (
      <Fragment>
        <h3 className="text-center">Export Data</h3>
        <PanelOptionsGroup title="Generate New File">
          <PanelOptionsGroup>
            <div className="gf-form">
              <FormLabel width={labelWidth_6}>Species</FormLabel>
              <Select
                options={keyOptions}
                onChange={this.onKeysChange}
                value={keyOptions.find((option: any) => option.value === "key")}
                isMulti={true}
                backspaceRemovesValue
              />
            </div>
          </PanelOptionsGroup>

          <PanelOptionsGroup>
            <div className="gf-form">
              <FormLabel width={labelWidth_6}>Analyzer</FormLabel>
              <Select
                options={analyzerOptions}
                onChange={this.onAnalyzersChange}
                value={analyzerOptions.find(
                  (option: any) => option.value === "key"
                )}
                isMulti={true}
                backspaceRemovesValue
              />
            </div>
          </PanelOptionsGroup>
          <PanelOptionsGroup>
            <div className="gf-form">
              <FormLabel width={labelWidth_6}>Port</FormLabel>
              <Select
                options={portOptions}
                onChange={this.onPortsChange}
                value={portOptions.find(
                  (option: any) => option.value === "key"
                )}
                isMulti={true}
                backspaceRemovesValue
              />
            </div>
          </PanelOptionsGroup>
          <PanelOptionsGroup>
            <div className="gf-form">
              <Switch
                label="Processed Data"
                checked={this.state.isProcessedData}
                onChange={() => this.onProcessedDataSwitchChange(!this.state.isProcessedData)}
              />
            </div>
          </PanelOptionsGroup>
          <PanelOptionsGroup>
            <div className="time-generate-btn">
              <div className="gf-form time-picker-container">
                <FormLabel width={labelWidth_7}>Time Range</FormLabel>
                <TimePicker
                  timeZone="browser"
                  selectOptions={DEFAULT_TIME_OPTIONS}
                  onChange={this.onDateChange}
                  value={this.state.timeRange}
                  onMoveBackward={() => console.log("Move Backward")}
                  onMoveForward={() => console.log("Move forward")}
                  onZoom={() => console.log("Zoom")}
                />

                <div className="gf-form col-md-1">
                  <Button
                    size="md"
                    variant="primary"
                    value="Generate"
                    onClick={this.generateFile}
                    disabled={
                      !(
                        this.state.keys.length &&
                        this.state.analyzers.length &&
                        this.state.ports.length
                      )
                    }
                  >
                    Generate
                  </Button>
                </div>
              </div>
            </div>
          </PanelOptionsGroup>
        </PanelOptionsGroup>
        <PanelOptionsGroup title="Recently Generated Files">
          <div className="row" style={styleObj}>
            <div className="gf-form col-md-12 col-sm-12">
              <ul id="file-list" style={{ listStyle: "none" }}>
                {fileItems}
              </ul>
            </div>
          </div>
        </PanelOptionsGroup>
      </Fragment>
    );
  }
}
