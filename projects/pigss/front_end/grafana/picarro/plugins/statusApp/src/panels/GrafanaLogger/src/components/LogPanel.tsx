import React, { PureComponent, Fragment } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { toast } from 'react-toastify';

import { notifyError, notifySuccess } from '../utils/Notifications';
import { LogProps } from './types';
import { LogLayout } from './LogLayout';
import { LOG_LIMIT, REFRESH_INTERVAL, storageKey } from '../constants';
import { SocketURL } from '../constants';
import { LogService } from '..//services/LogService';

interface Props extends PanelProps<LogProps> { }

interface State {
  data: string[][];
  query: object;
  interval: number;
  timeRange: number;
  ws: WebSocket;
}

interface picarroStorage {
  logState: State;
  logProps: Props;
}

export class LogPanel extends PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);
    const rangeFromProps = this.props.data.request.range;
    // @ts-ignore
    const defaultTimeRange = Math.floor((rangeFromProps.to._d.getTime() - rangeFromProps.from._d.getTime()) / 60);
    this.state = {
      data: [],
      query: {},
      interval: this.getInterval(),
      timeRange: defaultTimeRange,
      ws: null
    };
  }

  getPicarroStorage = () => {
    // get picarroStorage object from sessionStorage
    if (window.sessionStorage) {
      return sessionStorage.getItem(storageKey);
    }
    return null;
  }

  setPicarroStorage = (logStorage: picarroStorage) => {
    // set picarroStorage object in sessionStorage
    if (window.sessionStorage) {
      sessionStorage.setItem(storageKey, JSON.stringify(logStorage));
    }
  }

  getInterval = () => {
    let interval = REFRESH_INTERVAL;
    try {
      window.location.search.split("&").forEach(entry => {
        if (entry.indexOf("refresh") !== -1) {
          interval = parseInt(entry.split("=")[1].slice(0, -1));
        }
      });
    } catch (error) {
    } finally {
      return interval;
    }
  }

  getQueryObj = (props: any, initial: boolean = false) => {
    /* 
    ** Removing @ts-ignore gives build err, as it thinks properties "probably" doesn't exist. 
    */
    // @ts-ignore
    const start = new Date(this.props.data.request.range.from).getTime();
    // @ts-ignore
    const end = new Date(this.props.data.request.range.to).getTime();
    // @ts-ignore
    const interval = this.getInterval();
    const rowid = this.state.data.length ? this.state.data[0][0] : -1;
    const limit = initial ? LOG_LIMIT : this.props.options.limit;
    const query: any = {
      rowid,
      level: this.props.options.level.map((item: any) => item.value),
      limit,
      start,
      end,
      interval,
    };
    return query;
  }

  getLogsData = (queryObj) => {
    return LogService.getLogs(queryObj).then((response: any) => { return response.json(); });
  }

  updateLogsData = (query: object) => {
    if (this.state.ws.readyState === 1) {
      this.state.ws.send(JSON.stringify(query));
    }
  }

  setupWSComm = () => {
    const ws: WebSocket = new WebSocket(SocketURL);
    this.setState(() => { return { ws } });

    ws.onopen = () => {
      notifySuccess("Websocket connection established. Logs will be updated soon.");
      const queryObj = this.getQueryObj(this.props);
      this.updateLogsData(queryObj);
    };

    ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      const rows = JSON.parse(evt.data).reverse();
      // Remove the previous logs data on front-end, if the rows are more than LOG_LIMIT.
      if (this.state.data.length > LOG_LIMIT) {
        this.setState({ data: [] });
      }
      this.setPicarroStorage({ logProps: this.props, logState: { ...this.state, data: [...rows, ...this.state.data] } });
      this.setState(() => { return { data: [...rows, ...this.state.data] } });
    };

    ws.onclose = () => {
      toast.dismiss();
      setTimeout(() => {
        notifyError("Websocket connection closed. Trying to reconnect again.");
        this.setupWSComm();
      }, this.state.interval);
    };
  }

  componentDidMount() {
    const savedData = this.getPicarroStorage();
    if (savedData !== null) {
      this.setState(() => {
        return {
          ...JSON.parse(savedData).logState
        }
      });
      this.setupWSComm();
    } else {
      this.getLogsData(this.getQueryObj(this.props, true)).then((data: any) => {
        this.setState(() => { return { data, ws: new WebSocket(SocketURL) } });
        this.setPicarroStorage({ logProps: this.props, logState: this.state });
        this.setupWSComm();
      });
    }
  }

  componentDidUpdate(prevProps: Props, prevState: State) {
    const interval = this.getInterval();
    const rangeFromProps = this.props.data.request.range;
    const rangeFromPrevProps = prevProps.data.request.range;
    // @ts-ignore
    const isDateTimeFromChanged = rangeFromProps.from._d.getTime() !== rangeFromPrevProps.from._d.getTime();
    // @ts-ignore
    const isDateTimeToChanged = rangeFromProps.to._d.getTime() !== rangeFromPrevProps.to._d.getTime();
    // @ts-ignore
    const currentTimeRange = Math.floor((rangeFromProps.to._d.getTime() - rangeFromProps.from._d.getTime()) / 60);
    if (currentTimeRange !== this.state.timeRange) {
      this.setState({ timeRange: currentTimeRange });
      const queryObj = this.getQueryObj(this.props, true);
      this.getLogsData(queryObj);
    } else if (
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

  componentWillUnmount() {
    // notiffy websocket to stop sending new messages
    this.setPicarroStorage({ logProps: this.props, logState: this.state });
    this.state.ws.send(JSON.stringify({ "message": "CLOSE" }));
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
