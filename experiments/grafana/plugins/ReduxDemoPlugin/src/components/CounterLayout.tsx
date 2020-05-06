import React, { Component, Fragment } from 'react';
import Counter from './Counter';
import { CounterProps } from './types';
import counter from './../reducers';

interface Props extends CounterProps { }
// const store = createStore(counter)
const store = {
  dispatch: function (obj) {
    console.log('h');
  },
  getState: function () {
    return 1;
  }
}

export class CounterLayout extends Component<Props, any> {
  constructor(props: any) {
    super(props);
    this.state = {
      count: this.props.options.count
    }
    this.handleClick = this.handleClick.bind(this);
  }

  handleClick(e) {
    this.setState({ count: this.state.count + 1 });
  }

  render() {
    const styleObj = {
      overflow: 'scroll',
      height: 'inherit',
    };

    return (
      <Fragment>
        <h3 className="text-center">
          Counter
        </h3>
        {/* <div className="container-fluid" style={styleObj}>
          <div className="row">{this.state.count}</div>
          <div className="row"><button className="btn btn-primary" onClick={this.handleClick}>+1</button></div>
        </div> */}
        <Counter
          value={store.getState()}
          onIncrement={() => store.dispatch({ type: 'INCREMENT' })}
          onDecrement={() => store.dispatch({ type: 'DECREMENT' })}
        />
      </Fragment>
    );
  }
}
