import React, {Component} from 'react';
import PanelPropsOptions from '@grafana/ui';
import './button.css';

export default class ButtonLayout extends Component<any, any> {
    render() {
        const from  = this.props.timeRange.raw.from;
        const to  = this.props.timeRange.raw.to;
        // const to = "now";
        // const from = "now-15m"
        return (
            <div className="row-test">
              <div className="btn-container">
                      <div className="btn-label-container" style={{gridColumnStart: 1, gridColumnEnd: 2}}>
                          <h4>Flow Setup</h4>
                          <a className="btn-panel-link btn-sampler" href={"/d/xemz2IvWk/sampler-setup?from=" + from + "&to=" + to}></a>
                      </div>
                      <div className="btn-label-container">
                          <h4>Analyzer Output Graphs</h4>
                          <a className="btn-panel-link btn-analyzer" href={"/d/rHPC-eKZz/analyzer-output-graphs?from=" + from + "&to=" + to}></a>
                      </div>
                      <div className="btn-label-container " style={{gridColumnStart: 1, gridColumnEnd: 2}}>
                          <h4>Concentration By Channel</h4>
                          <a className="btn-panel-link btn-valve-graphs" href={"/d/GTo10zcZz/concentration-by-valve?from=" +from + "&to=" + to}></a>
                      </div>
                      {/*<div className="btn-label-container ">*/}
                      {/*    <h4>Data Tables</h4>*/}
                      {/*    <a className="btn-panel-link btn-tables" href={"/d/1iflIi5Wz/summary?from=" + from + "&to=" +  to}></a>*/}
                      {/*</div>*/}
                  <div className="btn-label-container ">
                      <h4>Current Values</h4>
                      <a className="btn-panel-link btn-values" href={"/d/2Luty8cZk/current-values-table?from=" + from + "&to=" + to}></a>
                  </div>
              </div>
            </div>
        );
    }
}
