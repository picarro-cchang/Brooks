import React, { PureComponent } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
// @ts-ignore
// import socketIOClient from 'socket.io-client';

import { LogProps } from './types';
import { LogLayout } from './LogLayout';
// @ts-ignore
import { SocketURL } from '../constants/API';
import { LogService } from './../services/LogService';

interface Props extends PanelProps<LogProps> {}

interface State {
  data: string[][];
}

export class LogPanel extends PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      data: [],
    };
  }

  ws: WebSocket = new WebSocket(SocketURL);
  componentDidMount() {
    // Call REST to get the data
    // Set up web sockets to continually update the ui
    // this.updateLogsData(`?level=${this.props.options.level}&limit=${this.props.options.limit}`);
    this.getLogsData();

    this.ws.onopen = () => {
      // on connecting, do nothing but log it to the console
      console.log('web socket connected');
    }

    this.ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      const rows = JSON.parse(evt.data);
      // console.log('-->', rows)

      // Remove the previous logs data on front-end, if the rows are more than 1000.
      if(this.state.data.length > 1000) {
        this.setState({data: []})
      }
      this.setState({data: [...rows, ...this.state.data]});
    }

    this.ws.onclose = () => {
      console.log('web socket disconnected');
      this.ws = new WebSocket(SocketURL);
      this.updateLogsData(`?level=${this.props.options.level}&limit=${this.props.options.limit}`);
    }
  }

  wsSendParams = (o: object) => {
    console.error('Sending to websocket:', o);
    this.ws.send(JSON.stringify(o));
  };

  // componentWillUpdate() {
  //   // If the
  // }

  componentDidUpdate(prevProps: Props) {
    if (
      this.props.options.level !== prevProps.options.level ||
      this.props.options.limit !== prevProps.options.limit ||
      this.props.options.date !== prevProps.options.date
    ) {
      // TO DO: Make API
      console.log('Make call to the API', this.props);
      const query = `?level=${this.props.options.level}&limit=${this.props.options.limit}`;
      this.updateLogsData(query);
    }
  }

  getLogsData = () => {
    LogService.getLogs().then(response => {
      response.json().then(logArr => {
        this.setState({ data: [...this.state.data, ...logArr]})
      });
    })
  };

  updateLogsData = (query = '') => {
    LogService.getLogs(query).then(response => {
      response.json().then(logArr => {
        // console.log('logArr here', logArr);
        this.setState({ data: [...logArr] });
      });
    });
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
