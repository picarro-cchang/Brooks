import React, { PureComponent } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';

import { TableOptions } from './types';
import { TableLayout } from './TableLayout';

interface Props extends PanelProps<TableOptions> {}

export class TablePanel extends PureComponent<Props> {
  render() {
    const { options } = this.props;
    console.log('TablePanel', options);
    return (
      <ThemeContext.Consumer>
        {theme => {
          return <TableLayout options={options} theme={theme} />;
        }}
      </ThemeContext.Consumer>
    );
  }
}
