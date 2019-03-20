import React, { PureComponent } from 'react';
import {
    PanelProps,
    ThemeContext,
} from '@grafana/ui';

import { SimpleOptions } from '../types';
import { SimpleLayout } from './Simple/SimpleLayout';

interface Props extends PanelProps<SimpleOptions> { }

export class SimplePanel extends PureComponent<Props> {
    render() {
        console.log("SimplePanel props", this.props);
        const {
            options,
            width,
            height,
            onInterpolate,
        } = this.props;

        return (
            <ThemeContext.Consumer>
                {theme => {
                    return (
                        <SimpleLayout
                            width={width}
                            height={height}
                            options={options}
                            onInterpolate={onInterpolate}
                            theme={theme}
                        />
                    );
                }}
            </ThemeContext.Consumer>
        );
    }
}