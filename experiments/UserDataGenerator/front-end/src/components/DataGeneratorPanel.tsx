import React, { PureComponent } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
import { GrafanaTheme } from '@grafana/ui';

import { DataGeneratorPanelProps } from './../types';
import DataGeneratorLayout from './DataGeneratorLayout';

interface Props extends PanelProps<DataGeneratorPanelProps> { }

export class DataGeneratorPanel extends PureComponent<Props> {
  constructor(props: Props) {
    super(props);
  }

  render() {
    const { options } = this.props;
    return (
      <ThemeContext.Consumer>
        {(theme: GrafanaTheme) => {
          return <DataGeneratorLayout options={{ ...options }} theme={theme} />;
        }}
      </ThemeContext.Consumer>
    );
  }
}
