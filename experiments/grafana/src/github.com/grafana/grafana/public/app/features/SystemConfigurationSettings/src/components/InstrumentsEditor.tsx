import React, { Component  } from 'react';
import { EditorPositionsComponent} from "./EditorPositionsComponent";
import { EditorIntrumentsControls} from "./EditorIntrumentsControls";

import PicarroAPI from "../api/PicarroAPI";
import {
  ISGetInstruments,
  webSocket
 } from '../types';

export class InstrumentsEditor extends Component<any, any>   {
  constructor(props) {
    super(props);
    this.state = {
      slotsCount: 0,
      allInstrumentsData: [],
      socket : webSocket,
    };
  }

  updateIntruments() {
    const newState = { ...this.state };
    PicarroAPI.getRequest(ISGetInstruments).then(response => {
        response.text().then(data => {
            const jsonData = JSON.parse(data);
            newState['allInstrumentsData'] = jsonData;
            this.setState(newState);
        });
    });
  }

  componentDidMount() {
    this.updateIntruments();
    this.state.socket.on('update', () => this.updateIntruments());
  }

  render() {
    let EditorPositionsComponentElement = <div />;
    if (this.state.allInstrumentsData.length>0) {
      EditorPositionsComponentElement = <EditorPositionsComponent
              allInstrumentsData={this.state.allInstrumentsData}
              slotsCount={4}
              />;
    }
    return (
      <div>
        {EditorPositionsComponentElement}
        <EditorIntrumentsControls
        allInstrumentsData={this.state.allInstrumentsData}
        />
      </div>
    );
  }
}
