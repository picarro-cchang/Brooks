import React, { PureComponent } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';

import { LogProps } from './types';
import { LogLayout } from './LogLayout';
import { LOG_LIMIT } from './../constants';

// @ts-ignore
import { SocketURL } from '../constants';
import { LogService } from './../services/LogService';
// @ts-ignore
import console = require('console');

interface Props extends PanelProps<LogProps> { }

interface State {
  data: string[][];
  query: Object;
  interval: number;
}

export class LogPanel extends PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      data: [],
      query: {},
      interval: parseInt(this.props.replaceVariables('$interval')) || 1
    };
  }

  ws: WebSocket = new WebSocket(SocketURL);
  componentDidMount() {
    this.ws.onopen = () => {
      console.log('web socket connected');
      console.log(this.ws);
      this.updateLogsData(this.state.query);
    };

    this.ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      const rows = JSON.parse(evt.data);
      // Remove the previous logs data on front-end, if the rows are more than 1000.
      if (this.state.data.length > LOG_LIMIT) {
        this.setState({ data: [] });
      }
      this.setState({ data: [...rows.reverse(), ...this.state.data] });
    };

    this.ws.onclose = () => {
      console.log('web socket disconnected');
      this.ws = new WebSocket(SocketURL);
      this.updateLogsData(this.state.query);
    };
  }

  componentDidUpdate(prevProps: Props, prevState: State) {

    // @ts-ignore
    const isDateTimeFromChanged = this.props.data.request.range.raw.from !== prevProps.data.request.range.raw.from;
    // @ts-ignore
    const isDateTimeToChanged = this.props.data.request.range.raw.to !== prevProps.data.request.range.raw.to;
    // @ts-ignore
    const isIntervalChanged = this.props.data.request.interval !== prevProps.data.request.interval;
    // ERASE
    // @ts-ignore
    const interval = parseInt(this.props.replaceVariables('$interval'));

    if (
      JSON.stringify(this.props.options.level) !== JSON.stringify(prevProps.options.level) ||
      this.props.options.limit !== prevProps.options.limit ||
      interval !== this.state.interval ||
      isDateTimeFromChanged ||
      isDateTimeToChanged
    ) {
      this.setState(() => ({ interval }));

      console.log("Intrerval Now ", interval, isDateTimeFromChanged, isDateTimeToChanged, isIntervalChanged);
      const queryObj = this.getQueryObj(this.props);
      this.updateLogsData(queryObj);
    }
  }

  getQueryObj = (props: any) => {
    // @ts-ignore
    const start_date = new Date(this.props.data.request.range.from).getTime();
    // @ts-ignore
    const end_date = new Date(this.props.data.request.range.to).getTime();
    // @ts-ignore
    const interval = parseInt(this.props.replaceVariables('$interval'));
    // console.log("Intrerval Now ", interval);
    const query: any = {
      level: this.props.options.level.map((item: any) => item.value),
      limit: this.props.options.limit,
      start_date,
      end_date,
      interval
    };
    return query;
  }

  getLogsData = (query: any) => {
    LogService.getLogs(query).then(response => {
      response.json().then(logArr => {
        this.setState({ data: [...this.state.data, ...logArr] });
      });
    });
  };

  updateLogsData = (query: Object) => {
    if (this.ws.readyState) {
      this.ws.send(JSON.stringify(query));
    }
  };

  componentWillUnmount() {
    console.log('Component will unmount');
    this.ws.send('CLOSE');
    this.ws.close(1000, 'Client Initited Connection Termination');
  }

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
