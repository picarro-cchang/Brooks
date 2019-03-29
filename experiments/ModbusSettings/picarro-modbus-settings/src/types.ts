import { GrafanaTheme } from '@grafana/ui';

export interface ModbusOptions {
  slaveId: number;
  tcpPort: number;
  user: object;
  userOrgInfo: object;
}

export const defaults: ModbusOptions = {
  slaveId: 1,
  tcpPort: 50500,
  user: {},
  userOrgInfo: {},
};

export interface ModbusProps {
  width: number;
  height: number;
  options: ModbusOptions;
  theme: GrafanaTheme;
}
