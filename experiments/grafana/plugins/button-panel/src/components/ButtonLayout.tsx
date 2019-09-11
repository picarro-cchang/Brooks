import React, {Component} from 'react';
import PanelPropsOptions from '@grafana/ui';
import './button.css';

export default class ButtonLayout extends Component<any, any> {
    render() {
        return (
            <div className="row-test">
              <div className="btn-container">
                      <div className="btn-label-container" style={{gridColumnStart: 1, gridColumnEnd: 2}}>
                          <h4>Flow Setup</h4>
                          <a className="btn-panel-link btn-sampler" href="/d/xemz2IvWk"></a>
                      </div>
                      <div className="btn-label-container">
                          <h4>Analyzer Graphs</h4>
                          <a className="btn-panel-link btn-analyzer" href="/d/rHPC-eKZz"></a>
                      </div>
                      <div className="btn-label-container " style={{gridColumnStart: 1, gridColumnEnd: 2}}>
                          <h4>Graphs by Port</h4>
                          <a className="btn-panel-link btn-analyzer" href="/d/GTo10zcZz"></a>
                      </div>
                      <div className="btn-label-container ">
                          <h4>Data Tables</h4>
                          <a className="btn-panel-link btn-tables" href="/d/1iflIi5Wz"></a>
                      </div>
              </div>
            </div>
        );
    }
}
