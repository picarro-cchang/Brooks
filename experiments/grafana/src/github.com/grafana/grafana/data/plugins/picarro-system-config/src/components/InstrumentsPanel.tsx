import React, { PureComponent } from 'react';
import { PanelProps} from '@grafana/ui';
import { InstrumentsOptions } from '../types';
import { InstrumentsLayout } from './InstrumentsLayout';

interface Props extends PanelProps<InstrumentsOptions> { }

export class InstrumentsPanel extends PureComponent<Props> {
    render() {
        const { options } = this.props;
        return (
            <InstrumentsLayout
                options={options}
                />
        );
    }
}
