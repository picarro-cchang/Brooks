import React from "react";
import { DataGeneratorPanel } from "./../components/DataGeneratorPanel";
import { shallow } from "enzyme";
import { DataGeneratorPanelProps } from "../types";
import { PanelProps, ThemeContext } from "@grafana/ui";
import { GrafanaTheme } from "@grafana/ui";
import { DEFAULT_TIME_RANGE } from "./../constants/index";

jest.mock("./../services/DataGeneratorService.ts");
jest.mock("./../utils/Notifications.ts");

const defaultProps: PanelProps<DataGeneratorPanelProps> = {
  timeRange: DEFAULT_TIME_RANGE,
  id: 2,
  data: null,
  timeZone: "browser",
  options: null,
  onOptionsChange: () => {},
  renderCounter: 0,
  transparent: true,
  width: 1692,
  height: 812,
  replaceVariables: null,
  onChangeTimeRange: () => {}
};
const theme = { theme: "Grafana Dark" };
describe("<DataGeneratorPanel/>", () => {
  const wrapper = shallow(<DataGeneratorPanel {...defaultProps} {...theme} />);

  it("Create Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });
});
