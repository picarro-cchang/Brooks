import React, {Component, PureComponent} from 'react';
import { EditPanelOptions } from "../types";


class EditPanel extends PureComponent<EditPanelOptions> {

    //Make Rows based on Banks Available
    //ex: Bank Panel 1 then input box to change name
    banks: any;
    render() {
        let edit_list = [];

      //  const test = this.props.uistatus;
        this.banks = this.props.uistatus.bank;

       // console.log(banks)
        for (let key in this.banks) {
            let value = this.banks[key]
            if (value === "READY") {
                edit_list.push(
                    <div className="gf-form-inline">
                        <h4> Bank {key}</h4>
                        <input  type="text" value={key}/>
                        <br/>
                        <h5> Channel 1 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 1"}/>
                        <h5> Channel 2 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 2"}/>
                        <h5> Channel 3 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 3"}/>
                        <h5> Channel 4 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 4"}/>
                        <h5> Channel 5 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 5"}/>
                        <h5> Channel 6 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 6"}/>
                        <h5> Channel 7 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 7"}/>
                        <h5> Channel 8 </h5>
                        <input style={{color: "black", background: "white"}} type="text" value={"Bank " + key + "Channel 8"}/>
                    </div>
                )
            }
        }
        //console.log(typeof(banks))
       // const banks = JSON.stringify(test['bank'])
      //  console.log(test)
      //   for (let key in test) {
      //       if (key === 'bank') {
      //           value = test[key];
      //       }
      //       // Use `key` and `value`
      //   }


        return (
            <div className="gf-form-inline" style={{backgroundColor: "#888"}}>
                Hello
                {edit_list}
                <div className="row text-center" style={{marginTop: "10px", marginBottom: "10px", marginLeft: -25}}>
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
