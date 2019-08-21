import React, {Component, PureComponent, ReactText} from 'react';
import { EditPanelOptions } from "../types";
import ReactList from 'react-list';



class EditPanel extends PureComponent<EditPanelOptions> {

    //Make Rows based on Banks Available
    //ex: Bank Panel 1 then input box to change name
    banks: any;

    makeEditRow = () => {
        let edit_list = [];

        //  const test = this.props.uistatus;
        this.banks = this.props.uistatus.bank;
        // console.log(banks)
        for (let key in this.banks) {
            let value = this.banks[key];
            if (value === "READY") {
                edit_list.push(
                    <div className="gf-form-group">
                        <div className="row">
                            <label style={{marginLeft: 20, marginRight: 10, fontSize: 15}}> Bank {key}</label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 1 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 1"}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 2 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 2"}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 3 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 3"}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 4 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 4"}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 5 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 5"}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 6 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 6"}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 7 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 7"}/>
                        </div>
                        <div className="row">
                            <label style={{marginLeft: 30, marginRight: 10, fontSize: 15}}> Channel 8 </label>
                            <input className="col-sm-6" style={{
                                color: "black",
                                background: "white",
                                border: "1px solid black",
                                borderRadius: 2,
                            }} type="text" value={"Bank " + key + ", Channel 8"}/>
                        </div>
                    </div>
                )
            }
        }
        return (
            <div>
                {edit_list}
            </div>
        );
    };

    renderItem = () => <div>{this.makeEditRow()}</div>;

    render() {

        return (
                <div className="panel-plan" style={{ height: 550, backgroundColor: "#888", padding: 10, border: "3px solid #111", borderRadius: 7 }}>
                    <h2 style={{color: "white"}}>Edit Bank & Channel Names</h2>
                    <div style={{overflowX: "hidden", overflowY: "auto", maxHeight:440, borderRadius: 3}}>
                        <form>
                            <ReactList
                                itemRenderer={this.renderItem}
                                length={1}
                                type={"uniform"}
                            />
                        </form>
                    </div>
                <div className="row text-center" style={{marginTop: "10px", marginBottom: "10px"}}>
                    <div className="col-sm-4">
                        <button type="button"
                                className={"btn btn-block btn-success"}  style={{ marginBottom: 10,  width: 95, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                            Save
                        </button>
                    </div>
                    <div className="col-sm-4">
                        <button type="button"
                                onClick={(e) => this.props.switches(0)}
                                className={"btn btn-block btn-danger"} style={{ marginBottom: 10,  width: 95, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}

export default EditPanel;
