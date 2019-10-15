// @ts-ignore
import React, {Component, PureComponent, ReactText} from 'react';
import ReactList from 'react-list';
import {Plan, PlanSavePanelOptions} from './../types';

class PlanSavePanel extends PureComponent<PlanSavePanelOptions> {
    renderItem = (index: number, key: ReactText) => (
        <div className="container" style={{paddingTop: "5px"}} key={key}>
            <div className="btn-group d-flex" style={{marginLeft: "0px"}}>
                <button type="button" className="btn btn-light w-100 btn-small"
                        onClick={e => this.props.ws_sender({element: "plan_save_filename",
                            name: this.props.plan.plan_files[index+1]})}
                style={{color: "black"}}>
                    {this.props.plan.plan_files[index+1]}
                </button>
                <button type="button" className="btn btn-danger btn-small"
                        onClick={e => this.props.ws_sender({element: "plan_delete_filename",
                            name: this.props.plan.plan_files[index+1]})}>X
                </button>
            </div>
        </div>)
    render() {
        return (
            <div className="panel-save" >
                <h2 style={{color: 'white'}}>Save Plan</h2>
                <div className="panel-save-inner">
                    <form>
                        <ReactList
                            itemRenderer={this.renderItem}
                            length={this.props.plan.num_plan_files}
                            type={"uniform"}
                        />
                    </form>
                </div>
                <div className="col-sm-12"  style={{marginTop: "20px"}}>
                    <input onChange={(e) => this.props.ws_sender({element: "plan_save_filename", name: e.target.value})}
                           value={this.props.plan.plan_filename} type="text" className="form-control input-large"
                           style={{ backgroundColor: 'white', borderRadius: 3, color: 'black', height: 35}}
                           placeholder="Filename (without extension)" />
                </div>

                <div className="container" style={{marginTop: "20px"}}>
                    <div className="text-center">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_save_cancel"})}
                                    className={"btn btn-group-2 btn-cancel"}>
                                Cancel
                            </button>
                            <button type="button"
                                    onClick={e => {
                                        this.props.updateFileName(false);
                                        this.props.ws_sender({element: "plan_save_ok"});
                                    }}
                                    className={"btn btn-group-2 btn-green"}>
                                OK
                            </button>

                    </div>
                </div>

            </div>
        );
    }
}

export default PlanSavePanel;
