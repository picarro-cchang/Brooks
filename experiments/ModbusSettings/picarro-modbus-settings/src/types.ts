import { GrafanaTheme } from '@grafana/ui';

export interface ModbusOptions {
  slaveId: number;
  tcpPort: number;
}

export const defaults: ModbusOptions = {
  slaveId: 10,
  tcpPort: 50500,
};

export interface ModbusProps {
  width: number;
  height: number;
  options: ModbusOptions;
  theme: GrafanaTheme;
}
