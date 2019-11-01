import React, { PureComponent, Fragment } from 'react';
import JSONTree from 'react-json-tree'

import { SupervisorStatusLayoutProps } from '../types';
import SupervisorStatusService from './../services';
import './Layout.css';

interface Props extends SupervisorStatusLayoutProps { }

export class SupervisorStatusLayout extends PureComponent<Props, any> {
  constructor(props: Props) {
    super(props);
    this.state = {
      status: {},
    }
  }

  componentWillMount() {
    SupervisorStatusService.getStatus().then((response: any) => {
      response.json().then((status: any) => {
        this.setState({ status });
      });
    });
  }

  render() {

    const styleObj = {
      overflow: 'scroll',
      height: 'inherit',
    };

    const theme = {
      scheme: 'picarro',
      author: 'Picarro Inc.',
      base00: '#00000000',
      base01: '#383830',
      base02: '#49483e',
      base03: '#75715e',
      base04: '#a59f85',
      base05: '#f8f8f2',
      base06: '#f5f4f1',
      base07: '#f9f8f5',
      base08: '#f92672',
      base09: '#fd971f',
      base0A: '#f4bf75',
      base0B: '#a6e22e',
      base0C: '#a1efe4',
      base0D: '#66d9ef',
      base0E: '#ae81ff',
      base0F: '#cc6633'
    };

    return (
      <Fragment>
        <h3 className="text-center">Supervisor Status</h3>
        <div className="container-fluid padding-bottom-24" style={styleObj}>
          <JSONTree data={this.state.status} theme={theme} invertTheme={false} />
        </div>
      </Fragment>
    )
  }
}
