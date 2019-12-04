import React, { PureComponent, Fragment } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { notifyError, notifySuccess } from '../utils/Notifications';
import { CounterPanelProps } from './types';
import { CounterLayout } from './CounterLayout';

interface Props extends PanelProps<CounterPanelProps> { }

interface State {
  count: number;
}

export class CounterPanel extends PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      count: 0
    };
  }
  render() {
    const { options } = this.props;
    return (
      <ThemeContext.Consumer>
        {theme => {
          return (
            <Fragment>
              <CounterLayout options={{ ...options }} theme={theme} />
              <ToastContainer />
            </Fragment>
          );
        }}
      </ThemeContext.Consumer>
    );
  }
}
