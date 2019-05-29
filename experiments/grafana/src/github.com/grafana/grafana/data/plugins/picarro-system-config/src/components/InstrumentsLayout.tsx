import React, { Component } from 'react';
import { InstrumentsProps,  ISGetInstruments, webSocket} from '../types';
import {RackPositionsComponent} from './RackPositionsComponent'
import {NewInstrumentsComponent} from './NewInstrumentsComponent'
import {InstrumentViewComponent} from './InstrumentViewComponent'
import PicarroAPI from "../api/PicarroAPI";

interface Props extends InstrumentsProps { };


export class InstrumentsLayout extends Component<Props, any> {
    constructor(props) {
        super(props);
        this.state = {
            allInstrumentsData: this.props.options.allInstrumentsData,
            activeInstrument: "",
            componentID: "InstrumentsSettingsViewApp",
            socket : webSocket
        };
    }
    componentDidMount(): void {
        this.updateIntruments();
        this.state.socket.on('update', () => this.updateIntruments())

    }
    updateIntruments() {
        const newState = { ...this.state };
        PicarroAPI.getRequest(ISGetInstruments).then(response => {
            response.text().then(data => {
                const jsonData = JSON.parse(data);
                newState['allInstrumentsData'] = jsonData
                this.setState(newState);
                // console.log(this.state["allInstrumentsData"])
            });
        });
    }

   setActive(IP){
      for (var i = 0; i < this.state.allInstrumentsData.length; i++) {
            if (IP===this.state.allInstrumentsData[i]["ip"]){
               var activeInstrument = this.state.activeInstrument
               activeInstrument = IP
               this.setState({activeInstrument})
            }
         }
    }

    render() {
        const newInstuments = this.state.allInstrumentsData.filter(
            instrument => instrument.position_in_rack === null)
        const instumentsWithPosition = this.state.allInstrumentsData.filter(
            instrument => instrument.position_in_rack != null)

        const activeInstrument = this.state.activeInstrument===null ? null :
            this.state.allInstrumentsData.filter(instrument => instrument.ip === this.state.activeInstrument)[0]


        return (
            <div>
              <div className="row">
                <div className="column left-column">
                  <div className="container_row">          
                    <div className="InstrumentsListWraper">
                      <div className="RackPositionsComponent">
                        <RackPositionsComponent
                          instrumentsWithPosition={instumentsWithPosition}
                          parent={this}
                          activeInstrument={this.state.activeInstrument}
                          slots_n={4} 
                        />
                      </div>
                          {newInstuments.length>0 
                            &&
                            <div className="NewInstrumentsComponent">
                              <NewInstrumentsComponent 
                                instruments={newInstuments}
                                parent={this}
                                activeInstrument={this.state.activeInstrument}
                              />
                            </div>
                          }
                    </div>
                  </div>
                </div>

                <div className="column right-column">
                  <div className="InstrumentViewWraper">
                    <InstrumentViewComponent 
                      parent={this}
                      activeInstrument={activeInstrument}/>
                  </div>
                </div>


              </div>
            </div>
        )
    }
}
