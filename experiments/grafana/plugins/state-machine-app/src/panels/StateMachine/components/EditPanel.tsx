import React, {Component, PureComponent, ReactText} from 'react';
import { EditPanelOptions } from "../types";
import ReactList from 'react-list';



class EditPanel extends PureComponent<EditPanelOptions> {

    state = {
        initialized: false,
        modal_info: {
            show: false,
            html: "",
            num_buttons: 0,
            buttons: {}
        },
        uistatus: {},
        plan: {
            bank_names: this.props.plan.bank_names
        }
    };
    constructor(props) {
        super(props);
        this.handleBankInputChange = this.handleBankInputChange.bind(this)
    }
    //Make Rows based on Banks Available
    //ex: Bank Panel 1 then input box to change name
    banks: any;
    handleBankInputChange(event, key) {
        const target = event.target;
        const value = target.value;
        const { bank_names } = { ...this.state.plan };
        const currentNames = bank_names[key];
        currentNames.name = value;

        this.setState({...this.state.plan.bank_names, [key]: { name: value }});
    }

    handleChannelChange(event, key, val) {
        const target = event.target;
        const value = target.value;
        const { channels } = { ...this.state.plan.bank_names[key] };
        const currentName = channels;
        currentName[val] = value;

        this.setState({...this.state.plan.bank_names[key].channels, [val]: value});
    }

    makeEditRow = () => {
        let edit_list = [];

        this.banks = this.props.uistatus.bank;
        for (let key in this.banks) {
            let value = this.banks[key];
            if (value === "READY") {
                edit_list.push(
                    <div className="gf-form-group">
                        <div className="row">
                            <label className="edit-label"> Bank {key}</label>
                            <input name={"bank" + key} className="col-sm-6 edit-panel"  type="text"
                            onChange={(e) => this.handleBankInputChange(e, key)}
                            value={this.state.plan.bank_names[key].name}/>
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 1 </label>
                            <input name={"1"} className="col-sm-6 edit-panel" type="text"
                                   value={this.state.plan.bank_names[key].channels[1]}
                                  onChange={(e) => this.handleChannelChange(e, key, 1)}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 2 </label>
                            <input className="col-sm-6 edit-panel" type="text" value={this.state.plan.bank_names[key].channels[2]}
                                  onChange={(e) => this.handleChannelChange(e, key, 2)}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 3 </label>
                            <input className="col-sm-6 edit-panel" type="text" value={this.state.plan.bank_names[key].channels[3]}
                                  onChange={(e) => this.handleChannelChange(e, key, 3)}
                             />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 4 </label>
                            <input className="col-sm-6 edit-panel" type="text" value={this.state.plan.bank_names[key].channels[4]}
                                   onChange={(e) => this.handleChannelChange(e, key, 4)}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 5 </label>
                            <input className="col-sm-6 edit-panel"  type="text" value={this.state.plan.bank_names[key].channels[5]}
                                   onChange={(e) => this.handleChannelChange(e, key, 5)}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 6 </label>
                            <input className="col-sm-6 edit-panel"  type="text" value={this.state.plan.bank_names[key].channels[6]}
                                  onChange={(e) => this.handleChannelChange(e, key, 6)}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 7 </label>
                            <input className="col-sm-6 edit-panel"  type="text" value={this.state.plan.bank_names[key].channels[7]}
                                   onChange={(e) => this.handleChannelChange(e, key, 7)}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label" > Channel 8 </label>
                            <input className="col-sm-6 edit-panel" type="text" value={this.state.plan.bank_names[key].channels[8]}
                                   onChange={(e) => this.handleChannelChange(e, key, 8)}
                            />
                        </div>
                    </div>
                );
            }
        }

        return (
            <div>
                {edit_list}
            </div>
        );
    };

    handleClick = (e) => {
        e.preventDefault();
        console.log("hello", e.target)
    };
   renderItem = () => <div>{this.makeEditRow()}</div>;

    render() {
        const channels1 = this.state.plan.bank_names[1].channels;
        const channels2 = this.state.plan.bank_names[2].channels;
        const channels3 = this.state.plan.bank_names[3].channels;
        const channels4 = this.state.plan.bank_names[4].channels;


        return (
                <div className="panel-edit">
                        <h2 style={{color: "white"}}>Edit Bank & Channel Names</h2>
                        <div className="panel-plan-inner">
                                <ReactList
                                    itemRenderer={this.renderItem}
                                    length={1}
                                    type={"uniform"}
                                    name="reactlist"
                                    value={this.state.plan.bank_names}
                                />

                        </div>
                    <div className="row text-center button-edit" style={{marginTop: "10px", marginBottom: "10px", alignContent: "center"}}>
                        <div className="col-sm-4">
                            <button type="submit"
                                //onClick = {this.handleClick}
                                    onClick={(e) => {this.props.ws_sender(
                                        {element: "edit_save",
                                            bank_names: {
                                                1: {name: this.state.plan.bank_names[1].name, channels: channels1},
                                                2: {name: this.state.plan.bank_names[2].name, channels: channels2},
                                                3: {name: this.state.plan.bank_names[3].name, channels: channels3},
                                                4: {name: this.state.plan.bank_names[4].name, channels: channels4}
                                            }
                                        }); console.log("ehhlo")}}
                                    className={"btn btn-block btn-success btn-edit-panel"}  >
                                Ok
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "edit_cancel"})}
                                    className={"btn btn-block btn-danger btn-edit-panel"}>
                                Cancel
                            </button>
                        </div>
                    </div>

            </div>
        );
    }
}

export default EditPanel;
