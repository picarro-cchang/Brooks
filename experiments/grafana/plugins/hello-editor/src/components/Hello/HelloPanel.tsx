import React, { PureComponent } from 'react';
import {
    PanelProps,
    ThemeContext,
} from '@grafana/ui';

import { HelloOptions } from '../../types';
import { HelloLayout } from './HelloLayout';

interface Props extends PanelProps<HelloOptions> { }

export class HelloPanel extends PureComponent<Props> {
    render() {
        const {
            options
        } = this.props;

        return (
            <ThemeContext.Consumer>
                {theme => {
                    return (
                        <HelloLayout
                            options={options}
                            theme={theme} />
                    );
                }}
            </ThemeContext.Consumer>
        );
    }
}
