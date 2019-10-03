import React, { PureComponent } from "react";
import { PanelProps } from "@grafana/ui";
import { Options } from "../types";
import { MFCLayout } from "./MFCLayout";
import socketIOClient from "socket.io-client";

interface Props extends PanelProps<Options> {}

interface State {
    options: {
        flow_rate: number;
        set_point: number;
    };
}

export class MFCPanel extends PureComponent<Props, State> {
    state = {options: this.props.options};


    componentDidMount() {
        const url = 'http://localhost:5001';
        const socket = socketIOClient(url);

        socket.on('update', (data) => {
            this.setState({options: data}, () => console.log(this.state.options));
        });

        setInterval(() => {
            socket.emit('update')
        }, 1000 )
    }




    render() {
    console.log('render');

    return (
        <div>
          <MFCLayout options={this.state.options}/>
        </div>
    );
  }
}
