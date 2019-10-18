import React, { PureComponent, Fragment } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
import { GrafanaTheme } from '@grafana/ui';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

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
          return <Fragment>
            <DataGeneratorLayout options={{ ...options }} theme={theme} />;
            <ToastContainer />
          </Fragment>
        }}
      </ThemeContext.Consumer>
    );
  }
}
