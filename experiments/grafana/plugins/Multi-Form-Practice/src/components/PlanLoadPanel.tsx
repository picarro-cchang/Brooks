import React, {Component, PureComponent, ReactText} from 'react';
import ReactList from 'react-list';
import {Plan, PlanLoadPanelOptions} from './../types';

class PlanLoadPanel extends PureComponent<PlanLoadPanelOptions> {
    renderItem = (index: number, key: ReactText) => (
        <div className="container" style={{paddingTop: "5px"}} key={key}>
            <div className="btn-group d-flex">
                <button type="button" className="btn btn-light w-100 btn-small"
                        onClick={e => this.props.ws_sender({element: "plan_load_filename",
                            name: this.props.plan.plan_files[index+1]})}>
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
            <div className="panel-plan" style={{marginTop: 10, backgroundColor: "#ccc", padding: 10, border: "3px solid #111", borderRadius: 10}}>
                <h2 style={{ color: 'black'}}>Load Plan</h2>
                <div style={{overflowX: "hidden", overflowY: "auto", maxHeight:520}}>
                    <form>
                        <ReactList
                            itemRenderer={this.renderItem}
                            length={this.props.plan.num_plan_files}
                            type={"uniform"}
                        />
                    </form>
                </div>
                <div className="container" style={{marginTop: "20px"}}>
                    <div className="row text-center">
                        <div className="col-sm-12">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_load_cancel"})}
                                    className={"btn btn-block btn-xlarge btn-danger"}>
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        );
    }
}

export default PlanLoadPanel;
