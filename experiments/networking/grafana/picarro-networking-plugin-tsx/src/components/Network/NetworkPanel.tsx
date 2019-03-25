import React, { PureComponent } from 'react';
import {
    PanelProps,
    ThemeContext,
} from '@grafana/ui';

import { NetworkOptions } from '../../types';
import { NetworkLayout } from './NetworkLayout';

interface Props extends PanelProps<NetworkOptions> { }

export class NetworkPanel extends PureComponent<Props> {
    render() {
        const {
            options
        } = this.props;

        return (
            <ThemeContext.Consumer>
                {theme => {
                    return (
                        <NetworkLayout
                            options={options}
                            theme={theme} />
                    );
                }}
            </ThemeContext.Consumer>
        );
    }
}
