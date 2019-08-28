import React, { PureComponent } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
// @ts-ignore
// import socketIOClient from 'socket.io-client';

import { LogProps } from './types';
import { LogLayout } from './LogLayout';
// @ts-ignore
import { SocketURL } from '../constants/API';
import { LogService } from './../services/LogService';

interface Props extends PanelProps<LogProps> { }

interface State {
  data: string[][];
  query: Object;
}

const LIMIT = 100;

export class LogPanel extends PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      data: [],
      query: {}
    };
  }

  ws: WebSocket = new WebSocket(SocketURL);
  componentDidMount() {

    this.ws.onopen = () => {
      console.log('web socket connected');
      // @ts-ignore
      const start_date = new Date(this.props.options.date.from).getTime();
      // @ts-ignore
      const end_date = new Date(this.props.options.date.to).getTime();
      const query: any = {
        level: this.props.options.level,
        limit: this.props.options.level,
        start_date,
        end_date
      }
      this.setState({query});
      this.updateLogsData(query);
    }

    this.ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      const rows = JSON.parse(evt.data);
      // console.log('-->', rows)
      // Remove the previous logs data on front-end, if the rows are more than 1000.
      if (this.state.data.length > LIMIT) {
        this.setState({ data: [] })
      }
      this.setState({ data: [...rows, ...this.state.data] });
    }

    this.ws.onclose = () => {
      console.log('web socket disconnected');
      this.ws = new WebSocket(SocketURL);
      this.updateLogsData(this.state.query);
    }
  }

  componentDidUpdate(prevProps: Props) {
    if (
      this.props.options.level !== prevProps.options.level ||
      this.props.options.limit !== prevProps.options.limit ||
      this.props.options.date !== prevProps.options.date
    ) {
      // @ts-ignore
      const start_date = new Date(this.props.options.date.from).getTime();
      // @ts-ignore
      const end_date = new Date(this.props.options.date.to).getTime();
      const query: any = {
        level: this.props.options.level,
        limit: this.props.options.limit,
        start_date,
        end_date
      }
      this.setState({query});
      this.updateLogsData(query);
    }
  }

  getLogsData = (query: any) => {
    LogService.getLogs(query).then(response => {
      response.json().then(logArr => {
        this.setState({ data: [...this.state.data, ...logArr] })
      });
    })
  };

  updateLogsData = (query: Object) => {
    this.ws.send(JSON.stringify(query));
  };

  render() {
    const { options } = this.props;
    return (
      <ThemeContext.Consumer>
        {theme => {
          return <LogLayout options={{ ...options, data: this.state.data }} theme={theme} />;
        }}
      </ThemeContext.Consumer>
    );
  }
}
