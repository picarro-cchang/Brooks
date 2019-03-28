import React, { Component } from 'react';
import { NetworkProps } from '../../types';

interface Props extends NetworkProps { }

export class NetworkLayout extends Component<Props, any> {
    constructor(props) {
        super(props);
    }

    render() {
        const { options } = this.props;
        const {
            networkType,
            ip,
            gateway,
            netmask,
            dns
        } = options;

        return (
            <form className="gf-form-group ng-pristine ng-invalid network-grid">
                <div className="gf-form">
                    <span className="gf-form-label width-10">Network Type</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14 ng-not-empty ng-valid ng-valid-required"
                        value={networkType}
                    />
                </div>

                <div className="gf-form">
                    <span className="gf-form-label width-10">IP</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        value={ip}
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">Gateway</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={gateway}
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">Netmask</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={netmask}
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">DNS</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={dns}
                    />
                </div>
            </form>

        );
    }
}
