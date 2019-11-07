import React, { PureComponent, Fragment } from 'react';
import { PanelProps, ThemeContext, GrafanaTheme } from '@grafana/ui';

import { SupervisorStatusProps } from '../types';
import { SupervisorStatusLayout } from './SupervisorStatusLayout';

interface Props extends PanelProps<SupervisorStatusProps> { }

export class SupervisorStatusPanel extends PureComponent<Props> {

  constructor(props: Props) {
    super(props);
  }

  render() {
    const { options } = this.props;
    return <ThemeContext.Consumer>
      {(theme: GrafanaTheme) => {
        return (
          <Fragment>
            <SupervisorStatusLayout options={{ ...options }} theme={theme}></SupervisorStatusLayout>
          </Fragment>
        )
      }}
    </ThemeContext.Consumer>
  }
}
