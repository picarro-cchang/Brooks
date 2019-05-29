import React from 'react';
import { ValvePanelOptions } from '../types';
import { PanelProps, ThemeContext } from '@grafana/ui';
import store from '../store';
import RadioButtons from './RadioButtons';
import { setValveMode } from '../actions/valveActions';

interface Props extends PanelProps<ValvePanelOptions> {}
interface ValvePanelState {
  valveMode: number;
}

export default class ValvePanel extends React.Component<
  Props,
  ValvePanelState
> {
  unsubscribe: () => void;
  state: ValvePanelState = { valveMode: -1 };

  componentWillMount() {
    this.unsubscribe = store.subscribe(() => {
      this.setState({ ...store.getState().valve });
    });
  }

  componentWillUnmount() {
    if (this.unsubscribe) this.unsubscribe();
  }

  render() {
    console.log('ValvePanel props', this.props);
    const { options } = this.props;
    const { numberOfValves, buttonsPerRow } = options;
    const data = [{ value: -1, text: 'Scan' }];

    for (let i = 0; i < numberOfValves; i++) {
      data.push({ value: i, text: 'Valve ' + i.toString() });
    }

    return (
      <ThemeContext.Consumer>
        {theme => {
          return (
            <div>
              <div
                style={{
                  display: 'flex',
                  width: '100%',
                  height: '100%',
                  flexDirection: 'column',
                }}
              >
                <RadioButtons
                  name="opt"
                  data={data}
                  perRow={buttonsPerRow}
                  valueField={'value'}
                  textField={'text'}
                  selectedValue={this.state.valveMode.toString()}
                  onChange={(sel: any) =>
                    store.dispatch(setValveMode(Number(sel.selectedValue)))
                  }
                />
              </div>
            </div>
          );
        }}
      </ThemeContext.Consumer>
    );
  }
}
