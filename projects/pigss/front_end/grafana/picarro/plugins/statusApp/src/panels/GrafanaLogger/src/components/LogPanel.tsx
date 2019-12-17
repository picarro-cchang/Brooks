import React, { PureComponent, Fragment } from 'react';
import { PanelProps, ThemeContext } from '@grafana/ui';
import { dateMath } from '@grafana/data';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { toast } from 'react-toastify';

import { notifyError } from '../utils/Notifications';
import { LogProps } from './types';
import { LogLayout } from './LogLayout';
import { LOG_LIMIT, REFRESH_INTERVAL, storageKey } from '../constants';
import { SocketURL } from '../constants';
import { LogService } from '..//services/LogService';

interface Props extends PanelProps<LogProps> { }

interface State {
  data?: string[][];
  query?: object;
  interval?: number;
  timeRange?: number;
  ws?: WebSocket;
}

interface picarroStorage {
  logState: State;
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
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(logStorage));
      } catch (error) {
        this.clearPicarroStorage();
      }
    }
  }

  clearPicarroStorage = () => {
    sessionStorage.removeItem(storageKey);
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
    const rowid = initial ? -1 : this.state.data.length ? this.state.data[0][0] : -1;
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
    if (this.state.ws && this.state.ws.readyState === 1) {
      this.state.ws.send(JSON.stringify(query));
    }
  }

  filterLogs = (logs: any, from?: Date) => {
    return logs.filter((elem) => {
      return new Date(elem[1]) >= from;
    });
  }

  setupWSComm = () => {
    const ws: WebSocket = new WebSocket(SocketURL);
    this.setState(() => { return { ws } });

    ws.onopen = () => {
      const queryObj = this.getQueryObj(this.props);
      this.updateLogsData(queryObj);
    };

    ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      const rows = JSON.parse(evt.data).reverse();
      let logs = [...rows, ...this.state.data];
      if (this.state.data.length > 0) {
        // filter messages from front-end that doesn't fall in the timerange
        // @ts-ignore
        const fromDate = new Date(dateMath.parse(this.props.data.request.range.raw.from));
        this.setState(() => {
          const filteredLogs = this.filterLogs(logs, fromDate);
          this.setPicarroStorage({ logState: { ...this.state, ws: ws, data: [...logs, ...this.state.data] } });
          return { data: filteredLogs };
        });
      } else {
        this.setState(() => { return { data: logs } });
        this.setPicarroStorage({ logState: { ...this.state, ws: ws, data: [...logs, ...this.state.data] } });
      }
      // Remove the previous logs data on front-end, if the rows are more than LOG_LIMIT.
      if (this.state.data.length > LOG_LIMIT) {
        this.state.data.length = LOG_LIMIT;
      }
    };

    ws.onclose = (event) => {
      toast.dismiss();
      setTimeout(() => {
        // If client did not initiated close event, spawn a new websocket connection
        if (event.code !== 1000) {
          setTimeout(() => notifyError("Websocket connection closed. Trying to reconnect again."), this.state.interval * 1000);
          this.setupWSComm();
        }
      }, this.state.interval * 1000);
    };
  }

  getStateFromSavedData = () => {
    const savedData = this.getPicarroStorage();
    if (savedData !== null) {
      return { ...(JSON.parse(savedData).logState) };
    }
    return null;
  }

  isSavedDataCurrent = (fromTime: Date, logState: State) => {
    if (logState !== null && logState.data !== undefined) {
      return logState.data.length ? new Date(logState.data[logState.data.length - 1][1]) <= fromTime : false;
    }
    return false;
  }

  componentDidMount() {
    // @ts-ignore
    const fromTime = new Date(dateMath.parse(this.props.data.request.range.raw.from));
    const logState = { ...this.getStateFromSavedData() };
    if (this.isSavedDataCurrent(fromTime, logState)) {
      // Filter data according to timeRange
      logState.data = this.filterLogs(logState.data, fromTime)
      this.setState(() => { return { ...logState } });
    } else {
      this.getLogsData(this.getQueryObj(this.props, true)).then((data: any) => {
        const orderedLogs = data.reverse();
        this.setState(() => {
          return { data: orderedLogs };
        });
        this.setPicarroStorage({ logState: { ...this.state, data: orderedLogs } });
      });
    }
    this.setupWSComm();
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
    if (currentTimeRange !== this.state.timeRange ||
      JSON.stringify(this.props.options.level) !== JSON.stringify(prevProps.options.level)) {
      // @ts-ignore
      const fromTime = new Date(dateMath.parse(this.props.data.request.range.raw.from));
      const logState = { ...this.getStateFromSavedData() };
      if (this.isSavedDataCurrent(fromTime, logState)) {
        // Filter data according to timeRange
        logState.data = this.filterLogs(logState.data, fromTime)
        this.setState(() => { return { ...logState, timeRange: currentTimeRange } });
      } else {
        this.setState({ timeRange: currentTimeRange });
        const queryObj = this.getQueryObj(this.props, true);
        this.getLogsData(queryObj).then((data: any) => {
          const logs = data.reverse();
          this.setState(() => { return { data: logs } });
          this.setPicarroStorage({ logState: { ...this.state, data: logs } });
        });
      }
    } else if (
      this.props.options.limit !== prevProps.options.limit ||
      interval !== this.state.interval ||
      isDateTimeFromChanged ||
      isDateTimeToChanged
    ) {
      this.setState(() => ({ interval }));
    }
    const queryObj = this.getQueryObj(this.props);
    this.updateLogsData(queryObj);
  }

  componentWillUnmount() {
    // notiffy websocket to stop sending new messages
    this.setPicarroStorage({ logState: this.state });
    if (this.state.ws !== null) {
      this.state.ws.send(JSON.stringify({ "message": "CLOSE" }));
      this.state.ws.close(1000, "Normal Closure");
    }
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
