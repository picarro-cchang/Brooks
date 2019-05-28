import React, { PureComponent } from 'react';
import {
  // NullValueMode,
  PanelProps,
  // processTimeSeries,
  ThemeContext,
} from '@grafana/ui';

import { SimpleOptions } from '../types';
import { SimpleLayout } from './Simple/SimpleLayout';

interface Props extends PanelProps<SimpleOptions> {}

export class SimplePanel extends PureComponent<Props> {
  render() {
    console.log('SimplePanel props', this.props);
    // console.log("panelData", this.props.panelData);
    const {
      options,
      // panelData,
      timeRange,
      width,
      height,
      onInterpolate,
    } = this.props;

    return (
      <ThemeContext.Consumer>
        {theme => {
          return (
            <SimpleLayout
              timeRange={timeRange}
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

    /* 
        if (panelData.timeSeries) {
            const timeSeries = processTimeSeries({
                timeSeries: panelData.timeSeries,
                nullValueMode: NullValueMode.Null,
            });
            console.log("timeSeries", timeSeries);

            return (
                <ThemeContext.Consumer>
                    {theme => {
                        return (
                            <SimpleLayout
                                timeSeries={timeSeries}
                                timeRange={timeRange}
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
        } else {
            return <div>Panel needs time series data</div>;
        }
        */
  }
}
