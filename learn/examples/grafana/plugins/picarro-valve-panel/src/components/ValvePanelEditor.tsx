// Libraries
import React, { PureComponent } from 'react';

// Components
import { PanelOptionsGroup, PanelEditorProps, Select, SelectOptionItem } from '@grafana/ui';

// Types
import { FormField } from '@grafana/ui';
import { ValvePanelOptions } from '../types';

export class ValvePanelEditor extends PureComponent<PanelEditorProps<ValvePanelOptions>> 
{
    buttonsPerRowOptions: SelectOptionItem[] = [
        {value: 1, label: '1'},
        {value: 2, label: '2'},
        {value: 3, label: '3'},
        {value: 4, label: '4'},
        {value: 5, label: '5'},
        {value: 6, label: '6'},
        {value: 7, label: '7'},
        {value: 8, label: '8'},
        {value: 9, label: '9'},
        {value: 10, label: '10'},
    ];

    labelWidth = 12;

    onNumberOfValvesChange = ({ target }) =>
        this.props.onChange({ ...this.props.options, numberOfValves: Number(target.value) });

    onButtonsPerRowChange = ( item: SelectOptionItem ) =>
        {
            return this.props.onChange({ ...this.props.options, buttonsPerRow: Number(item.value) });
        };

    render() {
        const { options } = this.props;
        const {
            numberOfValves,
            buttonsPerRow
        } = options;
    
        return (
            <PanelOptionsGroup title="Valve panel options">
                <FormField
                    label="Number of valves"
                    labelWidth={this.labelWidth}
                    onChange={this.onNumberOfValvesChange}
                    value={numberOfValves}
                />
                <div className="gf-form-inline">
                    <div className="gf-form">
                        <span className="gf-form-label width-12">Buttons per row</span>
                        <Select
                            onChange={this.onButtonsPerRowChange}
                            value={this.buttonsPerRowOptions.find(e => buttonsPerRow === e.value)}
                            options={this.buttonsPerRowOptions}
                        />
                    </div>
                </div>
            </PanelOptionsGroup>
        );
    }
}