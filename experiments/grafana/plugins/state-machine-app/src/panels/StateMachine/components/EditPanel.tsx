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
        // this.handleBankInputChange = this.handleBankInputChange.bind(this)
    }
    //Make Rows based on Banks Available
    //ex: Bank Panel 1 then input box to change name
    banks: any;
    bank_list:  any;

    makeEditRow = () => {
        let edit_list = [];
        this.bank_list = [];
        //let banks_list = [];
        this.banks = this.props.uistatus.bank;
        for (let key in this.banks) {
            let value = this.banks[key];
            if (value === "READY") {
                this.bank_list.push(key);
                edit_list.push(
                    <div className="gf-form-group">
                        <div className="row">
                            <label className="edit-label"> Bank {key}</label>
                            <input name={"bank" + key} className="col-sm-6 edit-panel"  type="text"
                            onChange={(e) => console.log('')}
                                   defaultValue={this.state.plan.bank_names[key].name}
                            maxLength={14}/>
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 1 </label>
                            <input name={"bank" + key + "1"} className="col-sm-6 edit-panel" type="text"
                                   onChange={(e) => console.log('')}
                                   defaultValue={this.state.plan.bank_names[key].channels[1]}
                                   maxLength={8}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 2 </label>
                            <input name={"bank" + key + "2"} className="col-sm-6 edit-panel" type="text" defaultValue={this.state.plan.bank_names[key].channels[2]}
                                   onChange={(e) => console.log('')}
                                   maxLength={8}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 3 </label>
                            <input name={"bank" + key + "3"} className="col-sm-6 edit-panel" type="text" defaultValue={this.state.plan.bank_names[key].channels[3]}
                                   onChange={(e) => console.log('')}
                                   maxLength={8}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 4 </label>
                            <input name={"bank" + key + "4"} className="col-sm-6 edit-panel" type="text" defaultValue={this.state.plan.bank_names[key].channels[4]}
                                   onChange={(e) => console.log('')}
                                   maxLength={8}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 5 </label>
                            <input name={"bank" + key + "5"} className="col-sm-6 edit-panel"  type="text" defaultValue={this.state.plan.bank_names[key].channels[5]}
                                   onChange={(e) => console.log('')}
                                   maxLength={8}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 6 </label>
                            <input name={"bank" + key + "6"} className="col-sm-6 edit-panel"  type="text" defaultValue={this.state.plan.bank_names[key].channels[6]}
                                   onChange={(e) => console.log('')}
                                   maxLength={8}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label"> Channel 7 </label>
                            <input name={"bank" + key + "7"} className="col-sm-6 edit-panel"  type="text" defaultValue={this.state.plan.bank_names[key].channels[7]}
                                   onChange={(e) => console.log('yo')}
                                   maxLength={8}
                            />
                        </div>
                        <div className="row">
                            <label className="edit-label" > Channel 8 </label>
                            <input name={"bank" + key + "8"} className="col-sm-6 edit-panel" type="text" defaultValue={this.state.plan.bank_names[key].channels[8]}
                                   onChange={(e) => console.log('yo')}

                                // onChange={(e) => this.handleChannelChange(e, key, 8)}
                                   maxLength={8}
                            />
                        </div>
                    </div>
                );
            }
        }
        return (
            <div className="panel-plan-inner">
                {edit_list}
            </div>
        );
    };

    handleSubmit = (event) => {
        event.preventDefault();
        let bankName, bankValue;
        const targets = event.target;
        const length = targets.length;
        for (let key in this.bank_list) {
            let bankNum = this.bank_list[key]
            bankName = "bank" + bankNum;
            bankValue = targets[bankName].value;
            const { bank_names } = {...this.state.plan};
            const currentName = bank_names[bankNum];
            currentName.name = bankValue;
            this.setState({...this.state.plan.bank_names, [bankNum]: {name: bankValue}});
            console.log(bankName, " changed");
            const {channels} = {...this.state.plan.bank_names[bankNum]};
            const currentNames = channels;
            for (let i = 1; i < 9; i++){
                const chanName = bankName + i;
                const chanValue = targets[chanName].value;
                currentNames[i] = chanValue;
                this.setState({...this.state.plan.bank_names[bankNum].channels, [i]: chanValue});
                console.log(chanName, " changed");

            }
        }
        console.log(this.state.plan.bank_names);
        const channels1 = this.state.plan.bank_names[1].channels;
        const channels2 = this.state.plan.bank_names[2].channels;
        const channels3 = this.state.plan.bank_names[3].channels;
        const channels4 = this.state.plan.bank_names[4].channels;
        this.props.ws_sender(
            {element: "edit_save",
                bank_names: {
                    1: {name: this.state.plan.bank_names[1].name, channels: channels1},
                    2: {name: this.state.plan.bank_names[2].name, channels: channels2},
                    3: {name: this.state.plan.bank_names[3].name, channels: channels3},
                    4: {name: this.state.plan.bank_names[4].name, channels: channels4}
                }
            });
    };
    render() {



        return (
                <div className="panel-edit">
                        <h2 style={{color: "white"}}>Edit Bank & Channel Names</h2>
                    <form onSubmit={this.handleSubmit} >
                            {this.makeEditRow()}
                    <div className="row text-center button-edit" style={{marginTop: "10px", marginBottom: "10px", alignContent: "center"}}>
                        <div className="col-sm-4">
                            <button type="submit"
                                    className={"btn btn-block btn-green btn-edit-panel"}  >

                                Ok
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => {
                                        this.props.ws_sender({element: "edit_cancel"});
                                    }}
                                    className={"btn btn-block btn-cancel btn-edit-panel"}>
                                Cancel
                            </button>
                        </div>
                    </div>
                    </form>
            </div>
        );
    }
}

export default EditPanel;
