import React, { PureComponent } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';

import { ModbusOptions } from '../types';
import { ModbusLayout } from './ModbusSettings/ModbusLayout';

interface Props extends PanelProps<ModbusOptions> {}

export class ModbusPanel extends PureComponent<Props> {
  render() {
    const { options, width, height } = this.props;

    return (
      <ThemeContext.Consumer>
        {theme => {
          return (
            <ModbusLayout
              width={width}
              height={height}
              options={options}
              theme={theme}
            />
          );
        }}
      </ThemeContext.Consumer>
    );
  }
}
