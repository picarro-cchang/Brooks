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
                          <a className="btn-panel-link btn-analyzer" href="/d/0C5NddvZk"></a>
                      </div>
                      <div className="btn-label-container " style={{gridColumnStart: 1, gridColumnEnd: 2}}>
                          <h4>Graphs by Port</h4>
                          <a className="btn-panel-link btn-valve-graphs" href="/d/pV3XhcDWz"></a>
                      </div>
                      <div className="btn-label-container ">
                          <h4>Data Tables</h4>
                          <a className="btn-panel-link btn-tables" href="/d/vCQ3IOvWk"></a>
                      </div>
              </div>
            </div>
        );
    }
}
