import React, { PureComponent, Fragment } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { notifyError, notifySuccess } from '../utils/Notifications';
import { LogProps } from './types';
import { LogLayout } from './LogLayout';
import { LOG_LIMIT, REFRESH_INTERVAL } from '../constants';
import { SocketURL } from '../constants';

interface Props extends PanelProps<LogProps> { }

interface State {
  data: string[][];
  query: object;
  interval: number;
}

export class LogPanel extends PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      data: [],
      query: {},
      interval: parseInt(this.props.replaceVariables('$interval'), 10) || REFRESH_INTERVAL,
    };
  }

  ws: WebSocket = new WebSocket(SocketURL);
  componentDidMount() {
    this.ws.onopen = () => {
      notifySuccess('Web socket connected');
      const queryObj = this.getQueryObj(this.props);
      this.updateLogsData(queryObj);
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
      notifyError('Web socket connection closed.');
      this.ws = new WebSocket(SocketURL);
      const queryObj = this.getQueryObj(this.props);
      this.updateLogsData(queryObj);
    };
  }

  componentDidUpdate(prevProps: Props, prevState: State) {

    // @ts-ignore
    const isDateTimeFromChanged = this.props.data.request.range.from._d.getTime() !== prevProps.data.request.range.from._d.getTime();
    // @ts-ignore
    const isDateTimeToChanged = this.props.data.request.range.to._d.getTime() !== prevProps.data.request.range.to._d.getTime();
    const interval = parseInt(this.props.replaceVariables('$interval'), 10);

    if (
      JSON.stringify(this.props.options.level) !== JSON.stringify(prevProps.options.level) ||
      this.props.options.limit !== prevProps.options.limit ||
      interval !== this.state.interval ||
      isDateTimeFromChanged ||
      isDateTimeToChanged
    ) {
      this.setState(() => ({ interval }));
      const queryObj = this.getQueryObj(this.props);
      this.updateLogsData(queryObj);
    }
  }

  getQueryObj = (props: any) => {
    // Removing @ts-ingore gives build err, as it thinks properties "probably" doesn't exist.
    // @ts-ignore
    const start = new Date(this.props.data.request.range.from).getTime();
    // @ts-ignore
    const end = new Date(this.props.data.request.range.to).getTime();
    // @ts-ignore
    const interval = parseInt(this.props.replaceVariables('$interval'), 10);
    const query: any = {
      level: this.props.options.level.map((item: any) => item.value),
      limit: this.props.options.limit,
      start,
      end,
      interval,
    };
    return query;
  };

  updateLogsData = (query: object) => {
    if (this.ws.readyState) {
      this.ws.send(JSON.stringify(query));
    }
  };

  componentWillUnmount() {
    this.ws.send('CLOSE');
    this.ws.close(1000, 'Client Initiated Connection Termination');
  }

  render() {
    const { options } = this.props;
    return (
      <ThemeContext.Consumer>
        {theme => {
          return (
            <Fragment>
              <LogLayout options={{ ...options, data: this.state.data }} theme={theme} />
              <ToastContainer />
            </Fragment>
          );
        }}
      </ThemeContext.Consumer>
    );
  }
}
